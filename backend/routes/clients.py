from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user
from models import ClientCreate, ClientResponse, ClientUpdate, ClientBulkImport

router = APIRouter()


@router.post("/clients/import")
async def import_clients_bulk(data: ClientBulkImport, current_user: dict = Depends(get_current_user)):
    imported = 0
    skipped = 0
    for client_data in data.clients:
        exists = await db.clients.find_one({"user_id": current_user["id"], "name": client_data.name})
        if exists:
            skipped += 1
            continue
        client_doc = {
            "id": str(uuid.uuid4()), "user_id": current_user["id"],
            "name": client_data.name, "phone": client_data.phone or "",
            "email": client_data.email or "", "notes": client_data.notes or "",
            "sms_reminder": client_data.sms_reminder if client_data.sms_reminder is not None else True,
            "total_visits": 0, "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.clients.insert_one(client_doc)
        imported += 1
    return {"imported": imported, "skipped": skipped, "total": imported + skipped}


@router.post("/clients", response_model=ClientResponse)
async def create_client(data: ClientCreate, current_user: dict = Depends(get_current_user)):
    client_id = str(uuid.uuid4())
    client_doc = {
        "id": client_id, "user_id": current_user["id"],
        "name": data.name, "phone": data.phone or "",
        "email": data.email or "", "notes": data.notes or "",
        "sms_reminder": data.sms_reminder if data.sms_reminder is not None else True,
        "total_visits": 0, "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.clients.insert_one(client_doc)
    return ClientResponse(**{k: v for k, v in client_doc.items() if k != "user_id"})


@router.get("/clients", response_model=List[ClientResponse])
async def get_clients(current_user: dict = Depends(get_current_user)):
    return await db.clients.find(
        {"user_id": current_user["id"]}, {"_id": 0, "user_id": 0}
    ).sort("name", 1).to_list(1000)


@router.get("/clients/search/appointments")
async def search_client_appointments(query: str, current_user: dict = Depends(get_current_user)):
    clients = await db.clients.find(
        {"user_id": current_user["id"], "name": {"$regex": query, "$options": "i"}},
        {"_id": 0}
    ).to_list(20)
    if not clients:
        return {"clients": [], "appointments": []}
    client_ids = [c["id"] for c in clients]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    appointments = await db.appointments.find(
        {"user_id": current_user["id"], "client_id": {"$in": client_ids},
         "date": {"$gte": today}, "status": {"$ne": "cancelled"}},
        {"_id": 0, "user_id": 0}
    ).sort([("date", 1), ("time", 1)]).to_list(50)
    return {
        "clients": [{"id": c["id"], "name": c["name"], "phone": c.get("phone", "")} for c in clients],
        "appointments": appointments
    }


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id, "user_id": current_user["id"]}, {"_id": 0, "user_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return client


@router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, data: ClientUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.clients.update_one({"id": client_id, "user_id": current_user["id"]}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return await db.clients.find_one({"id": client_id}, {"_id": 0, "user_id": 0})


@router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.clients.delete_one({"id": client_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return {"message": "Cliente eliminato"}


@router.get("/clients/{client_id}/history")
async def get_client_history(client_id: str, current_user: dict = Depends(get_current_user)):
    from routes.loyalty import get_or_create_loyalty
    client = await db.clients.find_one({"id": client_id, "user_id": current_user["id"]}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    appointments = await db.appointments.find(
        {"client_id": client_id, "user_id": current_user["id"]}, {"_id": 0}
    ).sort("date", -1).to_list(500)
    payments = await db.payments.find(
        {"client_id": client_id, "user_id": current_user["id"]}, {"_id": 0}
    ).sort("date", -1).to_list(500)
    total_spent = sum(p.get("total_paid", 0) for p in payments)
    total_visits = len([a for a in appointments if a.get("status") == "completed"])
    loyalty = await get_or_create_loyalty(client_id, current_user["id"])
    return {
        "client": client, "appointments": appointments, "payments": payments,
        "total_spent": total_spent, "total_visits": total_visits,
        "last_visit": appointments[0]["date"] if appointments else None,
        "loyalty_points": loyalty["points"],
        "loyalty_total_earned": loyalty["total_points_earned"],
        "active_rewards": [r for r in loyalty.get("active_rewards", []) if not r.get("redeemed")]
    }


@router.get("/clients/{client_id}/whatsapp")
async def get_whatsapp_link(client_id: str, message: str = None, current_user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id, "user_id": current_user["id"]}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    phone = client.get("phone", "")
    if not phone:
        raise HTTPException(status_code=400, detail="Cliente senza numero di telefono")
    phone = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not phone.startswith("39"):
        phone = "39" + phone
    default_msg = f"Ciao {client['name']}! Ti ricordiamo il tuo appuntamento presso MBHS SALON."
    msg = message or default_msg
    return {"url": f"https://wa.me/{phone}?text={msg}", "phone": phone}


@router.get("/clients/{client_id}/cards")
async def get_client_cards(client_id: str, current_user: dict = Depends(get_current_user)):
    return await db.cards.find(
        {"client_id": client_id, "user_id": current_user["id"], "active": True}, {"_id": 0}
    ).to_list(50)


@router.get("/clients/{client_id}/loyalty")
async def get_client_loyalty_points(client_id: str, current_user: dict = Depends(get_current_user)):
    loyalty = await db.loyalty.find_one(
        {"client_id": client_id, "user_id": current_user["id"]}, {"_id": 0}
    )
    if not loyalty:
        return {"points": 0, "total_earned": 0}
    return {"points": loyalty.get("points", 0), "total_earned": loyalty.get("total_earned", 0)}
