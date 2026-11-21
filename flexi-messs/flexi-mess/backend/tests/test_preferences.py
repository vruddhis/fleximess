from decimal import Decimal

from app.models import Preference
from tests.conftest import headers

MEALS = ["breakfast", "lunch", "snacks", "dinner"]
NUTRIENTS = ["calories_kcal", "protein_g", "carbs_g", "fibre_g", "sugar_g"]


def test_new_user_has_empty_preferences(client, auth):
    r = client.get("/api/preferences", headers=headers(auth))
    assert r.status_code == 200
    body = r.json()
    for meal in MEALS:
        assert body[meal] == {n: None for n in NUTRIENTS}


def test_save_and_read_back_per_meal_targets(client, auth, db_session):
    payload = {
        "breakfast": {"calories_kcal": 450, "protein_g": 20, "carbs_g": 55.5, "fibre_g": 8, "sugar_g": 10},
        "lunch": {"calories_kcal": 700, "protein_g": 35.25},
        "dinner": {"fibre_g": 12.04},
    }
    r = client.put("/api/preferences", json=payload, headers=headers(auth))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["breakfast"] == {"calories_kcal": 450, "protein_g": 20.0, "carbs_g": 55.5, "fibre_g": 8.0, "sugar_g": 10.0}
    assert body["lunch"]["protein_g"] == 35.3          # numeric(6,1): rounded half-up
    assert body["lunch"]["carbs_g"] is None
    assert body["dinner"]["fibre_g"] == 12.0
    assert body["snacks"] == {n: None for n in NUTRIENTS}
    assert body["updated_at"]

    # stored in the real Supabase columns
    p = db_session.get(Preference, auth["_username"])
    db_session.refresh(p)
    assert p.breakfast_calories_kcal == Decimal("450")
    assert p.lunch_protein_g == Decimal("35.3")
    assert p.dinner_fibre_g == Decimal("12.0")

    assert client.get("/api/preferences", headers=headers(auth)).json()["breakfast"]["calories_kcal"] == 450


def test_put_is_full_replacement(client, auth):
    h = headers(auth)
    client.put("/api/preferences", json={"lunch": {"calories_kcal": 600, "protein_g": 30}}, headers=h)
    r = client.put("/api/preferences", json={"lunch": {"calories_kcal": 650}}, headers=h)
    assert r.json()["lunch"] == {"calories_kcal": 650, "protein_g": None, "carbs_g": None, "fibre_g": None, "sugar_g": None}


def test_bounds_match_database_check_constraints(client, auth):
    h = headers(auth)
    for bad in [{"breakfast": {"calories_kcal": 2001}}, {"lunch": {"protein_g": 300.1}}, {"dinner": {"fibre_g": 101}},
                {"snacks": {"sugar_g": -1}}, {"lunch": {"carbs_g": 301}}, {"breakfast": {"calories_kcal": 450.5}}]:
        assert client.put("/api/preferences", json=bad, headers=h).status_code == 422, bad
    edge = {"breakfast": {"calories_kcal": 2000, "protein_g": 300, "carbs_g": 0, "fibre_g": 100, "sugar_g": 300}}
    assert client.put("/api/preferences", json=edge, headers=h).status_code == 200


def test_put_creates_row_if_missing(client, auth, db_session):
    db_session.delete(db_session.get(Preference, auth["_username"]))
    db_session.flush()
    r = client.put("/api/preferences", json={"snacks": {"calories_kcal": 250}}, headers=headers(auth))
    assert r.status_code == 200 and r.json()["snacks"]["calories_kcal"] == 250
