from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database import db


# ============== USER ==============

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


# ============== OPERATOR ==============

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


# ============== CLIENT ==============

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

class ClientBulkImport(BaseModel):
    clients: List[dict]


# ============== SERVICE ==============

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


# ============== APPOINTMENT ==============

class AppointmentCreate(BaseModel):
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = ""
    service_ids: List[str]
    operator_id: Optional[str] = None
    date: str
    time: str
    notes: Optional[str] = ""
    promo_id: Optional[str] = None
    card_id: Optional[str] = None

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
    promo_id: Optional[str] = None
    promo_name: Optional[str] = None
    card_id: Optional[str] = None
    card_name: Optional[str] = None
    created_at: str

class AppointmentUpdate(BaseModel):
    client_id: Optional[str] = None
    service_ids: Optional[List[str]] = None
    operator_id: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ============== SMS ==============

class SMSRequest(BaseModel):
    appointment_id: str
    message: Optional[str] = None


# ============== SETTINGS ==============

class SettingsUpdate(BaseModel):
    salon_name: Optional[str] = None
    name: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    working_days: Optional[List[str]] = None


# ============== PREPAID CARD ==============

class PrepaidCardCreate(BaseModel):
    client_id: str
    card_type: str
    name: str
    total_value: float
    total_services: Optional[int] = None
    valid_until: Optional[str] = None
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


# ============== RECURRING ==============

class RecurringAppointmentCreate(BaseModel):
    appointment_id: str
    repeat_weeks: int = 0
    repeat_months: int = 0
    repeat_count: int


# ============== LOYALTY ==============

class LoyaltyRedeemRequest(BaseModel):
    reward_type: str

LOYALTY_POINTS_PER_EURO = 10

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


# ============== PUBLIC BOOKING ==============

class PublicBookingRequest(BaseModel):
    client_name: str
    client_phone: str
    service_ids: List[str]
    operator_id: Optional[str] = None
    date: str
    time: str
    notes: Optional[str] = ""


# ============== CHECKOUT ==============

class CheckoutData(BaseModel):
    payment_method: str
    discount_type: Optional[str] = "none"
    discount_value: Optional[float] = 0
    total_paid: float
    card_id: Optional[str] = None
    loyalty_points_used: Optional[int] = 0
    promo_id: Optional[str] = None
    promo_free_service: Optional[str] = None
