import os
from datetime import date, datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, load_only

from .database import get_db
from .models import Food, Menu, MenuItem, Mess, Preference, User, MEAL_TYPES

SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-this-secret-key-please")
ALGORITHM = "HS256"
TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
password_hasher = PasswordHasher()

app = FastAPI(title="FlexiMess Demo API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginInput(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class SignupInput(LoginInput):
    name: str = Field(min_length=1)


class StudentPreferencesInput(BaseModel):
    username: str = Field(min_length=1)
    breakfast_calories: int | None = Field(default=None, ge=0)
    lunch_calories: int | None = Field(default=None, ge=0)
    snacks_calories: int | None = Field(default=None, ge=0)
    dinner_calories: int | None = Field(default=None, ge=0)
    nutrition_preferences: list[str] | None = Field(default=None, max_length=2)


def start_session(user: User, response: Response) -> dict:
    now = datetime.now(timezone.utc)
    session_id = jwt.encode(
        {
            "sub": user.username,
            "iat": now,
            "exp": now + timedelta(minutes=TOKEN_MINUTES),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response.set_cookie(
        "session_id",
        session_id,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=TOKEN_MINUTES * 60,
    )
    return {"user": {"username": user.username, "name": user.name}}


def get_current_user(
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not session_id:
        raise HTTPException(status_code=401, detail="Please log in first")

    try:
        payload = jwt.decode(session_id, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    username = payload.get("sub")
    user = db.get(User, username) if username else None
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User account is unavailable")
    return user


student_preferences: dict[str, dict] = {}


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "FlexiMess demo API is running", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login")
@app.post("/api/auth/login")
def login(
    data: LoginInput,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    username = data.username.strip().lower()
    user = db.get(User, username)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    try:
        password_hasher.verify(user.password_hash, data.password)
    except (VerifyMismatchError, VerificationError):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return start_session(user, response)


@app.post("/auth/signup", status_code=201)
@app.post("/api/auth/signup", status_code=201)
def signup(
    data: SignupInput,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    username = data.username.strip().lower()
    if db.get(User, username):
        raise HTTPException(status_code=409, detail="Username already exists")

    user = User(
        username=username,
        name=data.name.strip(),
        password_hash=password_hasher.hash(data.password),
    )
    db.add(user)
    db.flush()
    if db.get(Preference, username) is None:
        db.add(Preference(username=username))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists")

    db.refresh(user)
    return start_session(user, response)


@app.get("/auth/me")
@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"user": {"username": user.username, "name": user.name}}


@app.post("/auth/logout")
@app.post("/api/auth/logout")
def logout(
    response: Response,
) -> dict[str, str]:
    response.delete_cookie("session_id")
    return {"message": "Logged out"}


@app.post("/api/preferences")
def save_student_preferences(
    data: StudentPreferencesInput,
    user: User = Depends(get_current_user),
) -> dict:
    #connect to the database here and add to the database. can also be empty so be careful
    username = data.username.strip()
    if username != user.username:
        raise HTTPException(status_code=403, detail="You can only update your own preferences")

    preferences = student_preferences.setdefault(username, {})
    updates = data.model_dump(exclude={"username"}, exclude_unset=True)
    if "nutrition_preferences" in updates:
        allowed_preferences = {"High protein", "High fiber", "Low sugar", "Low carbohydrate"}
        if any(value not in allowed_preferences for value in updates["nutrition_preferences"]):
            raise HTTPException(status_code=400, detail="Unsupported nutrition preference")
    preferences.update(updates)
    return {"username": username, **preferences}


@app.get("/api/preferences/sort")
def get_sort_preferences(user: User = Depends(get_current_user)) -> list[str]:
    #add database connection here
    return student_preferences.get(user.username, {}).get(
        "nutrition_preferences",
        ["High protein", "Low sugar"],
    )


@app.get("/api/history")
def get_student_history(
    user: User = Depends(get_current_user),
) -> list[dict]:
    today = date.today()
    yesterday = date.fromordinal(today.toordinal() - 1)
    return [
        {
            "itemID": 1,
            "name": "Idli",
            "hostelID": 1,
            "grams": 100,
            "date": today.isoformat(),
            "protein": 2,
            "fibre": 0.2,
        },
        {
            "itemID": 2,
            "name": "Rice",
            "hostelID": 1,
            "grams": 200,
            "date": yesterday.isoformat(),
            "protein": 5.4,
            "fibre": 0.8,
        },
    ]


@app.get("/api/messes")
def list_messes(db: Session = Depends(get_db)) -> list[dict[str, int | str]]:
    messes = db.scalars(select(Mess).order_by(Mess.mess_name)).all()
    return [
        {"mess_id": mess.mess_id, "mess_name": mess.mess_name}
        for mess in messes
    ]


@app.get("/api/foods")
def list_foods(
    q: str = Query(default=""),
    mess_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(Food).options(
        load_only(Food.food_id, Food.food_name, Food.category_id),
        joinedload(Food.category),
        joinedload(Food.nutrition),
    )
    if mess_id is not None:
        mess_food_ids = select(MenuItem.food_id).join(
            Menu, Menu.menu_id == MenuItem.menu_id,
        ).where(Menu.mess_id == mess_id)
        stmt = stmt.where(Food.food_id.in_(mess_food_ids))
    if q.strip():
        stmt = stmt.where(Food.food_name.ilike(f"%{q.strip()}%"))

    foods = db.scalars(stmt.order_by(Food.food_name)).unique().all()
    return [
        {
            "food_id": food.food_id,
            "name": food.food_name,
            "category": food.category.category_name if food.category else None,
            "nutrition": {
                "calories_kcal": float(food.nutrition.calories_kcal or 0) if food.nutrition else 0,
                "protein_g": float(food.nutrition.protein_g or 0) if food.nutrition else 0,
                "fiber_g": float(food.nutrition.fiber_g or 0) if food.nutrition else 0,
                "sugar_g": float(food.nutrition.sugar_g or 0) if food.nutrition else 0,
            },
        }
        for food in foods
    ]


@app.get("/api/menus")
def list_menus(
    menu_date: date = Query(default_factory=date.today),
    meal_type: str | None = None,
    mess_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    meal = meal_type.casefold() if meal_type else None
    if meal and meal not in MEAL_TYPES:
        raise HTTPException(status_code=400, detail="Use breakfast, lunch, snacks, or dinner")

    stmt = select(Menu).options(
        joinedload(Menu.mess),
        joinedload(Menu.items)
        .joinedload(MenuItem.food)
        .load_only(Food.food_id, Food.food_name),
        joinedload(Menu.items)
        .joinedload(MenuItem.food)
        .joinedload(Food.nutrition),
    ).where(Menu.menu_date == menu_date)
    if meal:
        stmt = stmt.where(Menu.meal_type == meal)
    if mess_id is not None:
        stmt = stmt.where(Menu.mess_id == mess_id)

    menus = db.scalars(
        stmt.order_by(Menu.mess_id, Menu.meal_type),
    ).unique().all()
    return [
        {
            "mess_id": menu.mess_id,
            "mess_name": menu.mess.mess_name,
            "menu_date": menu.menu_date.isoformat(),
            "meal_type": menu.meal_type,
            "items": [
                {
                    "food_id": item.food.food_id,
                    "food_item": item.food.food_name,
                    "mess_id": menu.mess_id,
                    "hostel_id": menu.mess_id,
                    "calories": float(item.food.nutrition.calories_kcal or 0) if item.food.nutrition else 0,
                    "protein": float(item.food.nutrition.protein_g or 0) if item.food.nutrition else 0,
                    "fiber": float(item.food.nutrition.fiber_g or 0) if item.food.nutrition else 0,
                    "sugar": float(item.food.nutrition.sugar_g or 0) if item.food.nutrition else 0,
                }
                for item in menu.items
            ],
        }
        for menu in menus
    ]
