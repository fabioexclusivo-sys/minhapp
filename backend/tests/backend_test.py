"""Backend regression tests - The Law of Silence / NEON SYNDICATE (iteration 2).

Covers: auth (signup/login/me + backward-compat defaults), catalog, character create,
buy weapon/vehicle, hire crew, heist run + history, property buy/upgrade,
business buy/collect, bank deposit/withdraw, pvp targets/history, rankings.
"""
import os
import uuid

import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"

backend_env = dotenv_values("/app/backend/.env")
MONGO_URL = os.environ.get("MONGO_URL") or backend_env.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or backend_env.get("DB_NAME")

DEFAULT_KEYS = ["properties", "businesses", "bank", "armors", "hired_crew", "weapons", "vehicles", "ammo", "equipped", "stats"]


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def mongo():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def account(client, mongo):
    """Create a fresh test user, return dict with creds/token/id. Cleaned up at end."""
    suffix = uuid.uuid4().hex[:8]
    creds = {
        "email": f"TEST_{suffix}@example.com",
        "username": f"TEST_{suffix}",
        "password": "test1234",
    }
    r = client.post(f"{API}/auth/signup", json=creds)
    assert r.status_code == 200, f"signup failed {r.status_code}: {r.text[:400]}"
    data = r.json()
    assert "token" in data and "user" in data
    uid = data["user"]["id"]
    info = {**creds, "token": data["token"], "id": uid}
    yield info
    mongo.users.delete_one({"id": uid})
    mongo.operations.delete_many({"user_id": uid})


@pytest.fixture(scope="session")
def auth(account):
    return {"Authorization": f"Bearer {account['token']}", "Content-Type": "application/json"}


@pytest.fixture(scope="class")
def character(client, auth):
    """Ensure a character exists (xdist workers each get their own account)."""
    me = client.get(f"{API}/auth/me", headers=auth).json()
    if not me.get("specialization"):
        r = client.post(f"{API}/character/create", json={"avatar_id": "a1", "specialization": "shooter"}, headers=auth)
        assert r.status_code == 200, r.text[:300]
    return True


# ---------- health / catalog ----------
class TestHealthCatalog:
    def test_root(self, client):
        r = client.get(f"{API}/")
        assert r.status_code == 200

    def test_catalog(self, client):
        r = client.get(f"{API}/catalog")
        assert r.status_code == 200
        d = r.json()
        for key in ["specializations", "weapons", "armors", "vehicles", "npcs", "heists", "districts", "ammo_prices", "properties", "businesses"]:
            assert key in d and len(d[key]) > 0, f"catalog missing {key}"
        assert len(d["specializations"]) == 6


# ---------- auth ----------
class TestAuth:
    def test_signup_defaults(self, account, client):
        r = client.post(f"{API}/auth/login", json={"email": account["email"], "password": account["password"]})
        assert r.status_code == 200
        u = r.json()["user"]
        for k in DEFAULT_KEYS:
            assert k in u, f"login user missing backward-compat key {k}"
        assert "_id" not in u and "password_hash" not in u
        assert u["money"] == 800

    def test_login_bad_password(self, client, account):
        r = client.post(f"{API}/auth/login", json={"email": account["email"], "password": "wrongpass"})
        assert r.status_code == 401

    def test_duplicate_email(self, client, account):
        r = client.post(f"{API}/auth/signup", json={"email": account["email"], "username": "TEST_other", "password": "test1234"})
        assert r.status_code == 400

    def test_signup_validation(self, client):
        r = client.post(f"{API}/auth/signup", json={"email": "notanemail", "username": "ab", "password": "1"})
        assert r.status_code == 422

    def test_me_requires_token(self, client):
        r = client.get(f"{API}/auth/me")
        assert r.status_code == 401
        r = client.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401

    def test_me_backward_compat_defaults(self, client, auth, account, mongo):
        """Strip legacy fields in DB and confirm /auth/me re-injects defaults."""
        mongo.users.update_one({"id": account["id"]}, {"$unset": {"properties": "", "businesses": "", "bank": "", "armors": "", "hired_crew": ""}})
        r = client.get(f"{API}/auth/me", headers=auth)
        assert r.status_code == 200
        u = r.json()
        for k in DEFAULT_KEYS:
            assert k in u, f"/auth/me missing {k} for pre-migration user"
        assert u["bank"] == 0 and u["properties"] == [] and u["businesses"] == []
        # restore
        mongo.users.update_one({"id": account["id"]}, {"$set": {"properties": [], "businesses": [], "bank": 0, "armors": [], "hired_crew": []}})

    def test_bcrypt_hash_format(self, mongo, account):
        doc = mongo.users.find_one({"id": account["id"]})
        assert doc["password_hash"].startswith("$2b$"), doc["password_hash"][:10]


