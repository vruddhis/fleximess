# FlexiMess – fresh backend implementation



## Stack
- FastAPI + SQLAlchemy 2
- PostgreSQL
- Argon2 password hashing (`pwdlib`)
- Signed JWT bearer tokens
- Existing InstiApp scraper and nutrition CSV, retained from the project scraping folder

## 1. PostgreSQL
Create the database once:

```sql
CREATE DATABASE flexi_mess;
```

Then run `sql/schema.sql` against `flexi_mess` (psql or pgAdmin). The API also creates missing tables at startup, but it does not modify an already-existing table; run the SQL file when upgrading an old database. The scraper depends on unique constraints for `messes.mess_name` and `foods.food_name`.

## 2. Environment (PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your PostgreSQL password and a random secret. Set the same database for scraper commands. For the API use `postgresql+psycopg://...`; scraper scripts accept `postgresql://...`.

## 3. Run API

```powershell
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000/  | Swagger: http://127.0.0.1:8000/docs

## 4. Populate menus

```powershell
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/flexi_mess"
python scrape_mess.py --dry-run
python scrape_mess.py
python load_nutrition.py nutrition_seed.csv
```

Run the scraper daily using Windows Task Scheduler / cron. It only loads current/future menu dates, matching the original project's assumption that InstiApp day 1 is Monday. Verify that assumption against the live InstiApp response before relying on dates. `--dry-run` previews parsed results without DB writes.

## 5. Frontend
Set `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_AUTH_MODE=api
```

Use the `frontend/src/api.js` and updated auth files supplied in this package. Restart Vite after changing `.env`.

## 6. Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---:|---|
| POST | `/api/auth/signup` | No | Create account + JWT |
| POST | `/api/auth/login` | No | Login + JWT |
| GET | `/api/auth/me` | Yes | Current user |
| POST | `/api/auth/logout` | Yes | Logout acknowledgement; client clears JWT |
| GET | `/api/messes` | No | Mess list |
| GET | `/api/foods?q=` | No | Search foods/nutrition |
| GET | `/api/menus?menu_date=YYYY-MM-DD&meal_type=lunch` | No | Menus by date/meal/mess/search |
| GET | `/api/recommendations?menu_date=YYYY-MM-DD&meal_type=lunch` | Yes | Rule-based ranked messes |
| GET/PUT | `/api/preferences` | Yes | Nutrition goals + calorie targets |
| GET | `/api/favorites` | Yes | Favourite dishes |
| POST/DELETE | `/api/favorites/{food_id}` | Yes | Add/remove favourite |
| GET | `/api/notifications?days=7` | Yes | Upcoming favourite menu matches |
| POST | `/api/meal-logs` | Yes | Save one meal containing multiple foods |
| GET | `/api/meal-logs` | Yes | Meal history |
| GET | `/api/meal-logs/summary?summary_date=YYYY-MM-DD` | Yes | Daily nutrition summary |
| DELETE | `/api/meal-logs/{log_id}` | Yes | Delete own log |

### Meal log body
```json
{
  "mess_id": 1,
  "meal_date": "2026-11-17",
  "meal_type": "lunch",
  "items": [{"food_id": 15, "quantity_g": 180}],
  "notes": "Lunch"
}
```

### Preference body
```json
{
  "goals": "high_protein",
  "priority_goals": ["high_protein", "high_fiber"],
  "breakfast_calories": 400,
  "lunch_calories": 600,
  "snacks_calories": 250,
  "dinner_calories": 500
}
```
Allowed goals: `high_protein`, `high_fiber`, `low_sugar`, `low_carbohydrate`, `low_calories`, `balanced`.

## Important limitations / checks
- JWT logout is client-side token removal; there is no server-side revocation list in this simple implementation. For production, add refresh-token rotation/revocation and HTTPS.
- Recommendations are transparent, rule-based comparisons of available menu nutrition, not dietetic advice. Portion size uses `serving_weight_g` when present, otherwise 100 g as a comparison assumption.
- Missing nutrition remains `null`; the API does not interpret unknown values as zero.
- Scraper source format and weekday mapping are upstream assumptions. Check live responses and the dry-run output after any InstiApp change.
- Push notifications are not implemented; `/api/notifications` supplies an in-app feed.
