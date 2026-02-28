from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, Response
import requests as http_requests
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'salone-parrucchiera-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Twilio Config (optional)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Initialize Twilio client if credentials are available
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        from twilio.rest import Client
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except ImportError:
        pass

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# ============== MODELS ==============

# User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    salon_name: Optional[str] = "Il Mio Salone"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    salon_name: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Operator Models
class OperatorCreate(BaseModel):
    name: str
    phone: Optional[str] = ""
    color: Optional[str] = "#C58970"

class OperatorResponse(BaseModel):
    id: str
    name: str
    phone: str
    color: str
    active: bool
    created_at: str

class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    color: Optional[str] = None
    active: Optional[bool] = None

# Client Models
class ClientCreate(BaseModel):
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    notes: Optional[str] = ""
    sms_reminder: Optional[bool] = True

class ClientResponse(BaseModel):
    id: str
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    notes: Optional[str] = ""
    sms_reminder: Optional[bool] = False
    send_sms_reminders: Optional[bool] = False
    created_at: str
    total_visits: int = 0

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    sms_reminder: Optional[bool] = None

# Service Models
class ServiceCreate(BaseModel):
    name: str
    category: str
    duration: int
    price: float
    color: Optional[str] = None
    sort_order: Optional[int] = None

class ServiceResponse(BaseModel):
    id: str
    name: str
    category: str
    duration: int
    price: float
    color: Optional[str] = None
    sort_order: Optional[int] = None
    created_at: str

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None

# Appointment Models
class AppointmentCreate(BaseModel):
    client_id: Optional[str] = None
    client_name: Optional[str] = None  # For new/generic clients
    client_phone: Optional[str] = ""
    service_ids: List[str]
    operator_id: Optional[str] = None
    date: str
    time: str
    notes: Optional[str] = ""

class AppointmentResponse(BaseModel):
    id: str
    client_id: str
    client_name: str
    client_phone: Optional[str] = ""
    service_ids: List[str]
    services: List[dict]
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None
    operator_color: Optional[str] = None
    date: str
    time: str
    end_time: str
    total_duration: int
    total_price: float
    status: str
    notes: Optional[str] = ""
    sms_sent: Optional[bool] = False
    source: Optional[str] = "manual"
    paid: Optional[bool] = False
    created_at: str

class AppointmentUpdate(BaseModel):
    client_id: Optional[str] = None
    service_ids: Optional[List[str]] = None
    operator_id: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# SMS Model
class SMSRequest(BaseModel):
    appointment_id: str
    message: Optional[str] = None

# Settings Model
class SettingsUpdate(BaseModel):
    salon_name: Optional[str] = None
    name: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    working_days: Optional[List[str]] = None

# Prepaid Card / Subscription Models
class PrepaidCardCreate(BaseModel):
    client_id: str
    card_type: str  # "prepaid" or "subscription"
    name: str  # e.g., "Card 10 Pieghe", "Abbonamento Mensile"
    total_value: float  # Total amount paid
    total_services: Optional[int] = None  # For service-based cards (e.g., 10 pieghe)
    valid_until: Optional[str] = None  # Expiry date for subscriptions
    notes: Optional[str] = ""

class PrepaidCardResponse(BaseModel):
    id: str
    client_id: str
    client_name: str
    card_type: str
    name: str
    total_value: float
    remaining_value: float
    total_services: Optional[int]
    used_services: int
    valid_until: Optional[str]
    notes: str
    active: bool
    created_at: str
    transactions: List[dict]

class PrepaidCardUpdate(BaseModel):
    name: Optional[str] = None
    total_value: Optional[float] = None
    remaining_value: Optional[float] = None
    total_services: Optional[int] = None
    valid_until: Optional[str] = None
    notes: Optional[str] = None
    active: Optional[bool] = None

class CardTransaction(BaseModel):
    card_id: str
    amount: float
    appointment_id: Optional[str] = None
    description: Optional[str] = ""

# Recurring Appointment Model
class RecurringAppointmentCreate(BaseModel):
    appointment_id: str
    repeat_weeks: int = 0  # Every X weeks (0 if using months)
    repeat_months: int = 0  # Every X months (0 if using weeks)
    repeat_count: int  # How many times to repeat

# Loyalty Program Models
class LoyaltyRedeemRequest(BaseModel):
    reward_type: str  # "sconto_colorazione" or "taglio_gratuito"

# Loyalty config - defaults, overridden by DB
LOYALTY_POINTS_PER_EURO = 10  # 1 point every 10€ spent
DEFAULT_LOYALTY_REWARDS = {
    "sconto_colorazione": {
        "name": "Sconto 10% Colorazione",
        "description": "Sconto del 10% sul prossimo servizio di colorazione",
        "points_required": 5,
        "discount_percent": 10,
    },
    "taglio_gratuito": {
        "name": "Taglio Gratuito",
        "description": "Un taglio completamente gratuito",
        "points_required": 10,
    }
}

async def get_loyalty_rewards(user_id: str):
    rewards = await db.loyalty_rewards.find({"user_id": user_id}, {"_id": 0}).to_list(50)
    if rewards:
        return {r["key"]: r for r in rewards}
    return DEFAULT_LOYALTY_REWARDS

# ============== HELPER FUNCTIONS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token non valido")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")

def calculate_end_time(start_time: str, duration_minutes: int) -> str:
    hours, minutes = map(int, start_time.split(':'))
    total_minutes = hours * 60 + minutes + duration_minutes
    end_hours = (total_minutes // 60) % 24
    end_minutes = total_minutes % 60
    return f"{end_hours:02d}:{end_minutes:02d}"

def format_phone_e164(phone: str) -> str:
    """Format phone number to E.164 format for Twilio"""
    phone = ''.join(filter(str.isdigit, phone))
    if phone.startswith('39'):
        return f"+{phone}"
    elif phone.startswith('3') and len(phone) == 10:
        return f"+39{phone}"
    elif not phone.startswith('+'):
        return f"+39{phone}"
    return phone

async def send_sms_reminder(phone: str, message: str, salon_name: str) -> dict:
    """Send SMS via Twilio"""
    if not twilio_client or not TWILIO_PHONE_NUMBER:
        return {"success": False, "error": "Twilio non configurato"}
    
    try:
        formatted_phone = format_phone_e164(phone)
        sms = twilio_client.messages.create(
            body=f"[{salon_name}] {message}",
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_phone
        )
        return {"success": True, "sid": sms.sid}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
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
    
    # Create default services
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
    
    # Create default operator (owner)
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
            id=user_id,
            email=data.email,
            name=data.name,
            salon_name=data.salon_name,
            created_at=user_doc["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
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
            id=user["id"],
            email=user["email"],
            name=user["name"],
            salon_name=user["salon_name"],
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        salon_name=current_user["salon_name"],
        created_at=current_user["created_at"]
    )


@api_router.put("/auth/change-password")
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

# ============== OPERATOR ROUTES ==============

@api_router.post("/operators", response_model=OperatorResponse)
async def create_operator(data: OperatorCreate, current_user: dict = Depends(get_current_user)):
    operator_id = str(uuid.uuid4())
    operator_doc = {
        "id": operator_id,
        "user_id": current_user["id"],
        "name": data.name,
        "phone": data.phone or "",
        "color": data.color or "#C58970",
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.operators.insert_one(operator_doc)
    return OperatorResponse(**{k: v for k, v in operator_doc.items() if k != "user_id"})

@api_router.get("/operators", response_model=List[OperatorResponse])
async def get_operators(current_user: dict = Depends(get_current_user)):
    operators = await db.operators.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0, "user_id": 0}
    ).sort("name", 1).to_list(100)
    return operators

