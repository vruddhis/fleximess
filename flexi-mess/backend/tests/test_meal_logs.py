from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Food, Nutrition, Mess, MealLog, MealLogItem
from tests.conftest import headers, new_username

DAY = date(2026, 11, 20)


@pytest.fixture
def foods_with_nutrition(db_session):
    rows = db_session.scalars(select(Food).join(Nutrition).where(Nutrition.basis_unit == "g",
                                                                 Nutrition.calories_kcal.is_not(None)).limit(2)).all()
    assert len(rows) == 2, "need two foods with gram-based nutrition"
    return rows


@pytest.fixture
def mess_id(db_session):
    return db_session.scalars(select(Mess.mess_id).limit(1)).first()


def expected(food, grams):
    n = food.nutrition
    return float((n.calories_kcal * Decimal(str(grams)) / n.basis_amount).quantize(Decimal("0.01")))


def log_payload(mess_id, items, meal_type="lunch", log_date=DAY):
    return {"mess_id": mess_id, "log_date": log_date.isoformat(), "meal_type": meal_type, "items": items}


def test_create_log_writes_header_and_items(client, auth, db_session, foods_with_nutrition, mess_id):
    f1, f2 = foods_with_nutrition
    r = client.post("/api/meal-logs", headers=headers(auth), json=log_payload(mess_id, [
        {"food_id": f1.food_id, "grams": 150}, {"food_name": f2.food_name.upper(), "grams": 80.04}]))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["created"] is True and body["meal_type"] == "lunch" and body["log_date"] == DAY.isoformat()
    items = {i["food_name"]: i for i in body["items"]}
    assert set(items) == {f1.food_name, f2.food_name}          # name matched case-insensitively to canonical name
    assert items[f1.food_name]["nutrition"]["calories_kcal"] == expected(f1, 150)
    assert items[f2.food_name]["grams"] == 80.0                 # numeric(7,1)
    assert body["totals"]["calories_kcal"] == round(expected(f1, 150) + expected(f2, 80.0), 2)

    header = db_session.get(MealLog, body["log_id"])
    assert header.username == auth["_username"] and header.mess_id == mess_id
    assert len(db_session.scalars(select(MealLogItem).where(MealLogItem.log_id == header.log_id)).all()) == 2


def test_second_post_for_same_meal_merges_into_existing_log(client, auth, foods_with_nutrition, mess_id):
    f1, f2 = foods_with_nutrition
    h = headers(auth)
    first = client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": f1.food_id, "grams": 100}])).json()
    r = client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [
        {"food_id": f1.food_id, "grams": 200}, {"food_id": f2.food_id, "grams": 50}]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] is False and body["log_id"] == first["log_id"]
    grams = {i["food_name"]: i["grams"] for i in body["items"]}
    assert grams == {f1.food_name: 200.0, f2.food_name: 50.0}  # existing food's grams replaced, not duplicated

    other_meal = client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": f1.food_id, "grams": 10}], meal_type="dinner"))
    assert other_meal.status_code == 201 and other_meal.json()["log_id"] != first["log_id"]


def test_unknown_food_name_is_stored_without_nutrition(client, auth, mess_id):
    r = client.post("/api/meal-logs", headers=headers(auth), json=log_payload(mess_id, [{"food_name": "Homemade laddoo zz", "grams": 40}]))
    assert r.status_code == 201, r.text
    item = r.json()["items"][0]
    assert item["food_name"] == "Homemade laddoo zz"
    assert all(v is None for v in item["nutrition"].values())
    assert all(v is None for v in r.json()["totals"].values())


def test_meal_log_validation(client, auth, foods_with_nutrition, mess_id):
    f1, _ = foods_with_nutrition
    h = headers(auth)
    ok_item = {"food_id": f1.food_id, "grams": 100}
    assert client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [ok_item], meal_type="brunch")).status_code == 422
    assert client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [])).status_code == 422
    assert client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": f1.food_id, "grams": 0}])).status_code == 422
    assert client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": f1.food_id, "grams": 0.04}])).status_code == 422
    assert client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"grams": 10}])).status_code == 422
    assert client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [ok_item, {"food_name": f1.food_name, "grams": 5}])).status_code == 400
    assert client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": 999999999, "grams": 10}])).status_code == 404
    assert client.post("/api/meal-logs", headers=h, json=log_payload(999999, [ok_item])).status_code == 404


def test_history_and_summary(client, auth, foods_with_nutrition, mess_id):
    f1, f2 = foods_with_nutrition
    h = headers(auth)
    client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": f1.food_id, "grams": 100}], meal_type="breakfast"))
    client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": f2.food_id, "grams": 100}], meal_type="lunch"))
    client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": f2.food_id, "grams": 100}], log_date=date(2026, 11, 1)))

    all_logs = client.get("/api/meal-logs", headers=h).json()
    assert len(all_logs) == 3 and all_logs[0]["log_date"] >= all_logs[-1]["log_date"]
    one_day = client.get("/api/meal-logs", headers=h, params={"start_date": DAY.isoformat(), "end_date": DAY.isoformat()}).json()
    assert {l["meal_type"] for l in one_day} == {"breakfast", "lunch"}

    s = client.get("/api/meal-logs/summary", headers=h, params={"summary_date": DAY.isoformat()}).json()
    assert s["meal_count"] == 2
    assert s["totals"]["calories_kcal"] == round(expected(f1, 100) + expected(f2, 100), 2)


def test_delete_item_and_log(client, auth, db_session, foods_with_nutrition, mess_id):
    f1, f2 = foods_with_nutrition
    h = headers(auth)
    log = client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [
        {"food_id": f1.food_id, "grams": 100}, {"food_id": f2.food_id, "grams": 100}])).json()
    first, second = log["items"]

    r = client.delete(f"/api/meal-logs/{log['log_id']}/items/{first['item_id']}", headers=h)
    assert r.status_code == 200 and r.json()["log_deleted"] is False
    assert len(client.get(f"/api/meal-logs/{log['log_id']}", headers=h).json()["items"]) == 1

    r = client.delete(f"/api/meal-logs/{log['log_id']}/items/{second['item_id']}", headers=h)
    assert r.json()["log_deleted"] is True                     # empty header removed
    assert client.get(f"/api/meal-logs/{log['log_id']}", headers=h).status_code == 404

    log2 = client.post("/api/meal-logs", headers=h, json=log_payload(mess_id, [{"food_id": f1.food_id, "grams": 100}])).json()
    assert client.delete(f"/api/meal-logs/{log2['log_id']}", headers=h).status_code == 200
    db_session.expire_all()
    assert db_session.get(MealLog, log2["log_id"]) is None
    assert not db_session.scalars(select(MealLogItem).where(MealLogItem.log_id == log2["log_id"])).all()  # cascade


def test_users_cannot_see_each_others_logs(client, auth, foods_with_nutrition, mess_id):
    f1, _ = foods_with_nutrition
    log = client.post("/api/meal-logs", headers=headers(auth), json=log_payload(mess_id, [{"food_id": f1.food_id, "grams": 100}])).json()
    other = client.post("/api/auth/signup", json={"name": "Other", "username": new_username(), "password": "password123"}).json()
    oh = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get(f"/api/meal-logs/{log['log_id']}", headers=oh).status_code == 404
    assert client.delete(f"/api/meal-logs/{log['log_id']}", headers=oh).status_code == 404
    assert client.get("/api/meal-logs", headers=oh).json() == []
