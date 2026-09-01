from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
import os, uuid, bcrypt, jwt, random, logging
from datetime import datetime, timezone, timedelta

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

app = FastAPI()
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tls")

# ========== GAME CATALOGS ==========
SPECIALIZATIONS = [
    {"id": "hacker", "name": "Hacker", "desc": "Bypass digital security, cameras, alarms.", "color": "#00F0FF"},
    {"id": "shooter", "name": "Shooter", "desc": "Combat expert. Superior in gunfights.", "color": "#EF4444"},
    {"id": "driver", "name": "Driver", "desc": "Getaway master. Faster escapes, better routes.", "color": "#F59E0B"},
    {"id": "infiltrator", "name": "Infiltrator", "desc": "Silent entry. Avoid alarms and detection.", "color": "#A855F7"},
    {"id": "negotiator", "name": "Negotiator", "desc": "De-escalate hostage & NPC situations.", "color": "#EC4899"},
    {"id": "technician", "name": "Technician", "desc": "Cracks locks, safes, mechanical security.", "color": "#10B981"},
]

WEAPONS = [
    # MELEE
    {"id": "knife", "name": "Tactical Knife", "cat": "melee", "slot": "melee", "damage": 18, "accuracy": 60, "reliability": 90, "price": 450, "ammo_type": None},
    {"id": "bat", "name": "Baseball Bat", "cat": "melee", "slot": "melee", "damage": 22, "accuracy": 55, "reliability": 95, "price": 680, "ammo_type": None},
    {"id": "katana", "name": "Katana", "cat": "melee", "slot": "melee", "damage": 35, "accuracy": 70, "reliability": 88, "price": 3800, "ammo_type": None},
    # PISTOLS
    {"id": "glock17", "name": "Glock 17", "cat": "pistol", "slot": "secondary", "damage": 32, "accuracy": 68, "reliability": 85, "price": 3400, "ammo_type": "pistol"},
    {"id": "beretta", "name": "M9 Beretta", "cat": "pistol", "slot": "secondary", "damage": 34, "accuracy": 72, "reliability": 82, "price": 4200, "ammo_type": "pistol"},
    {"id": "tec9", "name": "TEC-9", "cat": "pistol", "slot": "secondary", "damage": 40, "accuracy": 55, "reliability": 70, "price": 6200, "ammo_type": "pistol"},
    # SMGS
    {"id": "ump45", "name": "UMP-45", "cat": "smg", "slot": "primary", "damage": 48, "accuracy": 62, "reliability": 78, "price": 12500, "ammo_type": "smg"},
    {"id": "mp5", "name": "MP5", "cat": "smg", "slot": "primary", "damage": 50, "accuracy": 70, "reliability": 88, "price": 15800, "ammo_type": "smg"},
    {"id": "p90", "name": "P90", "cat": "smg", "slot": "primary", "damage": 55, "accuracy": 68, "reliability": 82, "price": 19500, "ammo_type": "smg"},
    # RIFLES
    {"id": "ak47", "name": "AK-47", "cat": "rifle", "slot": "primary", "damage": 72, "accuracy": 65, "reliability": 92, "price": 32000, "ammo_type": "rifle"},
    {"id": "m4a1", "name": "M4A1", "cat": "rifle", "slot": "primary", "damage": 68, "accuracy": 78, "reliability": 90, "price": 38000, "ammo_type": "rifle"},
    {"id": "scarl", "name": "SCAR-L", "cat": "rifle", "slot": "primary", "damage": 75, "accuracy": 80, "reliability": 88, "price": 46000, "ammo_type": "rifle"},
    # SHOTGUNS
    {"id": "mossberg", "name": "Mossberg 500", "cat": "shotgun", "slot": "primary", "damage": 88, "accuracy": 50, "reliability": 90, "price": 26000, "ammo_type": "shotgun"},
    {"id": "spas12", "name": "SPAS-12", "cat": "shotgun", "slot": "primary", "damage": 92, "accuracy": 55, "reliability": 85, "price": 34000, "ammo_type": "shotgun"},
    {"id": "aa12", "name": "AA-12", "cat": "shotgun", "slot": "primary", "damage": 95, "accuracy": 60, "reliability": 78, "price": 55000, "ammo_type": "shotgun"},
    # SNIPERS
    {"id": "awm", "name": "AWM", "cat": "sniper", "slot": "primary", "damage": 120, "accuracy": 95, "reliability": 88, "price": 68000, "ammo_type": "sniper"},
    {"id": "m24", "name": "M24", "cat": "sniper", "slot": "primary", "damage": 105, "accuracy": 92, "reliability": 90, "price": 55000, "ammo_type": "sniper"},
    {"id": "dragunov", "name": "Dragunov", "cat": "sniper", "slot": "primary", "damage": 100, "accuracy": 88, "reliability": 92, "price": 48000, "ammo_type": "sniper"},
    # SPECIAL
    {"id": "railgun", "name": "Railgun", "cat": "special", "slot": "primary", "damage": 150, "accuracy": 90, "reliability": 75, "price": 145000, "ammo_type": "special"},
    {"id": "plasma", "name": "Plasma Rifle", "cat": "special", "slot": "primary", "damage": 140, "accuracy": 85, "reliability": 78, "price": 128000, "ammo_type": "special"},
    {"id": "smartsmg", "name": "Smart SMG", "cat": "special", "slot": "primary", "damage": 95, "accuracy": 98, "reliability": 82, "price": 98000, "ammo_type": "special"},
]

ARMORS = [
    {"id": "light_armor", "name": "Light Armor", "damage_reduction": 15, "price": 2400, "slot": "armor"},
    {"id": "med_armor", "name": "Tactical Vest", "damage_reduction": 30, "price": 9500, "slot": "armor"},
    {"id": "heavy_armor", "name": "Heavy Armor", "damage_reduction": 50, "price": 32000, "slot": "armor"},
]

