# puts typical serving sizes into foods.default_serving_g and default_serving_desc
# run the ALTER TABLE for those two columns first (they are in schema_full.sql)
# kept on foods and not menu_items because scrape_mess.py rebuilds menu_items every run
#   python load_servings.py   (reads serving_weights.csv)
import csv
import os
import sys

import psycopg2

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "serving_weights.csv"
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
updated, missing = 0, []

with open(CSV_PATH, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        cur.execute(
            "UPDATE foods SET default_serving_g = %s, default_serving_desc = %s WHERE food_name = %s",
            (r["default_serving_g"], r["default_serving_desc"], r["food_name"]),
        )
        if cur.rowcount:
            updated += 1
        else:
            missing.append(r["food_name"])

conn.commit()
conn.close()
print(f"updated {updated} foods")
if missing:
    print("not found in foods:", ", ".join(missing))
