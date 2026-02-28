from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user, hash_password, verify_password, create_token
from models import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter()


@router.post("/auth/register", response_model=TokenResponse)
async def register(data: UserCreate):
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")

    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": data.email,
        "password": hash_password(data.password),
        "name": data.name,
        "salon_name": data.salon_name,
        "opening_time": "09:00",
        "closing_time": "19:00",
        "working_days": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.users.insert_one(user_doc)

    default_services = [
        {"name": "Taglio Donna", "category": "taglio", "duration": 45, "price": 35.0},
        {"name": "Piega", "category": "piega", "duration": 30, "price": 25.0},
        {"name": "Colore", "category": "colore", "duration": 90, "price": 60.0},
        {"name": "Meches", "category": "colore", "duration": 120, "price": 80.0},
        {"name": "Trattamento Ristrutturante", "category": "trattamento", "duration": 30, "price": 30.0},
        {"name": "Shampoo", "category": "altro", "duration": 10, "price": 5.0},
    ]

    for svc in default_services:
        service_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            **svc,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.services.insert_one(service_doc)

    operator_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": data.name,
        "phone": "",
        "color": "#C58970",
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.operators.insert_one(operator_doc)

    token = create_token(user_id)

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id, email=data.email, name=data.name,
            salon_name=data.salon_name, created_at=user_doc["created_at"]
        )
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Credenziali non valide")

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenziali non valide")

    token = create_token(user["id"])

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"], email=user["email"], name=user["name"],
            salon_name=user["salon_name"], created_at=user["created_at"]
        )
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"], email=current_user["email"],
        name=current_user["name"], salon_name=current_user["salon_name"],
        created_at=current_user["created_at"]
    )


@router.put("/auth/change-password")
async def change_password(data: dict, current_user: dict = Depends(get_current_user)):
    current_pw = data.get("current_password", "")
    new_pw = data.get("new_password", "")
    if not current_pw or not new_pw:
        raise HTTPException(status_code=400, detail="Password corrente e nuova password sono obbligatorie")
    if len(new_pw) < 6:
        raise HTTPException(status_code=400, detail="La nuova password deve avere almeno 6 caratteri")
    user = await db.users.find_one({"id": current_user["id"]})
    if not user or not verify_password(current_pw, user["password"]):
        raise HTTPException(status_code=400, detail="Password corrente non corretta")
    await db.users.update_one({"id": current_user["id"]}, {"$set": {"password": hash_password(new_pw)}})
    return {"success": True, "message": "Password aggiornata con successo"}