VEHICLES = [
    {"id": "starter", "name": "Rusty Sedan", "cat": "compact", "speed": 38, "handling": 45, "armor": 20, "escape": 30, "price": 0, "utility": "None. Starter beater."},
    {"id": "compact_x", "name": "Street Compact", "cat": "compact", "speed": 55, "handling": 62, "armor": 28, "escape": 50, "price": 5800, "utility": "Blends in traffic — reduces detection."},
    {"id": "hatchback", "name": "Turbo Hatchback", "cat": "compact", "speed": 65, "handling": 78, "armor": 24, "escape": 62, "price": 11500, "utility": "Tight cornering. Great for old town alleys."},
    {"id": "nightfall", "name": "Nightfall GT", "cat": "sport", "speed": 84, "handling": 76, "armor": 42, "escape": 81, "price": 22000, "utility": "Balanced getaway. All-purpose."},
    {"id": "chrome_r", "name": "Chrome Roadster", "cat": "sport", "speed": 88, "handling": 82, "armor": 38, "escape": 85, "price": 34000, "utility": "Highway escape specialist."},
    {"id": "muscle_v8", "name": "Muscle V8", "cat": "muscle", "speed": 78, "handling": 62, "armor": 65, "escape": 70, "price": 28500, "utility": "Ram police blockades."},
    {"id": "phantom_s", "name": "Phantom Super", "cat": "super", "speed": 95, "handling": 88, "armor": 55, "escape": 92, "price": 78000, "utility": "Outrun helicopters. Premium heist getaway."},
    {"id": "hypercar", "name": "Aeon Hypercar", "cat": "super", "speed": 99, "handling": 92, "armor": 48, "escape": 96, "price": 145000, "utility": "The fastest thing in Neon City."},
    {"id": "neon_bike", "name": "Neon Sport Bike", "cat": "bike", "speed": 92, "handling": 95, "armor": 15, "escape": 88, "price": 24000, "utility": "Squeeze through gridlock. High reward, high risk."},
    {"id": "armored_suv", "name": "Armored SUV", "cat": "armored", "speed": 62, "handling": 55, "armor": 95, "escape": 68, "price": 62000, "utility": "Reduces crew casualties in shootouts."},
    {"id": "riot_truck", "name": "Riot Truck", "cat": "armored", "speed": 55, "handling": 45, "armor": 99, "escape": 60, "price": 105000, "utility": "Bank & armored transport specialist."},
    {"id": "stealth_van", "name": "Stealth Van", "cat": "utility", "speed": 60, "handling": 60, "armor": 55, "escape": 72, "price": 48000, "utility": "Fits full 4-person crew + gear. Reduces heat gain."},
    {"id": "prototype_x", "name": "Prototype X", "cat": "special", "speed": 96, "handling": 90, "armor": 75, "escape": 94, "price": 220000, "utility": "Experimental EMP shielding. Deters police pursuit."},
]

NPCS = [
    {"id": "npc_1", "name": "Vex", "spec": "shooter", "skill": 65, "cut": 15, "hire_cost": 800},
    {"id": "npc_2", "name": "Maya", "spec": "hacker", "skill": 72, "cut": 18, "hire_cost": 1200},
    {"id": "npc_3", "name": "Dante", "spec": "driver", "skill": 68, "cut": 15, "hire_cost": 1000},
    {"id": "npc_4", "name": "Lena", "spec": "negotiator", "skill": 60, "cut": 12, "hire_cost": 700},
    {"id": "npc_5", "name": "Kaz", "spec": "infiltrator", "skill": 75, "cut": 18, "hire_cost": 1400},
    {"id": "npc_6", "name": "Rook", "spec": "technician", "skill": 70, "cut": 16, "hire_cost": 1100},
    {"id": "npc_7", "name": "Blade", "spec": "shooter", "skill": 82, "cut": 22, "hire_cost": 2500},
    {"id": "npc_8", "name": "Ghost", "spec": "infiltrator", "skill": 88, "cut": 25, "hire_cost": 3800},
    {"id": "npc_9", "name": "Cipher", "spec": "hacker", "skill": 90, "cut": 25, "hire_cost": 4200},
    {"id": "npc_10", "name": "Wraith", "spec": "driver", "skill": 85, "cut": 22, "hire_cost": 3200},
]

HEISTS = [
    {"id": "op_convenience", "name": "Convenience Store", "type": "quick", "district": "downtown", "min_level": 1, "min_crew": 0, "difficulty": 1, "reward_min": 280, "reward_max": 620, "heat_gain": 5, "duration": 10},
    {"id": "op_atm", "name": "ATM Grab", "type": "quick", "district": "downtown", "min_level": 1, "min_crew": 0, "difficulty": 1, "reward_min": 320, "reward_max": 720, "heat_gain": 4, "duration": 8},
    {"id": "op_gasstation", "name": "Gas Station Robbery", "type": "quick", "district": "old_town", "min_level": 2, "min_crew": 0, "difficulty": 2, "reward_min": 480, "reward_max": 950, "heat_gain": 6, "duration": 12},
    {"id": "op_street_drug", "name": "Street Drug Deal", "type": "street", "district": "north_side", "min_level": 3, "min_crew": 1, "difficulty": 3, "reward_min": 850, "reward_max": 1850, "heat_gain": 10, "duration": 14},
    {"id": "op_jewelry", "name": "Jewelry Store", "type": "street", "district": "upper_east", "min_level": 5, "min_crew": 1, "difficulty": 4, "reward_min": 1450, "reward_max": 2800, "heat_gain": 15, "duration": 16},
    {"id": "op_warehouse", "name": "Warehouse Raid", "type": "street", "district": "industrial", "min_level": 7, "min_crew": 2, "difficulty": 5, "reward_min": 1950, "reward_max": 3400, "heat_gain": 18, "duration": 20},
    {"id": "op_armored", "name": "Armored Transport", "type": "heist", "district": "docks", "min_level": 10, "min_crew": 2, "difficulty": 6, "reward_min": 3400, "reward_max": 5800, "heat_gain": 25, "duration": 24},
    {"id": "op_casino", "name": "Casino Vault", "type": "heist", "district": "upper_east", "min_level": 15, "min_crew": 3, "difficulty": 7, "reward_min": 5500, "reward_max": 9500, "heat_gain": 30, "duration": 30},
    {"id": "op_bank", "name": "Downtown Bank", "type": "heist", "district": "downtown", "min_level": 20, "min_crew": 3, "difficulty": 8, "reward_min": 8500, "reward_max": 15000, "heat_gain": 40, "duration": 35},
    {"id": "op_datacenter", "name": "Corp Data Center", "type": "major", "district": "black_island", "min_level": 25, "min_crew": 4, "difficulty": 9, "reward_min": 13000, "reward_max": 21000, "heat_gain": 45, "duration": 40},
    {"id": "op_penthouse", "name": "Kingpin's Penthouse", "type": "major", "district": "black_island", "min_level": 30, "min_crew": 4, "difficulty": 10, "reward_min": 19000, "reward_max": 34000, "heat_gain": 55, "duration": 50},
]

