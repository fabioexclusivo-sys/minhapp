import { useAuth } from "../../AuthContext";
import { api, fmtDetail } from "../../api";
import { toast } from "sonner";

const SLOTS = ["primary", "secondary", "melee", "armor", "vehicle"];

export default function Inventory() {
  const { user, catalog, setUser, refresh } = useAuth();
  if (!catalog) return null;

  const equip = async (item_id, slot) => {
    try { await api.post("/player/equip", { item_id, slot }); const u = await refresh(); setUser(u); toast.success("Equipped."); }
    catch (e) { toast.error(fmtDetail(e.response?.data?.detail)); }
  };

  const repair = async (v) => {
    try { const { data } = await api.post("/player/repair", { vehicle_id: v.id }); await refresh(); toast.success(`Repaired for $${data.cost}`); }
    catch (e) { toast.error(fmtDetail(e.response?.data?.detail)); }
  };

  const findW = (id) => catalog.weapons.find(w => w.id === id);
  const findA = (id) => catalog.armors.find(a => a.id === id);
  const findV = (id) => catalog.vehicles.find(v => v.id === id);

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div>
        <h2 className="font-display" style={{ fontSize: 24, color: "#fff", letterSpacing: "0.1em", marginBottom: 4 }}>INVENTORY</h2>
        <div style={{ color: "#64748B", fontSize: 13 }}>Everything you own. One slot per category — equipping a new item replaces the old.</div>
      </div>

      <div className="card-glow" style={{ padding: 20 }}>
        <div className="label-caps neon-cyan" style={{ marginBottom: 12 }}>EQUIPPED LOADOUT</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 12 }}>
          {SLOTS.map(s => {
            const id = user.equipped[s];
            let item = null;
            if (s === "armor") item = findA(id); else if (s === "vehicle") item = findV(id); else item = findW(id);
            return (
              <div key={s} data-testid={`slot-${s}`} style={{ border: "1px solid #1a2436", padding: 14, background: id ? "rgba(0,240,255,0.04)" : "transparent" }}>
                <div className="label-caps neon-pink">{s.toUpperCase()}</div>
                <div className="font-display" style={{ fontSize: 15, color: id ? "#fff" : "#475569", marginTop: 4 }}>{item ? item.name.toUpperCase() : "— EMPTY —"}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card-glow" style={{ padding: 20 }}>
        <div className="label-caps neon-cyan" style={{ marginBottom: 12 }}>WEAPONS OWNED</div>
        {user.weapons.length === 0 && <div style={{ color: "#64748B", fontSize: 13 }}>No weapons yet. Visit Arsenal.</div>}
        <div style={{ display: "grid", gap: 8 }}>
          {user.weapons.map(w => {
            const meta = findW(w.id); if (!meta) return null;
            const equipped = user.equipped[meta.slot] === w.id;
            return (
              <div key={w.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: 12, border: `1px solid ${equipped ? "rgba(0,240,255,0.5)" : "#1a2436"}` }}>
                <div>
                  <div className="font-display" style={{ color: "#fff", fontSize: 14 }}>{meta.name} <span style={{ color: "#64748B", fontSize: 11 }}>× {w.qty}</span></div>
                  <div style={{ fontSize: 11, color: "#94a3b8" }}>DMG {meta.damage} · ACC {meta.accuracy} · REL {meta.reliability}</div>
                </div>
                <button data-testid={`equip-w-${w.id}`} onClick={() => equip(w.id, meta.slot)} className={equipped ? "btn-outline" : "btn-primary"} style={{ padding: "8px 14px", fontSize: 11 }} disabled={equipped}>{equipped ? "EQUIPPED" : "EQUIP"}</button>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card-glow" style={{ padding: 20 }}>
        <div className="label-caps neon-cyan" style={{ marginBottom: 12 }}>ARMOR OWNED</div>
        {user.armors.length === 0 && <div style={{ color: "#64748B", fontSize: 13 }}>No armor yet. Visit Arsenal.</div>}
        <div style={{ display: "grid", gap: 8 }}>
          {user.armors.map(a => {
            const meta = findA(a.id); if (!meta) return null;
            const eq = user.equipped.armor === a.id;
            return (
              <div key={a.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: 12, border: `1px solid ${eq ? "rgba(0,240,255,0.5)" : "#1a2436"}` }}>
                <div><div className="font-display" style={{ color: "#fff" }}>{meta.name} × {a.qty}</div><div style={{ fontSize: 11, color: "#94a3b8" }}>-{meta.damage_reduction}% damage taken</div></div>
                <button data-testid={`equip-a-${a.id}`} onClick={() => equip(a.id, "armor")} className={eq ? "btn-outline" : "btn-primary"} style={{ padding: "8px 14px", fontSize: 11 }} disabled={eq}>{eq ? "EQUIPPED" : "EQUIP"}</button>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card-glow" style={{ padding: 20 }}>
        <div className="label-caps neon-cyan" style={{ marginBottom: 12 }}>VEHICLES OWNED</div>
        <div style={{ display: "grid", gap: 8 }}>
          {user.vehicles.map(v => {
            const meta = findV(v.id); if (!meta) return null;
            const eq = user.equipped.vehicle === v.id;
            const dmg = 100 - v.condition;
            return (
              <div key={v.instance_id || v.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: 12, border: `1px solid ${eq ? "rgba(0,240,255,0.5)" : "#1a2436"}` }}>
                <div>
                  <div className="font-display" style={{ color: "#fff" }}>{meta.name}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8" }}>SPD {meta.speed} · HND {meta.handling} · ARM {meta.armor} · ESC {meta.escape} · CND {v.condition}%</div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {dmg > 0 && <button data-testid={`repair-${v.id}`} onClick={() => repair(v)} className="btn-outline" style={{ padding: "8px 14px", fontSize: 11 }}>REPAIR (${dmg * 50})</button>}
                  <button data-testid={`equip-v-${v.id}`} onClick={() => equip(v.id, "vehicle")} className={eq ? "btn-outline" : "btn-primary"} style={{ padding: "8px 14px", fontSize: 11 }} disabled={eq}>{eq ? "IN USE" : "USE"}</button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card-glow" style={{ padding: 20 }}>
        <div className="label-caps neon-cyan" style={{ marginBottom: 12 }}>AMMUNITION</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 10 }}>
          {Object.entries(user.ammo).map(([k, v]) => (
            <div key={k} style={{ padding: 12, border: "1px solid #1a2436" }}>
              <div className="label-caps">{k}</div>
              <div className="font-display" style={{ fontSize: 20, color: v > 0 ? "#fff" : "#475569" }}>{v}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
