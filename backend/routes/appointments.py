from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from auth import get_current_user
from models import (
    AppointmentCreate, AppointmentResponse, AppointmentUpdate,
    RecurringAppointmentCreate, CheckoutData, get_loyalty_rewards, LOYALTY_POINTS_PER_EURO
)
from utils import calculate_end_time

router = APIRouter()


# ============== Loyalty helpers (used by checkout) ==============

async def get_or_create_loyalty(client_id: str, user_id: str):
    loyalty = await db.loyalty.find_one({"client_id": client_id, "user_id": user_id}, {"_id": 0})
    if not loyalty:
        loyalty = {
            "id": str(uuid.uuid4()), "client_id": client_id, "user_id": user_id,
            "points": 0, "total_points_earned": 0, "total_points_redeemed": 0,
            "history": [], "active_rewards": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.loyalty.insert_one(loyalty)
        loyalty.pop("_id", None)
    return loyalty


async def award_loyalty_points(client_id: str, user_id: str, amount_paid: float, appointment_id: str):
    points_earned = int(amount_paid // LOYALTY_POINTS_PER_EURO)
    if points_earned <= 0:
        return 0
    loyalty = await get_or_create_loyalty(client_id, user_id)
    history_entry = {
        "id": str(uuid.uuid4()), "type": "earned", "points": points_earned,
        "description": f"+{points_earned} punti per pagamento di €{amount_paid:.2f}",
        "appointment_id": appointment_id, "date": datetime.now(timezone.utc).isoformat()
    }
    await db.loyalty.update_one(
        {"id": loyalty["id"]},
        {"$inc": {"points": points_earned, "total_points_earned": points_earned},
         "$push": {"history": history_entry}}
    )
    return points_earned


# ============== CRUD ==============

@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    client_name = ""
    client_phone = ""
    client_id = data.client_id or ""

    if data.client_id:
        client = await db.clients.find_one({"id": data.client_id, "user_id": current_user["id"]}, {"_id": 0})
        if client:
            client_name = client["name"]
            client_phone = client.get("phone", "")
        else:
            raise HTTPException(status_code=404, detail="Cliente non trovato")
    elif data.client_name:
        client_name = data.client_name
        client_phone = data.client_phone or ""
        if client_name.lower() != "cliente generico":
            new_client_id = str(uuid.uuid4())
            new_client = {
                "id": new_client_id, "user_id": current_user["id"],
                "name": client_name, "phone": client_phone, "notes": "",
                "send_sms_reminders": False, "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.clients.insert_one(new_client)
            client_id = new_client_id
        else:
            client_id = "generic"
    else:
        raise HTTPException(status_code=400, detail="Specificare un cliente")

    services = await db.services.find(
        {"id": {"$in": data.service_ids}, "user_id": current_user["id"]}, {"_id": 0, "user_id": 0}
    ).to_list(100)
    if len(services) != len(data.service_ids):
        raise HTTPException(status_code=404, detail="Uno o più servizi non trovati")

    operator_name = None
    operator_color = None
    if data.operator_id:
        operator = await db.operators.find_one({"id": data.operator_id, "user_id": current_user["id"]}, {"_id": 0})
        if operator:
            operator_name = operator["name"]
            operator_color = operator.get("color", "#C58970")

    total_duration = sum(s["duration"] for s in services)
    total_price = sum(s["price"] for s in services)
    end_time = calculate_end_time(data.time, total_duration)

    appointment_id = str(uuid.uuid4())
    appointment_doc = {
        "id": appointment_id, "user_id": current_user["id"],
        "client_id": client_id, "client_name": client_name, "client_phone": client_phone,
        "service_ids": data.service_ids,
        "services": [{"id": s["id"], "name": s["name"], "duration": s["duration"], "price": s["price"]} for s in services],
        "operator_id": data.operator_id, "operator_name": operator_name, "operator_color": operator_color,
        "date": data.date, "time": data.time, "end_time": end_time,
        "total_duration": total_duration, "total_price": total_price,
        "status": "scheduled", "notes": data.notes or "", "sms_sent": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.appointments.insert_one(appointment_doc)
    return AppointmentResponse(**{k: v for k, v in appointment_doc.items() if k != "user_id"})


@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(
    date: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None,
    status: Optional[str] = None, operator_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"user_id": current_user["id"]}
    if date:
        query["date"] = date
    elif start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    if status:
        query["status"] = status
    if operator_id:
        query["operator_id"] = operator_id
    return await db.appointments.find(
        query, {"_id": 0, "user_id": 0}
    ).sort([("date", 1), ("time", 1)]).to_list(1000)


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "user_id": current_user["id"]}, {"_id": 0, "user_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return appointment


@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(appointment_id: str, data: AppointmentUpdate, current_user: dict = Depends(get_current_user)):
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "user_id": current_user["id"]}, {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")

    update_data = {}
    if data.client_id:
        client = await db.clients.find_one({"id": data.client_id, "user_id": current_user["id"]}, {"_id": 0})
        if not client:
            raise HTTPException(status_code=404, detail="Cliente non trovato")
        update_data["client_id"] = data.client_id
        update_data["client_name"] = client["name"]
        update_data["client_phone"] = client.get("phone", "")

    if data.service_ids:
        services = await db.services.find(
            {"id": {"$in": data.service_ids}, "user_id": current_user["id"]}, {"_id": 0, "user_id": 0}
        ).to_list(100)
        if len(services) != len(data.service_ids):
            raise HTTPException(status_code=404, detail="Uno o più servizi non trovati")
        update_data["service_ids"] = data.service_ids
        update_data["services"] = [{"id": s["id"], "name": s["name"], "duration": s["duration"], "price": s["price"]} for s in services]
        update_data["total_duration"] = sum(s["duration"] for s in services)
        update_data["total_price"] = sum(s["price"] for s in services)

    if data.operator_id is not None:
        if data.operator_id:
            operator = await db.operators.find_one({"id": data.operator_id, "user_id": current_user["id"]}, {"_id": 0})
            if operator:
                update_data["operator_id"] = data.operator_id
                update_data["operator_name"] = operator["name"]
                update_data["operator_color"] = operator.get("color", "#C58970")
        else:
            update_data["operator_id"] = None
            update_data["operator_name"] = None
            update_data["operator_color"] = None

    if data.date:
        update_data["date"] = data.date
    if data.time:
        update_data["time"] = data.time
    if data.status:
        update_data["status"] = data.status
        if data.status == "completed":
            await db.clients.update_one({"id": appointment["client_id"]}, {"$inc": {"total_visits": 1}})
    if data.notes is not None:
        update_data["notes"] = data.notes

    if "time" in update_data or "total_duration" in update_data:
        time = update_data.get("time", appointment["time"])
        duration = update_data.get("total_duration", appointment["total_duration"])
        update_data["end_time"] = calculate_end_time(time, duration)

    if update_data:
        await db.appointments.update_one({"id": appointment_id}, {"$set": update_data})
    return await db.appointments.find_one({"id": appointment_id}, {"_id": 0, "user_id": 0})


@router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.appointments.delete_one({"id": appointment_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return {"message": "Appuntamento eliminato"}


# ============== CHECKOUT ==============

@router.post("/appointments/{appointment_id}/checkout")
async def checkout_appointment(appointment_id: str, data: CheckoutData, current_user: dict = Depends(get_current_user)):
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "user_id": current_user["id"]}, {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")

    payment_id = str(uuid.uuid4())
    payment_doc = {
        "id": payment_id, "user_id": current_user["id"],
        "appointment_id": appointment_id, "client_id": appointment["client_id"],
        "client_name": appointment["client_name"], "services": appointment["services"],
        "original_amount": appointment["total_price"],
        "discount_type": data.discount_type, "discount_value": data.discount_value,
        "total_paid": data.total_paid, "payment_method": data.payment_method,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payments.insert_one(payment_doc)

    await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {"status": "completed", "paid": True, "payment_id": payment_id,
                  "payment_method": data.payment_method, "amount_paid": data.total_paid}}
    )

    if data.payment_method == "prepaid" and data.card_id:
        card = await db.cards.find_one({"id": data.card_id, "user_id": current_user["id"], "active": True})
        if card:
            new_remaining = max(0, card["remaining_value"] - data.total_paid)
            new_used = card.get("used_services", 0) + len(appointment.get("services", []))
            transaction = {
                "date": datetime.now(timezone.utc).isoformat(),
                "description": f"Servizi: {', '.join([s['name'] for s in appointment['services']])}",
                "amount": data.total_paid, "appointment_id": appointment_id
            }
            update_fields = {"remaining_value": new_remaining, "used_services": new_used}
            total_svc = card.get("total_services")
            if new_remaining <= 0 or (total_svc and new_used >= total_svc):
                update_fields["active"] = False
            await db.cards.update_one(
                {"id": card["id"]},
                {"$set": update_fields, "$push": {"transactions": transaction}}
            )

    if data.loyalty_points_used > 0:
        await db.loyalty.update_one(
            {"client_id": appointment["client_id"], "user_id": current_user["id"]},
            {"$inc": {"points": -data.loyalty_points_used}}
        )

    loyalty_before = await get_or_create_loyalty(appointment["client_id"], current_user["id"])
    points_before = loyalty_before["points"]
    points_earned = await award_loyalty_points(
        appointment["client_id"], current_user["id"], data.total_paid, appointment_id
    )
    points_after = points_before + points_earned

    if data.promo_id:
        promo = await db.promotions.find_one({"id": data.promo_id, "user_id": current_user["id"]}, {"_id": 0})
        if promo:
            await db.promo_usage.insert_one({
                "id": str(uuid.uuid4()), "promo_id": data.promo_id, "user_id": current_user["id"],
                "client_id": appointment.get("client_id", ""), "client_name": appointment.get("client_name", ""),
                "appointment_id": appointment_id,
                "free_service": data.promo_free_service or promo.get("free_service_name", ""),
                "used_at": datetime.now(timezone.utc).isoformat()
            })

    threshold_reached = None
    if points_before < 10 and points_after >= 10:
        threshold_reached = 10
    elif points_before < 5 and points_after >= 5:
        threshold_reached = 5

    return {
        "success": True, "payment_id": payment_id, "message": "Pagamento registrato con successo",
        "loyalty_points_earned": points_earned, "loyalty_total_points": points_after,
        "loyalty_threshold_reached": threshold_reached,
        "client_phone": appointment.get("client_phone", ""),
        "client_name": appointment.get("client_name", "")
    }


# ============== RECURRING ==============

@router.post("/appointments/recurring")
async def create_recurring_appointments(data: RecurringAppointmentCreate, current_user: dict = Depends(get_current_user)):
    original = await db.appointments.find_one(
        {"id": data.appointment_id, "user_id": current_user["id"]}, {"_id": 0}
    )
    if not original:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")

    created_appointments = []
    original_date = datetime.strptime(original["date"], "%Y-%m-%d")

    for i in range(1, data.repeat_count + 1):
        if data.repeat_months > 0:
            new_month = original_date.month + (data.repeat_months * i)
            new_year = original_date.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            try:
                new_date = original_date.replace(year=new_year, month=new_month)
            except ValueError:
                import calendar
                last_day = calendar.monthrange(new_year, new_month)[1]
                new_date = original_date.replace(year=new_year, month=new_month, day=min(original_date.day, last_day))
        else:
            new_date = original_date + timedelta(weeks=data.repeat_weeks * i)

        appointment_id = str(uuid.uuid4())
        appointment_doc = {
            "id": appointment_id, "user_id": current_user["id"],
            "client_id": original["client_id"], "client_name": original["client_name"],
            "client_phone": original.get("client_phone", ""),
            "service_ids": original["service_ids"], "services": original["services"],
            "operator_id": original.get("operator_id"), "operator_name": original.get("operator_name"),
            "operator_color": original.get("operator_color"),
            "date": new_date.strftime("%Y-%m-%d"), "time": original["time"],
            "end_time": original["end_time"], "total_duration": original["total_duration"],
            "total_price": original["total_price"], "status": "scheduled",
            "notes": original.get("notes", ""), "sms_sent": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.appointments.insert_one(appointment_doc)
        created_appointments.append({"id": appointment_id, "date": appointment_doc["date"], "time": appointment_doc["time"]})

    return {"created": len(created_appointments), "appointments": created_appointments}
