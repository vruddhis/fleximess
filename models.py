from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Date, DateTime, Boolean,
    ForeignKey, Numeric, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "students"
    student_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    ldap_id = Column(String(80), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    preferences = relationship("StudentPreference", back_populates="student", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="student", cascade="all, delete-orphan")
    meal_logs = relationship("MealLog", back_populates="student", cascade="all, delete-orphan")

class Mess(Base):
    __tablename__ = "messes"
    mess_id = Column(Integer, primary_key=True)
    mess_name = Column(String(100), nullable=False, unique=True)
    menus = relationship("Menu", back_populates="mess")

class Menu(Base):
    __tablename__ = "menus"
    menu_id = Column(BigInteger, primary_key=True)
    mess_id = Column(Integer, ForeignKey("messes.mess_id"), nullable=False)
    menu_date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("mess_id", "menu_date", "meal_type", name="uq_menu_mess_date_meal"),
        CheckConstraint("meal_type IN ('breakfast','lunch','snacks','dinner')", name="ck_menu_meal_type"),
    )
    mess = relationship("Mess", back_populates="menus")
    items = relationship("MenuItem", back_populates="menu", cascade="all, delete-orphan")

class FoodCategory(Base):
    __tablename__ = "food_categories"
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(50), nullable=False, unique=True)

class Food(Base):
    __tablename__ = "foods"
    food_id = Column(BigInteger, primary_key=True)
    food_name = Column(String(150), nullable=False, unique=True, index=True)
    category_id = Column(Integer, ForeignKey("food_categories.category_id"))
    description = Column(Text)
    nutrition = relationship("Nutrition", back_populates="food", uselist=False)
    menu_items = relationship("MenuItem", back_populates="food")

class MenuItem(Base):
    __tablename__ = "menu_items"
    menu_id = Column(BigInteger, ForeignKey("menus.menu_id", ondelete="CASCADE"), primary_key=True)
    food_id = Column(BigInteger, ForeignKey("foods.food_id"), primary_key=True)
    serving_weight_g = Column(Numeric(8,2))
    serving_description = Column(String(100))
    menu = relationship("Menu", back_populates="items")
    food = relationship("Food", back_populates="menu_items")

class Nutrition(Base):
    __tablename__ = "nutrition"
    nutrition_id = Column(BigInteger, primary_key=True)
    food_id = Column(BigInteger, ForeignKey("foods.food_id"), nullable=False, unique=True)
    basis_amount = Column(Numeric(8,2), nullable=False, default=100)
    basis_unit = Column(String(10), nullable=False, default="g")
    calories_kcal = Column(Numeric(8,2))
    protein_g = Column(Numeric(8,2))
    carbs_g = Column(Numeric(8,2))
    fat_g = Column(Numeric(8,2))
    fiber_g = Column(Numeric(8,2))
    sugar_g = Column(Numeric(8,2))
    source = Column(Text)
    confidence = Column(String(10))
    food = relationship("Food", back_populates="nutrition")

class StudentPreference(Base):
    __tablename__ = "student_preferences"
    preference_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    goal = Column(String(30), nullable=False, default="balanced")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("student_id", name="uq_preference_student"),)
    student = relationship("User", back_populates="preferences")

class Favorite(Base):
    __tablename__ = "favorites"
    favorite_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    food_id = Column(BigInteger, ForeignKey("foods.food_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("student_id", "food_id", name="uq_favorite_student_food"),)
    student = relationship("User", back_populates="favorites")
    food = relationship("Food")

class MealLog(Base):
    __tablename__ = "meal_logs"
    log_id = Column(BigInteger, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    mess_id = Column(Integer, ForeignKey("messes.mess_id"), nullable=False)
    food_id = Column(BigInteger, ForeignKey("foods.food_id"), nullable=False)
    meal_date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)
    quantity_g = Column(Numeric(8,2), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("quantity_g > 0", name="ck_meal_log_quantity"),
        CheckConstraint("meal_type IN ('breakfast','lunch','snacks','dinner')", name="ck_meal_log_meal_type"),
    )
    student = relationship("User", back_populates="meal_logs")
    mess = relationship("Mess")
    food = relationship("Food")
