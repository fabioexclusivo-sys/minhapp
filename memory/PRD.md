# THE LAW OF SILENCE — PRD

## Concept
Online browser crime/heist progression game (Omerta-inspired, cyberpunk Neon City aesthetic). Player creates an account (email + username + password JWT), picks avatar + specialization, then grinds to build a criminal empire through operations, PvP, properties, and businesses.

## Stack
- Frontend: React (CRA) + Framer Motion + Lucide icons + Sonner toasts
- Backend: FastAPI + Motor (async MongoDB) + PyJWT + bcrypt
- DB: MongoDB (users, operations, raids collections)

## Core loop (implemented)
Signup → Character Select (avatar + spec) → Enter Neon City → Grind (heists, businesses) → Buy weapons/vehicles/armor/ammo/properties/businesses → Hire crew → Run heists (auto random events + outcomes) → Upgrade → PvP raids

## What's built (Feb 2026 — v1)
- **Auth**: JWT bearer, email/username/password signup, login, /me
- **Character**: 6 avatars × 6 specializations (Hacker/Shooter/Driver/Infiltrator/Negotiator/Technician). Only visual + spec bonus in heists.
- **HUD + BottomNav (11 tabs)**: Money, XP bar, HP bar, Heat, Rep, Level always visible
- **Arsenal**: 21 weapons across 7 categories with Damage/Accuracy/Reliability, 3 armors, ammo shop
- **Garage**: 13 vehicles (compact/sport/muscle/super/bike/armored/utility/special) each with unique heist utility
- **Inventory**: equipment slots (primary/secondary/melee/armor/vehicle), qty tracking, repair, equip/unequip
- **Crew**: 10 hireable NPCs with specializations & skill
- **Heists**: 11 operations across 4 tiers (quick/street/heist/major), server-side random event simulation, 5 outcome tiers (PERFECT SUCCESS → DISASTER), animated event ticker
- **Assets**: 5 properties (safehouse tiers with storage + security), 5 businesses (car wash → casino) with daily income + inspection risk (fines), Bank deposit/withdraw
- **PvP**: raid other players' properties. Attack power vs defense = success probability. Loot on success, resource loss on failure.
- **Rankings**: global leaderboard sorted by level, rep, earnings
- **Map**: 8 districts of Neon City
- **Progress**: stats + rankings

## Balance / Grind (Feb 2026 v1)
- Starting cash: **$800** (hard start)
- Rewards nerfed ~40% vs prototype; prices boosted ~40%. Estimated 4-6 weeks of daily play to reach End Game.
- Businesses accrue income hourly (cap 48h) to force daily engagement.
- Inspection rolls per collect; risk scales with time since last collect.
- PvP requires level 5+, health 40+.

## Reference images integration
- Character Select: reference cards image as top banner
- Arsenal: reference tiers image as banner
- Garage: reference cards image as banner
- Map: NO reference image (removed per user feedback) — pure UI

## Test credentials (dev)
- Create via `/api/auth/signup` — see `/app/memory/test_credentials.md`
- Sample: `tester@lawofsilence.com` / `test1234` (spec=hacker, avatar=av_1)

## Backlog (P1)
- Crew PvE raids on player properties (auto police/gang raids on tick, defenders lose stash if security low)
- Property upgrades: security → 100 cap, add car/weapon storage upgrades
- Business auto-collect timer + upgrade tiers
- Real-time cooperative heists between friends (multiplayer session)
- Character avatar portraits with generated cyberpunk art (Gemini Nano Banana)
- Achievements + daily missions
- Chat between players / crew invites
- Anti-abuse: PvP cooldowns, protection windows for new players

## Backlog (P2)
- Sound/music
- Mobile PWA install
- Push notifications when raided
