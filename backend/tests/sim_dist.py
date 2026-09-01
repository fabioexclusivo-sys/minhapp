"""Offline Monte-Carlo of simulate_heist to measure the real outcome distribution."""
import sys
from collections import Counter

sys.path.insert(0, "/app/backend")
import server  # noqa


def run(heist_id, n=4000, heat=0, rep=0, crew=0, weapon=None, armor=None):
    heist = server.find_item(server.HEISTS, heist_id)
    crew_ids = [c["id"] for c in server.NPCS[:crew]]
    user = {
        "specialization": "shooter",
        "equipped": {"primary": weapon, "secondary": None, "melee": None, "armor": armor, "vehicle": "starter"},
        "vehicles": [{"id": "starter", "condition": 100, "instance_id": "s1"}],
        "reputation": rep,
        "heat": heat,
    }
    c = Counter()
    cash = 0
    for _ in range(n):
        r = server.simulate_heist(user, heist, crew_ids, "starter")
        c[r["outcome"]] += 1
        cash += r["rewards"]["cash"]
    good = c["PERFECT SUCCESS"] + c["SUCCESS"]
    print(f"{heist_id} diff={heist['difficulty']} heat={heat} crew={crew} weapon={weapon} -> "
          f"non-success={1 - good / n:.1%} avg_cash=${cash // n} {dict(c)}")


run("op_atm")
run("op_convenience")
run("op_atm", heat=60)
run("op_atm", weapon="w_glock", crew=2)
run("op_street_drug", crew=1)
run("op_jewelry", crew=2)
run("op_armored", crew=3)
run("op_casino", crew=4)
