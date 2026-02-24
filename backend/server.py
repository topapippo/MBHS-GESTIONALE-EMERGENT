from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# Client Models
class ClientCreate(BaseModel):
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    notes: Optional[str] = ""

class ClientResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: str
    notes: str
    created_at: str
    total_visits: int = 0

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None

# Service Models
class ServiceCreate(BaseModel):
    name: str
    category: str  # taglio, colore, piega, trattamento
    duration: int  # minutes
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
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    notes: Optional[str] = ""

class AppointmentResponse(BaseModel):
    id: str
    client_id: str
    client_name: str
    service_ids: List[str]
    services: List[dict]
    date: str
    time: str
    end_time: str
    total_duration: int
    total_price: float
    status: str  # scheduled, completed, cancelled
    notes: str
    created_at: str

class AppointmentUpdate(BaseModel):
    client_id: Optional[str] = None
    service_ids: Optional[List[str]] = None
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# Settings Model
class SettingsUpdate(BaseModel):
    salon_name: Optional[str] = None
    name: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    working_days: Optional[List[str]] = None

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

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(data: UserCreate):
    # Check if user exists
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

# ============== CLIENT ROUTES ==============

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
    
    client = await db.clients.find_one(
        {"id": client_id}, 
        {"_id": 0, "user_id": 0}
    )
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
    
    service = await db.services.find_one(
        {"id": service_id}, 
        {"_id": 0, "user_id": 0}
    )
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
    
    total_duration = sum(s["duration"] for s in services)
    total_price = sum(s["price"] for s in services)
    end_time = calculate_end_time(data.time, total_duration)
    
    appointment_id = str(uuid.uuid4())
    appointment_doc = {
        "id": appointment_id,
        "user_id": current_user["id"],
        "client_id": data.client_id,
        "client_name": client["name"],
        "service_ids": data.service_ids,
        "services": [{"id": s["id"], "name": s["name"], "duration": s["duration"], "price": s["price"]} for s in services],
        "date": data.date,
        "time": data.time,
        "end_time": end_time,
        "total_duration": total_duration,
        "total_price": total_price,
        "status": "scheduled",
        "notes": data.notes or "",
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
    current_user: dict = Depends(get_current_user)
):
    query = {"user_id": current_user["id"]}
    
    if date:
        query["date"] = date
    elif start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    
    if status:
        query["status"] = status
    
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
    
    if data.date:
        update_data["date"] = data.date
    if data.time:
        update_data["time"] = data.time
    if data.status:
        update_data["status"] = data.status
        # Update client visits if completed
        if data.status == "completed":
            await db.clients.update_one(
                {"id": appointment["client_id"]},
                {"$inc": {"total_visits": 1}}
            )
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    # Recalculate end time if time or services changed
    if "time" in update_data or "total_duration" in update_data:
        time = update_data.get("time", appointment["time"])
        duration = update_data.get("total_duration", appointment["total_duration"])
        update_data["end_time"] = calculate_end_time(time, duration)
    
    if update_data:
        await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": update_data}
        )
    
    updated = await db.appointments.find_one(
        {"id": appointment_id}, 
        {"_id": 0, "user_id": 0}
    )
    return updated

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.appointments.delete_one({"id": appointment_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return {"message": "Appuntamento eliminato"}

# ============== STATS ROUTES ==============

@api_router.get("/stats/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Today's appointments
    today_appointments = await db.appointments.find(
        {"user_id": current_user["id"], "date": today, "status": {"$ne": "cancelled"}},
        {"_id": 0, "user_id": 0}
    ).sort("time", 1).to_list(100)
    
    # Total clients
    total_clients = await db.clients.count_documents({"user_id": current_user["id"]})
    
    # This month stats
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
    
    # Upcoming appointments (next 7 days)
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
        "monthly_revenue": monthly_revenue,
        "monthly_appointments": monthly_appointments_count,
        "upcoming_appointments": upcoming
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
    
    return {
        "total_revenue": sum(daily_revenue.values()),
        "total_appointments": len(appointments),
        "daily_revenue": [{"date": k, "revenue": v} for k, v in sorted(daily_revenue.items())],
        "service_breakdown": [{"name": k, **v} for k, v in sorted(service_revenue.items(), key=lambda x: x[1]["revenue"], reverse=True)]
    }

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
        "working_days": current_user.get("working_days", ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"])
    }

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
