"""
Load nutrition_seed.csv into the nutrition table.

    $env:DATABASE_URL = "postgresql://postgres:PASS@localhost:5432/flexi_mess"
    python load_nutrition.py

Matches rows to foods by exact food_name. Re-runnable (upserts on food_id).
Prints any CSV names that don't exist in foods yet (usually spelling differences).
"""
import csv
import os
import sys

import psycopg2

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "nutrition_seed.csv"

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
loaded, missing = 0, []

with open(CSV_PATH, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        cur.execute("SELECT food_id FROM foods WHERE food_name = %s", (r["food_name"],))
        row = cur.fetchone()
        if not row:
            missing.append(r["food_name"])
            continue
        cur.execute(
            """INSERT INTO nutrition
                 (food_id, basis_amount, basis_unit, calories_kcal, protein_g,
                  carbs_g, fat_g, fiber_g, sugar_g, source, confidence)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (food_id) DO UPDATE SET
                  basis_amount=EXCLUDED.basis_amount, basis_unit=EXCLUDED.basis_unit,
                  calories_kcal=EXCLUDED.calories_kcal, protein_g=EXCLUDED.protein_g,
                  carbs_g=EXCLUDED.carbs_g, fat_g=EXCLUDED.fat_g,
                  fiber_g=EXCLUDED.fiber_g, sugar_g=EXCLUDED.sugar_g,
                  source=EXCLUDED.source, confidence=EXCLUDED.confidence""",
            (row[0], r["basis_amount"], r["basis_unit"], r["calories_kcal"],
             r["protein_g"], r["carbs_g"], r["fat_g"], r["fiber_g"], r["sugar_g"],
             r["source"], r["confidence"]),
        )
        loaded += 1

conn.commit()
conn.close()
print(f"loaded {loaded} rows")
if missing:
    print("not found in foods (check spelling / run the scraper first):")
    for m in missing:
        print("  -", m)
