from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import Response, FileResponse
from datetime import datetime, timezone
import uuid
import os
import requests as http_requests
import logging

from database import db
from auth import get_current_user
from models import PublicBookingRequest

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== Object Storage with Local Fallback ==============

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "mbhssalon"
_storage_key = None
_use_local_storage = False

# Local upload directory (use /tmp on platforms where /app is read-only)
LOCAL_UPLOAD_DIR = "/app/backend/uploads"
try:
    os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)
except PermissionError:
    LOCAL_UPLOAD_DIR = "/tmp/uploads"
    os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)


def init_storage():
    global _storage_key, _use_local_storage
    if _use_local_storage:
        return None
    if _storage_key:
        return _storage_key
    try:
        resp = http_requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=10)
        resp.raise_for_status()
        _storage_key = resp.json()["storage_key"]
        return _storage_key
    except Exception as e:
        logger.warning(f"Object storage unavailable, using local storage: {e}")
        _use_local_storage = True
        return None


def put_object(path: str, data: bytes, content_type: str) -> dict:
    global _use_local_storage
    
    # Try remote storage first
    if not _use_local_storage:
        try:
            key = init_storage()
            if key:
                resp = http_requests.put(
                    f"{STORAGE_URL}/objects/{path}",
                    headers={"X-Storage-Key": key, "Content-Type": content_type},
                    data=data, timeout=120
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"Remote storage failed, falling back to local: {e}")
            _use_local_storage = True
    
    # Fallback to local storage
    filename = path.split("/")[-1]
    local_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
    with open(local_path, "wb") as f:
        f.write(data)
    return {"path": f"local://{filename}", "size": len(data)}


def get_object(path: str):
    global _use_local_storage
    
    # Check if it's a local file
    if path.startswith("local://"):
        filename = path.replace("local://", "")
        local_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                data = f.read()
            # Determine content type from extension
            ext = filename.split(".")[-1].lower()
            mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
            return data, mime_map.get(ext, "application/octet-stream")
        raise HTTPException(status_code=404, detail="File non trovato")
    
    # Try remote storage
    try:
        key = init_storage()
        if key:
            resp = http_requests.get(
                f"{STORAGE_URL}/objects/{path}",
                headers={"X-Storage-Key": key}, timeout=60
            )
            resp.raise_for_status()
            return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
    except Exception as e:
        logger.error(f"Failed to get object from remote storage: {e}")
    
    raise HTTPException(status_code=404, detail="File non trovato")


# ============== Default Website Config ==============

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


# ============== PUBLIC BOOKING ==============

@router.get("/public/services")
async def get_public_services():
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0, "id": 1})
    if not user:
        user = await db.users.find_one({}, {"_id": 0, "id": 1})
    if not user:
        return []
    return await db.services.find({"user_id": user["id"]}, {"_id": 0, "user_id": 0}).to_list(100)


@router.get("/public/operators")
async def get_public_operators():
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0, "id": 1})
    if not user:
        user = await db.users.find_one({}, {"_id": 0, "id": 1})
    if not user:
        return []
    return await db.operators.find({"user_id": user["id"]}, {"_id": 0, "user_id": 0}).to_list(50)


