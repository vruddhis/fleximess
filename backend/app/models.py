from datetime import date, datetime
from sqlalchemy import String, Text, Integer, BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, UniqueConstraint, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

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
    food_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    food_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("food_categories.category_id"))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[Category | None] = relationship()
    nutrition: Mapped["Nutrition | None"] = relationship(back_populates="food", uselist=False)

class Menu(Base):
    __tablename__ = "menus"
    __table_args__ = (UniqueConstraint("mess_id", "menu_date", "meal_type"), CheckConstraint("meal_type IN ('breakfast','lunch','snacks','dinner')"))
    menu_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    mess_id: Mapped[int] = mapped_column(ForeignKey("messes.mess_id", ondelete="CASCADE"), nullable=False)
    menu_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    mess: Mapped[Mess] = relationship()
    items: Mapped[list["MenuItem"]] = relationship(cascade="all, delete-orphan")

class MenuItem(Base):
    __tablename__ = "menu_items"
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.menu_id", ondelete="CASCADE"), primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.food_id"), primary_key=True)
    serving_weight_g: Mapped[float | None] = mapped_column(Numeric(8,2))
    serving_description: Mapped[str | None] = mapped_column(String(100))
    food: Mapped[Food] = relationship()

class Nutrition(Base):
    __tablename__ = "nutrition"
    nutrition_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.food_id", ondelete="CASCADE"), unique=True)
    basis_amount: Mapped[float] = mapped_column(Numeric(8,2), default=100)
    basis_unit: Mapped[str] = mapped_column(String(10), default="g")
    calories_kcal: Mapped[float | None] = mapped_column(Numeric(8,2))
    protein_g: Mapped[float | None] = mapped_column(Numeric(8,2))
    carbs_g: Mapped[float | None] = mapped_column(Numeric(8,2))
    fat_g: Mapped[float | None] = mapped_column(Numeric(8,2))
    fiber_g: Mapped[float | None] = mapped_column(Numeric(8,2))
    sugar_g: Mapped[float | None] = mapped_column(Numeric(8,2))
    source: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(10))
    food: Mapped[Food] = relationship(back_populates="nutrition")

class User(Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    hostel_id: Mapped[int | None] = mapped_column(ForeignKey("messes.mess_id", ondelete="SET NULL"))
    role: Mapped[str] = mapped_column(String(10), default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    preferences: Mapped["Preference | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class Preference(Base):
    __tablename__ = "user_preferences"
    username: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), primary_key=True)
    goals: Mapped[str] = mapped_column(String(100), default="balanced")
    priority_goals: Mapped[str] = mapped_column(Text, default="[]")
    breakfast_calories: Mapped[int | None] = mapped_column(Integer)
    lunch_calories: Mapped[int | None] = mapped_column(Integer)
    snacks_calories: Mapped[int | None] = mapped_column(Integer)
    dinner_calories: Mapped[int | None] = mapped_column(Integer)
    user: Mapped[User] = relationship(back_populates="preferences")

class Favorite(Base):
    __tablename__ = "favorites"
    username: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.food_id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class MealLog(Base):
    __tablename__ = "meal_logs"
    log_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    username: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    mess_id: Mapped[int] = mapped_column(ForeignKey("messes.mess_id"), nullable=False)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.food_id"), nullable=False)
    meal_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity_g: Mapped[float] = mapped_column(Numeric(8,2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    food: Mapped[Food] = relationship()
    mess: Mapped[Mess] = relationship()