@api_router.put("/operators/{operator_id}", response_model=OperatorResponse)
async def update_operator(operator_id: str, data: OperatorUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    result = await db.operators.update_one(
        {"id": operator_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Operatore non trovato")
    
    operator = await db.operators.find_one({"id": operator_id}, {"_id": 0, "user_id": 0})
    return operator

@api_router.delete("/operators/{operator_id}")
async def delete_operator(operator_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.operators.delete_one({"id": operator_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Operatore non trovato")
    return {"message": "Operatore eliminato"}

# ============== CLIENT ROUTES ==============

class ClientBulkImport(BaseModel):
    clients: List[ClientCreate]

@api_router.post("/clients/import")
async def import_clients_bulk(data: ClientBulkImport, current_user: dict = Depends(get_current_user)):
    """Import multiple clients at once"""
    imported = 0
    skipped = 0
    
    for client_data in data.clients:
        # Check if client already exists
        exists = await db.clients.find_one({
            "user_id": current_user["id"], 
            "name": client_data.name
        })
        if exists:
            skipped += 1
            continue
        
        client_doc = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "name": client_data.name,
            "phone": client_data.phone or "",
            "email": client_data.email or "",
            "notes": client_data.notes or "",
            "sms_reminder": client_data.sms_reminder if client_data.sms_reminder is not None else True,
            "total_visits": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.clients.insert_one(client_doc)
        imported += 1
    
    return {"imported": imported, "skipped": skipped, "total": imported + skipped}

@api_router.post("/clients", response_model=ClientResponse)
async def create_client(data: ClientCreate, current_user: dict = Depends(get_current_user)):
    client_id = str(uuid.uuid4())
    client_doc = {
        "id": client_id,
        "user_id": current_user["id"],
        "name": data.name,
        "phone": data.phone or "",
        "email": data.email or "",
        "notes": data.notes or "",
        "sms_reminder": data.sms_reminder if data.sms_reminder is not None else True,
        "total_visits": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.clients.insert_one(client_doc)
    return ClientResponse(**{k: v for k, v in client_doc.items() if k != "user_id"})

@api_router.get("/clients", response_model=List[ClientResponse])
async def get_clients(current_user: dict = Depends(get_current_user)):
    clients = await db.clients.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0, "user_id": 0}
    ).sort("name", 1).to_list(1000)
    return clients

@api_router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = await db.clients.find_one(
        {"id": client_id, "user_id": current_user["id"]}, 
        {"_id": 0, "user_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return client

@api_router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, data: ClientUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    result = await db.clients.update_one(
        {"id": client_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    client = await db.clients.find_one({"id": client_id}, {"_id": 0, "user_id": 0})
    return client

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.clients.delete_one({"id": client_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return {"message": "Cliente eliminato"}

# ============== SERVICE ROUTES ==============

@api_router.post("/services", response_model=ServiceResponse)
async def create_service(data: ServiceCreate, current_user: dict = Depends(get_current_user)):
    service_id = str(uuid.uuid4())
    service_doc = {
        "id": service_id,
        "user_id": current_user["id"],
        "name": data.name,
        "category": data.category,
        "duration": data.duration,
        "price": data.price,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.services.insert_one(service_doc)
    return ServiceResponse(**{k: v for k, v in service_doc.items() if k != "user_id"})

@api_router.get("/services", response_model=List[ServiceResponse])
async def get_services(current_user: dict = Depends(get_current_user)):
    services = await db.services.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0, "user_id": 0}
    ).sort("sort_order", 1).to_list(1000)
    return services

@api_router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, data: ServiceUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    result = await db.services.update_one(
        {"id": service_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    
    service = await db.services.find_one({"id": service_id}, {"_id": 0, "user_id": 0})
    return service

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.services.delete_one({"id": service_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return {"message": "Servizio eliminato"}

# ============== APPOINTMENT ROUTES ==============

@api_router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    # Get or create client
    client_name = ""
    client_phone = ""
    client_id = data.client_id or ""
    
    if data.client_id:
        client = await db.clients.find_one(
            {"id": data.client_id, "user_id": current_user["id"]}, 
            {"_id": 0}
        )
        if client:
            client_name = client["name"]
            client_phone = client.get("phone", "")
        else:
            raise HTTPException(status_code=404, detail="Cliente non trovato")
    elif data.client_name:
        # New client or generic - create on the fly
        client_name = data.client_name
        client_phone = data.client_phone or ""
        if client_name.lower() != "cliente generico":
            # Create new client in address book
            new_client_id = str(uuid.uuid4())
            new_client = {
                "id": new_client_id,
                "user_id": current_user["id"],
                "name": client_name,
                "phone": client_phone,
                "notes": "",
                "send_sms_reminders": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.clients.insert_one(new_client)
            client_id = new_client_id
        else:
            client_id = "generic"
    else:
        raise HTTPException(status_code=400, detail="Specificare un cliente")
    
    # Get services
    services = await db.services.find(
        {"id": {"$in": data.service_ids}, "user_id": current_user["id"]}, 
        {"_id": 0, "user_id": 0}
    ).to_list(100)
    
    if len(services) != len(data.service_ids):
        raise HTTPException(status_code=404, detail="Uno o più servizi non trovati")
    
    # Get operator if specified
    operator_name = None
    operator_color = None
    if data.operator_id:
        operator = await db.operators.find_one(
            {"id": data.operator_id, "user_id": current_user["id"]},
            {"_id": 0}
        )
        if operator:
            operator_name = operator["name"]
            operator_color = operator.get("color", "#C58970")
    
    total_duration = sum(s["duration"] for s in services)
    total_price = sum(s["price"] for s in services)
    end_time = calculate_end_time(data.time, total_duration)
    
    appointment_id = str(uuid.uuid4())
    appointment_doc = {
        "id": appointment_id,
        "user_id": current_user["id"],
        "client_id": client_id,
        "client_name": client_name,
        "client_phone": client_phone,
        "service_ids": data.service_ids,
        "services": [{"id": s["id"], "name": s["name"], "duration": s["duration"], "price": s["price"]} for s in services],
        "operator_id": data.operator_id,
        "operator_name": operator_name,
        "operator_color": operator_color,
        "date": data.date,
        "time": data.time,
        "end_time": end_time,
        "total_duration": total_duration,
        "total_price": total_price,
        "status": "scheduled",
        "notes": data.notes or "",
        "sms_sent": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appointment_doc)
    
    return AppointmentResponse(**{k: v for k, v in appointment_doc.items() if k != "user_id"})

@api_router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    operator_id: Optional[str] = None,
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
    
    appointments = await db.appointments.find(
        query, 
        {"_id": 0, "user_id": 0}
    ).sort([("date", 1), ("time", 1)]).to_list(1000)
    
    return appointments

@api_router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "user_id": current_user["id"]}, 
        {"_id": 0, "user_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return appointment

@api_router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(appointment_id: str, data: AppointmentUpdate, current_user: dict = Depends(get_current_user)):
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "user_id": current_user["id"]}, 
        {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    update_data = {}
    
    if data.client_id:
        client = await db.clients.find_one(
            {"id": data.client_id, "user_id": current_user["id"]}, 
            {"_id": 0}
        )
        if not client:
            raise HTTPException(status_code=404, detail="Cliente non trovato")
        update_data["client_id"] = data.client_id
        update_data["client_name"] = client["name"]
        update_data["client_phone"] = client.get("phone", "")
    
    if data.service_ids:
        services = await db.services.find(
            {"id": {"$in": data.service_ids}, "user_id": current_user["id"]}, 
            {"_id": 0, "user_id": 0}
        ).to_list(100)
        
        if len(services) != len(data.service_ids):
            raise HTTPException(status_code=404, detail="Uno o più servizi non trovati")
        
        update_data["service_ids"] = data.service_ids
        update_data["services"] = [{"id": s["id"], "name": s["name"], "duration": s["duration"], "price": s["price"]} for s in services]
        update_data["total_duration"] = sum(s["duration"] for s in services)
        update_data["total_price"] = sum(s["price"] for s in services)
    
    if data.operator_id is not None:
        if data.operator_id:
            operator = await db.operators.find_one(
                {"id": data.operator_id, "user_id": current_user["id"]},
                {"_id": 0}
            )
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
            await db.clients.update_one(
                {"id": appointment["client_id"]},
                {"$inc": {"total_visits": 1}}
            )
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    if "time" in update_data or "total_duration" in update_data:
        time = update_data.get("time", appointment["time"])
        duration = update_data.get("total_duration", appointment["total_duration"])
        update_data["end_time"] = calculate_end_time(time, duration)
    
    if update_data:
        await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": update_data}
        )
    
    updated = await db.appointments.find_one({"id": appointment_id}, {"_id": 0, "user_id": 0})
    return updated

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.appointments.delete_one({"id": appointment_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return {"message": "Appuntamento eliminato"}

# ============== APPOINTMENT CHECKOUT ==============

class CheckoutData(BaseModel):
    payment_method: str = "cash"  # cash, prepaid
    discount_type: str = "none"   # none, percent, fixed, loyalty
    discount_value: float = 0
    total_paid: float
    card_id: Optional[str] = None  # ID della card prepagata/abbonamento
    loyalty_points_used: int = 0   # Punti fedeltà usati
    promo_id: Optional[str] = None  # ID promozione applicata
    promo_free_service: Optional[str] = None  # Nome servizio omaggio

@api_router.post("/appointments/{appointment_id}/checkout")
async def checkout_appointment(appointment_id: str, data: CheckoutData, current_user: dict = Depends(get_current_user)):
    """Process payment for an appointment"""
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    # Create payment record
    payment_id = str(uuid.uuid4())
    payment_doc = {
        "id": payment_id,
        "user_id": current_user["id"],
        "appointment_id": appointment_id,
        "client_id": appointment["client_id"],
        "client_name": appointment["client_name"],
        "services": appointment["services"],
        "original_amount": appointment["total_price"],
        "discount_type": data.discount_type,
        "discount_value": data.discount_value,
        "total_paid": data.total_paid,
        "payment_method": data.payment_method,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payments.insert_one(payment_doc)
    
    # Update appointment status
    await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {
            "status": "completed",
            "paid": True,
            "payment_id": payment_id,
            "payment_method": data.payment_method,
            "amount_paid": data.total_paid
        }}
    )
    
    # If using prepaid card, deduct from card
    if data.payment_method == "prepaid" and data.card_id:
        card = await db.cards.find_one({
            "id": data.card_id,
            "user_id": current_user["id"],
            "active": True
        })
        if card:
            new_remaining = max(0, card["remaining_value"] - data.total_paid)
            new_used = card.get("used_services", 0) + len(appointment.get("services", []))
            transaction = {
                "date": datetime.now(timezone.utc).isoformat(),
                "description": f"Servizi: {', '.join([s['name'] for s in appointment['services']])}",
                "amount": data.total_paid,
                "appointment_id": appointment_id
            }
            update_fields = {
                "remaining_value": new_remaining,
                "used_services": new_used
            }
            # Deactivate card if value is 0 or services exhausted
            total_svc = card.get("total_services")
            if new_remaining <= 0 or (total_svc and new_used >= total_svc):
                update_fields["active"] = False
            await db.cards.update_one(
                {"id": card["id"]},
                {"$set": update_fields, "$push": {"transactions": transaction}}
            )
    
    # If redeeming loyalty points, deduct them
    if data.loyalty_points_used > 0:
        await db.loyalty.update_one(
            {"client_id": appointment["client_id"], "user_id": current_user["id"]},
            {"$inc": {"points": -data.loyalty_points_used}}
        )
    
    # Award loyalty points and check thresholds
    loyalty_before = await get_or_create_loyalty(appointment["client_id"], current_user["id"])
    points_before = loyalty_before["points"]
    points_earned = await award_loyalty_points(
        appointment["client_id"], current_user["id"], data.total_paid, appointment_id
    )
    points_after = points_before + points_earned
    
    # Record promo usage if applied
    if data.promo_id:
        promo = await db.promotions.find_one({"id": data.promo_id, "user_id": current_user["id"]}, {"_id": 0})
        if promo:
            await db.promo_usage.insert_one({
                "id": str(uuid.uuid4()),
                "promo_id": data.promo_id,
                "user_id": current_user["id"],
                "client_id": appointment.get("client_id", ""),
                "client_name": appointment.get("client_name", ""),
                "appointment_id": appointment_id,
                "free_service": data.promo_free_service or promo.get("free_service_name", ""),
                "used_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Check if crossed 5 or 10 point threshold
    threshold_reached = None
    if points_before < 10 and points_after >= 10:
        threshold_reached = 10
    elif points_before < 5 and points_after >= 5:
        threshold_reached = 5
    
    return {
        "success": True,
        "payment_id": payment_id,
        "message": "Pagamento registrato con successo",
        "loyalty_points_earned": points_earned,
        "loyalty_total_points": points_after,
        "loyalty_threshold_reached": threshold_reached,
        "client_phone": appointment.get("client_phone", ""),
        "client_name": appointment.get("client_name", "")
    }

# Get client cards for checkout
@api_router.get("/clients/{client_id}/cards")
async def get_client_cards(client_id: str, current_user: dict = Depends(get_current_user)):
    cards = await db.cards.find(
        {"client_id": client_id, "user_id": current_user["id"], "active": True},
        {"_id": 0}
    ).to_list(50)
    return cards

# Get client loyalty points
@api_router.get("/clients/{client_id}/loyalty")
async def get_client_loyalty(client_id: str, current_user: dict = Depends(get_current_user)):
    loyalty = await db.loyalty.find_one(
        {"client_id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not loyalty:
        return {"points": 0, "total_earned": 0}
    return {"points": loyalty.get("points", 0), "total_earned": loyalty.get("total_earned", 0)}


# ============== RECURRING APPOINTMENTS ==============

@api_router.post("/appointments/recurring")
async def create_recurring_appointments(data: RecurringAppointmentCreate, current_user: dict = Depends(get_current_user)):
    """Create recurring appointments based on an existing appointment"""
    # Get original appointment
    original = await db.appointments.find_one(
        {"id": data.appointment_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not original:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    created_appointments = []
    original_date = datetime.strptime(original["date"], "%Y-%m-%d")
    
    for i in range(1, data.repeat_count + 1):
        if data.repeat_months > 0:
            # Monthly recurrence
            new_month = original_date.month + (data.repeat_months * i)
            new_year = original_date.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            try:
                new_date = original_date.replace(year=new_year, month=new_month)
            except ValueError:
                # Handle end-of-month (e.g., Jan 31 -> Feb 28)
                import calendar
                last_day = calendar.monthrange(new_year, new_month)[1]
                new_date = original_date.replace(year=new_year, month=new_month, day=min(original_date.day, last_day))
        else:
            new_date = original_date + timedelta(weeks=data.repeat_weeks * i)
        
        appointment_id = str(uuid.uuid4())
        appointment_doc = {
            "id": appointment_id,
            "user_id": current_user["id"],
            "client_id": original["client_id"],
            "client_name": original["client_name"],
            "client_phone": original.get("client_phone", ""),
            "service_ids": original["service_ids"],
            "services": original["services"],
            "operator_id": original.get("operator_id"),
            "operator_name": original.get("operator_name"),
            "operator_color": original.get("operator_color"),
            "date": new_date.strftime("%Y-%m-%d"),
            "time": original["time"],
            "end_time": original["end_time"],
            "total_duration": original["total_duration"],
            "total_price": original["total_price"],
            "status": "scheduled",
            "notes": original.get("notes", ""),
            "sms_sent": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.appointments.insert_one(appointment_doc)
        created_appointments.append({
            "id": appointment_id,
            "date": appointment_doc["date"],
            "time": appointment_doc["time"]
        })
    
    return {
        "created": len(created_appointments),
        "appointments": created_appointments
    }

# ============== CLIENT SEARCH (for Planning) ==============

@api_router.get("/clients/search/appointments")
async def search_client_appointments(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """Search clients and return their upcoming appointments"""
    # Find matching clients
    clients = await db.clients.find(
        {
            "user_id": current_user["id"],
            "name": {"$regex": query, "$options": "i"}
        },
        {"_id": 0}
    ).to_list(20)
    
    if not clients:
        return {"clients": [], "appointments": []}
    
    client_ids = [c["id"] for c in clients]
    
    # Get upcoming appointments for these clients
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    appointments = await db.appointments.find(
        {
            "user_id": current_user["id"],
            "client_id": {"$in": client_ids},
            "date": {"$gte": today},
            "status": {"$ne": "cancelled"}
        },
        {"_id": 0, "user_id": 0}
    ).sort([("date", 1), ("time", 1)]).to_list(50)
    
    return {
        "clients": [{"id": c["id"], "name": c["name"], "phone": c.get("phone", "")} for c in clients],
        "appointments": appointments
    }

# ============== PREPAID CARDS / SUBSCRIPTIONS ==============

@api_router.post("/cards", response_model=PrepaidCardResponse)
async def create_prepaid_card(data: PrepaidCardCreate, current_user: dict = Depends(get_current_user)):
    """Create a new prepaid card or subscription for a client"""
    # Verify client exists
    client = await db.clients.find_one(
        {"id": data.client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    card_id = str(uuid.uuid4())
    card_doc = {
        "id": card_id,
        "user_id": current_user["id"],
        "client_id": data.client_id,
        "client_name": client["name"],
        "card_type": data.card_type,
        "name": data.name,
        "total_value": data.total_value,
        "remaining_value": data.total_value,
        "total_services": data.total_services,
        "used_services": 0,
        "valid_until": data.valid_until,
        "notes": data.notes or "",
        "active": True,
        "transactions": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.cards.insert_one(card_doc)
    
    return PrepaidCardResponse(**{k: v for k, v in card_doc.items() if k != "user_id"})

@api_router.get("/cards", response_model=List[PrepaidCardResponse])
async def get_cards(
    client_id: Optional[str] = None,
    active_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Get all prepaid cards, optionally filtered by client"""
    query = {"user_id": current_user["id"]}
    if client_id:
        query["client_id"] = client_id
    if active_only:
        query["active"] = True
    
    cards = await db.cards.find(query, {"_id": 0, "user_id": 0}).sort("created_at", -1).to_list(500)
    return cards

@api_router.get("/cards/{card_id}", response_model=PrepaidCardResponse)
async def get_card(card_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific card"""
    card = await db.cards.find_one(
        {"id": card_id, "user_id": current_user["id"]},
        {"_id": 0, "user_id": 0}
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card non trovata")
    return card

@api_router.put("/cards/{card_id}", response_model=PrepaidCardResponse)
async def update_card(card_id: str, data: PrepaidCardUpdate, current_user: dict = Depends(get_current_user)):
    """Update a prepaid card"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    result = await db.cards.update_one(
        {"id": card_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Card non trovata")
    
    card = await db.cards.find_one({"id": card_id}, {"_id": 0, "user_id": 0})
    return card

@api_router.delete("/cards/{card_id}")
async def delete_card(card_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a prepaid card"""
    result = await db.cards.delete_one({"id": card_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Card non trovata")
    return {"message": "Card eliminata"}

@api_router.post("/cards/{card_id}/use")
async def use_card(card_id: str, data: CardTransaction, current_user: dict = Depends(get_current_user)):
    """Deduct amount from a prepaid card (used when completing an appointment)"""
    card = await db.cards.find_one(
        {"id": card_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card non trovata")
    
    if not card["active"]:
        raise HTTPException(status_code=400, detail="Card non attiva")
    
    # Check validity
    if card.get("valid_until"):
        if datetime.strptime(card["valid_until"], "%Y-%m-%d").date() < datetime.now(timezone.utc).date():
            raise HTTPException(status_code=400, detail="Card scaduta")
    
    # Check remaining value
    if card["remaining_value"] < data.amount:
        raise HTTPException(status_code=400, detail=f"Credito insufficiente. Disponibile: €{card['remaining_value']:.2f}")
    
    # Create transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "amount": data.amount,
        "appointment_id": data.appointment_id,
        "description": data.description or f"Utilizzo card - €{data.amount:.2f}",
        "date": datetime.now(timezone.utc).isoformat()
    }
    
    new_remaining = card["remaining_value"] - data.amount
    new_used_services = card["used_services"] + 1
    
    # Check if card is exhausted
    is_exhausted = new_remaining <= 0
    if card.get("total_services"):
        is_exhausted = is_exhausted or new_used_services >= card["total_services"]
    
    await db.cards.update_one(
        {"id": card_id},
        {
            "$set": {
                "remaining_value": new_remaining,
                "used_services": new_used_services,
                "active": not is_exhausted
            },
            "$push": {"transactions": transaction}
        }
    )
    
    return {
        "success": True,
        "transaction": transaction,
        "remaining_value": new_remaining,
        "used_services": new_used_services,
        "card_active": not is_exhausted
    }

@api_router.post("/cards/{card_id}/recharge")
async def recharge_card(card_id: str, amount: float, current_user: dict = Depends(get_current_user)):
    """Add credit to a prepaid card"""
    card = await db.cards.find_one(
        {"id": card_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card non trovata")
    
    transaction = {
        "id": str(uuid.uuid4()),
        "amount": -amount,  # Negative = recharge
        "appointment_id": None,
        "description": f"Ricarica - €{amount:.2f}",
        "date": datetime.now(timezone.utc).isoformat()
    }
    
    new_remaining = card["remaining_value"] + amount
    new_total = card["total_value"] + amount
    
    await db.cards.update_one(
        {"id": card_id},
        {
            "$set": {
                "remaining_value": new_remaining,
                "total_value": new_total,
                "active": True
            },
            "$push": {"transactions": transaction}
        }
    )
    
    return {
        "success": True,
        "new_remaining": new_remaining,
        "new_total": new_total
    }

# ============== SMS ROUTES ==============

@api_router.post("/sms/send-reminder")
async def send_appointment_reminder(data: SMSRequest, current_user: dict = Depends(get_current_user)):
    """Send SMS reminder for a specific appointment"""
    appointment = await db.appointments.find_one(
        {"id": data.appointment_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    client = await db.clients.find_one(
        {"id": appointment["client_id"], "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not client or not client.get("phone"):
        raise HTTPException(status_code=400, detail="Cliente senza numero di telefono")
    
    if not client.get("sms_reminder", True):
        raise HTTPException(status_code=400, detail="Cliente ha disabilitato promemoria SMS")
    
    # Format message
    services_text = ", ".join([s["name"] for s in appointment["services"]])
    default_message = f"Promemoria: hai un appuntamento il {appointment['date']} alle {appointment['time']} per {services_text}. Ti aspettiamo!"
    message = data.message or default_message
    
    result = await send_sms_reminder(
        client["phone"],
        message,
        current_user["salon_name"]
    )
    
    if result["success"]:
        await db.appointments.update_one(
            {"id": data.appointment_id},
            {"$set": {"sms_sent": True}}
        )
        return {"success": True, "message": "SMS inviato con successo"}
    else:
        return {"success": False, "error": result.get("error", "Errore sconosciuto")}

@api_router.get("/sms/status")
async def get_sms_status(current_user: dict = Depends(get_current_user)):
    """Check if Twilio is configured"""
    return {
        "configured": twilio_client is not None and TWILIO_PHONE_NUMBER is not None,
        "phone_number": TWILIO_PHONE_NUMBER if TWILIO_PHONE_NUMBER else None
    }

# ============== STATS ROUTES ==============

@api_router.get("/stats/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    today_appointments = await db.appointments.find(
        {"user_id": current_user["id"], "date": today, "status": {"$ne": "cancelled"}},
        {"_id": 0, "user_id": 0}
    ).sort("time", 1).to_list(100)
    
    total_clients = await db.clients.count_documents({"user_id": current_user["id"]})
    total_operators = await db.operators.count_documents({"user_id": current_user["id"], "active": True})
    
    first_of_month = datetime.now(timezone.utc).replace(day=1).strftime("%Y-%m-%d")
    last_of_month = (datetime.now(timezone.utc).replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    last_of_month = last_of_month.strftime("%Y-%m-%d")
    
    monthly_appointments = await db.appointments.find(
        {
            "user_id": current_user["id"],
            "date": {"$gte": first_of_month, "$lte": last_of_month},
            "status": "completed"
        },
        {"_id": 0}
    ).to_list(1000)
    
    monthly_revenue = sum(a.get("total_price", 0) for a in monthly_appointments)
    monthly_appointments_count = len(monthly_appointments)
    
    next_week = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    upcoming = await db.appointments.find(
        {
            "user_id": current_user["id"],
            "date": {"$gte": today, "$lte": next_week},
            "status": "scheduled"
        },
        {"_id": 0, "user_id": 0}
    ).sort([("date", 1), ("time", 1)]).to_list(10)
    
    return {
        "today_appointments": today_appointments,
        "today_appointments_count": len(today_appointments),
        "today_revenue": sum(a.get("total_price", 0) for a in today_appointments if a.get("status") == "completed"),
        "total_clients": total_clients,
        "total_operators": total_operators,
        "monthly_revenue": monthly_revenue,
        "monthly_appointments": monthly_appointments_count,
        "upcoming_appointments": upcoming
    }


@api_router.get("/stats/daily-summary")
async def get_daily_summary(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    
    today_apts = await db.appointments.find(
        {"user_id": current_user["id"], "date": target_date, "status": {"$ne": "cancelled"}},
        {"_id": 0, "user_id": 0}
    ).to_list(200)
    
    yesterday_apts = await db.appointments.find(
        {"user_id": current_user["id"], "date": yesterday, "status": {"$ne": "cancelled"}},
        {"_id": 0, "user_id": 0}
    ).to_list(200)
    
    completed = [a for a in today_apts if a.get("status") == "completed"]
    total_earnings = sum(a.get("total_paid", a.get("total_price", 0)) for a in completed)
    yesterday_earnings = sum(a.get("total_paid", a.get("total_price", 0)) for a in yesterday_apts if a.get("status") == "completed")
    
    hourly = {}
    for h in range(8, 21):
        hourly[f"{h:02d}:00"] = 0
    for apt in today_apts:
        hour = apt.get("time", "09:00")[:2] + ":00"
        if hour in hourly:
            hourly[hour] += 1
    
    service_counts = {}
    for apt in today_apts:
        for svc in apt.get("services", []):
            name = svc.get("name", "Altro")
            service_counts[name] = service_counts.get(name, 0) + 1
    top_services = sorted(service_counts.items(), key=lambda x: -x[1])[:5]
    
    unique_clients = set()
    for apt in today_apts:
        cname = apt.get("client_name", "")
        if cname:
            unique_clients.add(cname)
    
    payment_methods = {}
    for apt in completed:
        pm = apt.get("payment_method", "non specificato")
        payment_methods[pm] = payment_methods.get(pm, 0) + 1
    
    return {
        "date": target_date,
        "total_appointments": len(today_apts),
        "completed_appointments": len(completed),
        "total_earnings": total_earnings,
        "yesterday_earnings": yesterday_earnings,
        "earnings_diff": total_earnings - yesterday_earnings,
        "unique_clients": len(unique_clients),
        "avg_per_client": round(total_earnings / len(unique_clients), 2) if unique_clients else 0,
        "hourly_distribution": hourly,
        "top_services": [{"name": s[0], "count": s[1]} for s in top_services],
        "payment_methods": payment_methods,
        "busiest_hour": max(hourly, key=hourly.get) if any(hourly.values()) else None,
        "busiest_hour_count": max(hourly.values()) if any(hourly.values()) else 0,
    }


@api_router.get("/stats/revenue")
async def get_revenue_stats(
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_user)
):
    appointments = await db.appointments.find(
        {
            "user_id": current_user["id"],
            "date": {"$gte": start_date, "$lte": end_date},
            "status": "completed"
        },
        {"_id": 0}
    ).to_list(10000)
    
    # Group by date
    daily_revenue = {}
    for apt in appointments:
        date = apt["date"]
        if date not in daily_revenue:
            daily_revenue[date] = 0
        daily_revenue[date] += apt.get("total_price", 0)
    
    # Group by service
    service_revenue = {}
    for apt in appointments:
        for svc in apt.get("services", []):
            name = svc["name"]
            if name not in service_revenue:
                service_revenue[name] = {"count": 0, "revenue": 0}
            service_revenue[name]["count"] += 1
            service_revenue[name]["revenue"] += svc["price"]
    
    # Group by operator
    operator_stats = {}
    for apt in appointments:
        op_name = apt.get("operator_name", "Non assegnato")
        if op_name not in operator_stats:
            operator_stats[op_name] = {"count": 0, "revenue": 0, "color": apt.get("operator_color", "#78716C")}
        operator_stats[op_name]["count"] += 1
        operator_stats[op_name]["revenue"] += apt.get("total_price", 0)
    
    return {
        "total_revenue": sum(daily_revenue.values()),
        "total_appointments": len(appointments),
        "daily_revenue": [{"date": k, "revenue": v} for k, v in sorted(daily_revenue.items())],
        "service_breakdown": [{"name": k, **v} for k, v in sorted(service_revenue.items(), key=lambda x: x[1]["revenue"], reverse=True)],
        "operator_breakdown": [{"name": k, **v} for k, v in sorted(operator_stats.items(), key=lambda x: x[1]["revenue"], reverse=True)]
    }

@api_router.get("/stats/export-pdf")
async def export_stats_pdf(
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate PDF report of statistics"""
    # Get stats data
    appointments = await db.appointments.find(
        {
            "user_id": current_user["id"],
            "date": {"$gte": start_date, "$lte": end_date},
            "status": "completed"
        },
        {"_id": 0}
    ).to_list(10000)
    
    total_revenue = sum(a.get("total_price", 0) for a in appointments)
    total_appointments = len(appointments)
    
    # Group by service
    service_stats = {}
    for apt in appointments:
        for svc in apt.get("services", []):
            name = svc["name"]
            if name not in service_stats:
                service_stats[name] = {"count": 0, "revenue": 0}
            service_stats[name]["count"] += 1
            service_stats[name]["revenue"] += svc["price"]
    
    # Group by operator
    operator_stats = {}
    for apt in appointments:
        op_name = apt.get("operator_name", "Non assegnato")
        if op_name not in operator_stats:
            operator_stats[op_name] = {"count": 0, "revenue": 0}
        operator_stats[op_name]["count"] += 1
        operator_stats[op_name]["revenue"] += apt.get("total_price", 0)
    
    # Generate simple text-based report (CSV format for easy import)
    report_lines = []
    report_lines.append(f"REPORT STATISTICHE - {current_user['salon_name']}")
    report_lines.append(f"Periodo: {start_date} - {end_date}")
    report_lines.append("")
    report_lines.append("=" * 50)
    report_lines.append("RIEPILOGO")
    report_lines.append("=" * 50)
    report_lines.append(f"Totale Incasso: €{total_revenue:.2f}")
    report_lines.append(f"Totale Appuntamenti: {total_appointments}")
    report_lines.append(f"Media per Appuntamento: €{(total_revenue/total_appointments if total_appointments > 0 else 0):.2f}")
    report_lines.append("")
    report_lines.append("=" * 50)
    report_lines.append("SERVIZI")
    report_lines.append("=" * 50)
    for name, data in sorted(service_stats.items(), key=lambda x: x[1]["revenue"], reverse=True):
        report_lines.append(f"{name}: {data['count']} volte - €{data['revenue']:.2f}")
    report_lines.append("")
    report_lines.append("=" * 50)
    report_lines.append("OPERATORI")
    report_lines.append("=" * 50)
    for name, data in sorted(operator_stats.items(), key=lambda x: x[1]["revenue"], reverse=True):
        report_lines.append(f"{name}: {data['count']} appuntamenti - €{data['revenue']:.2f}")
    
    report_content = "\n".join(report_lines)
    
    # Return as downloadable text file
    return StreamingResponse(
        io.BytesIO(report_content.encode('utf-8')),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=report_{start_date}_{end_date}.txt"
        }
    )

# ============== SETTINGS ROUTES ==============

@api_router.put("/settings", response_model=UserResponse)
async def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": update_data}
    )
    
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        salon_name=user["salon_name"],
        created_at=user["created_at"]
    )

@api_router.get("/settings")
async def get_settings(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "salon_name": current_user["salon_name"],
        "opening_time": current_user.get("opening_time", "09:00"),
        "closing_time": current_user.get("closing_time", "19:00"),
        "working_days": current_user.get("working_days", ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"]),
        "twilio_configured": twilio_client is not None
    }

# ============== PAYMENTS API ==============

@api_router.get("/payments")
async def get_payments(start: str = None, end: str = None, current_user: dict = Depends(get_current_user)):
    """Get payments within date range"""
    query = {"user_id": current_user["id"]}
    if start and end:
        query["date"] = {"$gte": start[:10], "$lte": end[:10]}
    
    payments = await db.payments.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return payments

# ============== CLIENT HISTORY ==============

@api_router.get("/clients/{client_id}/history")
async def get_client_history(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get complete history for a client"""
    client = await db.clients.find_one(
        {"id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    # Get all appointments
    appointments = await db.appointments.find(
        {"client_id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    ).sort("date", -1).to_list(500)
    
    # Get all payments
    payments = await db.payments.find(
        {"client_id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    ).sort("date", -1).to_list(500)
    
    # Calculate totals
    total_spent = sum(p.get("total_paid", 0) for p in payments)
    total_visits = len([a for a in appointments if a.get("status") == "completed"])
    
    # Get loyalty info
    loyalty = await get_or_create_loyalty(client_id, current_user["id"])
    
    return {
        "client": client,
        "appointments": appointments,
        "payments": payments,
        "total_spent": total_spent,
        "total_visits": total_visits,
        "last_visit": appointments[0]["date"] if appointments else None,
        "loyalty_points": loyalty["points"],
        "loyalty_total_earned": loyalty["total_points_earned"],
        "active_rewards": [r for r in loyalty.get("active_rewards", []) if not r.get("redeemed")]
    }

# ============== PUBLIC BOOKING API (no auth required) ==============

@api_router.get("/public/services")
async def get_public_services():
    """Get services for public booking page"""
    # Get melitobruno's services (main user)
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0, "id": 1})
    if not user:
        # Fallback to first user
        user = await db.users.find_one({}, {"_id": 0, "id": 1})
    if not user:
        return []
    services = await db.services.find(
        {"user_id": user["id"]},
        {"_id": 0, "user_id": 0}
    ).to_list(100)
    return services

@api_router.get("/public/operators")
async def get_public_operators():
    """Get operators for public booking page"""
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0, "id": 1})
    if not user:
        user = await db.users.find_one({}, {"_id": 0, "id": 1})
    if not user:
        return []
    operators = await db.operators.find(
        {"user_id": user["id"]},
        {"_id": 0, "user_id": 0}
    ).to_list(50)
    return operators

class PublicBookingRequest(BaseModel):
    client_name: str
    client_phone: str
    service_ids: List[str]
    operator_id: Optional[str] = None
    date: str
    time: str
    notes: Optional[str] = ""

@api_router.post("/public/booking")
async def create_public_booking(data: PublicBookingRequest):
    """Create booking from public page"""
    # Get melitobruno (main user)
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0})
    if not user:
        user = await db.users.find_one({}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Salone non configurato")
    
    user_id = user["id"]
    
    # Check if time slot is available
    existing = await db.appointments.find_one({
        "user_id": user_id,
        "date": data.date,
        "time": data.time,
        "operator_id": data.operator_id if data.operator_id else {"$exists": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Orario già occupato. Scegli un altro orario.")
    
    # Get or create client
    client = await db.clients.find_one(
        {"phone": data.client_phone, "user_id": user_id},
        {"_id": 0}
    )
    
    if not client:
        client_id = str(uuid.uuid4())
        client = {
            "id": client_id,
            "user_id": user_id,
            "name": data.client_name,
            "phone": data.client_phone,
            "notes": f"[Online] {data.notes}" if data.notes else "[Prenotazione Online]",
            "send_sms_reminders": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.clients.insert_one(client)
    else:
        client_id = client["id"]
    
    # Get services
    services = await db.services.find(
        {"id": {"$in": data.service_ids}, "user_id": user_id},
        {"_id": 0, "user_id": 0}
    ).to_list(20)
    
    if not services:
        raise HTTPException(status_code=400, detail="Servizi non validi")
    
    total_duration = sum(s["duration"] for s in services)
    total_price = sum(s["price"] for s in services)
    
    # Calculate end time
    start_hour, start_min = map(int, data.time.split(":"))
    end_minutes = start_hour * 60 + start_min + total_duration
    end_time = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
    
    # Get operator info - auto-assign first active operator if none selected
    assigned_operator_id = data.operator_id or None
    operator_name = None
    operator_color = None
    if assigned_operator_id:
        operator = await db.operators.find_one({"id": assigned_operator_id, "user_id": user_id}, {"_id": 0})
        if operator:
            operator_name = operator["name"]
            operator_color = operator.get("color")
    
    if not assigned_operator_id:
        # Auto-assign to first active operator so it shows in daily planning
        first_op = await db.operators.find_one({"user_id": user_id, "active": True}, {"_id": 0})
        if first_op:
            assigned_operator_id = first_op["id"]
            operator_name = first_op["name"]
            operator_color = first_op.get("color")
    
    # Create appointment
    appointment_id = str(uuid.uuid4())
    appointment = {
        "id": appointment_id,
        "user_id": user_id,
        "client_id": client_id,
        "client_name": data.client_name,
        "service_ids": data.service_ids,
        "services": services,
        "operator_id": assigned_operator_id,
        "operator_name": operator_name,
        "operator_color": operator_color,
        "date": data.date,
        "time": data.time,
        "end_time": end_time,
        "total_duration": total_duration,
        "total_price": total_price,
        "status": "scheduled",
        "notes": f"[Online] {data.notes}" if data.notes else "[Prenotazione Online]",
        "source": "online",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appointment)
    
    return {"success": True, "appointment_id": appointment_id, "booking_code": appointment_id[:8].upper()}

# --- Public: Lookup appointment by phone ---
@api_router.get("/public/my-appointments")
async def public_lookup_appointments(phone: str):
    """Lookup appointments by phone number"""
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0})
    if not user:
        user = await db.users.find_one({}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Salone non configurato")
    
    phone_clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    client = await db.clients.find_one(
        {"user_id": user["id"], "$or": [{"phone": phone}, {"phone": phone_clean}]},
        {"_id": 0}
    )
    if not client:
        return []
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    appointments = await db.appointments.find(
        {"user_id": user["id"], "client_id": client["id"], "date": {"$gte": today}, "status": {"$ne": "cancelled"}},
        {"_id": 0, "user_id": 0}
    ).sort("date", 1).to_list(20)
    
    return [{"id": a["id"], "date": a["date"], "time": a["time"], "services": [s["name"] for s in a.get("services", [])], "operator_name": a.get("operator_name", ""), "booking_code": a["id"][:8].upper()} for a in appointments]

@api_router.put("/public/appointments/{appointment_id}")
async def public_update_appointment(appointment_id: str, data: dict):
    """Update a public appointment (date/time only)"""
    phone = data.get("phone", "")
    if not phone:
        raise HTTPException(status_code=400, detail="Numero di telefono richiesto")
    
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0})
    if not user:
        user = await db.users.find_one({}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Salone non configurato")
    
    apt = await db.appointments.find_one({"id": appointment_id, "user_id": user["id"]}, {"_id": 0})
    if not apt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    # Verify phone matches client
    client = await db.clients.find_one({"id": apt["client_id"]}, {"_id": 0})
    phone_clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not client or (client.get("phone", "").replace(" ", "").replace("-", "").replace("+", "") != phone_clean):
        raise HTTPException(status_code=403, detail="Numero non corrispondente")
    
    new_date = data.get("date", apt["date"])
    new_time = data.get("time", apt["time"])
    
    # Check availability
    existing = await db.appointments.find_one({
        "user_id": user["id"], "date": new_date, "time": new_time,
        "id": {"$ne": appointment_id},
        "operator_id": apt.get("operator_id")
    })
    if existing:
        raise HTTPException(status_code=400, detail="Orario già occupato")
    
    await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {"date": new_date, "time": new_time}}
    )
    return {"success": True}

@api_router.delete("/public/appointments/{appointment_id}")
async def public_cancel_appointment(appointment_id: str, phone: str):
    """Cancel a public appointment"""
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0})
    if not user:
        user = await db.users.find_one({}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Salone non configurato")
    
    apt = await db.appointments.find_one({"id": appointment_id, "user_id": user["id"]}, {"_id": 0})
    if not apt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    client = await db.clients.find_one({"id": apt["client_id"]}, {"_id": 0})
    phone_clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not client or (client.get("phone", "").replace(" ", "").replace("-", "").replace("+", "") != phone_clean):
        raise HTTPException(status_code=403, detail="Numero non corrispondente")
    
    await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {"status": "cancelled"}}
    )
    return {"success": True}

# --- Color Reminder: Check clients due for color service ---
@api_router.get("/reminders/color-expiry")
async def get_color_expiry_reminders(current_user: dict = Depends(get_current_user)):
    """Get clients whose last color service was 30+ days ago"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Get color-related services
    color_keywords = ["color", "colore", "tinta", "meche", "balayage", "schiaritu", "colpi di sole"]
    services = await db.services.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(200)
    color_service_ids = [s["id"] for s in services if any(kw in s["name"].lower() for kw in color_keywords)]
    
    if not color_service_ids:
        return []
    
    # Find appointments with color services
    pipeline = [
        {"$match": {"user_id": current_user["id"], "service_ids": {"$in": color_service_ids}, "status": {"$ne": "cancelled"}}},
        {"$sort": {"date": -1}},
        {"$group": {"_id": "$client_id", "last_date": {"$first": "$date"}, "last_services": {"$first": "$services"}, "client_name": {"$first": "$client_name"}}},
        {"$match": {"last_date": {"$lte": cutoff}}}
    ]
    results = await db.appointments.aggregate(pipeline).to_list(100)
    
    # Get client phones
    client_ids = [r["_id"] for r in results]
    clients = {c["id"]: c for c in await db.clients.find({"id": {"$in": client_ids}}, {"_id": 0}).to_list(100)}
    
    # Check which have already been reminded
    sent = await db.reminders_sent.find({"user_id": current_user["id"], "type": "color_expiry"}, {"_id": 0}).to_list(500)
    sent_client_ids = {s["client_id"] for s in sent}
    
    return [{
        "client_id": r["_id"],
        "client_name": r["client_name"],
        "last_color_date": r["last_date"],
        "days_ago": (datetime.now(timezone.utc) - datetime.strptime(r["last_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)).days,
        "phone": clients.get(r["_id"], {}).get("phone", ""),
        "already_sent": r["_id"] in sent_client_ids
    } for r in results]

@api_router.post("/reminders/color-expiry/{client_id}/mark-sent")
async def mark_color_reminder_sent(client_id: str, current_user: dict = Depends(get_current_user)):
    await db.reminders_sent.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "type": "color_expiry",
        "client_id": client_id,
        "sent_at": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True}

@api_router.delete("/reminders/color-expiry/{client_id}/reset")
async def reset_color_reminder(client_id: str, current_user: dict = Depends(get_current_user)):
    await db.reminders_sent.delete_many({"user_id": current_user["id"], "type": "color_expiry", "client_id": client_id})
    return {"success": True}

# --- Loyalty: Modify/Delete points ---
@api_router.put("/loyalty/{client_id}/adjust-points")
async def adjust_loyalty_points(client_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Manually adjust loyalty points for a client"""
    points = data.get("points", 0)
    reason = data.get("reason", "Modifica manuale")
    
    loyalty = await get_or_create_loyalty(client_id, current_user["id"])
    new_points = max(0, loyalty["points"] + points)
    
    await db.loyalty.update_one(
        {"client_id": client_id, "user_id": current_user["id"]},
        {"$set": {"points": new_points}}
    )
    
    # Log the adjustment
    await db.loyalty_log.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "client_id": client_id,
        "points_change": points,
        "reason": reason,
        "new_total": new_points,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "new_points": new_points}

# ============== WHATSAPP MESSAGE ==============

@api_router.get("/clients/{client_id}/whatsapp")
async def get_whatsapp_link(client_id: str, message: str = None, current_user: dict = Depends(get_current_user)):
    """Generate WhatsApp link for client"""
    client = await db.clients.find_one(
        {"id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    phone = client.get("phone", "")
    if not phone:
        raise HTTPException(status_code=400, detail="Cliente senza numero di telefono")
    
    # Clean phone number
    phone = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not phone.startswith("39"):
        phone = "39" + phone
    
    default_msg = f"Ciao {client['name']}! Ti ricordiamo il tuo appuntamento presso MBHS SALON."
    msg = message or default_msg
    
    whatsapp_url = f"https://wa.me/{phone}?text={msg}"
    
    return {"url": whatsapp_url, "phone": phone}

# ============== LOYALTY PROGRAM ==============

async def get_or_create_loyalty(client_id: str, user_id: str):
    """Get or create a loyalty record for a client"""
    loyalty = await db.loyalty.find_one(
        {"client_id": client_id, "user_id": user_id},
        {"_id": 0}
    )
    if not loyalty:
        loyalty = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "user_id": user_id,
            "points": 0,
            "total_points_earned": 0,
            "total_points_redeemed": 0,
            "history": [],
            "active_rewards": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.loyalty.insert_one(loyalty)
        loyalty.pop("_id", None)
    return loyalty

async def award_loyalty_points(client_id: str, user_id: str, amount_paid: float, appointment_id: str):
    """Award loyalty points based on amount paid. 1 point per LOYALTY_POINTS_PER_EURO €"""
    points_earned = int(amount_paid // LOYALTY_POINTS_PER_EURO)
    if points_earned <= 0:
        return 0
    
    loyalty = await get_or_create_loyalty(client_id, user_id)
    
    history_entry = {
        "id": str(uuid.uuid4()),
        "type": "earned",
        "points": points_earned,
        "description": f"+{points_earned} punti per pagamento di €{amount_paid:.2f}",
        "appointment_id": appointment_id,
        "date": datetime.now(timezone.utc).isoformat()
    }
    
    await db.loyalty.update_one(
        {"id": loyalty["id"]},
        {
            "$inc": {
                "points": points_earned,
                "total_points_earned": points_earned
            },
            "$push": {"history": history_entry}
        }
    )
    return points_earned

@api_router.get("/loyalty")
async def get_all_loyalty(current_user: dict = Depends(get_current_user)):
    """Get loyalty info for all clients"""
    loyalties = await db.loyalty.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    # Enrich with client names
    for loy in loyalties:
        client = await db.clients.find_one(
            {"id": loy["client_id"], "user_id": current_user["id"]},
            {"_id": 0, "name": 1, "phone": 1}
        )
        loy["client_name"] = client["name"] if client else "Sconosciuto"
        loy["client_phone"] = client.get("phone", "") if client else ""
    
    return loyalties

@api_router.get("/loyalty/config")
async def get_loyalty_config(current_user: dict = Depends(get_current_user)):
    """Get loyalty program configuration"""
    rewards = await get_loyalty_rewards(current_user["id"])
    return {
        "points_per_euro": LOYALTY_POINTS_PER_EURO,
        "rewards": rewards
    }

@api_router.put("/loyalty/config")
async def update_loyalty_config(data: dict, current_user: dict = Depends(get_current_user)):
    """Update loyalty rewards configuration"""
    rewards = data.get("rewards", {})
    for key, reward in rewards.items():
        reward["key"] = key
        reward["user_id"] = current_user["id"]
        await db.loyalty_rewards.update_one(
            {"key": key, "user_id": current_user["id"]},
            {"$set": reward},
            upsert=True
        )
    updated = await get_loyalty_rewards(current_user["id"])
    return {"points_per_euro": LOYALTY_POINTS_PER_EURO, "rewards": updated}

@api_router.get("/loyalty/{client_id}")
async def get_client_loyalty(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get loyalty info for a specific client"""
    client = await db.clients.find_one(
        {"id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    loyalty = await get_or_create_loyalty(client_id, current_user["id"])
    loyalty["client_name"] = client["name"]
    loyalty["rewards_config"] = await get_loyalty_rewards(current_user["id"])
    return loyalty

@api_router.post("/loyalty/{client_id}/redeem")
async def redeem_loyalty_reward(client_id: str, data: LoyaltyRedeemRequest, current_user: dict = Depends(get_current_user)):
    """Redeem a loyalty reward"""
    client = await db.clients.find_one(
        {"id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    rewards = await get_loyalty_rewards(current_user["id"])
    reward = rewards.get(data.reward_type)
    if not reward:
        raise HTTPException(status_code=400, detail="Tipo di premio non valido")
    
    loyalty = await get_or_create_loyalty(client_id, current_user["id"])
    
    if loyalty["points"] < reward["points_required"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Punti insufficienti. Necessari: {reward['points_required']}, Disponibili: {loyalty['points']}"
        )
    
    # Create reward record
    reward_record = {
        "id": str(uuid.uuid4()),
        "reward_type": data.reward_type,
        "reward_name": reward["name"],
        "points_spent": reward["points_required"],
        "redeemed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    history_entry = {
        "id": str(uuid.uuid4()),
        "type": "redeemed",
        "points": -reward["points_required"],
        "description": f"Riscattato: {reward['name']}",
        "date": datetime.now(timezone.utc).isoformat()
    }
    
    await db.loyalty.update_one(
        {"id": loyalty["id"]},
        {
            "$inc": {
                "points": -reward["points_required"],
                "total_points_redeemed": reward["points_required"]
            },
            "$push": {
                "history": history_entry,
                "active_rewards": reward_record
            }
        }
    )
    
    return {
        "success": True,
        "message": f"Premio '{reward['name']}' riscattato con successo!",
        "reward": reward_record,
        "remaining_points": loyalty["points"] - reward["points_required"]
    }

@api_router.post("/loyalty/{client_id}/use-reward/{reward_id}")
async def use_loyalty_reward(client_id: str, reward_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a reward as used"""
    loyalty = await db.loyalty.find_one(
        {"client_id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not loyalty:
        raise HTTPException(status_code=404, detail="Record fedeltà non trovato")
    
    # Find and mark the reward as redeemed
    updated = False
    active_rewards = loyalty.get("active_rewards", [])
    for r in active_rewards:
        if r["id"] == reward_id and not r["redeemed"]:
            r["redeemed"] = True
            r["used_at"] = datetime.now(timezone.utc).isoformat()
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail="Premio non trovato o già utilizzato")
    
    await db.loyalty.update_one(
        {"id": loyalty["id"]},
        {"$set": {"active_rewards": active_rewards}}
    )
    
    return {"success": True, "message": "Premio utilizzato con successo!"}

@api_router.post("/loyalty/{client_id}/add-points")
async def add_manual_points(client_id: str, points: int, description: str = "Punti aggiunti manualmente", current_user: dict = Depends(get_current_user)):
    """Manually add loyalty points to a client"""
    client = await db.clients.find_one(
        {"id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    loyalty = await get_or_create_loyalty(client_id, current_user["id"])
    
    history_entry = {
        "id": str(uuid.uuid4()),
        "type": "manual",
        "points": points,
        "description": description,
        "date": datetime.now(timezone.utc).isoformat()
    }
    
    await db.loyalty.update_one(
        {"id": loyalty["id"]},
        {
            "$inc": {
                "points": points,
                "total_points_earned": max(0, points)
            },
            "$push": {"history": history_entry}
        }
    )
    
    return {"success": True, "message": f"{points} punti aggiunti a {client['name']}"}

# ============== REMINDERS / RICHIAMI ==============

# --- Message Templates ---

class MessageTemplateCreate(BaseModel):
    name: str
    text: str
    template_type: str = "appointment"  # "appointment" or "recall"

class MessageTemplateUpdate(BaseModel):
    name: Optional[str] = None
    text: Optional[str] = None

@api_router.get("/reminders/templates")
async def get_message_templates(current_user: dict = Depends(get_current_user)):
    """Get all message templates for the user"""
    templates = await db.message_templates.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "user_id": 0}
    ).to_list(50)
    
    if not templates:
        # Create defaults
        defaults = [
            {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "name": "Promemoria Appuntamento",
                "text": "Ciao {nome}! Ti ricordiamo il tuo appuntamento domani alle {ora} presso MBHS SALON. Servizi: {servizi}. Ti aspettiamo!",
                "template_type": "appointment",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "name": "Richiamo Cliente Inattivo",
                "text": "Ciao {nome}! Sono passati {giorni} giorni dalla tua ultima visita presso MBHS SALON. Torna a trovarci, ti aspettiamo!",
                "template_type": "recall",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for d in defaults:
            await db.message_templates.insert_one(d)
        templates = [{k: v for k, v in d.items() if k not in ("_id", "user_id")} for d in defaults]
    
    return templates

@api_router.post("/reminders/templates")
async def create_message_template(data: MessageTemplateCreate, current_user: dict = Depends(get_current_user)):
    """Create a new message template"""
    template = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "name": data.name,
        "text": data.text,
        "template_type": data.template_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.message_templates.insert_one(template)
    return {k: v for k, v in template.items() if k not in ("_id", "user_id")}

@api_router.put("/reminders/templates/{template_id}")
async def update_message_template(template_id: str, data: MessageTemplateUpdate, current_user: dict = Depends(get_current_user)):
    """Update a message template"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.message_templates.update_one(
        {"id": template_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template non trovato")
    template = await db.message_templates.find_one({"id": template_id}, {"_id": 0, "user_id": 0})
    return template

@api_router.delete("/reminders/templates/{template_id}")
async def delete_message_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a message template"""
    result = await db.message_templates.delete_one({"id": template_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return {"success": True}

# --- Reminders ---

@api_router.get("/reminders/tomorrow")
async def get_tomorrow_reminders(current_user: dict = Depends(get_current_user)):
    """Get appointments for tomorrow that need a reminder"""
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    appointments = await db.appointments.find(
        {"user_id": current_user["id"], "date": tomorrow, "status": {"$ne": "cancelled"}},
        {"_id": 0}
    ).to_list(100)
    
    # Check which have already been reminded
    reminded_ids = set()
    reminders_sent = await db.reminders_sent.find(
        {"user_id": current_user["id"], "type": "appointment", "date": tomorrow},
        {"_id": 0}
    ).to_list(500)
    for r in reminders_sent:
        reminded_ids.add(r.get("appointment_id"))
    
    results = []
    for apt in appointments:
        # Get client phone from clients collection if not on appointment
        client_phone = apt.get("client_phone", "")
        if not client_phone and apt.get("client_id"):
            cl = await db.clients.find_one({"id": apt["client_id"]}, {"_id": 0})
            if cl:
                client_phone = cl.get("phone", "")
        
        results.append({
            "id": apt["id"],
            "client_name": apt.get("client_name", ""),
            "client_phone": client_phone,
            "client_id": apt.get("client_id", ""),
            "date": apt["date"],
            "time": apt["time"],
            "services": apt.get("services", []),
            "operator_name": apt.get("operator_name", ""),
            "reminded": apt["id"] in reminded_ids
        })
    
    return results

@api_router.post("/reminders/batch-mark-sent")
async def batch_mark_reminders_sent(data: dict, current_user: dict = Depends(get_current_user)):
    """Mark multiple appointment reminders as sent (for batch WhatsApp send)"""
    appointment_ids = data.get("appointment_ids", [])
    if not appointment_ids:
        raise HTTPException(status_code=400, detail="Nessun appuntamento specificato")
    
    count = 0
    for apt_id in appointment_ids:
        apt = await db.appointments.find_one(
            {"id": apt_id, "user_id": current_user["id"]},
            {"_id": 0}
        )
        if apt:
            # Check if already sent
            existing = await db.reminders_sent.find_one(
                {"user_id": current_user["id"], "type": "appointment", "appointment_id": apt_id}
            )
            if not existing:
                await db.reminders_sent.insert_one({
                    "id": str(uuid.uuid4()),
                    "user_id": current_user["id"],
                    "type": "appointment",
                    "appointment_id": apt_id,
                    "client_id": apt.get("client_id"),
                    "date": apt["date"],
                    "sent_at": datetime.now(timezone.utc).isoformat()
                })
                count += 1
    
    return {"success": True, "marked_count": count}

@api_router.get("/reminders/auto-check")
async def auto_reminder_check(current_user: dict = Depends(get_current_user)):
    """Check if it's time to send reminders (after 15:00) and return pending ones"""
    now = datetime.now(timezone.utc)
    # Italian time is UTC+1 (or UTC+2 in summer). We check if current UTC hour >= 14 (which is ~15:00 in Italy)
    is_reminder_time = now.hour >= 14
    
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    appointments = await db.appointments.find(
        {"user_id": current_user["id"], "date": tomorrow, "status": {"$ne": "cancelled"}},
        {"_id": 0}
    ).to_list(100)
    
    reminded_ids = set()
    reminders_sent = await db.reminders_sent.find(
        {"user_id": current_user["id"], "type": "appointment", "date": tomorrow},
        {"_id": 0}
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
            if client_phone:  # only include clients with phone
                pending.append({
                    "id": apt["id"],
                    "client_name": apt.get("client_name", ""),
                    "client_phone": client_phone,
                    "time": apt["time"],
                    "services": apt.get("services", []),
                })
    
    return {
        "is_reminder_time": is_reminder_time,
        "tomorrow_date": tomorrow,
        "total_tomorrow": len(appointments),
        "already_sent": len(reminded_ids),
        "pending": pending
    }

@api_router.post("/reminders/appointment/{appointment_id}/mark-sent")
async def mark_reminder_sent(appointment_id: str, current_user: dict = Depends(get_current_user)):
    """Mark an appointment reminder as sent"""
    apt = await db.appointments.find_one(
        {"id": appointment_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not apt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    await db.reminders_sent.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "type": "appointment",
        "appointment_id": appointment_id,
        "client_id": apt.get("client_id"),
        "date": apt["date"],
        "sent_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True}

@api_router.delete("/reminders/appointment/{appointment_id}/reset")
async def reset_reminder(appointment_id: str, current_user: dict = Depends(get_current_user)):
    """Reset (un-mark) an appointment reminder so it can be resent"""
    result = await db.reminders_sent.delete_many(
        {"user_id": current_user["id"], "type": "appointment", "appointment_id": appointment_id}
    )
    return {"success": True, "deleted": result.deleted_count}

@api_router.get("/reminders/inactive-clients")
async def get_inactive_clients(current_user: dict = Depends(get_current_user)):
    """Get clients who haven't visited in 60+ days"""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
    
    # Get all clients
    clients = await db.clients.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    # Check which have already been recalled recently (within 30 days)
    recent_recalls = await db.reminders_sent.find(
        {
            "user_id": current_user["id"],
            "type": "inactive_recall",
            "sent_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}
        },
        {"_id": 0}
    ).to_list(500)
    recently_recalled_ids = {r.get("client_id") for r in recent_recalls}
    
    inactive = []
    for client in clients:
        # Find their most recent completed appointment
        last_apt = await db.appointments.find_one(
            {
                "client_id": client["id"],
                "user_id": current_user["id"],
                "status": "completed"
            },
            {"_id": 0},
            sort=[("date", -1)]
        )
        
        if last_apt and last_apt["date"] <= cutoff_date:
            days_ago = (datetime.now(timezone.utc) - datetime.strptime(last_apt["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)).days
            inactive.append({
                "client_id": client["id"],
                "client_name": client["name"],
                "client_phone": client.get("phone", ""),
                "last_visit": last_apt["date"],
                "days_ago": days_ago,
                "last_services": [s.get("name", "") for s in last_apt.get("services", [])],
                "already_recalled": client["id"] in recently_recalled_ids
            })
    
    # Sort by days_ago descending
    inactive.sort(key=lambda x: x["days_ago"], reverse=True)
    return inactive

@api_router.post("/reminders/inactive/{client_id}/mark-sent")
async def mark_inactive_recall_sent(client_id: str, current_user: dict = Depends(get_current_user)):
    """Mark an inactive client recall as sent"""
    client = await db.clients.find_one(
        {"id": client_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    await db.reminders_sent.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "type": "inactive_recall",
        "client_id": client_id,
        "sent_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True}

@api_router.delete("/reminders/inactive/{client_id}/reset")
async def reset_inactive_recall(client_id: str, current_user: dict = Depends(get_current_user)):
    """Reset an inactive recall so it can be resent"""
    result = await db.reminders_sent.delete_many(
        {"user_id": current_user["id"], "type": "inactive_recall", "client_id": client_id}
    )
    return {"success": True, "deleted": result.deleted_count}

# ============== CARD TEMPLATES / PACCHETTI PREIMPOSTATI ==============

class CardTemplateCreate(BaseModel):
    name: str
    card_type: str = "prepaid"  # "prepaid" or "subscription"
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

@api_router.get("/card-templates")
async def get_card_templates(current_user: dict = Depends(get_current_user)):
    """Get all card/package templates"""
    templates = await db.card_templates.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "user_id": 0}
    ).sort("created_at", -1).to_list(50)
    return templates

@api_router.post("/card-templates")
async def create_card_template(data: CardTemplateCreate, current_user: dict = Depends(get_current_user)):
    """Create a card/package template"""
    template = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "name": data.name,
        "card_type": data.card_type,
        "total_value": data.total_value,
        "total_services": data.total_services,
        "duration_months": data.duration_months,
        "notes": data.notes or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.card_templates.insert_one(template)
    return {k: v for k, v in template.items() if k not in ("_id", "user_id")}

@api_router.put("/card-templates/{template_id}")
async def update_card_template(template_id: str, data: CardTemplateUpdate, current_user: dict = Depends(get_current_user)):
    """Update a card template"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.card_templates.update_one(
        {"id": template_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template non trovato")
    template = await db.card_templates.find_one({"id": template_id}, {"_id": 0, "user_id": 0})
    return template

@api_router.delete("/card-templates/{template_id}")
async def delete_card_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a card template"""
    result = await db.card_templates.delete_one({"id": template_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return {"success": True}

# ============== REGISTRO USCITE / SCADENZIARIO ==============

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: str = "altro"  # affitto, fornitori, bollette, stipendi, tasse, altro
    due_date: str  # YYYY-MM-DD
    is_recurring: bool = False
    recurrence: Optional[str] = None  # monthly, quarterly, yearly
    notes: Optional[str] = ""

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    due_date: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence: Optional[str] = None
    notes: Optional[str] = None
    paid: Optional[bool] = None
    paid_date: Optional[str] = None

@api_router.get("/expenses")
async def get_expenses(
    paid: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all expenses, optionally filtered by paid status"""
    query = {"user_id": current_user["id"]}
    if paid is not None:
        query["paid"] = paid
    expenses = await db.expenses.find(query, {"_id": 0, "user_id": 0}).sort("due_date", 1).to_list(500)
    return expenses

@api_router.post("/expenses")
async def create_expense(data: ExpenseCreate, current_user: dict = Depends(get_current_user)):
    """Create a new expense"""
    expense = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "description": data.description,
        "amount": data.amount,
        "category": data.category,
        "due_date": data.due_date,
        "is_recurring": data.is_recurring,
        "recurrence": data.recurrence,
        "notes": data.notes or "",
        "paid": False,
        "paid_date": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.expenses.insert_one(expense)
    return {k: v for k, v in expense.items() if k not in ("_id", "user_id")}

@api_router.put("/expenses/{expense_id}")
async def update_expense(expense_id: str, data: ExpenseUpdate, current_user: dict = Depends(get_current_user)):
    """Update an expense"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    result = await db.expenses.update_one(
        {"id": expense_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Uscita non trovata")
    
    expense = await db.expenses.find_one({"id": expense_id}, {"_id": 0, "user_id": 0})
    return expense

@api_router.post("/expenses/{expense_id}/pay")
async def mark_expense_paid(expense_id: str, current_user: dict = Depends(get_current_user)):
    """Mark an expense as paid"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = await db.expenses.update_one(
        {"id": expense_id, "user_id": current_user["id"]},
        {"$set": {"paid": True, "paid_date": today}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Uscita non trovata")
    
    # If recurring, create the next occurrence
    expense = await db.expenses.find_one({"id": expense_id}, {"_id": 0})
    if expense and expense.get("is_recurring") and expense.get("recurrence"):
        due = datetime.strptime(expense["due_date"], "%Y-%m-%d")
        if expense["recurrence"] == "monthly":
            next_due = due.replace(month=due.month % 12 + 1) if due.month < 12 else due.replace(year=due.year + 1, month=1)
        elif expense["recurrence"] == "quarterly":
            next_month = due.month + 3
            next_year = due.year + (next_month - 1) // 12
            next_month = ((next_month - 1) % 12) + 1
            next_due = due.replace(year=next_year, month=next_month)
        elif expense["recurrence"] == "yearly":
            next_due = due.replace(year=due.year + 1)
        else:
            next_due = None
        
        if next_due:
            new_expense = {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "description": expense["description"],
                "amount": expense["amount"],
                "category": expense["category"],
                "due_date": next_due.strftime("%Y-%m-%d"),
                "is_recurring": True,
                "recurrence": expense["recurrence"],
                "notes": expense.get("notes", ""),
                "paid": False,
                "paid_date": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.expenses.insert_one(new_expense)
    
    return {"success": True}

@api_router.post("/expenses/{expense_id}/unpay")
async def mark_expense_unpaid(expense_id: str, current_user: dict = Depends(get_current_user)):
    """Mark an expense as unpaid"""
    result = await db.expenses.update_one(
        {"id": expense_id, "user_id": current_user["id"]},
        {"$set": {"paid": False, "paid_date": None}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Uscita non trovata")
    return {"success": True}

@api_router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an expense"""
    result = await db.expenses.delete_one({"id": expense_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Uscita non trovata")
    return {"success": True}

@api_router.get("/expenses/upcoming")
async def get_upcoming_expenses(days: int = 7, current_user: dict = Depends(get_current_user)):
    """Get unpaid expenses due within the next N days"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    future = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
    
    expenses = await db.expenses.find(
        {
            "user_id": current_user["id"],
            "paid": False,
            "due_date": {"$lte": future}
        },
        {"_id": 0, "user_id": 0}
    ).sort("due_date", 1).to_list(50)
    
    # Mark overdue ones
    for exp in expenses:
        exp["overdue"] = exp["due_date"] < today
    
    return expenses

@api_router.get("/")
async def root():
    return {"message": "Salone Parrucchiera API", "status": "ok"}

# ============== PROMOZIONI ==============

class PromoCreate(BaseModel):
    name: str
    description: str
    rule_type: str  # under_30, first_visit, birthday, bring_friend, google_review, fidelity_vip, promo_code
    free_service_name: str
    promo_code: Optional[str] = None
    active: bool = True
    show_on_booking: bool = True

class PromoUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    free_service_name: Optional[str] = None
    promo_code: Optional[str] = None
    active: Optional[bool] = None
    show_on_booking: Optional[bool] = None

async def seed_default_promotions(user_id: str):
    """Seed default promotions if none exist for this user"""
    defaults = [
        {"name": "Speciale Under 30", "description": "Piega o trattamento lucidante GRATIS con qualsiasi servizio colore per le under 30", "rule_type": "under_30", "free_service_name": "Piega o Trattamento Lucidante", "promo_code": "UNDER30"},
        {"name": "Recensione Google", "description": "Lascia una recensione con foto su Google e ricevi un trattamento Olaplex o Maschera Ristrutturante IN OMAGGIO alla prossima visita", "rule_type": "review", "free_service_name": "Maschera Ristrutturante o Olaplex", "promo_code": "REVIEW"},
        {"name": "Porta un'Amica", "description": "Porta un'amica e ricevete entrambe un servizio extra GRATIS (taglio punte o trattamento)", "rule_type": "referral", "free_service_name": "Taglio Punte o Trattamento", "promo_code": "AMICA"},
        {"name": "Prima Visita", "description": "Per i nuovi clienti: consulenza colore personalizzata + trattamento IN OMAGGIO", "rule_type": "first_visit", "free_service_name": "Consulenza Colore + Trattamento", "promo_code": "BENVENUTA"},
        {"name": "Buon Compleanno!", "description": "Nel mese del tuo compleanno ricevi una piega o trattamento IN OMAGGIO con qualsiasi servizio", "rule_type": "birthday", "free_service_name": "Piega o Trattamento", "promo_code": "AUGURI"},
        {"name": "Fidelity VIP", "description": "Dopo 10 visite ricevi un servizio a scelta IN OMAGGIO", "rule_type": "loyalty_vip", "free_service_name": "Servizio a Scelta", "promo_code": "VIP10"},
        {"name": "Card Prepagata -15%", "description": "Acquista una card prepagata e ottieni il 15% di sconto su tutti i servizi", "rule_type": "promo_code", "free_service_name": "Sconto 15% su tutti i servizi", "promo_code": "CARD15"},
        {"name": "Abbonamento Mensile + Piega Omaggio", "description": "Sottoscrivi un abbonamento mensile e ricevi una piega extra IN OMAGGIO ogni mese", "rule_type": "promo_code", "free_service_name": "Piega Omaggio Mensile", "promo_code": "ABBO"},
    ]
    for d in defaults:
        promo = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": d["name"],
            "description": d["description"],
            "rule_type": d["rule_type"],
            "free_service_name": d["free_service_name"],
            "promo_code": d["promo_code"],
            "active": True,
            "show_on_booking": True,
            "usage_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.promotions.insert_one(promo)

@api_router.get("/promotions")
async def get_promotions(current_user: dict = Depends(get_current_user)):
    """Get all promotions"""
    promos = await db.promotions.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "user_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Auto-seed defaults if no promotions exist
    if not promos:
        await seed_default_promotions(current_user["id"])
        promos = await db.promotions.find(
            {"user_id": current_user["id"]},
            {"_id": 0, "user_id": 0}
        ).sort("created_at", -1).to_list(50)
    
    # Get usage counts
    for promo in promos:
        count = await db.promo_usage.count_documents({"promo_id": promo["id"]})
        promo["usage_count"] = count
    
    return promos

@api_router.post("/promotions")
async def create_promotion(data: PromoCreate, current_user: dict = Depends(get_current_user)):
    """Create a new promotion"""
    code = data.promo_code
    if not code and data.rule_type == "promo_code":
        code = f"MBHS{uuid.uuid4().hex[:6].upper()}"
    elif not code:
        code = data.rule_type.upper()[:4] + uuid.uuid4().hex[:4].upper()
    
    promo = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "name": data.name,
        "description": data.description,
        "rule_type": data.rule_type,
        "free_service_name": data.free_service_name,
        "promo_code": code,
        "active": data.active,
        "show_on_booking": data.show_on_booking,
        "usage_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.promotions.insert_one(promo)
    return {k: v for k, v in promo.items() if k not in ("_id", "user_id")}

@api_router.put("/promotions/{promo_id}")
async def update_promotion(promo_id: str, data: PromoUpdate, current_user: dict = Depends(get_current_user)):
    """Update a promotion"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    result = await db.promotions.update_one(
        {"id": promo_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promozione non trovata")
    promo = await db.promotions.find_one({"id": promo_id}, {"_id": 0, "user_id": 0})
    count = await db.promo_usage.count_documents({"promo_id": promo_id})
    promo["usage_count"] = count
    return promo

@api_router.delete("/promotions/{promo_id}")
async def delete_promotion(promo_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a promotion"""
    result = await db.promotions.delete_one({"id": promo_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Promozione non trovata")
    return {"success": True}

@api_router.get("/promotions/check/{client_id}")
async def check_client_promotions(client_id: str, current_user: dict = Depends(get_current_user)):
    """Check which promotions a client is eligible for (at checkout)"""
    promos = await db.promotions.find(
        {"user_id": current_user["id"], "active": True},
        {"_id": 0, "user_id": 0}
    ).to_list(50)
    
    eligible = []
    
    for promo in promos:
        rt = promo["rule_type"]
        
        if rt == "first_visit":
            # Check if client has any completed appointments
            count = await db.appointments.count_documents({
                "client_id": client_id,
                "user_id": current_user["id"],
                "status": "completed"
            })
            if count == 0:
                eligible.append(promo)
        
        elif rt == "fidelity_vip":
            # Check if 10+ visits
            count = await db.appointments.count_documents({
                "client_id": client_id,
                "user_id": current_user["id"],
                "status": "completed"
            })
            if count >= 10:
                # Check not already used in last 30 days
                recent = await db.promo_usage.find_one({
                    "promo_id": promo["id"],
                    "client_id": client_id,
                    "used_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}
                })
                if not recent:
                    eligible.append(promo)
        
        else:
            # under_30, birthday, bring_friend, google_review, promo_code → always suggest, operator decides
            eligible.append(promo)
    
    return eligible

@api_router.post("/promotions/{promo_id}/use")
async def use_promotion(promo_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Record usage of a promotion"""
    promo = await db.promotions.find_one(
        {"id": promo_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not promo:
        raise HTTPException(status_code=404, detail="Promozione non trovata")
    
    usage = {
        "id": str(uuid.uuid4()),
        "promo_id": promo_id,
        "user_id": current_user["id"],
        "client_id": data.get("client_id", ""),
        "client_name": data.get("client_name", ""),
        "appointment_id": data.get("appointment_id", ""),
        "free_service": promo["free_service_name"],
        "used_at": datetime.now(timezone.utc).isoformat()
    }
    await db.promo_usage.insert_one(usage)
    return {"success": True}

@api_router.post("/promotions/{promo_id}/validate-code")
async def validate_promo_code(promo_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Validate a promo code"""
    code = data.get("code", "")
    promo = await db.promotions.find_one(
        {"id": promo_id, "user_id": current_user["id"], "promo_code": code, "active": True},
        {"_id": 0, "user_id": 0}
    )
    if not promo:
        raise HTTPException(status_code=404, detail="Codice non valido")
    return promo

# Public endpoint for promotions on booking page
@api_router.get("/public/promotions/all")
async def get_all_public_promotions():
    """Get all active public promotions (for the shared booking page)"""
    promos = await db.promotions.find(
        {"active": True, "show_on_booking": True},
        {"_id": 0, "user_id": 0}
    ).to_list(20)
    return promos

@api_router.get("/public/promotions/{user_id}")
async def get_public_promotions(user_id: str):
    """Get active promotions for the public booking page"""
    promos = await db.promotions.find(
        {"user_id": user_id, "active": True, "show_on_booking": True},
        {"_id": 0, "user_id": 0}
    ).to_list(20)
    return promos

# ============== WEBSITE CMS ==============

# Object Storage config
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "mbhssalon"
_storage_key = None

def init_storage():
    global _storage_key
    if _storage_key:
        return _storage_key
    resp = http_requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    return _storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = http_requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str):
    key = init_storage()
    resp = http_requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# Default website config
DEFAULT_WEBSITE_CONFIG = {
    "salon_name": "BRUNO MELITO HAIR",
    "slogan": "Metti la testa a posto!!",
    "subtitle": "SOLO PER APPUNTAMENTO",
    "hero_description": "Scopri l'eccellenza dell'hair styling al Bruno Melito Hair. Dove ogni taglio e' un'opera d'arte e ogni cliente e' unica.",
    "about_title": "Dal 1983 con Passione",
    "about_text": "Dal 1983 con grande soddisfazione nostra e delle clienti che ci seguono, siamo un punto di riferimento per chi cerca qualita' e professionalita' nell'hair styling.",
    "about_text_2": "Abbiamo introdotto una nuova linea di prodotti altamente curativi, di ultima generazione: shampoo, maschere e finishing, senza parabeni, solfati e sale. Le colorazioni e le schiariture sono senza ammoniaca, ma con cheratina, olio di semi di lino, proteine della seta e olio di argan.",
    "about_features": ["Dal 1983 nel settore", "Senza parabeni e solfati", "Colorazioni senza ammoniaca", "Cheratina e olio di argan"],
    "years_experience": "40+",
    "year_founded": "1983",
    "phones": ["0823 18 78 320", "339 78 33 526"],
    "email": "melitobruno@gmail.com",
    "address": "Via Vito Nicola Melorio 101, Santa Maria Capua Vetere (CE)",
    "maps_url": "https://maps.google.com/?q=Via+Vito+Nicola+Melorio+101+Santa+Maria+Capua+Vetere",
    "whatsapp": "393397833526",
    "hours": {"mar": "08:00 - 19:00", "mer": "08:00 - 19:00", "gio": "08:00 - 19:00", "ven": "08:00 - 19:00", "sab": "08:00 - 19:00", "dom": "Chiuso", "lun": "Chiuso"},
    "service_categories": [
        {"title": "Taglio & Piega", "desc": "", "items": [{"name": "Taglio", "price": "10"}, {"name": "Piega Corti", "price": "10"}, {"name": "Piega Lunghi", "price": "12"}, {"name": "Piega Fantasy", "price": "15"}, {"name": "Piastra/Ferro", "price": "+ 3"}]},
        {"title": "Colorazione", "desc": "Tutte le colorazioni sono senza ammoniaca, con cheratina e olio di argan", "items": [{"name": "Colorazione Parziale / Completa / Cuffia / Cartine / Balayage / Giochi di Colore", "price": "Da 30"}]},
        {"title": "Modellanti", "desc": "", "items": [{"name": "Permanente / Ondulazione / Anticrespo / Stiratura Classica", "price": "Da 40"}]}
    ],
    "gallery_title": "Tendenze P/E 2026",
    "gallery_subtitle": "Lasciati ispirare dalle ultime tendenze Primavera Estate 2026."
}

# --- Upload endpoint ---
@api_router.post("/website/upload")
async def website_upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
        raise HTTPException(status_code=400, detail="Formato non supportato. Usa JPG, PNG, GIF o WebP.")
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
    file_id = str(uuid.uuid4())
    path = f"{APP_NAME}/uploads/{file_id}.{ext}"
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 10MB.")
    result = put_object(path, data, mime_map.get(ext, "image/jpeg"))
    doc = {
        "id": file_id,
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": mime_map.get(ext, "image/jpeg"),
        "size": result.get("size", len(data)),
        "is_deleted": False,
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.website_files.insert_one(doc)
    return {"id": file_id, "path": result["path"], "url": f"/api/website/files/{file_id}"}

# --- Serve uploaded files (PUBLIC) ---
@api_router.get("/website/files/{file_id}")
async def website_serve_file(file_id: str):
    record = await db.website_files.find_one({"id": file_id, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File non trovato")
    data, content_type = get_object(record["storage_path"])
    return Response(content=data, media_type=record.get("content_type", content_type))

# --- Website Config CRUD ---
@api_router.get("/website/config")
async def get_website_config(current_user: dict = Depends(get_current_user)):
    config = await db.website_config.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not config:
        return {**DEFAULT_WEBSITE_CONFIG, "user_id": current_user["id"]}
    # Merge with defaults for missing fields
    merged = {**DEFAULT_WEBSITE_CONFIG, **config}
    return merged

@api_router.put("/website/config")
async def update_website_config(data: dict, current_user: dict = Depends(get_current_user)):
    data["user_id"] = current_user["id"]
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.website_config.update_one(
        {"user_id": current_user["id"]},
        {"$set": data},
        upsert=True
    )
    config = await db.website_config.find_one({"user_id": current_user["id"]}, {"_id": 0})
    return config

# --- Website Reviews CRUD ---
@api_router.get("/website/reviews")
async def get_website_reviews(current_user: dict = Depends(get_current_user)):
    reviews = await db.website_reviews.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    return reviews

@api_router.post("/website/reviews")
async def create_website_review(data: dict, current_user: dict = Depends(get_current_user)):
    review = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "name": data.get("name", ""),
        "text": data.get("text", ""),
        "rating": data.get("rating", 5),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.website_reviews.insert_one(review)
    return {k: v for k, v in review.items() if k != "_id"}

@api_router.put("/website/reviews/{review_id}")
async def update_website_review(review_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    await db.website_reviews.update_one(
        {"id": review_id, "user_id": current_user["id"]},
        {"$set": {"name": data.get("name"), "text": data.get("text"), "rating": data.get("rating", 5)}}
    )
    review = await db.website_reviews.find_one({"id": review_id}, {"_id": 0})
    return review

@api_router.delete("/website/reviews/{review_id}")
async def delete_website_review(review_id: str, current_user: dict = Depends(get_current_user)):
    await db.website_reviews.delete_one({"id": review_id, "user_id": current_user["id"]})
    return {"success": True}

# --- Website Gallery CRUD ---
@api_router.get("/website/gallery")
async def get_website_gallery(current_user: dict = Depends(get_current_user)):
    items = await db.website_gallery.find({"user_id": current_user["id"], "is_deleted": {"$ne": True}}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return items

@api_router.post("/website/gallery")
async def create_website_gallery_item(data: dict, current_user: dict = Depends(get_current_user)):
    count = await db.website_gallery.count_documents({"user_id": current_user["id"], "is_deleted": {"$ne": True}})
    item = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "image_url": data.get("image_url", ""),
        "label": data.get("label", ""),
        "tag": data.get("tag", ""),
        "section": data.get("section", "gallery"),
        "sort_order": count,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.website_gallery.insert_one(item)
    return {k: v for k, v in item.items() if k != "_id"}

@api_router.put("/website/gallery/{item_id}")
async def update_website_gallery_item(item_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    update_data = {}
    for key in ["label", "tag", "sort_order", "section", "image_url"]:
        if key in data:
            update_data[key] = data[key]
    if update_data:
        await db.website_gallery.update_one({"id": item_id, "user_id": current_user["id"]}, {"$set": update_data})
    item = await db.website_gallery.find_one({"id": item_id}, {"_id": 0})
    return item

@api_router.delete("/website/gallery/{item_id}")
async def delete_website_gallery_item(item_id: str, current_user: dict = Depends(get_current_user)):
    await db.website_gallery.update_one({"id": item_id, "user_id": current_user["id"]}, {"$set": {"is_deleted": True}})
    return {"success": True}

# --- PUBLIC Website endpoints (no auth) ---
@api_router.get("/public/website")
async def public_get_website():
    config = await db.website_config.find_one({}, {"_id": 0, "user_id": 0})
    if not config:
        config = {k: v for k, v in DEFAULT_WEBSITE_CONFIG.items()}
    else:
        config = {**DEFAULT_WEBSITE_CONFIG, **{k: v for k, v in config.items() if k != "user_id"}}
    reviews = await db.website_reviews.find({}, {"_id": 0, "user_id": 0}).to_list(100)
    gallery = await db.website_gallery.find({"is_deleted": {"$ne": True}}, {"_id": 0, "user_id": 0}).sort("sort_order", 1).to_list(100)
    services = await db.services.find({}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return {"config": config, "reviews": reviews, "gallery": gallery, "services": services}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_event():
    try:
        init_storage()
        logger.info("Object storage initialized")
    except Exception as e:
        logger.warning(f"Object storage init deferred: {e}")
