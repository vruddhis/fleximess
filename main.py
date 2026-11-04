from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, select
from app.config import settings
from app.database import Base, engine, get_db
from app import models, schemas
from app.models import User, Mess, Menu, Food, MenuItem, Nutrition, StudentPreference, Favorite, MealLog
from app.security import hash_password, verify_password, create_access_token, get_current_user

# Creates missing tables on first run. For an existing database, run migration.sql first.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlexiMess Optimiser API", version="1.0.0",
              description="Backend APIs for FlexiMess: menus, nutrition, preferences and meal tracking.")
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

def num(value):
    return float(value) if value is not None else None

def nutrition_for(food: Food, grams: float):
    n = food.nutrition
    if not n or not n.basis_amount or n.basis_unit.lower() != "g":
        return {k: None for k in ("calories_kcal","protein_g","carbs_g","fat_g","fiber_g","sugar_g")}
    factor = grams / float(n.basis_amount)
    return {k: (num(getattr(n, k)) * factor if getattr(n, k) is not None else None)
            for k in ("calories_kcal","protein_g","carbs_g","fat_g","fiber_g","sugar_g")}

def food_payload(food: Food, serving_weight=None, serving_description=None):
    n = food.nutrition
    return {
        "food_id": food.food_id, "food_name": food.food_name,
        "serving_weight_g": num(serving_weight),
        "serving_description": serving_description,
        "nutrition_per_100g": ({
            "basis_amount": num(n.basis_amount), "basis_unit": n.basis_unit,
            "calories_kcal": num(n.calories_kcal), "protein_g": num(n.protein_g),
            "carbs_g": num(n.carbs_g), "fat_g": num(n.fat_g),
            "fiber_g": num(n.fiber_g), "sugar_g": num(n.sugar_g),
            "source": n.source, "confidence": n.confidence
        } if n else None),
    }

@app.get("/")
def root():
    return {"message": "FlexiMess API is running", "docs": "/docs"}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(func.now()))
    return {"status": "ok", "database": "connected"}

@app.post("/api/auth/signup", response_model=schemas.TokenResponse, status_code=201)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    ldap = payload.ldap_id.strip().lower()
    if db.query(User).filter(func.lower(User.ldap_id) == ldap).first():
        raise HTTPException(409, "This LDAP ID is already registered.")
    user = User(name=payload.name.strip(), ldap_id=ldap, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    db.add(StudentPreference(student_id=user.student_id, goal="balanced"))
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.student_id), "student": {
        "student_id": user.student_id, "name": user.name, "ldap_id": user.ldap_id}}

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.ldap_id) == payload.ldap_id.strip().lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid LDAP ID or password.")
    return {"access_token": create_access_token(user.student_id), "student": {
        "student_id": user.student_id, "name": user.name, "ldap_id": user.ldap_id}}

@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"student_id": user.student_id, "name": user.name, "ldap_id": user.ldap_id}

@app.get("/api/messes")
def list_messes(db: Session = Depends(get_db)):
    return [{"mess_id": m.mess_id, "mess_name": m.mess_name}
            for m in db.query(Mess).order_by(Mess.mess_name).all()]

@app.get("/api/foods")
def search_foods(q: str = Query("", max_length=100), db: Session = Depends(get_db)):
    query = db.query(Food).options(joinedload(Food.nutrition))
    if q.strip():
        query = query.filter(Food.food_name.ilike(f"%{q.strip()}%"))
    return [food_payload(f) for f in query.order_by(Food.food_name).limit(100).all()]

@app.get("/api/menus")
def get_menus(
    menu_date: date = Query(default_factory=date.today),
    meal_type: schemas.MealType = "lunch",
    mess_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Menu).options(joinedload(Menu.mess), joinedload(Menu.items).joinedload(MenuItem.food).joinedload(Food.nutrition))
    query = query.filter(Menu.menu_date == menu_date, Menu.meal_type == meal_type)
    if mess_id:
        query = query.filter(Menu.mess_id == mess_id)
    if search:
        query = query.join(Menu.items).join(MenuItem.food).filter(Food.food_name.ilike(f"%{search}%"))
    menus = query.order_by(Menu.mess_id).all()
    return [{
        "menu_id": m.menu_id, "mess_id": m.mess_id, "mess_name": m.mess.mess_name,
        "menu_date": m.menu_date, "meal_type": m.meal_type,
        "items": [food_payload(i.food, i.serving_weight_g, i.serving_description) for i in m.items]
    } for m in menus]

