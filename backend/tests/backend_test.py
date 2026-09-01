"""Backend regression tests - The Law of Silence / NEON SYNDICATE (iteration 2).

Covers: auth (signup/login/me + backward-compat defaults), catalog, character create,
buy weapon/vehicle, hire crew, heist run + history, property buy/upgrade,
business buy/collect, bank deposit/withdraw, pvp targets/history, rankings.
"""
import os
import re
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


# ---------- iteration 3: daily missions ----------
MISSION_FIELDS = ["id", "title", "desc", "target", "type", "reward_cash", "reward_rep", "reward_xp", "progress", "complete", "claimed"]


class TestDailyMissions:
    def test_requires_auth(self, client):
        assert client.get(f"{API}/missions/daily").status_code == 401

    def test_daily_returns_three_with_all_fields(self, client, auth):
        r = client.get(f"{API}/missions/daily", headers=auth)
        assert r.status_code == 200, r.text[:400]
        missions = r.json()
        assert isinstance(missions, list)
        assert len(missions) == 3, f"expected 3 missions got {len(missions)}"
        ids = [m["id"] for m in missions]
        assert len(set(ids)) == 3, f"duplicate mission ids: {ids}"
        for m in missions:
            for f in MISSION_FIELDS:
                assert f in m, f"missing field {f} in {m}"
            assert isinstance(m["target"], int) and m["target"] > 0
            assert isinstance(m["progress"], int)
            assert m["progress"] <= m["target"]
            assert isinstance(m["complete"], bool) and isinstance(m["claimed"], bool)
            assert m["reward_cash"] > 0 and m["reward_xp"] > 0

    def test_daily_is_deterministic_for_same_user(self, client, auth):
        a = [m["id"] for m in client.get(f"{API}/missions/daily", headers=auth).json()]
        b = [m["id"] for m in client.get(f"{API}/missions/daily", headers=auth).json()]
        assert a == b, f"missions not deterministic: {a} vs {b}"

    def test_claim_unknown_mission_404(self, client, auth):
        r = client.post(f"{API}/missions/claim", json={"mission_id": "mission_does_not_exist"}, headers=auth)
        assert r.status_code == 404, f"{r.status_code} {r.text[:200]}"

    def test_claim_incomplete_400(self, client, auth, mongo, account):
        # zero out progress-driving stats so no mission can be complete
        mongo.users.update_one({"id": account["id"]}, {"$set": {
            "stats.ops_completed": 0, "stats.enemies_killed": 0, "stats.total_earnings": 0,
            "stats.raids_survived": 0, "weapons": [], "hired_crew": [],
        }})
        missions = client.get(f"{API}/missions/daily", headers=auth).json()
        target = missions[0]
        r = client.post(f"{API}/missions/claim", json={"mission_id": target["id"]}, headers=auth)
        assert r.status_code == 400, f"expected 400 for incomplete, got {r.status_code} {r.text[:200]}"

    def test_claim_awards_and_second_claim_rejected(self, client, auth, mongo, account):
        missions = client.get(f"{API}/missions/daily", headers=auth).json()
        m = missions[0]
        # force completion in DB for whatever mission type it is
        field = {
            "ops_quick": "stats.ops_completed", "ops_heist": "stats.ops_completed",
            "kills": "stats.enemies_killed", "earnings": "stats.total_earnings",
            "raids_survived": "stats.raids_survived",
        }.get(m["type"])
        if field:
            mongo.users.update_one({"id": account["id"]}, {"$set": {field: m["target"] + 5}})
        elif m["type"] == "buy_weapon":
            mongo.users.update_one({"id": account["id"]}, {"$set": {"weapons": [{"id": "w_pistol_9mm"}]}})
        elif m["type"] == "hire_crew":
            mongo.users.update_one({"id": account["id"]}, {"$set": {"hired_crew": [{"id": "npc_1"}]}})
        else:
            pytest.fail(f"unhandled mission type {m['type']}")
        # confirm it now shows complete
        refreshed = next(x for x in client.get(f"{API}/missions/daily", headers=auth).json() if x["id"] == m["id"])
        assert refreshed["complete"] is True, f"mission not complete after seeding progress: {refreshed}"
        assert refreshed["progress"] == refreshed["target"]

        before = client.get(f"{API}/player/state", headers=auth).json()
        r = client.post(f"{API}/missions/claim", json={"mission_id": m["id"]}, headers=auth)
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        assert body["ok"] is True
        assert body["reward"]["cash"] == m["reward_cash"]
        assert body["reward"]["xp"] == m["reward_xp"]
        assert body["reward"]["rep"] == m["reward_rep"]
        assert body["money"] == before["money"] + m["reward_cash"]

        after = client.get(f"{API}/player/state", headers=auth).json()
        assert after["money"] == before["money"] + m["reward_cash"]
        assert after["reputation"] == before["reputation"] + m["reward_rep"]
        # xp may roll over on level-up
        if after["level"] == before["level"]:
            assert after["xp"] == before["xp"] + m["reward_xp"]
        else:
            assert after["level"] > before["level"]

        # mission now marked claimed
        again = next(x for x in client.get(f"{API}/missions/daily", headers=auth).json() if x["id"] == m["id"])
        assert again["claimed"] is True

        # second claim rejected
        r2 = client.post(f"{API}/missions/claim", json={"mission_id": m["id"]}, headers=auth)
        assert r2.status_code == 400, f"double-claim allowed! {r2.status_code} {r2.text[:200]}"


