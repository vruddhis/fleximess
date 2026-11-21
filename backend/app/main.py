import os, json
from datetime import date, datetime, timedelta, timezone
from typing import Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, or_
from .database import Base, engine, get_db
from .models import Mess, Food, Menu, MenuItem, Nutrition, User, Preference, Favorite, MealLog

SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-this-secret-key-please")
ALGORITHM = "HS256"
TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
password_hash = PasswordHasher()
bearer = HTTPBearer(auto_error=False)
app = FastAPI(title="FlexiMess API", version="1.0.0", description="Fresh FastAPI backend for FlexiMess")
origins = [x.strip() for x in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=8, max_length=128)
class LoginIn(BaseModel):
    username: str
    password: str
class PreferenceIn(BaseModel):
    goals: str = "balanced"
    priority_goals: list[str] = []
    breakfast_calories: Optional[int] = None
    lunch_calories: Optional[int] = None
    snacks_calories: Optional[int] = None
    dinner_calories: Optional[int] = None
class MealItemIn(BaseModel):
    food_id: int
    quantity_g: float = Field(gt=0, le=5000)
class MealLogIn(BaseModel):
    mess_id: int
    meal_date: date
    meal_type: str
    items: list[MealItemIn] = Field(min_length=1)
    notes: Optional[str] = None

MEALS = {"breakfast", "lunch", "snacks", "dinner"}
GOALS = {"high_protein", "high_fiber", "low_sugar", "low_carbohydrate", "low_calories", "balanced"}

def make_token(username: str):
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": username, "iat": now, "exp": now + timedelta(minutes=TOKEN_MINUTES)}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if not creds:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired access token")
    user = db.get(User, username) if username else None
    if not user or not user.is_active:
        raise HTTPException(401, "User account is unavailable")
    return user

def food_dict(food: Food):
    n = food.nutrition
    return {"food_id": food.food_id, "name": food.food_name, "category": food.category.category_name if food.category else None,
            "description": food.description, "nutrition": nutrition_dict(n) if n else None}

def nutrition_dict(n):
    if not n: return None
    return {"basis_amount": float(n.basis_amount), "basis_unit": n.basis_unit,
            "calories_kcal": float(n.calories_kcal) if n.calories_kcal is not None else None,
            "protein_g": float(n.protein_g) if n.protein_g is not None else None,
            "carbs_g": float(n.carbs_g) if n.carbs_g is not None else None,
            "fat_g": float(n.fat_g) if n.fat_g is not None else None,
            "fiber_g": float(n.fiber_g) if n.fiber_g is not None else None,
            "sugar_g": float(n.sugar_g) if n.sugar_g is not None else None, "source": n.source, "confidence": n.confidence}

def menu_item_dict(item: MenuItem):
    return {**food_dict(item.food), "serving_weight_g": float(item.serving_weight_g) if item.serving_weight_g else None,
            "serving_description": item.serving_description}

def scaled(n, grams):
    if not n or n.basis_unit.lower() != "g": return {}
    factor = grams / float(n.basis_amount)
    return {k: (round(float(getattr(n, attr)) * factor, 2) if getattr(n, attr) is not None else None)
            for k, attr in [("calories_kcal", "calories_kcal"), ("protein_g", "protein_g"), ("carbs_g", "carbs_g"), ("fat_g", "fat_g"), ("fiber_g", "fiber_g"), ("sugar_g", "sugar_g")]}

@app.get("/")
def health(): return {"status": "ok", "service": "FlexiMess API"}

@app.post("/api/auth/signup", status_code=201)
def signup(data: SignupIn, db: Session = Depends(get_db)):
    username = data.username.strip().lower()
    if username in {"admin", "administrator", "root", "support", "system", "flexi", "flexiadmin"}:
        raise HTTPException(400, "This username is reserved")
    if db.get(User, username): raise HTTPException(409, "Username already exists")
    user = User(username=username, name=data.name.strip(), password_hash=password_hash.hash(data.password))
    db.add(user); db.flush(); db.add(Preference(username=username)); db.commit()
    return {"access_token": make_token(username), "token_type": "bearer", "user": {"username": username, "name": user.name}}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.get(User, data.username.strip().lower())
    if not user or not user.is_active:
        raise HTTPException(401, "Incorrect username or password")
    try:
        password_hash.verify(user.password_hash, data.password)
    except (VerifyMismatchError, VerificationError):
        raise HTTPException(401, "Incorrect username or password")
    return {"access_token": make_token(user.username), "token_type": "bearer", "user": {"username": user.username, "name": user.name}}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"user": {"username": user.username, "name": user.name, "hostel_id": user.hostel_id, "role": user.role}}

@app.post("/api/auth/logout")
def logout(user: User = Depends(current_user)):
    # JWT is stateless; frontend deletes its stored token. Short expiry bounds token lifetime.
    return {"message": "Logged out. Remove the access token on the client."}

