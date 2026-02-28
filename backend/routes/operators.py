from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user
from models import OperatorCreate, OperatorResponse, OperatorUpdate

router = APIRouter()


@router.post("/operators", response_model=OperatorResponse)
async def create_operator(data: OperatorCreate, current_user: dict = Depends(get_current_user)):
    operator_id = str(uuid.uuid4())
    operator_doc = {
        "id": operator_id, "user_id": current_user["id"],
        "name": data.name, "phone": data.phone or "", "color": data.color or "#C58970",
        "active": True, "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.operators.insert_one(operator_doc)
    return OperatorResponse(**{k: v for k, v in operator_doc.items() if k != "user_id"})


@router.get("/operators", response_model=List[OperatorResponse])
async def get_operators(current_user: dict = Depends(get_current_user)):
    return await db.operators.find(
        {"user_id": current_user["id"]}, {"_id": 0, "user_id": 0}
    ).sort("name", 1).to_list(100)


@router.put("/operators/{operator_id}", response_model=OperatorResponse)
async def update_operator(operator_id: str, data: OperatorUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.operators.update_one({"id": operator_id, "user_id": current_user["id"]}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Operatore non trovato")
    return await db.operators.find_one({"id": operator_id}, {"_id": 0, "user_id": 0})


@router.delete("/operators/{operator_id}")
async def delete_operator(operator_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.operators.delete_one({"id": operator_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Operatore non trovato")
    return {"message": "Operatore eliminato"}
