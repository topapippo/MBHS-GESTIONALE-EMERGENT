from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
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

class ServiceResponse(BaseModel):
    id: str
    name: str
    category: str
    duration: int
    price: float
    created_at: str

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None

# Appointment Models
class AppointmentCreate(BaseModel):
    client_id: str
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
    repeat_weeks: int  # Every X weeks
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
    ).sort("category", 1).to_list(1000)
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
    # Get client
    client = await db.clients.find_one(
        {"id": data.client_id, "user_id": current_user["id"]}, 
        {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
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
        "client_id": data.client_id,
        "client_name": client["name"],
        "client_phone": client.get("phone", ""),
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
    payment_method: str = "cash"  # cash, card, transfer, prepaid
    discount_type: str = "none"   # none, percent, fixed
    discount_value: float = 0
    total_paid: float

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
    if data.payment_method == "prepaid":
        # Find client's active prepaid card
        card = await db.cards.find_one({
            "client_id": appointment["client_id"],
            "user_id": current_user["id"],
            "active": True,
            "remaining_value": {"$gte": data.total_paid}
        })
        if card:
            new_remaining = card["remaining_value"] - data.total_paid
            transaction = {
                "date": datetime.now(timezone.utc).isoformat(),
                "description": f"Servizi: {', '.join([s['name'] for s in appointment['services']])}",
                "amount": data.total_paid
            }
            await db.cards.update_one(
                {"id": card["id"]},
                {
                    "$set": {"remaining_value": new_remaining},
                    "$push": {"transactions": transaction}
                }
            )
    
    # Award loyalty points and check thresholds
    loyalty_before = await get_or_create_loyalty(appointment["client_id"], current_user["id"])
    points_before = loyalty_before["points"]
    points_earned = await award_loyalty_points(
        appointment["client_id"], current_user["id"], data.total_paid, appointment_id
    )
    points_after = points_before + points_earned
    
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
    
    # Get operator info
    operator_name = None
    operator_color = None
    if data.operator_id:
        operator = await db.operators.find_one({"id": data.operator_id, "user_id": user_id}, {"_id": 0})
        if operator:
            operator_name = operator["name"]
            operator_color = operator.get("color")
    
    # Create appointment
    appointment_id = str(uuid.uuid4())
    appointment = {
        "id": appointment_id,
        "user_id": user_id,
        "client_id": client_id,
        "client_name": data.client_name,
        "service_ids": data.service_ids,
        "services": services,
        "operator_id": data.operator_id,
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
    
    return {"success": True, "appointment_id": appointment_id}

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
        results.append({
            "id": apt["id"],
            "client_name": apt.get("client_name", ""),
            "client_phone": apt.get("client_phone", ""),
            "client_id": apt.get("client_id", ""),
            "date": apt["date"],
            "time": apt["time"],
            "services": apt.get("services", []),
            "reminded": apt["id"] in reminded_ids
        })
    
    return results

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

@api_router.get("/reminders/inactive-clients")
async def get_inactive_clients(current_user: dict = Depends(get_current_user)):
    """Get clients who haven't visited in 60+ days"""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
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

# ============== HEALTH CHECK ==============

@api_router.get("/")
async def root():
    return {"message": "Salone Parrucchiera API", "status": "ok"}

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
