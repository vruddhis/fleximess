# FlexiMess – Backend + Frontend integration

Use the `backend/` directory in this delivery as the new backend. The previous root-level backend files from the original repository are intentionally not included in this clean delivery.

## Start locally (Windows PowerShell)

1. Create PostgreSQL database `flexi_mess`.
2. Run `backend/sql/schema.sql` in that database.
3. In `backend/`, create/activate a virtual environment and install `requirements.txt`.
4. Copy `.env.example` to `.env`, set `DATABASE_URL` and `SECRET_KEY`.
5. Start the API with `uvicorn app.main:app --reload` from `backend/`.
6. In `frontend/`, copy `.env.example` to `.env`, run `npm install`, then `npm run dev`.
7. In a second terminal, set scraper `DATABASE_URL` to `postgresql://...` and run `python scrape_mess.py --dry-run`, then `python scrape_mess.py` from `backend/`. Run `python load_nutrition.py nutrition_seed.csv` afterward.

See `backend/README.md` for full setup, API routes, request bodies, and limitations.
