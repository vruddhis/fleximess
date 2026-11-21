from sqlalchemy import select, func

from app.models import User, Preference, Mess, Menu, MenuItem
from tests.conftest import new_username, headers


def test_signup_login_me(client, db_session):
    username = new_username()
    r = client.post("/api/auth/signup", json={"name": "  Asha  ", "username": username.upper(), "password": "password123"})
    assert r.status_code == 201, r.text
    assert r.json()["user"] == {"username": username, "name": "Asha"}

    user = db_session.get(User, username)
    assert user.role == "student" and user.is_active and user.failed_login_count == 0
    assert db_session.get(Preference, username) is not None  # empty preferences row created

    r = client.post("/api/auth/login", json={"username": username, "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    db_session.refresh(user)
    assert user.last_login_at is not None

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["user"]["username"] == username


def test_login_rejects_bad_password_and_unknown_user(client, auth):
    assert client.post("/api/auth/login", json={"username": auth["_username"], "password": "wrong-pass"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "nobody_" + auth["_username"][-6:], "password": "x"}).status_code == 401


def test_signup_validation(client, auth):
    assert client.post("/api/auth/signup", json={"name": "X", "username": auth["_username"], "password": "password123"}).status_code == 409
    assert client.post("/api/auth/signup", json={"name": "X", "username": "admin", "password": "password123"}).status_code == 400
    assert client.post("/api/auth/signup", json={"name": "   ", "username": new_username(), "password": "password123"}).status_code == 422
    assert client.post("/api/auth/signup", json={"name": "X", "username": new_username(), "password": "short"}).status_code == 422


def test_protected_routes_require_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/preferences").status_code == 401
    assert client.get("/api/meal-logs").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401


def test_messes_lists_all(client, db_session):
    r = client.get("/api/messes")
    assert r.status_code == 200
    assert len(r.json()) == db_session.scalar(select(func.count()).select_from(Mess))


def test_menus_for_a_date_with_data(client, db_session):
    menu = db_session.scalars(select(Menu).join(MenuItem).limit(1)).first()
    assert menu is not None, "Supabase has no menus to browse"
    r = client.get("/api/menus", params={"menu_date": menu.menu_date.isoformat(), "meal_type": menu.meal_type, "mess_id": menu.mess_id})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1 and data[0]["menu_id"] == menu.menu_id
    item = data[0]["items"][0]
    assert {"food_id", "name", "nutrition", "serving_weight_g", "default_serving_g"} <= item.keys()

    r = client.get("/api/menus", params={"menu_date": menu.menu_date.isoformat(), "q": item["name"][:4]})
    assert r.status_code == 200 and r.json()
    assert client.get("/api/menus", params={"meal_type": "brunch"}).status_code == 400


def test_foods_search(client):
    r = client.get("/api/foods", params={"limit": 5})
    assert r.status_code == 200 and 0 < len(r.json()) <= 5
    name = r.json()[0]["name"]
    r = client.get("/api/foods", params={"q": name})
    assert any(f["name"] == name for f in r.json())


def test_recommendations_take_goals_from_query(client, auth, db_session):
    menu = db_session.scalars(select(Menu).limit(1)).first()
    params = {"menu_date": menu.menu_date.isoformat(), "meal_type": menu.meal_type, "goals": ["high_protein", "low_sugar"]}
    r = client.get("/api/recommendations", params=params, headers=headers(auth))
    assert r.status_code == 200, r.text
    scores = [m["score"] for m in r.json()]
    assert scores == sorted(scores, reverse=True)
    bad = client.get("/api/recommendations", params={"goals": ["eat_everything"]}, headers=headers(auth))
    assert bad.status_code == 400


def test_favorites_are_disabled(client, auth):
    h = headers(auth)
    assert client.get("/api/favorites", headers=h).status_code == 501
    assert client.post("/api/favorites/1", headers=h).status_code == 501
    assert client.delete("/api/favorites/1", headers=h).status_code == 501
    assert client.get("/api/notifications", headers=h).status_code == 501
