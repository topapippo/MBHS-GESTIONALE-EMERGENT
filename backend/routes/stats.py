from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone, timedelta
import io

from database import db
from auth import get_current_user
from models import SettingsUpdate, UserResponse
from utils import twilio_client, TWILIO_PHONE_NUMBER

router = APIRouter()


# ============== DASHBOARD ==============

@router.get("/stats/dashboard")
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
        {"user_id": current_user["id"], "date": {"$gte": first_of_month, "$lte": last_of_month}, "status": "completed"},
        {"_id": 0}
    ).to_list(1000)
    monthly_revenue = sum(a.get("total_price", 0) for a in monthly_appointments)
    next_week = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    upcoming = await db.appointments.find(
        {"user_id": current_user["id"], "date": {"$gte": today, "$lte": next_week}, "status": "scheduled"},
        {"_id": 0, "user_id": 0}
    ).sort([("date", 1), ("time", 1)]).to_list(10)
    return {
        "today_appointments": today_appointments, "today_appointments_count": len(today_appointments),
        "today_revenue": sum(a.get("total_price", 0) for a in today_appointments if a.get("status") == "completed"),
        "total_clients": total_clients, "total_operators": total_operators,
        "monthly_revenue": monthly_revenue, "monthly_appointments": len(monthly_appointments),
        "upcoming_appointments": upcoming
    }