DISTRICTS = [
    {"id": "downtown", "name": "Downtown", "level_range": "1-10", "color": "#38BDF8"},
    {"id": "old_town", "name": "Old Town", "level_range": "1-15", "color": "#10B981"},
    {"id": "north_side", "name": "North Side", "level_range": "3-15", "color": "#A855F7"},
    {"id": "docks", "name": "Docks", "level_range": "10-25", "color": "#06B6D4"},
    {"id": "upper_east", "name": "Upper East", "level_range": "15-30", "color": "#F59E0B"},
    {"id": "industrial", "name": "Industrial Zone", "level_range": "10-20", "color": "#F97316"},
    {"id": "south_side", "name": "South Side", "level_range": "20-35", "color": "#EF4444"},
    {"id": "black_island", "name": "Black Island", "level_range": "30+", "color": "#EC4899"},
]

AMMO_PRICES = {"pistol": 3, "smg": 5, "rifle": 8, "shotgun": 12, "sniper": 40, "special": 65}

PROPERTIES = [
    {"id": "prop_apartment", "name": "Downtown Apartment", "district": "downtown", "tier": 1, "storage_cars": 2, "storage_weapons": 6, "security": 15, "price": 8500, "desc": "Cramped but yours. Basic locks, no guards."},
    {"id": "prop_safehouse", "name": "Docks Safehouse", "district": "docks", "tier": 2, "storage_cars": 4, "storage_weapons": 12, "security": 35, "price": 32000, "desc": "Reinforced doors, one lookout. Cops think twice."},
    {"id": "prop_penthouse", "name": "Upper East Penthouse", "district": "upper_east", "tier": 3, "storage_cars": 8, "storage_weapons": 25, "security": 60, "price": 125000, "desc": "Private guards. Silent alarms. Legitimate facade."},
    {"id": "prop_compound", "name": "Industrial Compound", "district": "industrial", "tier": 4, "storage_cars": 15, "storage_weapons": 60, "security": 85, "price": 320000, "desc": "Armed patrols, cameras everywhere. A fortress."},
    {"id": "prop_estate", "name": "Black Island Estate", "district": "black_island", "tier": 5, "storage_cars": 30, "storage_weapons": 150, "security": 98, "price": 850000, "desc": "The kind of place law enforcement never touches."},
]

BUSINESSES = [
    {"id": "biz_carwash", "name": "Neon Car Wash", "district": "downtown", "price": 18000, "daily_income": 380, "inspection_risk": 0.06, "fine_min": 800, "fine_max": 2500, "desc": "Legit cover. Steady low income."},
    {"id": "biz_bar", "name": "Underground Bar", "district": "old_town", "price": 42000, "daily_income": 950, "inspection_risk": 0.14, "fine_min": 2500, "fine_max": 6500, "desc": "Cash-heavy. Health inspectors love this."},
    {"id": "biz_pawn", "name": "Pawn Shop", "district": "north_side", "price": 65000, "daily_income": 1550, "inspection_risk": 0.20, "fine_min": 4000, "fine_max": 12000, "desc": "Move stolen goods. Higher heat gain."},
    {"id": "biz_club", "name": "Neon Nightclub", "district": "upper_east", "price": 155000, "daily_income": 3400, "inspection_risk": 0.25, "fine_min": 8000, "fine_max": 25000, "desc": "The city's pulse. Cops watching."},
    {"id": "biz_casino", "name": "Underground Casino", "district": "black_island", "price": 480000, "daily_income": 8500, "inspection_risk": 0.35, "fine_min": 25000, "fine_max": 75000, "desc": "Massive daily print. Massive risk if raided."},
]

# ========== HELPERS ==========
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