@app.get("/api/messes")
def messes(db: Session = Depends(get_db)):
    return [{"mess_id": m.mess_id, "mess_name": m.mess_name} for m in db.scalars(select(Mess).order_by(Mess.mess_name)).all()]

@app.get("/api/foods")
def foods(q: str = "", limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    stmt = select(Food).options(joinedload(Food.nutrition), joinedload(Food.category)).order_by(Food.food_name).limit(limit)
    if q.strip(): stmt = select(Food).options(joinedload(Food.nutrition), joinedload(Food.category)).where(Food.food_name.ilike(f"%{q.strip()}%")).order_by(Food.food_name).limit(limit)
    return [food_dict(f) for f in db.scalars(stmt).unique().all()]

@app.get("/api/menus")
def menus(menu_date: date = Query(default_factory=date.today), meal_type: str | None = None, mess_id: int | None = None,
          q: str | None = None, db: Session = Depends(get_db)):
    if meal_type and meal_type.lower() not in MEALS: raise HTTPException(400, "Invalid meal_type")
    stmt = select(Menu).options(joinedload(Menu.mess), joinedload(Menu.items).joinedload(MenuItem.food).joinedload(Food.nutrition),
                                joinedload(Menu.items).joinedload(MenuItem.food).joinedload(Food.category)).where(Menu.menu_date == menu_date)
    if meal_type: stmt = stmt.where(Menu.meal_type == meal_type.lower())
    if mess_id: stmt = stmt.where(Menu.mess_id == mess_id)
    result = []
    for menu in db.scalars(stmt.order_by(Menu.mess_id, Menu.meal_type)).unique().all():
        items = [menu_item_dict(i) for i in menu.items]
        if q: items = [i for i in items if q.lower() in i["name"].lower()]
        if q and not items: continue
        result.append({"menu_id": menu.menu_id, "mess_id": menu.mess_id, "mess_name": menu.mess.mess_name,
                       "menu_date": menu.menu_date.isoformat(), "meal_type": menu.meal_type, "items": items})
    return result

@app.get("/api/recommendations")
def recommendations(menu_date: date = Query(default_factory=date.today), meal_type: str = "lunch", user: User = Depends(current_user), db: Session = Depends(get_db)):
    if meal_type.lower() not in MEALS: raise HTTPException(400, "Invalid meal_type")
    pref = db.get(Preference, user.username)
    goals = json.loads(pref.priority_goals or "[]") if pref else []
    if not goals and pref: goals = [pref.goals]
    menus_data = menus(menu_date, meal_type, None, None, db)
    scored = []
    for m in menus_data:
        totals = {k: 0.0 for k in ["calories_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g"]}
        count = 0
        for item in m["items"]:
            n = item.get("nutrition")
            grams = item.get("serving_weight_g") or 100
            if n:
                vals = scaled_obj(n, grams)
                for k, v in vals.items():
                    if v is not None: totals[k] += v
                count += 1
        def score_for(goal):
            if goal == "high_protein": return totals["protein_g"]
            if goal == "high_fiber": return totals["fiber_g"]
            if goal == "low_sugar": return -totals["sugar_g"]
            if goal == "low_carbohydrate": return -totals["carbs_g"]
            if goal == "low_calories": return -totals["calories_kcal"]
            return totals["protein_g"] + totals["fiber_g"] - totals["sugar_g"] * .1
        score = sum(score_for(g) * (1 / (idx + 1)) for idx, g in enumerate(goals or ["balanced"]))
        scored.append({**m, "nutrition_totals": {k: round(v, 2) for k, v in totals.items()}, "nutrition_coverage": count, "score": round(score, 3)})
    return sorted(scored, key=lambda x: x["score"], reverse=True)

def scaled_obj(n, grams):
    factor = grams / (n["basis_amount"] or 100) if n["basis_unit"] == "g" else 0
    return {k: (v * factor if v is not None else None) for k, v in [("calories_kcal", n["calories_kcal"]), ("protein_g", n["protein_g"]), ("carbs_g", n["carbs_g"]), ("fat_g", n["fat_g"]), ("fiber_g", n["fiber_g"]), ("sugar_g", n["sugar_g"])]}

@app.get("/api/preferences")
def get_preferences(user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(Preference, user.username)
    if not p: return {}
    return {"goals": p.goals, "priority_goals": json.loads(p.priority_goals or "[]"), "breakfast_calories": p.breakfast_calories,
            "lunch_calories": p.lunch_calories, "snacks_calories": p.snacks_calories, "dinner_calories": p.dinner_calories}

@app.put("/api/preferences")
def save_preferences(data: PreferenceIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if data.goals not in GOALS: raise HTTPException(400, "Unsupported goal")
    if len(data.priority_goals) > 2 or any(g not in GOALS for g in data.priority_goals): raise HTTPException(400, "Choose at most two valid goals")
    p = db.get(Preference, user.username) or Preference(username=user.username)
    p.goals = data.goals; p.priority_goals = json.dumps(data.priority_goals)
    for field in ["breakfast_calories", "lunch_calories", "snacks_calories", "dinner_calories"]:
        val = getattr(data, field)
        if val is not None and not 0 < val <= 5000: raise HTTPException(400, f"{field} must be between 1 and 5000")
        setattr(p, field, val)
    db.add(p); db.commit(); return get_preferences(user, db)

@app.get("/api/favorites")
def get_favorites(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Favorite).where(Favorite.username == user.username)).all()
    ids = [r.food_id for r in rows]
    if not ids: return []
    return [food_dict(f) for f in db.scalars(select(Food).options(joinedload(Food.nutrition), joinedload(Food.category)).where(Food.food_id.in_(ids))).unique().all()]

@app.post("/api/favorites/{food_id}", status_code=201)
def add_favorite(food_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(Food, food_id): raise HTTPException(404, "Food not found")
    if not db.get(Favorite, (user.username, food_id)): db.add(Favorite(username=user.username, food_id=food_id)); db.commit()
    return {"message": "Favourite saved"}

@app.delete("/api/favorites/{food_id}")
def remove_favorite(food_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(Favorite, (user.username, food_id))
    if row: db.delete(row); db.commit()
    return {"message": "Favourite removed"}

@app.get("/api/notifications")
def notifications(days: int = Query(7, ge=1, le=30), user: User = Depends(current_user), db: Session = Depends(get_db)):
    end = date.today() + timedelta(days=days)
    fav_ids = select(Favorite.food_id).where(Favorite.username == user.username)
    rows = db.execute(select(Menu, Mess.mess_name, Food).join(Mess, Mess.mess_id == Menu.mess_id).join(MenuItem, MenuItem.menu_id == Menu.menu_id).join(Food, Food.food_id == MenuItem.food_id).where(Menu.menu_date.between(date.today(), end), Food.food_id.in_(fav_ids)).order_by(Menu.menu_date)).all()
    return [{"menu_date": m.menu_date.isoformat(), "meal_type": m.meal_type, "mess_name": name, "food_id": f.food_id, "food_name": f.food_name} for m, name, f in rows]

@app.post("/api/meal-logs", status_code=201)
def create_meal_log(data: MealLogIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if data.meal_type.lower() not in MEALS: raise HTTPException(400, "Invalid meal_type")
    if not db.get(Mess, data.mess_id): raise HTTPException(404, "Mess not found")
    created = []
    for item in data.items:
        if not db.get(Food, item.food_id): raise HTTPException(404, f"Food {item.food_id} not found")
        row = MealLog(username=user.username, mess_id=data.mess_id, food_id=item.food_id, meal_date=data.meal_date,
                      meal_type=data.meal_type.lower(), quantity_g=item.quantity_g, notes=data.notes)
        db.add(row); db.flush(); created.append(row.log_id)
    db.commit(); return {"message": "Meal logged", "log_ids": created}

@app.get("/api/meal-logs")
def meal_history(start_date: date | None = None, end_date: date | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(MealLog).options(joinedload(MealLog.food).joinedload(Food.nutrition), joinedload(MealLog.mess)).where(MealLog.username == user.username)
    if start_date: stmt = stmt.where(MealLog.meal_date >= start_date)
    if end_date: stmt = stmt.where(MealLog.meal_date <= end_date)
    rows = db.scalars(stmt.order_by(MealLog.meal_date.desc(), MealLog.created_at.desc())).unique().all()
    out = []
    for r in rows:
        grams = float(r.quantity_g); n = r.food.nutrition
        out.append({"log_id": r.log_id, "meal_date": r.meal_date.isoformat(), "meal_type": r.meal_type, "mess_id": r.mess_id,
                    "mess_name": r.mess.mess_name, "food_id": r.food_id, "food_name": r.food.food_name, "quantity_g": grams,
                    "nutrition": scaled(n, grams) if n else None, "notes": r.notes})
    return out

@app.get("/api/meal-logs/summary")
def meal_summary(summary_date: date = Query(default_factory=date.today), user: User = Depends(current_user), db: Session = Depends(get_db)):
    logs = meal_history(summary_date, summary_date, user, db)
    keys = ["calories_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g"]
    totals = {k: 0.0 for k in keys}; known = {k: 0 for k in keys}
    for log in logs:
        for k, v in (log["nutrition"] or {}).items():
            if v is not None: totals[k] += v; known[k] += 1
    return {"date": summary_date.isoformat(), "meal_count": len(logs), "totals": {k: round(v, 2) if known[k] else None for k, v in totals.items()}, "items": logs}

@app.delete("/api/meal-logs/{log_id}")
def delete_meal_log(log_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(MealLog, log_id)
    if not row or row.username != user.username: raise HTTPException(404, "Meal log not found")
    db.delete(row); db.commit(); return {"message": "Meal log deleted"}
