from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from auth import get_current_user
from models import SMSRequest
from utils import send_sms_reminder, twilio_client, TWILIO_PHONE_NUMBER
from pydantic import BaseModel

router = APIRouter()


class MessageTemplateCreate(BaseModel):
    name: str
    text: str
    template_type: str = "appointment"

class MessageTemplateUpdate(BaseModel):
    name: Optional[str] = None
    text: Optional[str] = None


# ============== SMS ==============

@router.post("/sms/send-reminder")
async def send_appointment_reminder(data: SMSRequest, current_user: dict = Depends(get_current_user)):
    appointment = await db.appointments.find_one({"id": data.appointment_id, "user_id": current_user["id"]}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    client = await db.clients.find_one({"id": appointment["client_id"], "user_id": current_user["id"]}, {"_id": 0})
    if not client or not client.get("phone"):
        raise HTTPException(status_code=400, detail="Cliente senza numero di telefono")
    if not client.get("sms_reminder", True):
        raise HTTPException(status_code=400, detail="Cliente ha disabilitato promemoria SMS")
    services_text = ", ".join([s["name"] for s in appointment["services"]])
    default_message = f"Promemoria: hai un appuntamento il {appointment['date']} alle {appointment['time']} per {services_text}. Ti aspettiamo!"
    message = data.message or default_message
    result = await send_sms_reminder(client["phone"], message, current_user["salon_name"])
    if result["success"]:
        await db.appointments.update_one({"id": data.appointment_id}, {"$set": {"sms_sent": True}})
        return {"success": True, "message": "SMS inviato con successo"}
    return {"success": False, "error": result.get("error", "Errore sconosciuto")}


@router.get("/sms/status")
async def get_sms_status(current_user: dict = Depends(get_current_user)):
    return {"configured": twilio_client is not None and TWILIO_PHONE_NUMBER is not None,
            "phone_number": TWILIO_PHONE_NUMBER if TWILIO_PHONE_NUMBER else None}


# ============== REMINDERS / RICHIAMI ==============

@router.get("/reminders/color-expiry")
async def get_color_expiry_reminders(current_user: dict = Depends(get_current_user)):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    color_keywords = ["color", "colore", "tinta", "meche", "balayage", "schiaritu", "colpi di sole"]
    services = await db.services.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(200)
    color_service_ids = [s["id"] for s in services if any(kw in s["name"].lower() for kw in color_keywords)]
    if not color_service_ids:
        return []
    pipeline = [
        {"$match": {"user_id": current_user["id"], "service_ids": {"$in": color_service_ids}, "status": {"$ne": "cancelled"}}},
        {"$sort": {"date": -1}},
        {"$group": {"_id": "$client_id", "last_date": {"$first": "$date"}, "last_services": {"$first": "$services"}, "client_name": {"$first": "$client_name"}}},
        {"$match": {"last_date": {"$lte": cutoff}}}
    ]
    results = await db.appointments.aggregate(pipeline).to_list(100)
    client_ids = [r["_id"] for r in results]
    clients = {c["id"]: c for c in await db.clients.find({"id": {"$in": client_ids}}, {"_id": 0}).to_list(100)}
    sent = await db.reminders_sent.find({"user_id": current_user["id"], "type": "color_expiry"}, {"_id": 0}).to_list(500)
    sent_client_ids = {s["client_id"] for s in sent}
    return [{
        "client_id": r["_id"], "client_name": r["client_name"], "last_color_date": r["last_date"],
        "days_ago": (datetime.now(timezone.utc) - datetime.strptime(r["last_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)).days,
        "phone": clients.get(r["_id"], {}).get("phone", ""), "already_sent": r["_id"] in sent_client_ids
    } for r in results]


@router.post("/reminders/color-expiry/{client_id}/mark-sent")
async def mark_color_reminder_sent(client_id: str, current_user: dict = Depends(get_current_user)):
    await db.reminders_sent.insert_one({
        "id": str(uuid.uuid4()), "user_id": current_user["id"],
        "type": "color_expiry", "client_id": client_id,
        "sent_at": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True}


@router.delete("/reminders/color-expiry/{client_id}/reset")
async def reset_color_reminder(client_id: str, current_user: dict = Depends(get_current_user)):
    await db.reminders_sent.delete_many({"user_id": current_user["id"], "type": "color_expiry", "client_id": client_id})
    return {"success": True}


# ============== MESSAGE TEMPLATES ==============

@router.get("/reminders/templates")
async def get_message_templates(current_user: dict = Depends(get_current_user)):
    templates = await db.message_templates.find({"user_id": current_user["id"]}, {"_id": 0, "user_id": 0}).to_list(50)
    if not templates:
        defaults = [
            {"id": str(uuid.uuid4()), "user_id": current_user["id"], "name": "Promemoria Appuntamento",
             "text": "Ciao {nome}! Ti ricordiamo il tuo appuntamento domani alle {ora} presso MBHS SALON. Servizi: {servizi}. Ti aspettiamo!",
             "template_type": "appointment", "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "user_id": current_user["id"], "name": "Richiamo Cliente Inattivo",
             "text": "Ciao {nome}! Sono passati {giorni} giorni dalla tua ultima visita presso MBHS SALON. Torna a trovarci, ti aspettiamo!",
             "template_type": "recall", "created_at": datetime.now(timezone.utc).isoformat()}
        ]
        for d in defaults:
            await db.message_templates.insert_one(d)
        templates = [{k: v for k, v in d.items() if k not in ("_id", "user_id")} for d in defaults]
    return templates


@router.post("/reminders/templates")
async def create_message_template(data: MessageTemplateCreate, current_user: dict = Depends(get_current_user)):
    template = {
        "id": str(uuid.uuid4()), "user_id": current_user["id"],
        "name": data.name, "text": data.text, "template_type": data.template_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.message_templates.insert_one(template)
    return {k: v for k, v in template.items() if k not in ("_id", "user_id")}


@router.put("/reminders/templates/{template_id}")
async def update_message_template(template_id: str, data: MessageTemplateUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.message_templates.update_one({"id": template_id, "user_id": current_user["id"]}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return await db.message_templates.find_one({"id": template_id}, {"_id": 0, "user_id": 0})


@router.delete("/reminders/templates/{template_id}")
async def delete_message_template(template_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.message_templates.delete_one({"id": template_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return {"success": True}


# ============== TOMORROW REMINDERS ==============

@router.get("/reminders/tomorrow")
async def get_tomorrow_reminders(current_user: dict = Depends(get_current_user)):
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    appointments = await db.appointments.find(
        {"user_id": current_user["id"], "date": tomorrow, "status": {"$ne": "cancelled"}}, {"_id": 0}
    ).to_list(100)
    reminded_ids = set()
    reminders_sent = await db.reminders_sent.find(
        {"user_id": current_user["id"], "type": "appointment", "date": tomorrow}, {"_id": 0}
    ).to_list(500)
    for r in reminders_sent:
        reminded_ids.add(r.get("appointment_id"))
    results = []
    for apt in appointments:
        client_phone = apt.get("client_phone", "")
        if not client_phone and apt.get("client_id"):
            cl = await db.clients.find_one({"id": apt["client_id"]}, {"_id": 0})
            if cl:
                client_phone = cl.get("phone", "")
        results.append({
            "id": apt["id"], "client_name": apt.get("client_name", ""),
            "client_phone": client_phone, "client_id": apt.get("client_id", ""),
            "date": apt["date"], "time": apt["time"],
            "services": apt.get("services", []), "operator_name": apt.get("operator_name", ""),
            "reminded": apt["id"] in reminded_ids
        })
    return results


@router.post("/reminders/batch-mark-sent")
async def batch_mark_reminders_sent(data: dict, current_user: dict = Depends(get_current_user)):
    appointment_ids = data.get("appointment_ids", [])
    if not appointment_ids:
        raise HTTPException(status_code=400, detail="Nessun appuntamento specificato")
    count = 0
    for apt_id in appointment_ids:
        apt = await db.appointments.find_one({"id": apt_id, "user_id": current_user["id"]}, {"_id": 0})
        if apt:
            existing = await db.reminders_sent.find_one(
                {"user_id": current_user["id"], "type": "appointment", "appointment_id": apt_id}
            )
            if not existing:
                await db.reminders_sent.insert_one({
                    "id": str(uuid.uuid4()), "user_id": current_user["id"],
                    "type": "appointment", "appointment_id": apt_id,
                    "client_id": apt.get("client_id"), "date": apt["date"],
                    "sent_at": datetime.now(timezone.utc).isoformat()
                })
                count += 1
    return {"success": True, "marked_count": count}


@router.get("/reminders/auto-check")
async def auto_reminder_check(current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    is_reminder_time = now.hour >= 14
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    appointments = await db.appointments.find(
        {"user_id": current_user["id"], "date": tomorrow, "status": {"$ne": "cancelled"}}, {"_id": 0}
    ).to_list(100)
    reminded_ids = set()
    reminders_sent = await db.reminders_sent.find(
        {"user_id": current_user["id"], "type": "appointment", "date": tomorrow}, {"_id": 0}
    ).to_list(500)
    for r in reminders_sent:
        reminded_ids.add(r.get("appointment_id"))
    pending = []
    for apt in appointments:
        if apt["id"] not in reminded_ids:
            client_phone = apt.get("client_phone", "")
            if not client_phone and apt.get("client_id"):
                cl = await db.clients.find_one({"id": apt["client_id"]}, {"_id": 0})
                if cl:
                    client_phone = cl.get("phone", "")
            if client_phone:
                pending.append({
                    "id": apt["id"], "client_name": apt.get("client_name", ""),
                    "client_phone": client_phone, "time": apt["time"], "services": apt.get("services", []),
                })
    return {
        "is_reminder_time": is_reminder_time, "tomorrow_date": tomorrow,
        "total_tomorrow": len(appointments), "already_sent": len(reminded_ids), "pending": pending
    }


@router.post("/reminders/appointment/{appointment_id}/mark-sent")
async def mark_reminder_sent(appointment_id: str, current_user: dict = Depends(get_current_user)):
    apt = await db.appointments.find_one({"id": appointment_id, "user_id": current_user["id"]}, {"_id": 0})
    if not apt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    await db.reminders_sent.insert_one({
        "id": str(uuid.uuid4()), "user_id": current_user["id"],
        "type": "appointment", "appointment_id": appointment_id,
        "client_id": apt.get("client_id"), "date": apt["date"],
        "sent_at": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True}


@router.delete("/reminders/appointment/{appointment_id}/reset")
async def reset_reminder(appointment_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.reminders_sent.delete_many(
        {"user_id": current_user["id"], "type": "appointment", "appointment_id": appointment_id}
    )
    return {"success": True, "deleted": result.deleted_count}


# ============== INACTIVE CLIENTS ==============

@router.get("/reminders/inactive-clients")
async def get_inactive_clients(current_user: dict = Depends(get_current_user)):
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
    clients = await db.clients.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    recent_recalls = await db.reminders_sent.find(
        {"user_id": current_user["id"], "type": "inactive_recall",
         "sent_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}},
        {"_id": 0}
    ).to_list(500)
    recently_recalled_ids = {r.get("client_id") for r in recent_recalls}
    inactive = []
    for client in clients:
        last_apt = await db.appointments.find_one(
            {"client_id": client["id"], "user_id": current_user["id"], "status": "completed"},
            {"_id": 0}, sort=[("date", -1)]
        )
        if last_apt and last_apt["date"] <= cutoff_date:
            days_ago = (datetime.now(timezone.utc) - datetime.strptime(last_apt["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)).days
            inactive.append({
                "client_id": client["id"], "client_name": client["name"],
                "client_phone": client.get("phone", ""), "last_visit": last_apt["date"],
                "days_ago": days_ago, "last_services": [s.get("name", "") for s in last_apt.get("services", [])],
                "already_recalled": client["id"] in recently_recalled_ids
            })
    inactive.sort(key=lambda x: x["days_ago"], reverse=True)
    return inactive


@router.post("/reminders/inactive/{client_id}/mark-sent")
async def mark_inactive_recall_sent(client_id: str, current_user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id, "user_id": current_user["id"]}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    await db.reminders_sent.insert_one({
        "id": str(uuid.uuid4()), "user_id": current_user["id"],
        "type": "inactive_recall", "client_id": client_id,
        "sent_at": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True}


@router.delete("/reminders/inactive/{client_id}/reset")
async def reset_inactive_recall(client_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.reminders_sent.delete_many(
        {"user_id": current_user["id"], "type": "inactive_recall", "client_id": client_id}
    )
    return {"success": True, "deleted": result.deleted_count}
