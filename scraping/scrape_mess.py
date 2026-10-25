"""
Scrape InstiApp mess menus and load them into Postgres.

Setup:
    pip install requests psycopg2-binary
    export DATABASE_URL="postgresql://user:pass@localhost:5432/flexi_mess"
    python scrape_mess.py            # normal run
    python scrape_mess.py --dry-run  # just print what would be inserted

Run once/twice a day (cron). Safe to re-run: everything is upserted.
"""
import os
import re
import sys
import logging
from datetime import date, timedelta

import requests
import psycopg2

API_URL = "https://gymkhana.iitb.ac.in/instiapp/api/mess"
MEAL_TYPES = ["breakfast", "lunch", "snacks", "dinner"]

# Assumption: day 1 = Monday ... day 7 = Sunday. VERIFY against a real menu!
DAY1_IS_MONDAY = True

# Values that are not dishes
SKIP_VALUES = {"", "pest control", "mess closed", "closed", "na", "n/a", "-", "nil"}
# Placeholder / stale text seen in the real data
SKIP_PATTERN = re.compile(
    r"ask your mess|update menu|special lunch|independence day|pest control|tea party"
)
MAX_WORDS_PER_DISH = 7  # longer chunks = space-separated list we can't split safely


def is_unparseable(text: str) -> bool:
    """Detect meal strings we can't split reliably (logged and skipped for now).
    - very long chunks that are probably several dishes run together
    (Hostels 5/18 use newlines and Hostel 11 uses 'odd week:/even week:' labels;
    both are handled by split_dishes.)
    """
    t = (text or "").lower()
    for part in re.split(r"[,\n;](?![^()]*\))", t):
        words = re.sub(r"\([^)]*\)", "", part).split()
        if len(words) > MAX_WORDS_PER_DISH:
            return True
    return False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scraper")


def normalize(name: str) -> str:
    """Lowercase, collapse whitespace, tidy slashes. Used as the foods.food_name key."""
    s = name.strip().lower()
    s = re.sub(r"\s*/\s*", "/", s)      # "tea /coffee" -> "tea/coffee"
    s = re.sub(r"\s+", " ", s)
    return s.strip(" ./\"'")


WEEK_TAG = re.compile(r"^\s*(odd|even)\s+week\s*:\s*", re.I)

# Spelling variants -> one canonical dish name (keys/values are already-normalized, lowercase).
# Starter list built from the first real scrape; extend it as new variants show up.
ALIASES = {
    "sprouts matki": "matki sprouts",
    "chhole pindi": "chole pindi", "pindi chole": "chole pindi", "chole pendi": "chole pindi",
    "choole bhature": "chole bhature",
    "chicken hyderabadi dum biryani": "hyderabadi chicken biryani",
    "chicken hyderabadi": "hyderabadi chicken biryani",
    "chicken dum biryani": "chicken biryani",
    "bhindi do pyaaza": "bhindi do pyaza", "bhindi do pyaja": "bhindi do pyaza",
    "fried maggie": "fried maggi",
    "green peas pulav": "green peas pulao",
    "mix sprout": "mix sprouts",
    "channa dal": "chana dal",
    "soyabean chilly": "soyabean chili",
    "baigan bharta": "baingan bharta", "baigan bharata": "baingan bharta",
    "kadhai paneer": "kadai paneer",
    "kadi pakoda": "kadhi pakoda",
    "sahi paneer": "shahi paneer", "shai paneer": "shahi paneer",
    "dal makhni": "dal makhani", "dal mukhni": "dal makhani",
    "fruit custurd": "fruit custard",
    "vada pao": "vada pav",
    "gawar sbji": "gawar sabji",
    "tendali dry": "tendli dry",
    "egg bhiurji": "egg bhurji", "egg burji": "egg bhurji",
    "omlet": "omelette", "omlette": "omelette", "omlete": "omelette", "omelet": "omelette",
    "steam rice": "plain rice", "rice": "plain rice",
    "museli": "muesli", "meusli": "muesli",
    "chatny": "chutney", "chutey": "chutney", "chuteny": "chutney",
    "sambar": "sambhar",
    "mix pickle": "pickle",
    "milk shake": "milkshake",
    "icecream": "ice cream",
    "sev tamatar gravy": "sev tamatar", "sev-tamatar": "sev tamatar",
    # corn: all the same item for our purposes
    "corn salad": "sweet corn", "sweet corn salad": "sweet corn",
    "boiled corn salad": "sweet corn", "boiled corn": "sweet corn",
    "boiled sweet corn": "sweet corn",
    # toor / arhar dal tadka
    "toor dal": "toor dal tadka", "dal tadka": "toor dal tadka",
    "arhar dal tadka": "toor dal tadka", "arhar dal tadaka": "toor dal tadka",
    # other spelling / wording variants
    "green chiili": "green chilli", "corn flakes": "cornflakes", "rassam": "rasam", "fruits": "fruit",
    "veg raita": "raita", "butter chicken in lunch": "butter chicken",
    "bhurji": "egg bhurji", "sprouts moong salad": "moong sprouts",
    "veg tawa dry": "veg tawa", "dahi papdi chat": "papdi chat",
    "mix veg dry": "mix veg", "veg hakka noodles": "hakka noodles",
    "chana dal fry": "chana dal",
    # NOTE: milkshakes and sharbats are deliberately NOT merged:
    # milkshake / oreo milkshake / strawberry shake / strawberry sharbat stay separate.
    # bread / butter / jam
    "p.butter": "peanut butter",
}


