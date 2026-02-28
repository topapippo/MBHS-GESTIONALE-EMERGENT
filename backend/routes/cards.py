from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user
from models import PrepaidCardCreate, PrepaidCardResponse, PrepaidCardUpdate, CardTransaction

router = APIRouter()


# ============== PREPAID CARDS ==============

@router.post("/cards", response_model=PrepaidCardResponse)
async def create_prepaid_card(data: PrepaidCardCreate, current_user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": data.client_id, "user_id": current_user["id"]}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    card_id = str(uuid.uuid4())
    card_doc = {
        "id": card_id, "user_id": current_user["id"],
        "client_id": data.client_id, "client_name": client["name"],
        "card_type": data.card_type, "name": data.name,
        "total_value": data.total_value, "remaining_value": data.total_value,
        "total_services": data.total_services, "used_services": 0,
        "valid_until": data.valid_until, "notes": data.notes or "",
        "active": True, "transactions": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.cards.insert_one(card_doc)
    return PrepaidCardResponse(**{k: v for k, v in card_doc.items() if k != "user_id"})


@router.get("/cards", response_model=List[PrepaidCardResponse])
async def get_cards(client_id: Optional[str] = None, active_only: bool = True, current_user: dict = Depends(get_current_user)):
    query = {"user_id": current_user["id"]}
    if client_id:
        query["client_id"] = client_id
    if active_only:
        query["active"] = True
    return await db.cards.find(query, {"_id": 0, "user_id": 0}).sort("created_at", -1).to_list(500)


@router.get("/cards/{card_id}", response_model=PrepaidCardResponse)
async def get_card(card_id: str, current_user: dict = Depends(get_current_user)):
    card = await db.cards.find_one({"id": card_id, "user_id": current_user["id"]}, {"_id": 0, "user_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card non trovata")
    return card


@router.put("/cards/{card_id}", response_model=PrepaidCardResponse)
async def update_card(card_id: str, data: PrepaidCardUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.cards.update_one({"id": card_id, "user_id": current_user["id"]}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Card non trovata")
    return await db.cards.find_one({"id": card_id}, {"_id": 0, "user_id": 0})


@router.delete("/cards/{card_id}")
async def delete_card(card_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.cards.delete_one({"id": card_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Card non trovata")
    return {"message": "Card eliminata"}


@router.post("/cards/{card_id}/use")
async def use_card(card_id: str, data: CardTransaction, current_user: dict = Depends(get_current_user)):
    card = await db.cards.find_one({"id": card_id, "user_id": current_user["id"]}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card non trovata")
    if not card["active"]:
        raise HTTPException(status_code=400, detail="Card non attiva")
    if card.get("valid_until"):
        if datetime.strptime(card["valid_until"], "%Y-%m-%d").date() < datetime.now(timezone.utc).date():
            raise HTTPException(status_code=400, detail="Card scaduta")
    if card["remaining_value"] < data.amount:
        raise HTTPException(status_code=400, detail=f"Credito insufficiente. Disponibile: €{card['remaining_value']:.2f}")
    transaction = {
        "id": str(uuid.uuid4()), "amount": data.amount,
        "appointment_id": data.appointment_id,
        "description": data.description or f"Utilizzo card - €{data.amount:.2f}",
        "date": datetime.now(timezone.utc).isoformat()
    }
    new_remaining = card["remaining_value"] - data.amount
    new_used_services = card["used_services"] + 1
    is_exhausted = new_remaining <= 0
    if card.get("total_services"):
        is_exhausted = is_exhausted or new_used_services >= card["total_services"]
    await db.cards.update_one(
        {"id": card_id},
        {"$set": {"remaining_value": new_remaining, "used_services": new_used_services, "active": not is_exhausted},
         "$push": {"transactions": transaction}}
    )
    return {"success": True, "transaction": transaction, "remaining_value": new_remaining,
            "used_services": new_used_services, "card_active": not is_exhausted}


@router.post("/cards/{card_id}/recharge")
async def recharge_card(card_id: str, amount: float, current_user: dict = Depends(get_current_user)):
    card = await db.cards.find_one({"id": card_id, "user_id": current_user["id"]}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card non trovata")
    transaction = {
        "id": str(uuid.uuid4()), "amount": -amount, "appointment_id": None,
        "description": f"Ricarica - €{amount:.2f}", "date": datetime.now(timezone.utc).isoformat()
    }
    new_remaining = card["remaining_value"] + amount
    new_total = card["total_value"] + amount
    await db.cards.update_one(
        {"id": card_id},
        {"$set": {"remaining_value": new_remaining, "total_value": new_total, "active": True},
         "$push": {"transactions": transaction}}
    )
    return {"success": True, "new_remaining": new_remaining, "new_total": new_total}


# ============== CARD TEMPLATES ==============

from pydantic import BaseModel

class CardTemplateCreate(BaseModel):
    name: str
    card_type: str = "prepaid"
    total_value: float
    total_services: Optional[int] = None
    duration_months: Optional[int] = None
    notes: Optional[str] = ""

class CardTemplateUpdate(BaseModel):
    name: Optional[str] = None
    card_type: Optional[str] = None
    total_value: Optional[float] = None
    total_services: Optional[int] = None
    duration_months: Optional[int] = None
    notes: Optional[str] = None


@router.get("/card-templates")
async def get_card_templates(current_user: dict = Depends(get_current_user)):
    return await db.card_templates.find(
        {"user_id": current_user["id"]}, {"_id": 0, "user_id": 0}
    ).sort("created_at", -1).to_list(50)


@router.post("/card-templates")
async def create_card_template(data: CardTemplateCreate, current_user: dict = Depends(get_current_user)):
    template = {
        "id": str(uuid.uuid4()), "user_id": current_user["id"],
        "name": data.name, "card_type": data.card_type,
        "total_value": data.total_value, "total_services": data.total_services,
        "duration_months": data.duration_months, "notes": data.notes or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.card_templates.insert_one(template)
    return {k: v for k, v in template.items() if k not in ("_id", "user_id")}


@router.put("/card-templates/{template_id}")
async def update_card_template(template_id: str, data: CardTemplateUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.card_templates.update_one({"id": template_id, "user_id": current_user["id"]}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return await db.card_templates.find_one({"id": template_id}, {"_id": 0, "user_id": 0})


@router.delete("/card-templates/{template_id}")
async def delete_card_template(template_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.card_templates.delete_one({"id": template_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return {"success": True}