# ---------- iteration 3: offline raids tick ----------
class TestOfflineRaids:
    def test_requires_auth(self, client):
        assert client.post(f"{API}/tick/offline-raids").status_code == 401

    def test_fresh_user_no_events(self, client, auth, mongo, account):
        from datetime import datetime, timezone
        mongo.users.update_one({"id": account["id"]}, {"$set": {"last_tick": datetime.now(timezone.utc).isoformat()}})
        r = client.post(f"{API}/tick/offline-raids", headers=auth)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["events"] == []
        assert d["hours"] < 0.5

    def test_long_offline_with_properties_returns_events_and_updates_tick(self, client, auth, mongo, account):
        from datetime import datetime, timedelta, timezone
        old = (datetime.now(timezone.utc) - timedelta(hours=70)).isoformat()
        mongo.users.update_one({"id": account["id"]}, {"$set": {
            "last_tick": old,
            "money": 500000,
            "heat": 50,
            "properties": [
                {"id": "prop_apartment", "security": 0, "instance_id": "t1", "cash_stash": 1000},
                {"id": "prop_warehouse", "security": 0, "instance_id": "t2", "cash_stash": 1000},
            ],
        }})
        r = client.post(f"{API}/tick/offline-raids", headers=auth)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        for k in ["events", "hours", "total_lost", "money"]:
            assert k in d, f"missing key {k}"
        assert d["hours"] <= 72
        assert isinstance(d["events"], list)
        for e in d["events"]:
            assert set(["type", "prop", "msg", "amount"]).issubset(e.keys())
            assert e["type"] in ("police", "gang", "defended")
        assert d["total_lost"] >= 0
        # last_tick moved forward
        doc = mongo.users.find_one({"id": account["id"]})
        assert doc["last_tick"] != old, "last_tick was not updated"
        # money reduced by exactly total_lost
        assert d["money"] == 500000 - d["total_lost"]

    def test_high_security_defends(self, client, auth, mongo, account):
        from datetime import datetime, timedelta, timezone
        mongo.users.update_one({"id": account["id"]}, {"$set": {
            "last_tick": (datetime.now(timezone.utc) - timedelta(hours=70)).isoformat(),
            "money": 500000, "heat": 50,
            "properties": [{"id": "prop_apartment", "security": 100, "instance_id": "t1", "cash_stash": 1000}],
        }})
        d = client.post(f"{API}/tick/offline-raids", headers=auth).json()
        assert all(e["type"] == "defended" for e in d["events"]), f"security 100 should always defend: {d['events']}"
        assert d["total_lost"] == 0

    def test_naive_last_tick_does_not_crash(self, client, auth, mongo, account):
        """Legacy/naive (no timezone) last_tick values must not 500 the endpoint."""
        from datetime import datetime, timedelta
        mongo.users.update_one({"id": account["id"]}, {"$set": {
            "last_tick": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
            "properties": [],
        }})
        r = client.post(f"{API}/tick/offline-raids", headers=auth)
        assert r.status_code == 200, f"naive last_tick crashed: {r.status_code} {r.text[:300]}"


