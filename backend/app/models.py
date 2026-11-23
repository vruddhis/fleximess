"""ORM models mirroring the live Supabase schema (public schema).
"""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (String, Text, Integer, BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric,
                        UniqueConstraint, CheckConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

MEAL_TYPES = ("breakfast", "lunch", "snacks", "dinner")


class Mess(Base):
    __tablename__ = "messes"
    mess_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mess_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Category(Base):
    __tablename__ = "food_categories"
    category_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)


class Food(Base):
    __tablename__ = "foods"
    food_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    food_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("food_categories.category_id"))
    description: Mapped[str | None] = mapped_column(Text)
    default_serving_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    default_serving_desc: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[Category | None] = relationship()
    nutrition: Mapped["Nutrition | None"] = relationship(back_populates="food", uselist=False)


class Menu(Base):
    __tablename__ = "menus"
    __table_args__ = (UniqueConstraint("mess_id", "menu_date", "meal_type"),
                      CheckConstraint("meal_type IN ('breakfast','lunch','snacks','dinner')"))
    menu_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mess_id: Mapped[int] = mapped_column(ForeignKey("messes.mess_id"), nullable=False)
    menu_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    mess: Mapped[Mess] = relationship()
    items: Mapped[list["MenuItem"]] = relationship(cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.menu_id", ondelete="CASCADE"), primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.food_id"), primary_key=True)
    serving_weight_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    serving_description: Mapped[str | None] = mapped_column(String(100))
    food: Mapped[Food] = relationship()


class Nutrition(Base):
    __tablename__ = "nutrition"
    nutrition_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.food_id"), unique=True, nullable=False)
    basis_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, server_default="100")
    basis_unit: Mapped[str] = mapped_column(String(10), nullable=False, server_default="g")
    calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    source: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(10))
    food: Mapped[Food] = relationship(back_populates="nutrition")


class User(Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    hostel_id: Mapped[int | None] = mapped_column(ForeignKey("messes.mess_id", ondelete="SET NULL"))
    role: Mapped[str] = mapped_column(String(10), nullable=False, server_default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preferences: Mapped["Preference | None"] = relationship(back_populates="user", uselist=False)


# Per-meal nutrient targets in user_preferences. Note the DB spells "fibre".
# Maps column suffix -> maximum allowed by the DB CHECK constraint (minimum is 0).
PREFERENCE_NUTRIENTS = {
    "calories_kcal": 2000,
    "protein_g": 300,
    "carbs_g": 300,
    "fibre_g": 100,
    "sugar_g": 300,
}
PREFERENCE_COLUMNS = [f"{meal}_{nutrient}" for meal in MEAL_TYPES for nutrient in PREFERENCE_NUTRIENTS]


class Preference(Base):
    __tablename__ = "user_preferences"
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    breakfast_calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(6, 0))
    lunch_calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(6, 0))
    snacks_calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(6, 0))
    dinner_calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(6, 0))
    breakfast_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    lunch_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    snacks_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    dinner_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    breakfast_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    lunch_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    snacks_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    dinner_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    breakfast_fibre_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    lunch_fibre_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    snacks_fibre_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    dinner_fibre_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    breakfast_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    lunch_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    snacks_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    dinner_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user: Mapped[User] = relationship(back_populates="preferences")


class MealLog(Base):
    """Header row: one per (username, log_date, mess_id, meal_type)."""
    __tablename__ = "meal_logs"
    __table_args__ = (UniqueConstraint("username", "log_date", "mess_id", "meal_type"),
                      CheckConstraint("meal_type IN ('breakfast','lunch','snacks','dinner')"))
    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    mess_id: Mapped[int] = mapped_column(ForeignKey("messes.mess_id"), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    mess: Mapped[Mess] = relationship()
    items: Mapped[list["MealLogItem"]] = relationship(
        back_populates="log", cascade="all, delete-orphan", passive_deletes=True, order_by="MealLogItem.item_id")


class MealLogItem(Base):
    """Child row: one food eaten in a meal log. Stores the food NAME (no FK to
    foods) plus a snapshot of the nutrition for the grams eaten."""
    __tablename__ = "meal_log_items"
    __table_args__ = (UniqueConstraint("log_id", "food_name"),)
    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    log_id: Mapped[int] = mapped_column(ForeignKey("meal_logs.log_id", ondelete="CASCADE"), nullable=False)
    food_name: Mapped[str] = mapped_column(String(150), nullable=False)
    grams: Mapped[Decimal] = mapped_column(Numeric(7, 1), nullable=False)
    calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    log: Mapped[MealLog] = relationship(back_populates="items")
