import { useAuth } from "../../AuthContext";
import { api, fmtDetail, fmtMoney } from "../../api";
import { toast } from "sonner";

export default function Crew() {
  const { user, catalog, refresh } = useAuth();
  if (!catalog) return null;

  const specColor = (s) => catalog.specializations.find(x => x.id === s)?.color || "#94a3b8";

  const hire = async (npc) => {
    try { await api.post("/player/hire-crew", { npc_id: npc.id }); await refresh(); toast.success(`${npc.name} joined your crew.`); }
    catch (e) { toast.error(fmtDetail(e.response?.data?.detail)); }
  };

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div>
        <h2 className="font-display" style={{ fontSize: 24, color: "#fff", letterSpacing: "0.1em", marginBottom: 4 }}>CREW</h2>
        <div style={{ color: "#64748B", fontSize: 13 }}>Build a balanced team. Specializations stack. A diverse crew survives more heists.</div>
      </div>

      <div className="card-glow" style={{ padding: 20 }}>
        <div className="label-caps neon-cyan" style={{ marginBottom: 12 }}>YOUR ROSTER ({user.hired_crew.length})</div>
        {user.hired_crew.length === 0 ? <div style={{ color: "#64748B", fontSize: 13 }}>No crew members yet. Recruit below.</div> :
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 10 }}>
            {user.hired_crew.map(id => {
              const n = catalog.npcs.find(x => x.id === id); if (!n) return null;
              return (
                <div key={id} style={{ padding: 14, border: `1px solid ${specColor(n.spec)}55` }}>
                  <div className="font-display" style={{ color: "#fff", fontSize: 16 }}>{n.name.toUpperCase()}</div>
                  <div className="label-caps" style={{ color: specColor(n.spec) }}>{n.spec}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 4 }}>SKILL {n.skill} · CUT {n.cut}%</div>
                </div>
              );
            })}
          </div>}
      </div>

      <div>
        <div className="label-caps neon-pink" style={{ marginBottom: 10 }}>RECRUITMENT POOL</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 12 }}>
          {catalog.npcs.filter(n => !user.hired_crew.includes(n.id)).map(n => (
            <div key={n.id} className="card-glow" style={{ padding: 16, borderColor: `${specColor(n.spec)}44` }}>
              <div className="font-display" style={{ color: "#fff", fontSize: 16 }}>{n.name.toUpperCase()}</div>
              <div className="label-caps" style={{ color: specColor(n.spec) }}>{n.spec}</div>
              <div style={{ fontSize: 11, color: "#94a3b8", margin: "8px 0" }}>SKILL {n.skill} · CUT {n.cut}%</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div className="font-display neon-gold">{fmtMoney(n.hire_cost)}</div>
                <button data-testid={`hire-${n.id}`} onClick={() => hire(n)} disabled={user.money < n.hire_cost} className="btn-primary" style={{ padding: "6px 12px", fontSize: 11 }}>HIRE</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
