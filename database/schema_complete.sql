-- flexi mess database, run once on an empty database
-- order: menus and scraper tables, then login, preferences and meal logs

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------- menus (from the scraper) ----------

CREATE TABLE messes (
    mess_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mess_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE menus (
    menu_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mess_id INTEGER NOT NULL REFERENCES messes(mess_id),
    menu_date DATE NOT NULL,
    meal_type VARCHAR(20) NOT NULL
        CHECK (meal_type IN ('breakfast', 'lunch', 'snacks', 'dinner')),
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (mess_id, menu_date, meal_type)
);

CREATE TABLE food_categories (
    category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE foods (
    food_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    food_name VARCHAR(150) NOT NULL UNIQUE,
    category_id INTEGER REFERENCES food_categories(category_id),
    description TEXT,
    default_serving_g NUMERIC(8,2) CHECK (default_serving_g > 0),
    default_serving_desc VARCHAR(100)
);

CREATE TABLE menu_items (
    menu_id BIGINT NOT NULL REFERENCES menus(menu_id) ON DELETE CASCADE,
    food_id BIGINT NOT NULL REFERENCES foods(food_id),
    serving_weight_g NUMERIC(8,2) CHECK (serving_weight_g > 0),
    serving_description VARCHAR(100),
    PRIMARY KEY (menu_id, food_id)
);

CREATE TABLE nutrition (
    nutrition_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    food_id BIGINT NOT NULL UNIQUE REFERENCES foods(food_id),
    basis_amount NUMERIC(8,2) NOT NULL DEFAULT 100 CHECK (basis_amount > 0),
    basis_unit VARCHAR(10) NOT NULL DEFAULT 'g',
    calories_kcal NUMERIC(8,2) CHECK (calories_kcal >= 0),
    protein_g NUMERIC(8,2) CHECK (protein_g >= 0),
    carbs_g NUMERIC(8,2) CHECK (carbs_g >= 0),
    fat_g NUMERIC(8,2) CHECK (fat_g >= 0),
    fiber_g NUMERIC(8,2) CHECK (fiber_g >= 0),
    sugar_g NUMERIC(8,2) CHECK (sugar_g >= 0),
    source TEXT,
    confidence VARCHAR(10) CHECK (confidence IN ('low', 'medium', 'high'))
);

-- scraper helper tables
CREATE TABLE food_aliases (
    alias_name VARCHAR(150) PRIMARY KEY,
    canonical_name VARCHAR(150) NOT NULL,
    source VARCHAR(10) NOT NULL DEFAULT 'auto',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE name_review (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kind VARCHAR(20) NOT NULL,
    new_name VARCHAR(150) NOT NULL,
    candidate_name VARCHAR(150) NOT NULL DEFAULT '',
    status VARCHAR(10) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'merged', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (kind, new_name, candidate_name)
);

CREATE TABLE nutrition_raw (
    food_name VARCHAR(150) PRIMARY KEY,
    source_url TEXT NOT NULL,
    status VARCHAR(30) NOT NULL,
    page_title TEXT,
    title_match NUMERIC(3,2),
    basis_text VARCHAR(50),
    calories_kcal NUMERIC(8,2), protein_g NUMERIC(8,2), carbs_g NUMERIC(8,2),
    fat_g NUMERIC(8,2), fiber_g NUMERIC(8,2), sugar_g NUMERIC(8,2),
    alternatives TEXT,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- login ----------

CREATE TABLE users (
    -- usernames are checked by the backend
    username VARCHAR(20) PRIMARY KEY
        CHECK (username NOT IN ('admin', 'administrator', 'root', 'support', 'system', 'flexi', 'flexiadmin')),
    name VARCHAR(100) NOT NULL CHECK (length(trim(name)) > 0),
    -- bcrypt or argon2 hash only, never the password
    password_hash TEXT NOT NULL CHECK (length(password_hash) > 0),
    hostel_id INTEGER REFERENCES messes(mess_id) ON DELETE SET NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    failed_login_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_login_count >= 0),
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ
);

CREATE TABLE sessions (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(20) NOT NULL REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE,
    -- sha-256 of the token, the token itself is never stored
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ,
    CHECK (expires_at > created_at)
);

CREATE INDEX sessions_username_idx ON sessions (username);
CREATE INDEX sessions_expires_idx ON sessions (expires_at);

-- ---------- preferences: per-meal targets, one row per student ----------

CREATE TABLE user_preferences (
    username VARCHAR(20) PRIMARY KEY REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE,

    breakfast_calories_kcal NUMERIC(6,0) CHECK (breakfast_calories_kcal BETWEEN 0 AND 2000),
    lunch_calories_kcal     NUMERIC(6,0) CHECK (lunch_calories_kcal BETWEEN 0 AND 2000),
    snacks_calories_kcal    NUMERIC(6,0) CHECK (snacks_calories_kcal BETWEEN 0 AND 2000),
    dinner_calories_kcal    NUMERIC(6,0) CHECK (dinner_calories_kcal BETWEEN 0 AND 2000),

    breakfast_protein_g NUMERIC(6,1) CHECK (breakfast_protein_g BETWEEN 0 AND 300),
    lunch_protein_g     NUMERIC(6,1) CHECK (lunch_protein_g BETWEEN 0 AND 300),
    snacks_protein_g    NUMERIC(6,1) CHECK (snacks_protein_g BETWEEN 0 AND 300),
    dinner_protein_g    NUMERIC(6,1) CHECK (dinner_protein_g BETWEEN 0 AND 300),

    breakfast_carbs_g NUMERIC(6,1) CHECK (breakfast_carbs_g BETWEEN 0 AND 300),
    lunch_carbs_g     NUMERIC(6,1) CHECK (lunch_carbs_g BETWEEN 0 AND 300),
    snacks_carbs_g    NUMERIC(6,1) CHECK (snacks_carbs_g BETWEEN 0 AND 300),
    dinner_carbs_g    NUMERIC(6,1) CHECK (dinner_carbs_g BETWEEN 0 AND 300),

    breakfast_fibre_g NUMERIC(6,1) CHECK (breakfast_fibre_g BETWEEN 0 AND 100),
    lunch_fibre_g     NUMERIC(6,1) CHECK (lunch_fibre_g BETWEEN 0 AND 100),
    snacks_fibre_g    NUMERIC(6,1) CHECK (snacks_fibre_g BETWEEN 0 AND 100),
    dinner_fibre_g    NUMERIC(6,1) CHECK (dinner_fibre_g BETWEEN 0 AND 100),

    breakfast_sugar_g NUMERIC(6,1) CHECK (breakfast_sugar_g BETWEEN 0 AND 300),
    lunch_sugar_g     NUMERIC(6,1) CHECK (lunch_sugar_g BETWEEN 0 AND 300),
    snacks_sugar_g    NUMERIC(6,1) CHECK (snacks_sugar_g BETWEEN 0 AND 300),
    dinner_sugar_g    NUMERIC(6,1) CHECK (dinner_sugar_g BETWEEN 0 AND 300),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- meal logs ----------
-- one log per student, per day, per hostel, per meal (saving again replaces the items)

CREATE TABLE meal_logs (
    log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(20) NOT NULL REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE,
    log_date DATE NOT NULL,
    mess_id INTEGER NOT NULL REFERENCES messes(mess_id),
    meal_type VARCHAR(20) NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'snacks', 'dinner')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (username, log_date, mess_id, meal_type)
);

-- dish name and nutrition are copied in at save time, so later corrections do not change old logs
-- no link to foods, so a menu reload can never delete a student's history
CREATE TABLE meal_log_items (
    item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    log_id BIGINT NOT NULL REFERENCES meal_logs(log_id) ON DELETE CASCADE,
    food_name VARCHAR(150) NOT NULL,
    grams NUMERIC(7,1) NOT NULL CHECK (grams > 0),
    calories_kcal NUMERIC(8,2) CHECK (calories_kcal >= 0),
    protein_g NUMERIC(8,2) CHECK (protein_g >= 0),
    carbs_g NUMERIC(8,2) CHECK (carbs_g >= 0),
    fat_g NUMERIC(8,2) CHECK (fat_g >= 0),
    fiber_g NUMERIC(8,2) CHECK (fiber_g >= 0),
    sugar_g NUMERIC(8,2) CHECK (sugar_g >= 0),
    UNIQUE (log_id, food_name)
);

CREATE INDEX meal_logs_user_date_idx ON meal_logs (username, log_date);

-- ---------- dashboard view ----------

CREATE OR REPLACE VIEW menu_details AS
SELECT me.mess_name, m.menu_date, m.meal_type,
       f.food_name, fc.category_name,
       COALESCE(mi.serving_weight_g, f.default_serving_g) AS serving_g,
       COALESCE(mi.serving_description, f.default_serving_desc) AS serving_desc,
       n.calories_kcal AS kcal_per_100g,
       ROUND(n.calories_kcal * COALESCE(mi.serving_weight_g, f.default_serving_g) / n.basis_amount, 0) AS kcal_per_serving,
       ROUND(n.protein_g * COALESCE(mi.serving_weight_g, f.default_serving_g) / n.basis_amount, 1) AS protein_per_serving_g,
       n.confidence, m.scraped_at
FROM menus m
JOIN messes me USING (mess_id)
JOIN menu_items mi USING (menu_id)
JOIN foods f USING (food_id)
LEFT JOIN food_categories fc USING (category_id)
LEFT JOIN nutrition n USING (food_id);
