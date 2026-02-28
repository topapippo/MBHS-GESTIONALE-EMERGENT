from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user
from models import ServiceCreate, ServiceResponse, ServiceUpdate

router = APIRouter()


@router.post("/services", response_model=ServiceResponse)
async def create_service(data: ServiceCreate, current_user: dict = Depends(get_current_user)):
    service_id = str(uuid.uuid4())
    service_doc = {
        "id": service_id, "user_id": current_user["id"],
        "name": data.name, "category": data.category,
        "duration": data.duration, "price": data.price,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.services.insert_one(service_doc)
    return ServiceResponse(**{k: v for k, v in service_doc.items() if k != "user_id"})


@router.get("/services", response_model=List[ServiceResponse])
async def get_services(current_user: dict = Depends(get_current_user)):
    return await db.services.find(
        {"user_id": current_user["id"]}, {"_id": 0, "user_id": 0}
    ).sort("sort_order", 1).to_list(1000)


@router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, data: ServiceUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.services.update_one({"id": service_id, "user_id": current_user["id"]}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return await db.services.find_one({"id": service_id}, {"_id": 0, "user_id": 0})


@router.delete("/services/{service_id}")
async def delete_service(service_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.services.delete_one({"id": service_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return {"message": "Servizio eliminato"}