# One written item that is really several foods. Jam is always its own food (so it can sit
# in a different category from bread/butter).
MULTI_ALIASES = {
    "bbj": ["bread butter", "jam"],
    "bread butter jam": ["bread butter", "jam"],
    "bread butter and mix jam": ["bread butter", "jam"],
    "butter and mix jam": ["butter", "jam"],
    "peanut butter and mix jam": ["peanut butter", "jam"],
    "p.butter and mix jam": ["peanut butter", "jam"],
    "papad and pickle": ["papad", "pickle"],
    "mix jam": ["jam"], "mango jam": ["jam"], "and mango jam": ["jam"],
}


def _clean_part(part: str):
    """One comma/newline-separated chunk -> ([dish names], note).

    - text in (...) is removed from the name and returned as the note
      (e.g. 'pista barfi (2 pieces)' -> 'pista barfi', note '2 pieces')
    - 'tea/coffee' or 'bread' glued to the end of another dish is split off
      ('p.butter and mix jam tea/coffee' -> 'p.butter and mix jam', 'tea', 'coffee')
    - '+' and '/' mean several dishes ('sambhar/chutney', 'masala dosa + sambhar')
    """
    notes = [n.strip().lower() for n in re.findall(r"\(([^)]*)\)", part) if n.strip()]
    text = re.sub(r"\([^)]*\)", " ", part).lower().replace("&", " and ")
    text = re.sub(r"/?\s*with\s*/?\s*(?:and\s+)?without\s+(?:ghee|butter)", " ", text)
    text = re.sub(r"\bb\.?\s*b\.?\s*j\b", "bbj", text)              # b.b.j / b. b. j / b b j
    text = re.sub(r"\btea\s+and\s+coffee\b", "tea/coffee", text)
    text = re.sub(r"(\S)\s+(tea\s*/\s*coffee)", r"\1/\2", text)      # '... jam tea/coffee'
    if not text.strip().endswith("garlic bread"):
        text = re.sub(r"(\S)\s+(bread)\s*$", r"\1/\2", text)          # 'vada pav bread'
    names = []
    for piece in re.split(r"[/+]", text):
        n = normalize(piece)
        if n in MULTI_ALIASES:
            names.extend(MULTI_ALIASES[n])
        else:
            names.append(ALIASES.get(n, n))
    return names, "; ".join(notes)


