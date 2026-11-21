import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select, func
from .database import get_db
from .models import (Mess, Food, Menu, MenuItem, Nutrition, User, Preference, MealLog, MealLogItem,
                     MEAL_TYPES, PREFERENCE_NUTRIENTS)

SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-this-secret-key-please")
ALGORITHM = "HS256"
TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
password_hash = PasswordHasher()
bearer = HTTPBearer(auto_error=False)
app = FastAPI(title="FlexiMess API", version="1.1.0", description="FlexiMess backend (Supabase schema)")
origins = [x.strip() for x in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# NOTE: no Base.metadata.create_all() on startup. Supabase is the source of truth
# and the API must never create or alter tables there.

MEALS = set(MEAL_TYPES)
MealType = Literal["breakfast", "lunch", "snacks", "dinner"]
GOALS = {"high_protein", "high_fiber", "low_sugar", "low_carbohydrate", "low_calories", "balanced"}
RESERVED_USERNAMES = {"admin", "administrator", "root", "support", "system", "flexi", "flexiadmin"}
NUTRIENT_KEYS = ["calories_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g"]


# ---------- request schemas ----------

class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        # users_name_check: length(trim(name)) > 0
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class LoginIn(BaseModel):
    username: str
    password: str


class MealTargetsIn(BaseModel):
    """Targets for one meal. Bounds mirror the user_preferences CHECK constraints."""
    calories_kcal: Optional[int] = Field(None, ge=0, le=PREFERENCE_NUTRIENTS["calories_kcal"])
    protein_g: Optional[float] = Field(None, ge=0, le=PREFERENCE_NUTRIENTS["protein_g"])
    carbs_g: Optional[float] = Field(None, ge=0, le=PREFERENCE_NUTRIENTS["carbs_g"])
    fibre_g: Optional[float] = Field(None, ge=0, le=PREFERENCE_NUTRIENTS["fibre_g"])
    sugar_g: Optional[float] = Field(None, ge=0, le=PREFERENCE_NUTRIENTS["sugar_g"])


class PreferencesIn(BaseModel):
    """Full replacement of a user's per-meal targets. Omitted meals/fields are cleared (NULL)."""
    breakfast: MealTargetsIn = MealTargetsIn()
    lunch: MealTargetsIn = MealTargetsIn()
    snacks: MealTargetsIn = MealTargetsIn()
    dinner: MealTargetsIn = MealTargetsIn()


class MealItemIn(BaseModel):
    food_id: Optional[int] = None
    food_name: Optional[str] = Field(None, min_length=1, max_length=150)
    grams: float = Field(ge=0.1, le=5000)  # meal_log_items.grams numeric(7,1), CHECK grams > 0

    @model_validator(mode="after")
    def one_food_reference(self):
        if self.food_id is None and not (self.food_name and self.food_name.strip()):
            raise ValueError("Provide food_id or food_name")
        return self


class MealLogIn(BaseModel):
    mess_id: int
    log_date: date
    meal_type: MealType
    items: list[MealItemIn] = Field(min_length=1, max_length=50)


# ---------- helpers ----------

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


def _f(v):
    return float(v) if v is not None else None


def nutrition_dict(n: Nutrition | None):
    if not n:
        return None
    return {"basis_amount": float(n.basis_amount), "basis_unit": n.basis_unit,
            **{k: _f(getattr(n, k)) for k in NUTRIENT_KEYS}, "source": n.source, "confidence": n.confidence}


def food_dict(food: Food):
    return {"food_id": food.food_id, "name": food.food_name,
            "category": food.category.category_name if food.category else None,
            "description": food.description,
            "default_serving_g": _f(food.default_serving_g), "default_serving_desc": food.default_serving_desc,
            "nutrition": nutrition_dict(food.nutrition)}


def menu_item_dict(item: MenuItem):
    # Fall back to the food's default serving when the menu item has none.
    weight = item.serving_weight_g if item.serving_weight_g is not None else item.food.default_serving_g
    desc = item.serving_description or item.food.default_serving_desc
    return {**food_dict(item.food), "serving_weight_g": _f(weight), "serving_description": desc}


def scaled_nutrition(n: Nutrition | None, grams: float) -> dict:
    """Nutrition for `grams` of a food, rounded to 2 dp (fits numeric(8,2)). Empty if not gram-based."""
    if not n or (n.basis_unit or "").lower() != "g" or not n.basis_amount:
        return {}
    factor = Decimal(str(grams)) / Decimal(n.basis_amount)
    return {k: (getattr(n, k) * factor).quantize(Decimal("0.01"), ROUND_HALF_UP) if getattr(n, k) is not None else None
            for k in NUTRIENT_KEYS}


def utcnow():
    return datetime.now(timezone.utc)


# ---------- health & auth ----------

@app.get("/")
def health():
    return {"status": "ok", "service": "FlexiMess API"}


@app.post("/api/auth/signup", status_code=201)
def signup(data: SignupIn, db: Session = Depends(get_db)):
    username = data.username.strip().lower()
    if username in RESERVED_USERNAMES:
        raise HTTPException(400, "This username is reserved")
    if db.get(User, username):
        raise HTTPException(409, "Username already exists")
    user = User(username=username, name=data.name, password_hash=password_hash.hash(data.password))
    db.add(user)
    db.flush()
    db.add(Preference(username=username))  # all targets NULL until the user sets them
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Username already exists")
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
    user.last_login_at = utcnow()
    db.commit()
    return {"access_token": make_token(user.username), "token_type": "bearer", "user": {"username": user.username, "name": user.name}}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"user": {"username": user.username, "name": user.name, "hostel_id": user.hostel_id, "role": user.role}}


