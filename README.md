# FlexiMess Optimiser — FastAPI Backend

This backend is designed to work with the React/Vite frontend and the PostgreSQL tables in the  project.

## 1. What is included

- Student signup/login with Argon2 password hashing and JWT authentication
- Menu retrieval by date, meal, mess and food search
- Nutrition details per 100 g, and nutrition calculations for logged quantities
- Mess recommendations for high protein, high fibre, low calories or balanced goals
- Favourite dishes and a notification feed when favourites appear in upcoming menus
- Meal logging, daily nutrition summary, history and deletion
- Swagger API documentation at `/docs`

## 2. Requirements

Install:
- Python 3.10 or newer
- PostgreSQL 14 or newer
- The existing FlexiMess project files

## 3. Windows setup (PowerShell)

Open PowerShell in this `backend` folder.

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in the same terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Install Python packages:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Create PostgreSQL database

Open pgAdmin or SQL Shell (psql). Create a database named `flexi_mess`.

```sql
CREATE DATABASE flexi_mess;
```

If  starting with a completely empty database, the API creates all tables automatically when it starts.



## 5. Configure environment

Copy `.env.example` to `.env` in this backend folder. Edit the PostgreSQL username/password.

Example:
```env
DATABASE_URL=postgresql+psycopg://postgres:MyPassword@localhost:5432/flexi_mess
SECRET_KEY=put-a-long-random-secret-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_ORIGINS=http://localhost:5173
```

Do not commit `.env` to GitHub. Never use the example secret in a deployed application.

## 6. Start backend

From the backend folder, with the virtual environment activated:

```powershell
uvicorn app.main:app --reload
```

Open:
- API status: http://127.0.0.1:8000/
- Interactive API documentation: http://127.0.0.1:8000/docs

Stop the server with `Ctrl + C`.

## 7. Load the mess menus and nutrition

scraper is in the project's `scraping` folder. It uses the same PostgreSQL database. Set the same `DATABASE_URL` in the terminal and run it from that folder:

```powershell
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/flexi_mess"
python scrape_mess.py --dry-run
python scrape_mess.py
```

Then load nutrition seed data (run after the menu scraper has inserted foods):
```powershell
python load_nutrition.py
```

The scraper depends on the upstream InstiApp endpoint and its response format. Check its output and confirm the API returned menu data. Nutrition is only available for dishes matched in `nutrition_seed.csv`; missing nutrition is returned as `null`, not guessed.

## 8. API authentication

Signup/login return a JWT token. For protected APIs, send this header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

In Swagger, click **Authorize** and paste the token. Do not include the word `Bearer` if Swagger's bearer dialog adds it automatically.

## 9. Main endpoints

| Method | Endpoint | Login required? | Purpose |
|---|---|---:|---|
| POST | `/api/auth/signup` | No | Create student |
| POST | `/api/auth/login` | No | Login |
| GET | `/api/auth/me` | Yes | Current student |
| GET | `/api/messes` | No | List messes |
| GET | `/api/foods?q=rice` | No | Search dishes and nutrition |
| GET | `/api/menus?menu_date=2026-11-04&meal_type=lunch` | No | Menus |
| GET | `/api/recommendations?menu_date=2026-11-04&meal_type=lunch` | Yes | Ranked messes |
| GET/PUT | `/api/preferences` | Yes | Read/save goal |
| GET | `/api/favorites` | Yes | List favourites |
| POST | `/api/favorites/{food_id}` | Yes | Add favourite |
| DELETE | `/api/favorites/{food_id}` | Yes | Remove favourite |
| GET | `/api/notifications?days=7` | Yes | Upcoming favourite dishes |
| POST | `/api/meal-logs` | Yes | Log food in grams |
| GET | `/api/meal-logs` | Yes | Meal history |
| GET | `/api/meal-logs/summary?summary_date=2026-11-04` | Yes | Daily nutrition totals |
| DELETE | `/api/meal-logs/{log_id}` | Yes | Delete a log |

### Example request bodies

Signup:
```json
{"name":"Aprajita Singh","ldap_id":"aprajita","password":"your-password"}
```

Login:
```json
{"ldap_id":"aprajita","password":"your-password"}
```

Save preference:
```json
{"goal":"high_protein"}
```
Allowed goals: `high_protein`, `high_fiber`, `low_calories`, `balanced`.

Log a meal:
```json
{
  "mess_id": 1,
  "food_id": 10,
  "meal_date": "2026-11-04",
  "meal_type": "lunch",
  "quantity_g": 150,
  "notes": "Lunch"
}
```

## 10. Important frontend integration notes

The existing frontend currently uses `console.log` and hard-coded placeholder data in its login/dashboard pages. It will not call the backend until those handlers are connected to these endpoints.

For every protected request:
1. Read `access_token` from `localStorage`.
2. Add `Authorization: Bearer <token>` to the request headers.
3. On login/signup, save `access_token` and the returned `student` object.

Example frontend request:
```javascript
const API = "http://127.0.0.1:8000";

const response = await fetch(`${API}/api/menus?menu_date=2026-11-04&meal_type=lunch`);
const menus = await response.json();
```

Example protected request:
```javascript
const token = localStorage.getItem("access_token");
const response = await fetch(`${API}/api/favorites`, {
  headers: { Authorization: `Bearer ${token}` }
});
```

## 11. Recommendation and notification behaviour

- Recommendation scores are calculated from the available nutrition values of menu items. They are a simple ranking, not medical or dietetic advice.
- Menu-item nutrition totals use the item's `serving_weight_g` if available; otherwise the API uses 100 g as an explicitly assumed comparison portion.
- The notification endpoint provides an in-app feed of upcoming favourite-dish matches. Actual push/email notifications require a separate notification service and user permission.
- Nutrition values are only as accurate as the source and matching in the CSV. `source` and `confidence` are included in menu food responses.