@router.post("/public/booking")
async def create_public_booking(data: PublicBookingRequest):
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0})
    if not user:
        user = await db.users.find_one({}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Salone non configurato")
    user_id = user["id"]

    existing = await db.appointments.find_one({
        "user_id": user_id, "date": data.date, "time": data.time,
        "operator_id": data.operator_id if data.operator_id else {"$exists": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Orario già occupato. Scegli un altro orario.")

    client = await db.clients.find_one({"phone": data.client_phone, "user_id": user_id}, {"_id": 0})
    if not client:
        client_id = str(uuid.uuid4())
        client = {
            "id": client_id, "user_id": user_id, "name": data.client_name,
            "phone": data.client_phone,
            "notes": f"[Online] {data.notes}" if data.notes else "[Prenotazione Online]",
            "send_sms_reminders": True, "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.clients.insert_one(client)
    else:
        client_id = client["id"]

    services = await db.services.find({"id": {"$in": data.service_ids}, "user_id": user_id}, {"_id": 0, "user_id": 0}).to_list(20)
    if not services:
        raise HTTPException(status_code=400, detail="Servizi non validi")

    total_duration = sum(s["duration"] for s in services)
    total_price = sum(s["price"] for s in services)
    start_hour, start_min = map(int, data.time.split(":"))
    end_minutes = start_hour * 60 + start_min + total_duration
    end_time = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"

    assigned_operator_id = data.operator_id or None
    operator_name = None
    operator_color = None
    if assigned_operator_id:
        operator = await db.operators.find_one({"id": assigned_operator_id, "user_id": user_id}, {"_id": 0})
        if operator:
            operator_name = operator["name"]
            operator_color = operator.get("color")
    if not assigned_operator_id:
        first_op = await db.operators.find_one({"user_id": user_id, "active": True}, {"_id": 0})
        if first_op:
            assigned_operator_id = first_op["id"]
            operator_name = first_op["name"]
            operator_color = first_op.get("color")

    appointment_id = str(uuid.uuid4())
    appointment = {
        "id": appointment_id, "user_id": user_id, "client_id": client_id,
        "client_name": data.client_name, "service_ids": data.service_ids, "services": services,
        "operator_id": assigned_operator_id, "operator_name": operator_name, "operator_color": operator_color,
        "date": data.date, "time": data.time, "end_time": end_time,
        "total_duration": total_duration, "total_price": total_price,
        "status": "scheduled",
        "notes": f"[Online] {data.notes}" if data.notes else "[Prenotazione Online]",
        "source": "online", "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.appointments.insert_one(appointment)
    return {"success": True, "appointment_id": appointment_id, "booking_code": appointment_id[:8].upper()}


@router.get("/public/my-appointments")
async def public_lookup_appointments(phone: str):
    user = await db.users.find_one({"email": "melitobruno@gmail.com"}, {"_id": 0})
    if not user:
        user = await db.users.find_one({}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Salone non configurato")
    phone_clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    client = await db.clients.find_one(
        {"user_id": user["id"], "$or": [{"phone": phone}, {"phone": phone_clean}]}, {"_id": 0}
    )
    if not client:
        return []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    appointments = await db.appointments.find(
        {"user_id": user["id"], "client_id": client["id"], "date": {"$gte": today}, "status": {"$ne": "cancelled"}},
        {"_id": 0, "user_id": 0}
    ).sort("date", 1).to_list(20)
    return [{"id": a["id"], "date": a["date"], "time": a["time"],
             "services": [s["name"] for s in a.get("services", [])],
             "operator_name": a.get("operator_name", ""), "booking_code": a["id"][:8].upper()} for a in appointments]


@router.put("/public/appointments/{appointment_id}")
async def public_update_appointment(appointment_id: str, data: dict):
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
    client = await db.clients.find_one({"id": apt["client_id"]}, {"_id": 0})
    phone_clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not client or (client.get("phone", "").replace(" ", "").replace("-", "").replace("+", "") != phone_clean):
        raise HTTPException(status_code=403, detail="Numero non corrispondente")
    new_date = data.get("date", apt["date"])
    new_time = data.get("time", apt["time"])
    existing = await db.appointments.find_one({
        "user_id": user["id"], "date": new_date, "time": new_time,
        "id": {"$ne": appointment_id}, "operator_id": apt.get("operator_id")
    })
    if existing:
        raise HTTPException(status_code=400, detail="Orario già occupato")
    await db.appointments.update_one({"id": appointment_id}, {"$set": {"date": new_date, "time": new_time}})
    return {"success": True}


@router.delete("/public/appointments/{appointment_id}")
async def public_cancel_appointment(appointment_id: str, phone: str):
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
    await db.appointments.update_one({"id": appointment_id}, {"$set": {"status": "cancelled"}})
    return {"success": True}


# ============== WEBSITE CMS ==============

@router.post("/website/upload")
async def website_upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    image_exts = ("jpg", "jpeg", "png", "gif", "webp")
    video_exts = ("mp4", "webm", "mov")
    allowed = image_exts + video_exts
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Formato non supportato. Usa JPG, PNG, GIF, WebP, MP4, WebM o MOV.")
    
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", 
        "gif": "image/gif", "webp": "image/webp",
        "mp4": "video/mp4", "webm": "video/webm", "mov": "video/quicktime"
    }
    file_type = "video" if ext in video_exts else "image"
    max_size = 50 * 1024 * 1024 if file_type == "video" else 10 * 1024 * 1024
    
    file_id = str(uuid.uuid4())
    path = f"{APP_NAME}/uploads/{file_id}.{ext}"
    data = await file.read()
    if len(data) > max_size:
        raise HTTPException(status_code=400, detail=f"File troppo grande. Max {'50MB' if file_type == 'video' else '10MB'}.")
    result = put_object(path, data, mime_map.get(ext, "application/octet-stream"))
    doc = {
        "id": file_id, "storage_path": result["path"], "original_filename": file.filename,
        "content_type": mime_map.get(ext, "application/octet-stream"), "size": result.get("size", len(data)),
        "file_type": file_type, "is_deleted": False, "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.website_files.insert_one(doc)
    return {"id": file_id, "path": result["path"], "url": f"/api/website/files/{file_id}", "file_type": file_type}


@router.get("/website/files/{file_id}")
async def website_serve_file(file_id: str):
    record = await db.website_files.find_one({"id": file_id, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File non trovato")
    data, content_type = get_object(record["storage_path"])
    return Response(content=data, media_type=record.get("content_type", content_type))


@router.get("/website/config")
async def get_website_config(current_user: dict = Depends(get_current_user)):
    config = await db.website_config.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not config:
        return {**DEFAULT_WEBSITE_CONFIG, "user_id": current_user["id"]}
    return {**DEFAULT_WEBSITE_CONFIG, **config}


@router.put("/website/config")
async def update_website_config(data: dict, current_user: dict = Depends(get_current_user)):
    data["user_id"] = current_user["id"]
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.website_config.update_one({"user_id": current_user["id"]}, {"$set": data}, upsert=True)
    return await db.website_config.find_one({"user_id": current_user["id"]}, {"_id": 0})


@router.get("/website/reviews")
async def get_website_reviews(current_user: dict = Depends(get_current_user)):
    return await db.website_reviews.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)


@router.post("/website/reviews")
async def create_website_review(data: dict, current_user: dict = Depends(get_current_user)):
    review = {
        "id": str(uuid.uuid4()), "user_id": current_user["id"],
        "name": data.get("name", ""), "text": data.get("text", ""),
        "rating": data.get("rating", 5), "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.website_reviews.insert_one(review)
    return {k: v for k, v in review.items() if k != "_id"}


@router.put("/website/reviews/{review_id}")
async def update_website_review(review_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    await db.website_reviews.update_one(
        {"id": review_id, "user_id": current_user["id"]},
        {"$set": {"name": data.get("name"), "text": data.get("text"), "rating": data.get("rating", 5)}}
    )
    return await db.website_reviews.find_one({"id": review_id}, {"_id": 0})


@router.delete("/website/reviews/{review_id}")
async def delete_website_review(review_id: str, current_user: dict = Depends(get_current_user)):
    await db.website_reviews.delete_one({"id": review_id, "user_id": current_user["id"]})
    return {"success": True}


@router.get("/website/gallery")
async def get_website_gallery(current_user: dict = Depends(get_current_user)):
    return await db.website_gallery.find(
        {"user_id": current_user["id"], "is_deleted": {"$ne": True}}, {"_id": 0}
    ).sort("sort_order", 1).to_list(100)


@router.post("/website/gallery")
async def create_website_gallery_item(data: dict, current_user: dict = Depends(get_current_user)):
    count = await db.website_gallery.count_documents({"user_id": current_user["id"], "is_deleted": {"$ne": True}})
    item = {
        "id": str(uuid.uuid4()), "user_id": current_user["id"],
        "image_url": data.get("image_url", ""), "label": data.get("label", ""),
        "tag": data.get("tag", ""), "section": data.get("section", "gallery"),
        "file_type": data.get("file_type", "image"),
        "sort_order": count, "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.website_gallery.insert_one(item)
    return {k: v for k, v in item.items() if k != "_id"}


@router.put("/website/gallery/{item_id}")
async def update_website_gallery_item(item_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    update_data = {}
    for key in ["label", "tag", "sort_order", "section", "image_url"]:
        if key in data:
            update_data[key] = data[key]
    if update_data:
        await db.website_gallery.update_one({"id": item_id, "user_id": current_user["id"]}, {"$set": update_data})
    return await db.website_gallery.find_one({"id": item_id}, {"_id": 0})


@router.delete("/website/gallery/{item_id}")
async def delete_website_gallery_item(item_id: str, current_user: dict = Depends(get_current_user)):
    await db.website_gallery.update_one({"id": item_id, "user_id": current_user["id"]}, {"$set": {"is_deleted": True}})
    return {"success": True}


@router.get("/public/website")
async def public_get_website():
    config = await db.website_config.find_one({}, {"_id": 0, "user_id": 0})
    if not config:
        config = {k: v for k, v in DEFAULT_WEBSITE_CONFIG.items()}
    else:
        config = {**DEFAULT_WEBSITE_CONFIG, **{k: v for k, v in config.items() if k != "user_id"}}
    reviews = await db.website_reviews.find({}, {"_id": 0, "user_id": 0}).to_list(100)
    gallery = await db.website_gallery.find({"is_deleted": {"$ne": True}}, {"_id": 0, "user_id": 0}).sort("sort_order", 1).to_list(100)
    services = await db.services.find({}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    
    # Loyalty program info for public display
    loyalty_rewards = await db.loyalty_rewards.find({}, {"_id": 0, "user_id": 0}).to_list(10)
    loyalty_config = {
        "points_per_euro": 10,
        "rewards": {r["key"]: r for r in loyalty_rewards} if loyalty_rewards else {
            "discount_5": {"name": "Sconto 5%", "points_required": 50, "discount_percent": 5},
            "discount_10": {"name": "Sconto 10%", "points_required": 100, "discount_percent": 10},
            "free_service": {"name": "Servizio Omaggio", "points_required": 200, "discount_percent": 100},
        }
    }
    
    return {"config": config, "reviews": reviews, "gallery": gallery, "services": services, "loyalty": loyalty_config}
