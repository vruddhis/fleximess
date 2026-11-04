-- Run this against the EXISTING flexi_mess database before starting the API.
-- It adds uniqueness required by the scraper's ON CONFLICT statements and
-- creates the student-specific tables. Back up your database first.
ALTER TABLE messes ADD CONSTRAINT uq_messes_mess_name UNIQUE (mess_name);
ALTER TABLE foods ADD CONSTRAINT uq_foods_food_name UNIQUE (food_name);

CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    ldap_id VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS student_preferences (
    preference_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id INTEGER NOT NULL UNIQUE REFERENCES students(student_id) ON DELETE CASCADE,
    goal VARCHAR(30) NOT NULL DEFAULT 'balanced'
        CHECK (goal IN ('high_protein','high_fiber','low_calories','balanced')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS favorites (
    favorite_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    food_id BIGINT NOT NULL REFERENCES foods(food_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, food_id)
);
CREATE TABLE IF NOT EXISTS meal_logs (
    log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    mess_id INTEGER NOT NULL REFERENCES messes(mess_id),
    food_id BIGINT NOT NULL REFERENCES foods(food_id),
    meal_date DATE NOT NULL,
    meal_type VARCHAR(20) NOT NULL CHECK (meal_type IN ('breakfast','lunch','snacks','dinner')),
    quantity_g NUMERIC(8,2) NOT NULL CHECK (quantity_g > 0),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_menus_date_meal ON menus(menu_date, meal_type);
CREATE INDEX IF NOT EXISTS idx_meal_logs_student_date ON meal_logs(student_id, meal_date);