@router.get("/stats/daily-summary")
async def get_daily_summary(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    today_apts = await db.appointments.find(
        {"user_id": current_user["id"], "date": target_date, "status": {"$ne": "cancelled"}}, {"_id": 0, "user_id": 0}
    ).to_list(200)
    yesterday_apts = await db.appointments.find(
        {"user_id": current_user["id"], "date": yesterday, "status": {"$ne": "cancelled"}}, {"_id": 0, "user_id": 0}
    ).to_list(200)
    completed = [a for a in today_apts if a.get("status") == "completed"]
    total_earnings = sum(a.get("total_paid", a.get("total_price", 0)) for a in completed)
    yesterday_earnings = sum(a.get("total_paid", a.get("total_price", 0)) for a in yesterday_apts if a.get("status") == "completed")
    hourly = {f"{h:02d}:00": 0 for h in range(8, 21)}
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
    unique_clients = set(apt.get("client_name", "") for apt in today_apts if apt.get("client_name"))
    payment_methods = {}
    for apt in completed:
        pm = apt.get("payment_method", "non specificato")
        payment_methods[pm] = payment_methods.get(pm, 0) + 1
    return {
        "date": target_date, "total_appointments": len(today_apts),
        "completed_appointments": len(completed), "total_earnings": total_earnings,
        "yesterday_earnings": yesterday_earnings, "earnings_diff": total_earnings - yesterday_earnings,
        "unique_clients": len(unique_clients),
        "avg_per_client": round(total_earnings / len(unique_clients), 2) if unique_clients else 0,
        "hourly_distribution": hourly,
        "top_services": [{"name": s[0], "count": s[1]} for s in top_services],
        "payment_methods": payment_methods,
        "busiest_hour": max(hourly, key=hourly.get) if any(hourly.values()) else None,
        "busiest_hour_count": max(hourly.values()) if any(hourly.values()) else 0,
    }


@router.get("/stats/revenue")
async def get_revenue_stats(start_date: str, end_date: str, current_user: dict = Depends(get_current_user)):
    appointments = await db.appointments.find(
        {"user_id": current_user["id"], "date": {"$gte": start_date, "$lte": end_date}, "status": "completed"},
        {"_id": 0}
    ).to_list(10000)
    daily_revenue = {}
    for apt in appointments:
        d = apt["date"]
        daily_revenue[d] = daily_revenue.get(d, 0) + apt.get("total_price", 0)
    service_revenue = {}
    for apt in appointments:
        for svc in apt.get("services", []):
            name = svc["name"]
            if name not in service_revenue:
                service_revenue[name] = {"count": 0, "revenue": 0}
            service_revenue[name]["count"] += 1
            service_revenue[name]["revenue"] += svc["price"]
    operator_stats = {}
    for apt in appointments:
        op_name = apt.get("operator_name", "Non assegnato")
        if op_name not in operator_stats:
            operator_stats[op_name] = {"count": 0, "revenue": 0, "color": apt.get("operator_color", "#78716C")}
        operator_stats[op_name]["count"] += 1
        operator_stats[op_name]["revenue"] += apt.get("total_price", 0)
    return {
        "total_revenue": sum(daily_revenue.values()), "total_appointments": len(appointments),
        "daily_revenue": [{"date": k, "revenue": v} for k, v in sorted(daily_revenue.items())],
        "service_breakdown": [{"name": k, **v} for k, v in sorted(service_revenue.items(), key=lambda x: x[1]["revenue"], reverse=True)],
        "operator_breakdown": [{"name": k, **v} for k, v in sorted(operator_stats.items(), key=lambda x: x[1]["revenue"], reverse=True)]
    }


@router.get("/stats/export-pdf")
async def export_stats_pdf(start_date: str, end_date: str, current_user: dict = Depends(get_current_user)):
    appointments = await db.appointments.find(
        {"user_id": current_user["id"], "date": {"$gte": start_date, "$lte": end_date}, "status": "completed"},
        {"_id": 0}
    ).to_list(10000)
    total_revenue = sum(a.get("total_price", 0) for a in appointments)
    total_appointments = len(appointments)
    service_stats = {}
    for apt in appointments:
        for svc in apt.get("services", []):
            name = svc["name"]
            if name not in service_stats:
                service_stats[name] = {"count": 0, "revenue": 0}
            service_stats[name]["count"] += 1
            service_stats[name]["revenue"] += svc["price"]
    operator_stats = {}
    for apt in appointments:
        op_name = apt.get("operator_name", "Non assegnato")
        if op_name not in operator_stats:
            operator_stats[op_name] = {"count": 0, "revenue": 0}
        operator_stats[op_name]["count"] += 1
        operator_stats[op_name]["revenue"] += apt.get("total_price", 0)
    lines = [
        f"REPORT STATISTICHE - {current_user['salon_name']}", f"Periodo: {start_date} - {end_date}", "",
        "=" * 50, "RIEPILOGO", "=" * 50,
        f"Totale Incasso: €{total_revenue:.2f}", f"Totale Appuntamenti: {total_appointments}",
        f"Media per Appuntamento: €{(total_revenue/total_appointments if total_appointments > 0 else 0):.2f}", "",
        "=" * 50, "SERVIZI", "=" * 50,
    ]
    for name, data in sorted(service_stats.items(), key=lambda x: x[1]["revenue"], reverse=True):
        lines.append(f"{name}: {data['count']} volte - €{data['revenue']:.2f}")
    lines.extend(["", "=" * 50, "OPERATORI", "=" * 50])
    for name, data in sorted(operator_stats.items(), key=lambda x: x[1]["revenue"], reverse=True):
        lines.append(f"{name}: {data['count']} appuntamenti - €{data['revenue']:.2f}")
    return StreamingResponse(
        io.BytesIO("\n".join(lines).encode('utf-8')), media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=report_{start_date}_{end_date}.txt"}
    )


# ============== SETTINGS ==============

@router.put("/settings", response_model=UserResponse)
async def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    await db.users.update_one({"id": current_user["id"]}, {"$set": update_data})
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    return UserResponse(id=user["id"], email=user["email"], name=user["name"],
                        salon_name=user["salon_name"], created_at=user["created_at"])


@router.get("/settings")
async def get_settings(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"], "email": current_user["email"],
        "name": current_user["name"], "salon_name": current_user["salon_name"],
        "opening_time": current_user.get("opening_time", "09:00"),
        "closing_time": current_user.get("closing_time", "19:00"),
        "working_days": current_user.get("working_days", ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"]),
        "twilio_configured": twilio_client is not None
    }


# ============== PAYMENTS ==============

@router.get("/payments")
async def get_payments(start: str = None, end: str = None, current_user: dict = Depends(get_current_user)):
    query = {"user_id": current_user["id"]}
    if start and end:
        query["date"] = {"$gte": start[:10], "$lte": end[:10]}
    return await db.payments.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