@app.get("/api/menus/{menu_id}")
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    m = db.query(Menu).options(joinedload(Menu.mess), joinedload(Menu.items).joinedload(MenuItem.food).joinedload(Food.nutrition)).filter(Menu.menu_id == menu_id).first()
    if not m:
        raise HTTPException(404, "Menu not found.")
    return {"menu_id": m.menu_id, "mess_id": m.mess_id, "mess_name": m.mess.mess_name,
            "menu_date": m.menu_date, "meal_type": m.meal_type,
            "items": [food_payload(i.food, i.serving_weight_g, i.serving_description) for i in m.items]}

@app.get("/api/recommendations")
def recommendations(
    menu_date: date = Query(default_factory=date.today),
    meal_type: schemas.MealType = "lunch",
    goal: Optional[schemas.GoalType] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not goal:
        pref = db.query(StudentPreference).filter_by(student_id=user.student_id).first()
        goal = pref.goal if pref else "balanced"
    menus = db.query(Menu).options(joinedload(Menu.mess), joinedload(Menu.items).joinedload(MenuItem.food).joinedload(Food.nutrition)).filter(
        Menu.menu_date == menu_date, Menu.meal_type == meal_type).all()
    results = []
    for m in menus:
        totals = {k: 0.0 for k in ("calories_kcal","protein_g","carbs_g","fat_g","fiber_g")}
        known = 0
        for item in m.items:
            weight = num(item.serving_weight_g) or 100.0
            values = nutrition_for(item.food, weight)
            if values["calories_kcal"] is not None:
                known += 1
            for key in totals:
                if values[key] is not None:
                    totals[key] += values[key]
        if goal == "high_protein":
            score = totals["protein_g"]
        elif goal == "high_fiber":
            score = totals["fiber_g"]
        elif goal == "low_calories":
            score = -totals["calories_kcal"]
        else:
            score = totals["protein_g"] + totals["fiber_g"] * 2 - totals["calories_kcal"] * 0.01
        results.append({"menu_id":m.menu_id,"mess_id":m.mess_id,"mess_name":m.mess.mess_name,
                        "meal_type":m.meal_type,"menu_date":m.menu_date,"goal":goal,
                        "score":round(score,2),"nutrition_totals":{k:round(v,2) for k,v in totals.items()},
                        "nutrition_coverage":f"{known}/{len(m.items)} items"})
    results.sort(key=lambda x:x["score"], reverse=True)
    for index, row in enumerate(results, 1):
        row["rank"] = index
    return results

@app.get("/api/preferences")
def get_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pref = db.query(StudentPreference).filter_by(student_id=user.student_id).first()
    return {"goal": pref.goal if pref else "balanced"}

@app.put("/api/preferences")
def update_preferences(payload: schemas.PreferenceRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pref = db.query(StudentPreference).filter_by(student_id=user.student_id).first()
    if pref:
        pref.goal = payload.goal
    else:
        db.add(StudentPreference(student_id=user.student_id, goal=payload.goal))
    db.commit()
    return {"message":"Preferences saved", "goal":payload.goal}

@app.get("/api/favorites")
def get_favorites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Favorite).options(joinedload(Favorite.food).joinedload(Food.nutrition)).filter_by(student_id=user.student_id).all()
    return [food_payload(r.food) for r in rows]

@app.post("/api/favorites/{food_id}", status_code=201)
def add_favorite(food_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    food = db.query(Food).filter_by(food_id=food_id).first()
    if not food:
        raise HTTPException(404, "Food not found.")
    exists = db.query(Favorite).filter_by(student_id=user.student_id, food_id=food_id).first()
    if not exists:
        db.add(Favorite(student_id=user.student_id, food_id=food_id))
        db.commit()
    return {"message":"Dish added to favourites", "food_id":food_id}

@app.delete("/api/favorites/{food_id}")
def remove_favorite(food_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(Favorite).filter_by(student_id=user.student_id, food_id=food_id).first()
    if not row:
        raise HTTPException(404, "Favourite dish not found.")
    db.delete(row)
    db.commit()
    return {"message":"Dish removed from favourites"}

@app.get("/api/notifications")
def favorite_notifications(
    from_date: date = Query(default_factory=date.today),
    days: int = Query(7, ge=1, le=31),
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    end_date = from_date + timedelta(days=days-1)
    rows = db.query(Menu, Mess, MenuItem, Food).join(Mess, Menu.mess_id==Mess.mess_id).join(
        MenuItem, Menu.menu_id==MenuItem.menu_id).join(Food, MenuItem.food_id==Food.food_id).join(
        Favorite, Favorite.food_id==Food.food_id).filter(
        Favorite.student_id==user.student_id, Menu.menu_date.between(from_date,end_date)
    ).order_by(Menu.menu_date, Menu.meal_type, Mess.mess_name).all()
    return [{"date":m.menu_date,"meal_type":m.meal_type,"mess_id":mess.mess_id,
             "mess_name":mess.mess_name,"food_id":food.food_id,"food_name":food.food_name,
             "message":f"{food.food_name} is being served at {mess.mess_name}"} for m,mess,mi,food in rows]

@app.post("/api/meal-logs", status_code=201)
def create_meal_log(payload: schemas.MealLogCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Mess).filter_by(mess_id=payload.mess_id).first():
        raise HTTPException(404, "Mess not found.")
    food = db.query(Food).options(joinedload(Food.nutrition)).filter_by(food_id=payload.food_id).first()
    if not food:
        raise HTTPException(404, "Food not found.")
    log = MealLog(student_id=user.student_id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    values = nutrition_for(food, payload.quantity_g)
    return {"log_id":log.log_id,"message":"Meal logged successfully","food_name":food.food_name,
            "quantity_g":payload.quantity_g,"nutrition":values}

@app.get("/api/meal-logs")
def get_meal_logs(
    from_date: Optional[date] = None, to_date: Optional[date] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    query = db.query(MealLog).options(joinedload(MealLog.food).joinedload(Food.nutrition), joinedload(MealLog.mess)).filter(MealLog.student_id==user.student_id)
    if from_date: query = query.filter(MealLog.meal_date >= from_date)
    if to_date: query = query.filter(MealLog.meal_date <= to_date)
    logs = query.order_by(MealLog.meal_date.desc(), MealLog.created_at.desc()).all()
    output = []
    for item in logs:
        n = nutrition_for(item.food, float(item.quantity_g))
        output.append({"log_id":item.log_id,"meal_date":item.meal_date,"meal_type":item.meal_type,
                       "mess_id":item.mess_id,"mess_name":item.mess.mess_name,
                       "food_id":item.food_id,"food_name":item.food.food_name,
                       "quantity_g":num(item.quantity_g),"nutrition":n})
    return output

@app.get("/api/meal-logs/summary")
def meal_log_summary(
    summary_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    logs = db.query(MealLog).options(joinedload(MealLog.food).joinedload(Food.nutrition)).filter(
        MealLog.student_id==user.student_id, MealLog.meal_date==summary_date).all()
    totals = {k:0.0 for k in ("calories_kcal","protein_g","carbs_g","fat_g","fiber_g","sugar_g")}
    missing = 0
    for item in logs:
        values = nutrition_for(item.food, float(item.quantity_g))
        if values["calories_kcal"] is None: missing += 1
        for key, value in values.items():
            if value is not None: totals[key] += value
    return {"date":summary_date,"number_of_logged_items":len(logs),
            "items_without_nutrition":missing,"totals":{k:round(v,2) for k,v in totals.items()}}

@app.delete("/api/meal-logs/{log_id}")
def delete_meal_log(log_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(MealLog).filter_by(log_id=log_id, student_id=user.student_id).first()
    if not row: raise HTTPException(404, "Meal log not found.")
    db.delete(row)
    db.commit()
    return {"message":"Meal log deleted"}