@app.post("/api/auth/logout")
def logout(user: User = Depends(current_user)):
    # JWT is stateless; frontend deletes its stored token. Short expiry bounds token lifetime.
    return {"message": "Logged out. Remove the access token on the client."}


# ---------- menus & foods (read-only) ----------

@app.get("/api/messes")
def messes(db: Session = Depends(get_db)):
    return [{"mess_id": m.mess_id, "mess_name": m.mess_name} for m in db.scalars(select(Mess).order_by(Mess.mess_name)).all()]


@app.get("/api/foods")
def foods(q: str = "", limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    stmt = select(Food).options(joinedload(Food.nutrition), joinedload(Food.category))
    if q.strip():
        stmt = stmt.where(Food.food_name.ilike(f"%{q.strip()}%"))
    return [food_dict(f) for f in db.scalars(stmt.order_by(Food.food_name).limit(limit)).unique().all()]


@app.get("/api/menus")
def menus(menu_date: date = Query(default_factory=date.today), meal_type: str | None = None, mess_id: int | None = None,
          q: str | None = None, db: Session = Depends(get_db)):
    if meal_type and meal_type.lower() not in MEALS:
        raise HTTPException(400, "Invalid meal_type")
    stmt = select(Menu).options(joinedload(Menu.mess),
                                joinedload(Menu.items).joinedload(MenuItem.food).joinedload(Food.nutrition),
                                joinedload(Menu.items).joinedload(MenuItem.food).joinedload(Food.category)
                                ).where(Menu.menu_date == menu_date)
    if meal_type:
        stmt = stmt.where(Menu.meal_type == meal_type.lower())
    if mess_id:
        stmt = stmt.where(Menu.mess_id == mess_id)
    result = []
    for menu in db.scalars(stmt.order_by(Menu.mess_id, Menu.meal_type)).unique().all():
        items = [menu_item_dict(i) for i in menu.items]
        if q:
            items = [i for i in items if q.lower() in i["name"].lower()]
            if not items:
                continue
        result.append({"menu_id": menu.menu_id, "mess_id": menu.mess_id, "mess_name": menu.mess.mess_name,
                       "menu_date": menu.menu_date.isoformat(), "meal_type": menu.meal_type, "items": items})
    return result


@app.get("/api/recommendations")
def recommendations(menu_date: date = Query(default_factory=date.today), meal_type: str = "lunch",
                    goals: list[str] = Query(default=[]),
                    user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Rank messes for a meal. Goals are passed per request (?goals=high_protein&goals=low_sugar)
    because the Supabase user_preferences table has no column for goals."""
    if meal_type.lower() not in MEALS:
        raise HTTPException(400, "Invalid meal_type")
    if len(goals) > 2 or any(g not in GOALS for g in goals):
        raise HTTPException(400, "Choose at most two valid goals")
    scored = []
    for m in menus(menu_date, meal_type, None, None, db):
        totals = {k: 0.0 for k in NUTRIENT_KEYS}
        count = 0
        for item in m["items"]:
            n = item.get("nutrition")
            grams = item.get("serving_weight_g") or 100
            if n and n["basis_unit"] == "g" and n["basis_amount"]:
                factor = grams / n["basis_amount"]
                for k in NUTRIENT_KEYS:
                    if n[k] is not None:
                        totals[k] += n[k] * factor
                count += 1

        def score_for(goal):
            if goal == "high_protein": return totals["protein_g"]
            if goal == "high_fiber": return totals["fiber_g"]
            if goal == "low_sugar": return -totals["sugar_g"]
            if goal == "low_carbohydrate": return -totals["carbs_g"]
            if goal == "low_calories": return -totals["calories_kcal"]
            return totals["protein_g"] + totals["fiber_g"] - totals["sugar_g"] * .1

        score = sum(score_for(g) * (1 / (idx + 1)) for idx, g in enumerate(goals or ["balanced"]))
        scored.append({**m, "nutrition_totals": {k: round(v, 2) for k, v in totals.items()},
                       "nutrition_coverage": count, "score": round(score, 3)})
    return sorted(scored, key=lambda x: x["score"], reverse=True)


# ---------- preferences (user_preferences: per-meal targets) ----------

def preferences_dict(p: Preference | None):
    out = {meal: {nutrient: None for nutrient in PREFERENCE_NUTRIENTS} for meal in MEAL_TYPES}
    if p:
        for meal in MEAL_TYPES:
            for nutrient in PREFERENCE_NUTRIENTS:
                v = getattr(p, f"{meal}_{nutrient}")
                out[meal][nutrient] = (int(v) if nutrient == "calories_kcal" else float(v)) if v is not None else None
    return {**out, "updated_at": p.updated_at.isoformat() if p and p.updated_at else None}


@app.get("/api/preferences")
def get_preferences(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return preferences_dict(db.get(Preference, user.username))


@app.put("/api/preferences")
def save_preferences(data: PreferencesIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(Preference, user.username)
    if p is None:
        p = Preference(username=user.username)
        db.add(p)
    for meal in MEAL_TYPES:
        targets: MealTargetsIn = getattr(data, meal)
        for nutrient in PREFERENCE_NUTRIENTS:
            v = getattr(targets, nutrient)
            if v is not None:
                v = Decimal(v) if nutrient == "calories_kcal" else Decimal(str(v)).quantize(Decimal("0.1"), ROUND_HALF_UP)
            setattr(p, f"{meal}_{nutrient}", v)
    p.updated_at = utcnow()
    db.commit()
    db.refresh(p)
    return preferences_dict(p)


# ---------- favorites: disabled ----------
# The Supabase schema has no table that stores user<->food favourites
# (food_aliases is a food-name alias map used by the scraper). These endpoints
# stay disabled until the team decides on a schema. /api/notifications was
# favourites-based, so it is disabled too.

FAVORITES_DISABLED = "Favourites are disabled: the database has no favourites table yet."


@app.get("/api/favorites", status_code=501)
@app.post("/api/favorites/{food_id}", status_code=501)
@app.delete("/api/favorites/{food_id}", status_code=501)
@app.get("/api/notifications", status_code=501)
def favorites_disabled(food_id: int | None = None):
    raise HTTPException(501, FAVORITES_DISABLED)


# ---------- meal logs (meal_logs header + meal_log_items children) ----------

def meal_log_dict(log: MealLog):
    items = [{"item_id": i.item_id, "food_name": i.food_name, "grams": float(i.grams),
              "nutrition": {k: _f(getattr(i, k)) for k in NUTRIENT_KEYS}} for i in log.items]
    totals = {}
    for k in NUTRIENT_KEYS:
        known = [it["nutrition"][k] for it in items if it["nutrition"][k] is not None]
        totals[k] = round(sum(known), 2) if known else None
    return {"log_id": log.log_id, "log_date": log.log_date.isoformat(), "meal_type": log.meal_type,
            "mess_id": log.mess_id, "mess_name": log.mess.mess_name if log.mess else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None,
            "items": items, "totals": totals}


def _load_log(db: Session, log_id: int, username: str) -> MealLog:
    log = db.scalars(select(MealLog).options(selectinload(MealLog.items), joinedload(MealLog.mess))
                     .where(MealLog.log_id == log_id, MealLog.username == username)).first()
    if not log:
        raise HTTPException(404, "Meal log not found")
    return log


def _resolve_food(db: Session, item: MealItemIn) -> tuple[str, Food | None]:
    """Return (food_name to store, matching Food or None). Unknown names are allowed
    (meal_log_items has no FK to foods) but get no nutrition snapshot."""
    if item.food_id is not None:
        food = db.scalars(select(Food).options(joinedload(Food.nutrition)).where(Food.food_id == item.food_id)).first()
        if not food:
            raise HTTPException(404, f"Food {item.food_id} not found")
        return food.food_name, food
    name = item.food_name.strip()
    food = db.scalars(select(Food).options(joinedload(Food.nutrition)).where(func.lower(Food.food_name) == name.lower())).first()
    return (food.food_name if food else name), food


@app.post("/api/meal-logs", status_code=201)
def create_meal_log(data: MealLogIn, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Log foods for a meal. Supabase allows one log per (user, date, mess, meal), so if that
    log already exists the items are added to it (an existing food's grams are replaced).
    Returns 201 when a new log is created, 200 when an existing log is updated."""
    if not db.get(Mess, data.mess_id):
        raise HTTPException(404, "Mess not found")

    resolved = [(_resolve_food(db, item), item) for item in data.items]
    names = [name.lower() for (name, _), _ in resolved]
    if len(names) != len(set(names)):
        raise HTTPException(400, "The same food is listed more than once")

    log = db.scalars(select(MealLog).options(selectinload(MealLog.items)).where(
        MealLog.username == user.username, MealLog.log_date == data.log_date,
        MealLog.mess_id == data.mess_id, MealLog.meal_type == data.meal_type)).first()
    created = log is None
    if created:
        log = MealLog(username=user.username, log_date=data.log_date, mess_id=data.mess_id, meal_type=data.meal_type)
        db.add(log)

    existing = {i.food_name.lower(): i for i in log.items}
    for (name, food), item in resolved:
        grams = Decimal(str(item.grams)).quantize(Decimal("0.1"), ROUND_HALF_UP)
        snapshot = scaled_nutrition(food.nutrition if food else None, float(grams))
        row = existing.get(name.lower())
        if row is None:
            row = MealLogItem(food_name=name)
            log.items.append(row)
        row.grams = grams
        for k in NUTRIENT_KEYS:
            setattr(row, k, snapshot.get(k))
    log.updated_at = utcnow()

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This meal was modified at the same time; please retry")
    response.status_code = 201 if created else 200
    return {**meal_log_dict(_load_log(db, log.log_id, user.username)), "created": created}


@app.get("/api/meal-logs")
def meal_history(start_date: date | None = None, end_date: date | None = None,
                 user: User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(MealLog).options(selectinload(MealLog.items), joinedload(MealLog.mess)).where(MealLog.username == user.username)
    if start_date:
        stmt = stmt.where(MealLog.log_date >= start_date)
    if end_date:
        stmt = stmt.where(MealLog.log_date <= end_date)
    rows = db.scalars(stmt.order_by(MealLog.log_date.desc(), MealLog.created_at.desc())).unique().all()
    return [meal_log_dict(r) for r in rows]


@app.get("/api/meal-logs/summary")
def meal_summary(summary_date: date = Query(default_factory=date.today), user: User = Depends(current_user), db: Session = Depends(get_db)):
    logs = meal_history(summary_date, summary_date, user, db)
    totals = {}
    for k in NUTRIENT_KEYS:
        known = [log["totals"][k] for log in logs if log["totals"][k] is not None]
        totals[k] = round(sum(known), 2) if known else None
    return {"date": summary_date.isoformat(), "meal_count": len(logs), "totals": totals, "meals": logs}


@app.get("/api/meal-logs/{log_id}")
def get_meal_log(log_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return meal_log_dict(_load_log(db, log_id, user.username))


@app.delete("/api/meal-logs/{log_id}")
def delete_meal_log(log_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    log = _load_log(db, log_id, user.username)
    db.delete(log)  # meal_log_items rows are removed by ON DELETE CASCADE
    db.commit()
    return {"message": "Meal log deleted"}


@app.delete("/api/meal-logs/{log_id}/items/{item_id}")
def delete_meal_log_item(log_id: int, item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    log = _load_log(db, log_id, user.username)
    item = next((i for i in log.items if i.item_id == item_id), None)
    if not item:
        raise HTTPException(404, "Meal log item not found")
    log.items.remove(item)
    if not log.items:  # don't leave an empty header behind
        db.delete(log)
        db.commit()
        return {"message": "Item deleted; meal log was empty and has been removed", "log_deleted": True}
    log.updated_at = utcnow()
    db.commit()
    return {"message": "Item deleted", "log_deleted": False}
