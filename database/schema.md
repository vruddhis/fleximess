# Tables design and assumptions

1.messes
Purpose: Stores the messes.

Columns:
mess_id: Unique identifier for each mess; primary key.
mess_name: Name of the mess; required like "H10 mess".

Assumptions and decisions:
1.mess_id is used instead of the mess name to identify the mess.
2.i seperatly created this because if i want to change mess_name and stuff.

2.menus
Purpose: Represents a particular mess's menu for a specific date and meal type.

Columns:
menu_id: Unique identifier for a menu record; primary key.
mess_id: References the mess providing the menu; foreign key.
menu_date: Date for which the menu is intended.
meal_type: One of breakfast, lunch, snacks, or dinner.
scraped_at: Timestamp indicating when the record was inserted or last refreshed by the scraping process.

Assumptions:
1.Each mess has at most one menu for a given date and meal type means the  combination (mess_id, menu_date, meal_type) is unique.
2.scraped_at is distinct from menu_date: it records data-collection time, not the date of the meal.
3.The scraper must explicitly update scraped_at when refreshing an existing record.


3.food_categories
Purpose: to store reusable categories for classifying dishes.

Columns:
category_id: Unique category identifier; primary key.
category_name: Category name; required and unique.

Assumptions and decisions:
1.Each category is stored once and can be referenced by multiple foods.
2.A diah has at most one category.

4.foods
Purpose: to store food or dish records.

Columns:
food_id: Unique identifier for a food; primary key.
food_name: Name of the food; required.
category_id: Optional reference to a food category; foreign key.
description: Optional description.

Assumptions and decisions:
1.The same food can appear in multiple menus without creating a new food record every time.
2.The scraping pipeline will eventually need to map source dish names to food records.

# Have to handle spelling differences, aliases, and recipe variants.

5.menu_items
Purpose: Connects menus to their food items and optionally stores serving-size information.

Columns:
menu_id: References a menu; part of the primary key and a foreign key.
food_id: References a food; part of the primary key and a foreign key.
serving_weight_g: Optional serving weight in grams.i think it is important because one dish alone cant be served a lot. 
serving_description: Optional text describing the serving.

Assumptions and decisions:
1.A menu can contain many foods, and a food can appear in many menus.
2.The composite primary key (menu_id, food_id) identifies each menu-food association.
3.The same food cannot appear more than once in a menu.
4.Serving weight is optional because the source may not provide it.
5.A provided serving weight must be positive.
6.Deleting a menu automatically removes its associated menu_items rows.


6.nutrition
Purpose: to store nutritional estimates for food items.

Columns:
nutrition_id: Unique nutrition-record identifier; primary key.
food_id: References a food; foreign key and unique.
basis_amount: Amount against which nutrient values are measured; defaults to 100.
basis_unit: Measurement unit; i am thinking of grams (g).
calories_kcal: Energy estimate.
protein_g: Protein estimate.
carbs_g: Carbohydrate estimate.
fat_g: Fat estimate.
fiber_g: Fiber estimate.
sugar_g: Sugar estimate.
source: Source of the nutritional data.

Assumptions and decisions:

Nutrition is stored separately from food identity.

The initial design allows at most one nutrition record per food.

Nutrient values may be unknown; missing values are not treated as zero.

Values can be scaled to a serving only when the measurement basis and serving units are compatible.

Source and confidence fields help document the reliability of estimates.

Pending confirmation: Whether one nutrition profile per food is sufficient, given that prepared dishes can vary by recipe and cooking method.

# Relationship summary

One mess can have many menus.

One menu can contain many menu items.

One food can appear in many menu items.

One food category can classify many foods.

One food can have zero or one nutrition record.

The menu_items table implements the many-to-many relationship between menus and foods.

# Constraints and validation

Primary keys uniquely identify records.

Foreign keys ensure that references point to existing records.

Unique constraints prevent duplicate menu headers, category names, and nutrition records for the same food.

Check constraints restrict meal types, prevent invalid negative nutrient values, require positive measurement amounts, and validate confidence labels.

Missing serving or nutrient data may be stored as NULL where the schema permits it.