# ---------- character ----------
class TestCharacter:
    def test_create_character_invalid_spec(self, client, auth):
        r = client.post(f"{API}/character/create", json={"avatar_id": "a1", "specialization": "nope"}, headers=auth)
        assert r.status_code == 400

    def test_create_character(self, client, auth):
        r = client.post(f"{API}/character/create", json={"avatar_id": "a1", "specialization": "shooter"}, headers=auth)
        assert r.status_code == 200
        u = r.json()
        assert u["specialization"] == "shooter"
        assert u["avatar_id"] == "a1"
        # persistence
        r2 = client.get(f"{API}/auth/me", headers=auth)
        assert r2.json()["specialization"] == "shooter"


# ---------- shopping ----------
class TestShop:
    def test_buy_weapon_and_persist(self, client, auth):
        r = client.post(f"{API}/player/buy-weapon", json={"item_id": "knife"}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        state = client.get(f"{API}/player/state", headers=auth).json()
        assert any(w["id"] == "knife" for w in state["weapons"])

    def test_buy_weapon_not_found(self, client, auth):
        r = client.post(f"{API}/player/buy-weapon", json={"item_id": "bazooka9000"}, headers=auth)
        assert r.status_code == 404

    def test_buy_weapon_insufficient_funds(self, client, auth):
        r = client.post(f"{API}/player/buy-weapon", json={"item_id": "awm"}, headers=auth)
        assert r.status_code == 400

    def test_equip_weapon(self, client, auth):
        r = client.post(f"{API}/player/equip", json={"item_id": "knife", "slot": "melee"}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        state = client.get(f"{API}/player/state", headers=auth).json()
        assert state["equipped"]["melee"] == "knife"

    def test_buy_ammo(self, client, auth):
        before = client.get(f"{API}/player/state", headers=auth).json()["ammo"]["pistol"]
        r = client.post(f"{API}/player/buy-ammo", json={"ammo_type": "pistol", "quantity": 10}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        after = client.get(f"{API}/player/state", headers=auth).json()["ammo"]["pistol"]
        assert after == before + 10

    def test_hire_crew(self, client, auth, mongo, account):
        mongo.users.update_one({"id": account["id"]}, {"$set": {"money": 50000}})
        r = client.post(f"{API}/player/hire-crew", json={"npc_id": "npc_1"}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        state = client.get(f"{API}/player/state", headers=auth).json()
        crew = state["hired_crew"]
        ids = [c if isinstance(c, str) else (c.get("npc_id") or c.get("id")) for c in crew]
        assert "npc_1" in ids, crew

    def test_buy_vehicle(self, client, auth, mongo, account):
        mongo.users.update_one({"id": account["id"]}, {"$set": {"money": 200000}})
        cat = client.get(f"{API}/catalog").json()
        vid = sorted(cat["vehicles"], key=lambda v: v["price"])[0]["id"]
        r = client.post(f"{API}/player/buy-vehicle", json={"item_id": vid}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        state = client.get(f"{API}/player/state", headers=auth).json()
        assert any(v["id"] == vid for v in state["vehicles"])


# ---------- heists ----------
class TestHeists:
    def test_run_heist(self, client, auth, mongo, account, character):
        mongo.users.update_one({"id": account["id"]}, {"$set": {"health": 100}})
        r = client.post(f"{API}/heist/run", json={"heist_id": "op_atm", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert isinstance(d["outcome"], str) and len(d["outcome"]) > 0
        assert "rewards" in d and "cash" in d["rewards"]
        assert isinstance(d["events"], list) and len(d["events"]) > 0
        assert "user" in d and "_id" not in d["user"]

    def test_heist_level_gate(self, client, auth, character):
        r = client.post(f"{API}/heist/run", json={"heist_id": "op_penthouse", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
        assert r.status_code == 400

    def test_heist_not_found(self, client, auth, character):
        r = client.post(f"{API}/heist/run", json={"heist_id": "op_nope", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
        assert r.status_code == 404

    def test_history(self, client, auth, character):
        r = client.get(f"{API}/heist/history", headers=auth)
        assert r.status_code == 200
        ops = r.json()
        assert isinstance(ops, list) and len(ops) >= 1
        assert all("_id" not in o for o in ops)
        assert ops[0]["heist_id"] == "op_atm"

    def test_rankings(self, client):
        r = client.get(f"{API}/rankings")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------- backward-compat regression (legacy users without new fields) ----------
class TestLegacyUserCompat:
    def test_rankings_with_legacy_user_missing_stats(self, client, auth, account, mongo, character):
        """A pre-migration user document without `stats` must not break /api/rankings."""
        doc = mongo.users.find_one({"id": account["id"]})
        original_stats = doc.get("stats")
        mongo.users.update_one({"id": account["id"]}, {"$unset": {"stats": ""}})
        try:
            r = client.get(f"{API}/rankings")
            assert r.status_code == 200, f"/rankings returns {r.status_code} when any user doc lacks 'stats': {r.text[:200]}"
            rows = r.json()
            assert isinstance(rows, list)
            assert all("total_earnings" in row and "ops_completed" in row for row in rows)
        finally:
            if original_stats is not None:
                mongo.users.update_one({"id": account["id"]}, {"$set": {"stats": original_stats}})


# ---------- assets ----------
class TestAssets:
    def test_buy_property(self, client, auth, mongo, account):
        mongo.users.update_one({"id": account["id"]}, {"$set": {"money": 500000}})
        r = client.post(f"{API}/property/buy", json={"item_id": "prop_apartment"}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert any(p["id"] == "prop_apartment" for p in d["properties"])
        state = client.get(f"{API}/player/state", headers=auth).json()
        assert any(p["id"] == "prop_apartment" for p in state["properties"])

    def test_buy_property_duplicate(self, client, auth):
        r = client.post(f"{API}/property/buy", json={"item_id": "prop_apartment"}, headers=auth)
        assert r.status_code == 400

    def test_upgrade_security(self, client, auth):
        before = client.get(f"{API}/player/state", headers=auth).json()
        sec = next(p for p in before["properties"] if p["id"] == "prop_apartment")["security"]
        r = client.post(f"{API}/property/upgrade-security", json={"item_id": "prop_apartment"}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        after = client.get(f"{API}/player/state", headers=auth).json()
        assert next(p for p in after["properties"] if p["id"] == "prop_apartment")["security"] == sec + 5

    def test_buy_business_and_collect(self, client, auth, mongo, account):
        mongo.users.update_one({"id": account["id"]}, {"$set": {"money": 500000}})
        r = client.post(f"{API}/business/buy", json={"item_id": "biz_carwash"}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        assert any(b["id"] == "biz_carwash" for b in r.json()["businesses"])
        c = client.post(f"{API}/business/collect", headers=auth)
        assert c.status_code == 200, c.text[:300]
        d = c.json()
        for k in ["income", "fines", "net", "money", "events"]:
            assert k in d
        assert len(d["events"]) == 1

    def test_bank_deposit_withdraw(self, client, auth, mongo, account):
        mongo.users.update_one({"id": account["id"]}, {"$set": {"money": 10000, "bank": 0}})
        r = client.post(f"{API}/bank/deposit", json={"amount": 4000}, headers=auth)
        assert r.status_code == 200, r.text[:300]
        state = client.get(f"{API}/player/state", headers=auth).json()
        assert state["bank"] == 4000 and state["money"] == 6000
        r = client.post(f"{API}/bank/withdraw", json={"amount": 1500}, headers=auth)
        assert r.status_code == 200
        state = client.get(f"{API}/player/state", headers=auth).json()
        assert state["bank"] == 2500 and state["money"] == 7500

    def test_bank_invalid(self, client, auth):
        assert client.post(f"{API}/bank/deposit", json={"amount": -5}, headers=auth).status_code == 400
        assert client.post(f"{API}/bank/deposit", json={"amount": 99999999}, headers=auth).status_code == 400
        assert client.post(f"{API}/bank/withdraw", json={"amount": 99999999}, headers=auth).status_code == 400


# ---------- pvp ----------
class TestPvP:
    def test_targets(self, client, auth):
        r = client.get(f"{API}/pvp/targets", headers=auth)
        assert r.status_code == 200, r.text[:300]
        targets = r.json()
        assert isinstance(targets, list)
        assert all("password_hash" not in t and "_id" not in t for t in targets)

    def test_pvp_history(self, client, auth):
        r = client.get(f"{API}/pvp/history", headers=auth)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_raid_unknown_target(self, client, auth):
        r = client.post(f"{API}/pvp/raid", json={"target_username": "TEST_nonexistent_zzz", "property_id": "prop_apartment", "crew_ids": []}, headers=auth)
        assert r.status_code in (400, 404), f"{r.status_code} {r.text[:200]}"