def split_dishes(text: str):
    """Return [(dish, description)] in menu order, junk removed, duplicates merged.

    description goes into menu_items.serving_description: bracket notes ('2 pieces',
    'extra') and, for Hostel 11, 'odd week' / 'even week' (we keep ALL dishes for the day
    but remember the label so it can be filtered later). A dish listed under both
    labels, or with differing notes, gets None.
    """
    found = {}  # name -> description (dict keeps insertion order)
    for segment in (text or "").split(";"):
        tag = None
        m = WEEK_TAG.match(segment)
        if m:
            tag = m.group(1).lower() + " week"
            segment = segment[m.end():]
        # split on commas / newlines, but not inside (...)
        for part in re.split(r"[,\n](?![^()]*\))", segment):
            names, note = _clean_part(part)
            desc = "; ".join(x for x in (tag, note) if x)[:100] or None
            for n in names:
                if not n or n in SKIP_VALUES or SKIP_PATTERN.search(n):
                    continue
                if len(n) > 150:  # would overflow foods.food_name VARCHAR(150)
                    log.warning("dish name too long, skipped: %.60s...", n)
                    continue
                if n in found and found[n] != desc:
                    found[n] = None
                else:
                    found.setdefault(n, desc)
    return list(found.items())


def date_for_day(day: int, today: date) -> date:
    """Project API weekday number onto the current calendar week."""
    monday = today - timedelta(days=today.weekday())
    offset = (day - 1) if DAY1_IS_MONDAY else (day % 7)  # else: 1=Sunday-style
    d = monday + timedelta(days=offset)
    if not DAY1_IS_MONDAY and day == 1:
        d = monday - timedelta(days=1)
    return d


def fetch():
    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()
    return r.json()


def load(conn, hostels, today, dry_run=False):
    cur = conn.cursor() if conn else None
    stats = {"menus": 0, "items": 0, "skipped_past": 0, "empty": 0}

    for h in hostels:
        mess_name = h["name"]  # e.g. "Hostel 10"
        if not dry_run:
            cur.execute(
                """INSERT INTO messes (mess_name) VALUES (%s)
                   ON CONFLICT (mess_name) DO UPDATE SET mess_name = EXCLUDED.mess_name
                   RETURNING mess_id""",
                (mess_name,),
            )
            mess_id = cur.fetchone()[0]

        for entry in h.get("mess", []):
            menu_date = date_for_day(entry["day"], today)
            if menu_date < today:
                # keep history intact: never rewrite dates that already passed
                stats["skipped_past"] += 1
                continue

            for meal in MEAL_TYPES:
                raw = entry.get(meal, "")
                if is_unparseable(raw):
                    log.warning("UNPARSED %s %s %s: %.60s...", mess_name, menu_date, meal, raw)
                    stats["unparsed"] = stats.get("unparsed", 0) + 1
                    continue
                dishes = split_dishes(raw)
                if not dishes:
                    stats["empty"] += 1
                    continue

                if dry_run:
                    print(mess_name, menu_date, meal, [d if not t else f"{d} [{t}]" for d, t in dishes])
                    continue

                cur.execute(
                    """INSERT INTO menus (mess_id, menu_date, meal_type)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (mess_id, menu_date, meal_type)
                       DO UPDATE SET scraped_at = now()
                       RETURNING menu_id""",
                    (mess_id, menu_date, meal),
                )
                menu_id = cur.fetchone()[0]
                stats["menus"] += 1

                # replace items so menu changes are reflected
                cur.execute("DELETE FROM menu_items WHERE menu_id = %s", (menu_id,))
                for dish, tag in dishes:
                    cur.execute(
                        """INSERT INTO foods (food_name) VALUES (%s)
                           ON CONFLICT (food_name) DO UPDATE SET food_name = EXCLUDED.food_name
                           RETURNING food_id""",
                        (dish,),
                    )
                    food_id = cur.fetchone()[0]
                    cur.execute(
                        """INSERT INTO menu_items (menu_id, food_id, serving_description)
                           VALUES (%s, %s, %s)
                           ON CONFLICT (menu_id, food_id) DO NOTHING""",
                        (menu_id, food_id, tag),
                    )
                    stats["items"] += 1

    if not dry_run:
        conn.commit()
    log.info("done: %s", stats)


def main():
    dry_run = "--dry-run" in sys.argv
    hostels = fetch()
    log.info("fetched %d hostels", len(hostels))
    today = date.today()
    if dry_run:
        load(None, hostels, today, dry_run=True)
        return
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        load(conn, hostels, today)
    except Exception:
        conn.rollback()
        log.exception("load failed, rolled back")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