async def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = auth[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user = await db.users.find_one({"id": payload["sub"]})
        if not user:
            raise HTTPException(401, "User not found")
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

def xp_for_level(lvl: int) -> int:
    return 1000 + (lvl - 1) * 500

def check_level_up(user: dict) -> dict:
    while user["xp"] >= xp_for_level(user["level"]):
        user["xp"] -= xp_for_level(user["level"])
        user["level"] += 1
    return user

def find_item(items: list, iid: str):
    for it in items:
        if it["id"] == iid:
            return it
    return None

# ========== MODELS ==========
class SignupIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class CharacterIn(BaseModel):
    avatar_id: str
    specialization: str

class BuyIn(BaseModel):
    item_id: str

class EquipIn(BaseModel):
    item_id: str
    slot: str  # primary | secondary | melee | armor | vehicle

class AmmoIn(BaseModel):
    ammo_type: str
    quantity: int

class RepairIn(BaseModel):
    vehicle_id: str

class HireIn(BaseModel):
    npc_id: str

class HeistIn(BaseModel):
    heist_id: str
    crew_ids: List[str] = []
    vehicle_id: str

class BankIn(BaseModel):
    amount: int

class RaidIn(BaseModel):
    target_username: str
    property_id: str
    crew_ids: List[str] = []

# ========== AUTH ==========
@api.post("/auth/signup")
async def signup(data: SignupIn):
    email = data.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")
    if await db.users.find_one({"username": data.username}):
        raise HTTPException(400, "Username taken")
    uid = str(uuid.uuid4())
    user = {
        "id": uid,
        "email": email,
        "username": data.username,
        "password_hash": hash_password(data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "avatar_id": None,
        "specialization": None,
        "level": 1,
        "xp": 0,
        "money": 800,
        "reputation": 0,
        "heat": 0,
        "health": 100,
        "weapons": [],
        "armors": [],
        "vehicles": [{"id": "starter", "condition": 100, "instance_id": str(uuid.uuid4())}],
        "ammo": {"pistol": 20, "smg": 0, "rifle": 0, "shotgun": 0, "sniper": 0, "special": 0},
        "equipped": {"primary": None, "secondary": None, "melee": None, "armor": None, "vehicle": "starter"},
        "hired_crew": [],
        "properties": [],
        "businesses": [],
        "bank": 0,
        "last_tick": datetime.now(timezone.utc).isoformat(),
        "stats": {"ops_completed": 0, "ops_failed": 0, "enemies_killed": 0, "times_shot": 0, "crew_lost": 0, "total_earnings": 0, "total_spent": 0, "business_income": 0, "fines_paid": 0, "raids_survived": 0},
    }
    await db.users.insert_one(user)
    token = create_token(uid)
    user.pop("_id", None); user.pop("password_hash", None)
    return {"token": token, "user": user}

@api.post("/auth/login")
async def login(data: LoginIn):
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_token(user["id"])
    user.pop("_id", None); user.pop("password_hash", None)
    return {"token": token, "user": user}

@api.get("/auth/me")
async def me(request: Request):
    return await get_current_user(request)

# ========== CHARACTER ==========
@api.post("/character/create")
async def create_character(data: CharacterIn, request: Request):
    user = await get_current_user(request)
    if data.specialization not in [s["id"] for s in SPECIALIZATIONS]:
        raise HTTPException(400, "Invalid specialization")
    await db.users.update_one({"id": user["id"]}, {"$set": {"avatar_id": data.avatar_id, "specialization": data.specialization}})
    updated = await db.users.find_one({"id": user["id"]})
    updated.pop("_id", None); updated.pop("password_hash", None)
    return updated

# ========== CATALOG ==========
@api.get("/catalog")
async def catalog():
    return {"specializations": SPECIALIZATIONS, "weapons": WEAPONS, "armors": ARMORS, "vehicles": VEHICLES, "npcs": NPCS, "heists": HEISTS, "districts": DISTRICTS, "ammo_prices": AMMO_PRICES, "properties": PROPERTIES, "businesses": BUSINESSES}

# ========== PLAYER STATE ==========
@api.get("/player/state")
async def player_state(request: Request):
    return await get_current_user(request)

@api.post("/player/buy-weapon")
async def buy_weapon(data: BuyIn, request: Request):
    user = await get_current_user(request)
    w = find_item(WEAPONS, data.item_id)
    if not w:
        raise HTTPException(404, "Weapon not found")
    if user["money"] < w["price"]:
        raise HTTPException(400, "Not enough money")
    weapons = user["weapons"]
    existing = next((x for x in weapons if x["id"] == data.item_id), None)
    if existing:
        existing["qty"] += 1
    else:
        weapons.append({"id": data.item_id, "qty": 1})
    new_money = user["money"] - w["price"]
    new_spent = user["stats"]["total_spent"] + w["price"]
    await db.users.update_one({"id": user["id"]}, {"$set": {"weapons": weapons, "money": new_money, "stats.total_spent": new_spent}})
    return {"ok": True, "money": new_money, "weapons": weapons}

@api.post("/player/buy-armor")
async def buy_armor(data: BuyIn, request: Request):
    user = await get_current_user(request)
    a = find_item(ARMORS, data.item_id)
    if not a:
        raise HTTPException(404, "Armor not found")
    if user["money"] < a["price"]:
        raise HTTPException(400, "Not enough money")
    armors = user["armors"]
    ex = next((x for x in armors if x["id"] == data.item_id), None)
    if ex: ex["qty"] += 1
    else: armors.append({"id": data.item_id, "qty": 1})
    new_money = user["money"] - a["price"]
    await db.users.update_one({"id": user["id"]}, {"$set": {"armors": armors, "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + a["price"]}})
    return {"ok": True, "money": new_money, "armors": armors}

@api.post("/player/buy-vehicle")
async def buy_vehicle(data: BuyIn, request: Request):
    user = await get_current_user(request)
    v = find_item(VEHICLES, data.item_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    if user["money"] < v["price"]:
        raise HTTPException(400, "Not enough money")
    vehicles = user["vehicles"]
    vehicles.append({"id": data.item_id, "condition": 100, "instance_id": str(uuid.uuid4())})
    new_money = user["money"] - v["price"]
    await db.users.update_one({"id": user["id"]}, {"$set": {"vehicles": vehicles, "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + v["price"]}})
    return {"ok": True, "money": new_money, "vehicles": vehicles}

@api.post("/player/equip")
async def equip(data: EquipIn, request: Request):
    user = await get_current_user(request)
    slot = data.slot
    equipped = user["equipped"]
    if slot not in equipped:
        raise HTTPException(400, "Invalid slot")
    if slot == "vehicle":
        if not any(v["id"] == data.item_id for v in user["vehicles"]):
            raise HTTPException(400, "Vehicle not owned")
        equipped[slot] = data.item_id
    elif slot == "armor":
        if not any(a["id"] == data.item_id for a in user["armors"]):
            raise HTTPException(400, "Armor not owned")
        equipped[slot] = data.item_id
    else:
        w = find_item(WEAPONS, data.item_id)
        if not w or w["slot"] != slot:
            raise HTTPException(400, "Weapon can't be equipped in this slot")
        if not any(x["id"] == data.item_id for x in user["weapons"]):
            raise HTTPException(400, "Weapon not owned")
        equipped[slot] = data.item_id
    await db.users.update_one({"id": user["id"]}, {"$set": {"equipped": equipped}})
    return {"ok": True, "equipped": equipped}

@api.post("/player/buy-ammo")
async def buy_ammo(data: AmmoIn, request: Request):
    user = await get_current_user(request)
    if data.ammo_type not in AMMO_PRICES:
        raise HTTPException(400, "Invalid ammo type")
    if data.quantity <= 0 or data.quantity > 5000:
        raise HTTPException(400, "Invalid quantity")
    total = AMMO_PRICES[data.ammo_type] * data.quantity
    if user["money"] < total:
        raise HTTPException(400, "Not enough money")
    ammo = user["ammo"]
    ammo[data.ammo_type] = ammo.get(data.ammo_type, 0) + data.quantity
    new_money = user["money"] - total
    await db.users.update_one({"id": user["id"]}, {"$set": {"ammo": ammo, "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + total}})
    return {"ok": True, "money": new_money, "ammo": ammo}

@api.post("/player/repair")
async def repair(data: RepairIn, request: Request):
    user = await get_current_user(request)
    veh = next((v for v in user["vehicles"] if v.get("instance_id") == data.vehicle_id or v["id"] == data.vehicle_id), None)
    if not veh:
        raise HTTPException(404, "Vehicle not found")
    dmg = 100 - veh["condition"]
    cost = dmg * 50
    if user["money"] < cost:
        raise HTTPException(400, "Not enough money")
    veh["condition"] = 100
    new_money = user["money"] - cost
    await db.users.update_one({"id": user["id"]}, {"$set": {"vehicles": user["vehicles"], "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + cost}})
    return {"ok": True, "money": new_money, "cost": cost}

@api.post("/player/heal")
async def heal(request: Request):
    user = await get_current_user(request)
    missing = 100 - user["health"]
    cost = missing * 25
    if user["money"] < cost:
        raise HTTPException(400, "Not enough money")
    new_money = user["money"] - cost
    await db.users.update_one({"id": user["id"]}, {"$set": {"health": 100, "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + cost}})
    return {"ok": True, "money": new_money, "health": 100, "cost": cost}

@api.post("/player/hire-crew")
async def hire_crew(data: HireIn, request: Request):
    user = await get_current_user(request)
    npc = find_item(NPCS, data.npc_id)
    if not npc:
        raise HTTPException(404, "NPC not found")
    if data.npc_id in user["hired_crew"]:
        raise HTTPException(400, "Already hired")
    if user["money"] < npc["hire_cost"]:
        raise HTTPException(400, "Not enough money")
    hired = user["hired_crew"] + [data.npc_id]
    new_money = user["money"] - npc["hire_cost"]
    await db.users.update_one({"id": user["id"]}, {"$set": {"hired_crew": hired, "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + npc["hire_cost"]}})
    return {"ok": True, "money": new_money, "hired_crew": hired}

# ========== HEIST SIMULATION ==========
def simulate_heist(user: dict, heist: dict, crew_ids: List[str], vehicle_id: str) -> dict:
    """Runs a heist simulation and returns events + outcome."""
    events = []
    t = 0
    def add(msg, cat="info"):
        nonlocal t
        t += random.randint(2, 8)
        mm, ss = divmod(t, 60)
        events.append({"time": f"{mm:02d}:{ss:02d}", "msg": msg, "cat": cat})

    # gather player context
    spec = user["specialization"]
    weapon_id = user["equipped"].get("primary") or user["equipped"].get("secondary") or user["equipped"].get("melee")
    weapon = find_item(WEAPONS, weapon_id) if weapon_id else None
    veh = next((v for v in user["vehicles"] if v["id"] == vehicle_id), None)
    veh_data = find_item(VEHICLES, vehicle_id)
    armor_id = user["equipped"].get("armor")
    armor = find_item(ARMORS, armor_id) if armor_id else None
    crew_data = [find_item(NPCS, cid) for cid in crew_ids if find_item(NPCS, cid)]

    # base success prob
    difficulty = heist["difficulty"]
    base = max(0.15, 0.9 - difficulty * 0.06)
    # weapon bonus
    if weapon:
        base += (weapon["damage"] / 500) + (weapon["accuracy"] / 800)
    # vehicle bonus
    if veh_data:
        base += (veh_data["escape"] / 800)
    # armor
    if armor:
        base += armor["damage_reduction"] / 500
    # crew
    base += len(crew_data) * 0.04
    # crew specs
    specs_available = {spec} | {c["spec"] for c in crew_data}
    diverse_bonus = len(specs_available) * 0.02
    base += diverse_bonus
    # rep bonus
    base += min(0.15, user["reputation"] / 2000)
    # heat penalty
    base -= min(0.25, user["heat"] / 400)

    base = max(0.05, min(0.95, base))
    roll = random.random()

    # determine outcome tier
    if roll < base - 0.25:
        outcome = "PERFECT SUCCESS"; mult = 1.6; rep_mult = 2.0; hp_loss_pct = 0.05
    elif roll < base - 0.05:
        outcome = "SUCCESS"; mult = 1.0; rep_mult = 1.0; hp_loss_pct = 0.15
    elif roll < base + 0.15:
        outcome = "PARTIAL SUCCESS"; mult = 0.5; rep_mult = 0.4; hp_loss_pct = 0.35
    elif roll < base + 0.30:
        outcome = "FAILED"; mult = 0.0; rep_mult = -0.1; hp_loss_pct = 0.55
    else:
        outcome = "DISASTER"; mult = 0.0; rep_mult = -0.25; hp_loss_pct = 0.85

    # event generation
    add(f"Crew mobilized. Rolling to {heist['name']}.", "info")
    add("Vehicle en route to target.", "info")
    add("Crew entered the location.", "info")

    # security phase
    if "hacker" in specs_available or "technician" in specs_available or "infiltrator" in specs_available:
        add("Security system detected.", "warn")
        if "hacker" in specs_available:
            add("Hacker bypassed security cameras.", "good")
        if "technician" in specs_available:
            add("Technician cracked the vault lock.", "good")
        if "infiltrator" in specs_available:
            add("Infiltrator disabled the alarm silently.", "good")
    else:
        add("Alarm triggered — no bypass available.", "bad")

    # combat phase
    enemies_killed = 0
    times_shot = 0
    if outcome in ("PERFECT SUCCESS", "SUCCESS"):
        enemies_killed = random.randint(1, 3 + difficulty // 2)
        for _ in range(enemies_killed):
            add("You shot an enemy.", "combat")
        if outcome == "SUCCESS" and random.random() < 0.4:
            add("You were shot.", "bad"); times_shot += 1
    elif outcome == "PARTIAL SUCCESS":
        enemies_killed = random.randint(1, 4)
        times_shot = random.randint(1, 2)
        for _ in range(enemies_killed): add("You shot an enemy.", "combat")
        for _ in range(times_shot): add("You were shot.", "bad")
        add("Security alerted.", "warn")
    elif outcome == "FAILED":
        enemies_killed = random.randint(0, 2)
        times_shot = random.randint(2, 4)
        for _ in range(enemies_killed): add("You shot an enemy.", "combat")
        for _ in range(times_shot): add("You were shot.", "bad")
        add("Crew member down.", "bad")
        add("Police response incoming.", "bad")
    else:  # DISASTER
        times_shot = random.randint(3, 6)
        for _ in range(times_shot): add("You were shot.", "bad")
        add("Crew member down.", "bad")
        if len(crew_data) >= 2: add("Crew member down.", "bad")
        add("Escape route compromised.", "bad")
        add("Police lockdown deployed.", "bad")

    # cash / escape
    if outcome in ("PERFECT SUCCESS", "SUCCESS", "PARTIAL SUCCESS"):
        add("Cash secured.", "good")
    if outcome in ("PERFECT SUCCESS", "SUCCESS"):
        if "driver" in specs_available:
            add("Driver found an alternate escape route.", "good")
        add("Crew reached extraction.", "good")
        add("Police lost the trail.", "good")
        add("Escape successful.", "good")
    elif outcome == "PARTIAL SUCCESS":
        add("Vehicle damaged during escape.", "warn")
        add("Escape successful — barely.", "warn")
    elif outcome == "FAILED":
        add("Operation aborted.", "bad")
    else:
        add("Player down. Operation catastrophic failure.", "bad")

    # compute rewards & deltas
    base_cash = random.randint(heist["reward_min"], heist["reward_max"])
    cash = int(base_cash * mult)
    xp = int((heist["reward_min"] / 8) * (mult if mult > 0 else 0.2))
    rep = int(heist["difficulty"] * 3 * rep_mult)
    heat_gain = heist["heat_gain"] if mult >= 0.5 else int(heist["heat_gain"] * 1.5)
    if outcome == "PERFECT SUCCESS": heat_gain = int(heat_gain * 0.5)

    # damage
    hp_loss = int(100 * hp_loss_pct)
    if armor:
        hp_loss = int(hp_loss * (1 - armor["damage_reduction"] / 100))
    # veh damage
    veh_dmg = int(hp_loss_pct * 40)

    # ammo used
    ammo_used = 0
    if weapon and weapon["ammo_type"]:
        ammo_used = enemies_killed * random.randint(2, 6) + times_shot * random.randint(1, 3)

    crew_lost = sum(1 for e in events if e["msg"] == "Crew member down.")

    return {
        "events": events,
        "outcome": outcome,
        "rewards": {"cash": cash, "xp": xp, "rep": rep, "heat": heat_gain, "hp_loss": hp_loss, "veh_dmg": veh_dmg, "ammo_used": ammo_used, "ammo_type": weapon["ammo_type"] if weapon else None, "enemies_killed": enemies_killed, "times_shot": times_shot, "crew_lost": crew_lost},
    }

@api.post("/heist/run")
async def run_heist(data: HeistIn, request: Request):
    user = await get_current_user(request)
    if not user.get("specialization"):
        raise HTTPException(400, "Character not created")
    heist = find_item(HEISTS, data.heist_id)
    if not heist:
        raise HTTPException(404, "Heist not found")
    if user["level"] < heist["min_level"]:
        raise HTTPException(400, f"Level {heist['min_level']} required")
    if len(data.crew_ids) < heist["min_crew"]:
        raise HTTPException(400, f"Need at least {heist['min_crew']} crew members")
    if not any(v["id"] == data.vehicle_id for v in user["vehicles"]):
        raise HTTPException(400, "Vehicle not owned")
    if user["health"] < 30:
        raise HTTPException(400, "Health too low. Heal first.")
    # check ammo
    weapon_id = user["equipped"].get("primary") or user["equipped"].get("secondary")
    weapon = find_item(WEAPONS, weapon_id) if weapon_id else None
    if weapon and weapon["ammo_type"] and user["ammo"].get(weapon["ammo_type"], 0) < 5:
        raise HTTPException(400, f"Not enough {weapon['ammo_type']} ammo. Buy more.")

    result = simulate_heist(user, heist, data.crew_ids, data.vehicle_id)
    rew = result["rewards"]

    # apply deltas
    user["money"] += rew["cash"]
    user["xp"] += rew["xp"]
    user["reputation"] = max(0, user["reputation"] + rew["rep"])
    user["heat"] = min(100, max(0, user["heat"] + rew["heat"]))
    user["health"] = max(0, user["health"] - rew["hp_loss"])
    # vehicle damage
    veh = next((v for v in user["vehicles"] if v["id"] == data.vehicle_id), None)
    if veh:
        veh["condition"] = max(0, veh["condition"] - rew["veh_dmg"])
    # ammo
    if rew["ammo_type"] and rew["ammo_used"] > 0:
        user["ammo"][rew["ammo_type"]] = max(0, user["ammo"].get(rew["ammo_type"], 0) - rew["ammo_used"])
    # stats
    user["stats"]["enemies_killed"] += rew["enemies_killed"]
    user["stats"]["times_shot"] += rew["times_shot"]
    user["stats"]["crew_lost"] += rew["crew_lost"]
    user["stats"]["total_earnings"] += rew["cash"]
    if rew["cash"] > 0:
        user["stats"]["ops_completed"] += 1
    else:
        user["stats"]["ops_failed"] += 1
    # level up
    user = check_level_up(user)

    # save
    await db.users.update_one({"id": user["id"]}, {"$set": {
        "money": user["money"], "xp": user["xp"], "level": user["level"], "reputation": user["reputation"],
        "heat": user["heat"], "health": user["health"], "vehicles": user["vehicles"], "ammo": user["ammo"], "stats": user["stats"]
    }})

    # log operation
    op_record = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "heist_id": data.heist_id,
        "heist_name": heist["name"],
        "outcome": result["outcome"],
        "cash": rew["cash"], "xp": rew["xp"], "rep": rew["rep"], "heat": rew["heat"],
        "crew_ids": data.crew_ids, "vehicle_id": data.vehicle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.operations.insert_one(op_record)

    updated = await db.users.find_one({"id": user["id"]})
    updated.pop("_id", None); updated.pop("password_hash", None)
    return {"events": result["events"], "outcome": result["outcome"], "rewards": rew, "user": updated}

@api.get("/heist/history")
async def heist_history(request: Request, limit: int = 30):
    user = await get_current_user(request)
    ops = await db.operations.find({"user_id": user["id"]}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return ops

# ========== RANKINGS ==========
@api.get("/rankings")
async def rankings(limit: int = 25):
    users = await db.users.find({"specialization": {"$ne": None}}, {"_id": 0, "password_hash": 0, "email": 0}).sort([("level", -1), ("reputation", -1), ("stats.total_earnings", -1)]).limit(limit).to_list(limit)
    return [{"username": u["username"], "level": u["level"], "reputation": u["reputation"], "specialization": u["specialization"], "total_earnings": u["stats"]["total_earnings"], "ops_completed": u["stats"]["ops_completed"]} for u in users]

# ========== PROPERTIES ==========
@api.post("/property/buy")
async def buy_property(data: BuyIn, request: Request):
    user = await get_current_user(request)
    p = find_item(PROPERTIES, data.item_id)
    if not p:
        raise HTTPException(404, "Property not found")
    if any(x["id"] == data.item_id for x in user.get("properties", [])):
        raise HTTPException(400, "Already owned")
    if user["money"] < p["price"]:
        raise HTTPException(400, "Not enough money")
    props = user.get("properties", []) + [{"id": p["id"], "security": p["security"], "instance_id": str(uuid.uuid4()), "cash_stash": 0}]
    new_money = user["money"] - p["price"]
    await db.users.update_one({"id": user["id"]}, {"$set": {"properties": props, "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + p["price"]}})
    return {"ok": True, "money": new_money, "properties": props}

@api.post("/property/upgrade-security")
async def upgrade_security(data: BuyIn, request: Request):
    user = await get_current_user(request)
    prop = next((p for p in user.get("properties", []) if p["id"] == data.item_id), None)
    if not prop:
        raise HTTPException(404, "Property not owned")
    if prop["security"] >= 100:
        raise HTTPException(400, "Security maxed")
    upgrade_cost = int(prop["security"] * 250 + 2000)
    if user["money"] < upgrade_cost:
        raise HTTPException(400, "Not enough money")
    prop["security"] = min(100, prop["security"] + 5)
    new_money = user["money"] - upgrade_cost
    await db.users.update_one({"id": user["id"]}, {"$set": {"properties": user["properties"], "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + upgrade_cost}})
    return {"ok": True, "money": new_money, "properties": user["properties"], "cost": upgrade_cost}

# ========== BUSINESSES ==========
@api.post("/business/buy")
async def buy_business(data: BuyIn, request: Request):
    user = await get_current_user(request)
    b = find_item(BUSINESSES, data.item_id)
    if not b:
        raise HTTPException(404, "Business not found")
    if any(x["id"] == data.item_id for x in user.get("businesses", [])):
        raise HTTPException(400, "Already owned")
    if user["money"] < b["price"]:
        raise HTTPException(400, "Not enough money")
    biz = user.get("businesses", []) + [{"id": b["id"], "instance_id": str(uuid.uuid4()), "last_collected": datetime.now(timezone.utc).isoformat()}]
    new_money = user["money"] - b["price"]
    await db.users.update_one({"id": user["id"]}, {"$set": {"businesses": biz, "money": new_money, "stats.total_spent": user["stats"]["total_spent"] + b["price"]}})
    return {"ok": True, "money": new_money, "businesses": biz}

@api.post("/business/collect")
async def collect_business(request: Request):
    """Collect accumulated income from all businesses. Rolls inspection risk once per collect."""
    user = await get_current_user(request)
    now = datetime.now(timezone.utc)
    total_income = 0
    total_fines = 0
    events = []
    for biz in user.get("businesses", []):
        meta = find_item(BUSINESSES, biz["id"])
        if not meta: continue
        last = datetime.fromisoformat(biz["last_collected"])
        hours = (now - last).total_seconds() / 3600
        # accrues per hour, capped at 48 hours to force regular play
        accrued_hours = min(48, hours)
        income = int((meta["daily_income"] / 24) * accrued_hours)
        # inspection roll
        if random.random() < meta["inspection_risk"] * (accrued_hours / 24):
            fine = random.randint(meta["fine_min"], meta["fine_max"])
            total_fines += fine
            events.append({"biz": meta["name"], "type": "fine", "amount": fine, "msg": f"{meta['name']}: Inspection failed. Fine ${fine}."})
        else:
            events.append({"biz": meta["name"], "type": "income", "amount": income, "msg": f"{meta['name']}: +${income} collected."})
        total_income += income
        biz["last_collected"] = now.isoformat()
    net = total_income - total_fines
    new_money = max(0, user["money"] + net)
    user["stats"]["business_income"] += total_income
    user["stats"]["fines_paid"] += total_fines
    await db.users.update_one({"id": user["id"]}, {"$set": {"businesses": user["businesses"], "money": new_money, "stats": user["stats"]}})
    return {"income": total_income, "fines": total_fines, "net": net, "money": new_money, "events": events}

# ========== BANK ==========
@api.post("/bank/deposit")
async def bank_deposit(data: BankIn, request: Request):
    user = await get_current_user(request)
    if data.amount <= 0 or user["money"] < data.amount:
        raise HTTPException(400, "Invalid amount")
    await db.users.update_one({"id": user["id"]}, {"$inc": {"money": -data.amount, "bank": data.amount}})
    return {"money": user["money"] - data.amount, "bank": user.get("bank", 0) + data.amount}

@api.post("/bank/withdraw")
async def bank_withdraw(data: BankIn, request: Request):
    user = await get_current_user(request)
    if data.amount <= 0 or user.get("bank", 0) < data.amount:
        raise HTTPException(400, "Invalid amount")
    await db.users.update_one({"id": user["id"]}, {"$inc": {"money": data.amount, "bank": -data.amount}})
    return {"money": user["money"] + data.amount, "bank": user.get("bank", 0) - data.amount}

# ========== PVP RAID ==========
@api.get("/pvp/targets")
async def pvp_targets(request: Request, limit: int = 20):
    user = await get_current_user(request)
    targets = await db.users.find(
        {"id": {"$ne": user["id"]}, "specialization": {"$ne": None}, "properties": {"$ne": []}},
        {"_id": 0, "password_hash": 0, "email": 0}
    ).limit(limit).to_list(limit)
    result = []
    for t in targets:
        for p in t.get("properties", []):
            meta = find_item(PROPERTIES, p["id"])
            if not meta: continue
            result.append({
                "username": t["username"], "level": t["level"], "specialization": t["specialization"],
                "property_id": p["id"], "property_name": meta["name"], "property_tier": meta["tier"],
                "security": p["security"], "estimated_loot": p.get("cash_stash", 0) + meta["tier"] * 500
            })
    return result

@api.post("/pvp/raid")
async def pvp_raid(data: RaidIn, request: Request):
    attacker = await get_current_user(request)
    if attacker["level"] < 5:
        raise HTTPException(400, "Level 5+ required for PvP raids")
    if attacker["health"] < 40:
        raise HTTPException(400, "Health too low")
    defender = await db.users.find_one({"username": data.target_username})
    if not defender or defender["id"] == attacker["id"]:
        raise HTTPException(404, "Target not found")
    prop = next((p for p in defender.get("properties", []) if p["id"] == data.property_id), None)
    if not prop:
        raise HTTPException(404, "Property not found on target")
    prop_meta = find_item(PROPERTIES, data.property_id)

    # attack power: attacker level + crew skill + weapon
    weapon_id = attacker["equipped"].get("primary") or attacker["equipped"].get("secondary")
    weapon = find_item(WEAPONS, weapon_id) if weapon_id else None
    attack_power = attacker["level"] * 3 + (weapon["damage"] if weapon else 10)
    for cid in data.crew_ids:
        if cid in attacker["hired_crew"]:
            npc = find_item(NPCS, cid)
            if npc: attack_power += npc["skill"] * 0.6
    # defense power: security + defender level
    defense_power = prop["security"] + defender["level"] * 2 + prop_meta["tier"] * 8

    # roll
    total = attack_power + defense_power
    success_prob = attack_power / total if total > 0 else 0.5
    # cap to keep it interesting
    success_prob = max(0.1, min(0.85, success_prob))
    won = random.random() < success_prob

    events = []
    if won:
        # attacker steals cash_stash + a bonus
        stash = prop.get("cash_stash", 0)
        base_loot = int(prop_meta["tier"] * 800 + stash * 0.6)
        loot = max(400, min(base_loot, defender["money"] // 4 + stash))
        events.append(f"Breached {prop_meta['name']}. Guards down.")
        events.append(f"Extracted ${loot} in cash and valuables.")
        hp_loss = random.randint(10, 25)
        events.append(f"Took {hp_loss} damage during exchange.")
        # apply
        attacker["money"] += loot
        attacker["health"] = max(0, attacker["health"] - hp_loss)
        attacker["reputation"] += 8
        attacker["heat"] = min(100, attacker["heat"] + 15)
        # defender loses cash
        defender_money_loss = min(loot, defender["money"] + stash)
        new_def_money = max(0, defender["money"] - (defender_money_loss - stash) if stash < loot else defender["money"])
        prop["cash_stash"] = max(0, stash - loot)
        await db.users.update_one({"id": defender["id"]}, {"$set": {"money": new_def_money, "properties": defender["properties"]}})
        result = "RAID SUCCESSFUL"
    else:
        # attacker loses resources
        loss = random.randint(500, 2500) + attacker["level"] * 50
        loss = min(loss, attacker["money"])
        hp_loss = random.randint(25, 55)
        events.append(f"Security repelled the assault at {prop_meta['name']}.")
        events.append(f"Lost ${loss} in equipment and bribes.")
        events.append(f"Took {hp_loss} damage.")
        attacker["money"] = max(0, attacker["money"] - loss)
        attacker["health"] = max(0, attacker["health"] - hp_loss)
        attacker["reputation"] = max(0, attacker["reputation"] - 3)
        attacker["heat"] = min(100, attacker["heat"] + 25)
        # defender gets a small bonus for defending
        await db.users.update_one({"id": defender["id"]}, {"$inc": {"reputation": 4, "stats.raids_survived": 1}})
        result = "RAID FAILED"

    await db.users.update_one({"id": attacker["id"]}, {"$set": {"money": attacker["money"], "health": attacker["health"], "reputation": attacker["reputation"], "heat": attacker["heat"]}})
    updated = await db.users.find_one({"id": attacker["id"]})
    updated.pop("_id", None); updated.pop("password_hash", None)

    # log
    await db.raids.insert_one({"id": str(uuid.uuid4()), "attacker": attacker["username"], "defender": defender["username"], "property_id": data.property_id, "result": result, "timestamp": datetime.now(timezone.utc).isoformat()})
    return {"result": result, "events": events, "success_prob": round(success_prob, 2), "user": updated}

@api.get("/pvp/history")
async def pvp_history(request: Request, limit: int = 20):
    user = await get_current_user(request)
    raids = await db.raids.find({"$or": [{"attacker": user["username"]}, {"defender": user["username"]}]}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return raids

@api.get("/")
async def root():
    return {"game": "The Law of Silence", "status": "online"}

app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    log.info("The Law of Silence — backend online.")

@app.on_event("shutdown")
async def shutdown():
    client.close()
