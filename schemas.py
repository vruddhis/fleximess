from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, EmailStr

MealType = Literal["breakfast", "lunch", "snacks", "dinner"]
GoalType = Literal["high_protein", "high_fiber", "low_calories", "balanced"]

class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    ldap_id: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    ldap_id: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: dict

class PreferenceRequest(BaseModel):
    goal: GoalType

class MealLogCreate(BaseModel):
    mess_id: int
    food_id: int
    meal_date: date
    meal_type: MealType
    quantity_g: float = Field(gt=0, le=10000)
    notes: Optional[str] = None

class MealLogResponse(BaseModel):
    log_id: int
    mess_id: int
    mess_name: str
    food_id: int
    food_name: str
    meal_date: date
    meal_type: str
    quantity_g: float
    calories_kcal: Optional[float]
    protein_g: Optional[float]
    carbs_g: Optional[float]
    fat_g: Optional[float]
    fiber_g: Optional[float]
    model_config = ConfigDict(from_attributes=True)
