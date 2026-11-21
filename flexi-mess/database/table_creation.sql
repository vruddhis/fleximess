
CREATE TABLE messes (
    mess_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mess_name VARCHAR(100) NOT NULL
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
    food_name VARCHAR(150) NOT NULL,
    category_id INTEGER REFERENCES food_categories(category_id),
    description TEXT
);

CREATE TABLE menu_items (
    menu_id BIGINT NOT NULL
        REFERENCES menus(menu_id) ON DELETE CASCADE,
    food_id BIGINT NOT NULL REFERENCES foods(food_id),
    serving_weight_g NUMERIC(8,2) CHECK (serving_weight_g > 0),
    serving_description VARCHAR(100),
    PRIMARY KEY (menu_id, food_id)
);

CREATE TABLE nutrition (
    nutrition_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    food_id BIGINT NOT NULL UNIQUE REFERENCES foods(food_id),
    basis_amount NUMERIC(8,2) NOT NULL DEFAULT 100
        CHECK (basis_amount > 0),
    basis_unit VARCHAR(10) NOT NULL DEFAULT 'g',
    calories_kcal NUMERIC(8,2) CHECK (calories_kcal >= 0),
    protein_g NUMERIC(8,2) CHECK (protein_g >= 0),
    carbs_g NUMERIC(8,2) CHECK (carbs_g >= 0),
    fat_g NUMERIC(8,2) CHECK (fat_g >= 0),
    fiber_g NUMERIC(8,2) CHECK (fiber_g >= 0),
    sugar_g NUMERIC(8,2) CHECK (sugar_g >= 0),
    source TEXT,
    confidence VARCHAR(10)
        CHECK (confidence IN ('low', 'medium', 'high'))
);