# ---------- iteration 4: heist cooldown (server-enforced) ----------
class TestHeistCooldown:
    """POST /api/heist/run must reject a second run inside the tier cooldown window."""

    CD_MAP = {"quick": 90, "street": 240, "heist": 600, "major": 1200}

    def _reset(self, mongo, account, level=1, unset_cd=True):
        upd = {"$set": {"health": 100, "heat": 0, "level": level,
                        "ammo": {"9mm": 200, "5.56": 200, "7.62": 200, "12g": 200, ".45": 200},
                        "equipped": {}, "vehicles": [{"id": "starter", "instance_id": "s1", "condition": 100}]}}
        if unset_cd:
            upd["$unset"] = {"last_heist_at": ""}
        mongo.users.update_one({"id": account["id"]}, upd)

    def test_first_run_ok_second_blocked(self, client, auth, mongo, account, character):
        self._reset(mongo, account)
        r1 = client.post(f"{API}/heist/run", json={"heist_id": "op_atm", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
        assert r1.status_code == 200, r1.text[:400]
        d1 = r1.json()
        assert d1["cooldown_seconds"] == 90, f"quick cooldown should be 90, got {d1.get('cooldown_seconds')}"
        # last_heist_at persisted
        doc = mongo.users.find_one({"id": account["id"]})
        assert doc.get("last_heist_at"), "last_heist_at not persisted"

        # immediate second run -> 400 cooldown
        mongo.users.update_one({"id": account["id"]}, {"$set": {"health": 100}})
        r2 = client.post(f"{API}/heist/run", json={"heist_id": "op_atm", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
        assert r2.status_code == 400, f"second run should be blocked, got {r2.status_code}"
        detail = r2.json().get("detail", "")
        assert re.match(r"Cooldown active\. \d+s remaining", detail), f"unexpected detail: {detail}"

    @pytest.mark.parametrize("heist_id,level,crew,expected_cd", [
        ("op_atm", 1, [], 90),
        ("op_street_drug", 3, ["npc_1"], 240),
        ("op_armored", 10, ["npc_1", "npc_2"], 600),
    ])
    def test_cooldown_seconds_per_tier(self, client, auth, mongo, account, character, heist_id, level, crew, expected_cd):
        # need real npc ids from catalog
        npcs = client.get(f"{API}/catalog").json()["npcs"]
        crew_ids = [n["id"] for n in npcs[:len(crew)]]
        self._reset(mongo, account, level=level)
        mongo.users.update_one({"id": account["id"]}, {"$set": {"hired_crew": crew_ids}})
        r = client.post(f"{API}/heist/run", json={"heist_id": heist_id, "crew_ids": crew_ids, "vehicle_id": "starter"}, headers=auth)
        assert r.status_code == 200, r.text[:400]
        assert r.json()["cooldown_seconds"] == expected_cd

    def test_cooldown_expires(self, client, auth, mongo, account, character):
        """Setting last_heist_at far in the past must allow a new run."""
        from datetime import datetime, timedelta, timezone
        self._reset(mongo, account, unset_cd=False)
        mongo.users.update_one({"id": account["id"]}, {"$set": {
            "last_heist_at": (datetime.now(timezone.utc) - timedelta(seconds=5000)).isoformat()}})
        r = client.post(f"{API}/heist/run", json={"heist_id": "op_atm", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
        assert r.status_code == 200, r.text[:400]

    def test_cooldown_is_not_tier_of_last_run(self, client, auth, mongo, account, character):
        """Regression guard: cooldown is computed from the ATTEMPTED heist tier, not the last run's tier.

        After a 600s 'heist' tier op, a 90s 'quick' op becomes available after only 90s,
        which lets a player bypass the long cooldowns.
        """
        from datetime import datetime, timedelta, timezone
        self._reset(mongo, account, level=10, unset_cd=False)
        npcs = client.get(f"{API}/catalog").json()["npcs"]
        crew_ids = [n["id"] for n in npcs[:2]]
        mongo.users.update_one({"id": account["id"]}, {"$set": {"hired_crew": crew_ids, "last_heist_at": None}})
        r = client.post(f"{API}/heist/run", json={"heist_id": "op_armored", "crew_ids": crew_ids, "vehicle_id": "starter"}, headers=auth)
        assert r.status_code == 200, r.text[:400]
        assert r.json()["cooldown_seconds"] == 600
        # pretend 100s elapsed (< 600 heist cd, > 90 quick cd)
        mongo.users.update_one({"id": account["id"]}, {"$set": {
            "health": 100,
            "last_heist_at": (datetime.now(timezone.utc) - timedelta(seconds=100)).isoformat()}})
        r2 = client.post(f"{API}/heist/run", json={"heist_id": "op_atm", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
        assert r2.status_code == 400, (
            "EXPLOIT: long-tier cooldown bypassable by running a quick op "
            f"(got {r2.status_code} {r2.text[:200]})")


# ---------- iteration 4: heist difficulty nerf ----------
class TestHeistDifficulty:
    """40 op_atm runs as a fresh, unequipped user: >=30% must NOT be SUCCESS/PERFECT SUCCESS."""

    def test_outcome_distribution_is_harder(self, client, auth, mongo, account, character):
        from datetime import datetime, timedelta, timezone
        outcomes = []
        for _ in range(40):
            mongo.users.update_one({"id": account["id"]}, {"$set": {
                "health": 100, "heat": 0, "reputation": 0, "level": 1, "hired_crew": [],
                "equipped": {}, "armors": [], "weapons": [],
                "vehicles": [{"id": "starter", "instance_id": "s1", "condition": 100}],
                "last_heist_at": (datetime.now(timezone.utc) - timedelta(seconds=5000)).isoformat(),
            }})
            r = client.post(f"{API}/heist/run", json={"heist_id": "op_atm", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
            assert r.status_code == 200, r.text[:300]
            outcomes.append(r.json()["outcome"])
        good = [o for o in outcomes if o in ("PERFECT SUCCESS", "SUCCESS")]
        not_good_rate = 1 - len(good) / len(outcomes)
        print(f"\nOutcome distribution (40 op_atm runs): "
              f"{ {o: outcomes.count(o) for o in set(outcomes)} } -> non-success rate {not_good_rate:.0%}")
        assert not_good_rate >= 0.30, f"heists still too easy: only {not_good_rate:.0%} non-success | {outcomes}"

    def test_failed_outcome_pays_nothing(self, client, auth, mongo, account, character):
        """FAILED/DISASTER must give 0 cash; verify via history that any failed op recorded cash 0."""
        r = client.get(f"{API}/heist/history", headers=auth)
        assert r.status_code == 200
        ops = r.json()
        bad = [o for o in ops if o["outcome"] in ("FAILED", "DISASTER")]
        if not bad:
            pytest.skip("no failed ops recorded in history yet")
        assert all(o["cash"] == 0 for o in bad), f"failed ops paid cash: {bad[:3]}"

    def test_health_gate_blocks_run(self, client, auth, mongo, account, character):
        from datetime import datetime, timedelta, timezone
        mongo.users.update_one({"id": account["id"]}, {"$set": {
            "health": 10,
            "last_heist_at": (datetime.now(timezone.utc) - timedelta(seconds=5000)).isoformat()}})
        r = client.post(f"{API}/heist/run", json={"heist_id": "op_atm", "crew_ids": [], "vehicle_id": "starter"}, headers=auth)
        assert r.status_code == 400
        assert "Health" in r.json()["detail"]
