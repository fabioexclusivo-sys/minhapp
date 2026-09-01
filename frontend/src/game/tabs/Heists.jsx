import { useEffect, useState } from "react";
import { useAuth } from "../../AuthContext";
import { api, fmtDetail, fmtMoney } from "../../api";
import { toast } from "sonner";

const TYPE_COLORS = { quick: "#10B981", street: "#38BDF8", heist: "#F59E0B", major: "#EF4444" };

export default function Heists() {
  const { user, catalog, refresh } = useAuth();
  const [selected, setSelected] = useState(null);
  const [crewSel, setCrewSel] = useState([]);
  const [vehSel, setVehSel] = useState(user.equipped.vehicle || "starter");
  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState([]);
  const [outcome, setOutcome] = useState(null);
  const [history, setHistory] = useState([]);
  const [cdLeft, setCdLeft] = useState(0);

  useEffect(() => { (async () => { try { const { data } = await api.get("/heist/history"); setHistory(data); } catch {} })(); }, []);
  useEffect(() => {
    if (!user.last_heist_at) return;
    const t = setInterval(() => {
      const elapsed = (Date.now() - new Date(user.last_heist_at).getTime()) / 1000;
      const cdMap = { quick: 90, street: 240, heist: 600, major: 1200 };
      const lastType = history[0]?.heist_id ? (catalog?.heists.find(h => h.id === history[0].heist_id)?.type || "quick") : "quick";
      const cd = cdMap[lastType] || 180;
      setCdLeft(Math.max(0, Math.ceil(cd - elapsed)));
    }, 1000);
    return () => clearInterval(t);
  }, [user.last_heist_at, history, catalog]);

  if (!catalog) return null;

  const start = async () => {
    if (!selected) return;
    setRunning(true); setEvents([]); setOutcome(null);
    try {
      const { data } = await api.post("/heist/run", { heist_id: selected.id, crew_ids: crewSel, vehicle_id: vehSel });
      // stream events
      for (let i = 0; i < data.events.length; i++) {
        await new Promise(r => setTimeout(r, 600));
        setEvents(prev => [...prev, data.events[i]]);
      }
      await new Promise(r => setTimeout(r, 400));
      setOutcome({ outcome: data.outcome, rewards: data.rewards });
      await refresh();
      const { data: h } = await api.get("/heist/history"); setHistory(h);
    } catch (e) { toast.error(fmtDetail(e.response?.data?.detail)); setRunning(false); }
  };

  const closeOutcome = () => { setRunning(false); setOutcome(null); setEvents([]); setSelected(null); };

  const outcomeClass = { "PERFECT SUCCESS": "outcome-perfect", "SUCCESS": "outcome-success", "PARTIAL SUCCESS": "outcome-partial", "FAILED": "outcome-failed", "DISASTER": "outcome-disaster" };

  const toggleCrew = (id) => setCrewSel(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  return (
    <div style={{ display: "grid", gap: 20 }}>
      {!running && !selected && <>
        <div>
          <h2 className="font-display" style={{ fontSize: 24, color: "#fff", letterSpacing: "0.1em", marginBottom: 4 }}>OPERATIONS</h2>
          <div style={{ color: "#64748B", fontSize: 13 }}>Prepare well. During the operation you observe — the events unfold based on your crew, gear and specialization.</div>
        </div>
        {cdLeft > 0 && <div style={{ padding: 14, background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.4)", color: "#EF4444", fontFamily: "Orbitron", fontSize: 12, letterSpacing: "0.15em" }} data-testid="cooldown-banner">
          ⏱ COOLDOWN ACTIVE · {Math.floor(cdLeft / 60)}m {cdLeft % 60}s remaining before your next operation
        </div>}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 12 }}>
          {catalog.heists.map(h => {
            const locked = user.level < h.min_level;
            const color = TYPE_COLORS[h.type];
            return (
              <div key={h.id} className="card-glow" data-testid={`heist-${h.id}`} onClick={() => !locked && setSelected(h)} style={{ padding: 18, opacity: locked ? 0.4 : 1, cursor: locked ? "not-allowed" : "pointer", borderColor: `${color}55` }}>
                <div className="label-caps" style={{ color }}>{h.type.toUpperCase()} · {h.district.replace("_", " ").toUpperCase()}</div>
                <div className="font-display" style={{ color: "#fff", fontSize: 18, marginTop: 4, letterSpacing: "0.06em" }}>{h.name.toUpperCase()}</div>
                <div style={{ marginTop: 10, fontSize: 12, color: "#94a3b8" }}>Difficulty {h.difficulty}/10 · Min Crew {h.min_crew}</div>
                <div style={{ marginTop: 4, fontSize: 12 }}>Reward: <span className="font-display neon-gold">{fmtMoney(h.reward_min)} – {fmtMoney(h.reward_max)}</span></div>
                <div style={{ marginTop: 4, fontSize: 11, color: locked ? "#EF4444" : "#64748B" }}>{locked ? `LOCKED · LVL ${h.min_level}` : `MIN LEVEL ${h.min_level}`}</div>
              </div>
            );
          })}
        </div>

        <div className="card-glow" style={{ padding: 20 }}>
          <div className="label-caps neon-purple" style={{ marginBottom: 10 }}>HEIST HISTORY</div>
          {history.length === 0 ? <div style={{ color: "#64748B", fontSize: 13 }}>No operations yet.</div> :
            <div style={{ display: "grid", gap: 6 }}>
              {history.slice(0, 10).map(o => (
                <div key={o.id} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #1a2436", fontSize: 12 }}>
                  <span style={{ color: "#fff" }}>{o.heist_name}</span>
                  <span className={outcomeClass[o.outcome]} style={{ fontFamily: "Orbitron", fontSize: 10 }}>{o.outcome}</span>
                  <span className="font-display neon-gold">{fmtMoney(o.cash)}</span>
                </div>
              ))}
            </div>}
        </div>
      </>}

      {!running && selected && <div className="hologram-border card-glow" style={{ padding: 24 }}>
        <button data-testid="back-to-heists" onClick={() => setSelected(null)} className="btn-outline" style={{ padding: "6px 12px", fontSize: 11, marginBottom: 16 }}>← BACK</button>
        <div className="label-caps neon-cyan">PREPARE OPERATION</div>
        <h2 className="font-display" style={{ fontSize: 28, color: "#fff", letterSpacing: "0.08em" }}>{selected.name.toUpperCase()}</h2>
        <div style={{ color: "#94a3b8", fontSize: 13, marginBottom: 20 }}>Reward: <span className="neon-gold">{fmtMoney(selected.reward_min)} – {fmtMoney(selected.reward_max)}</span> · Difficulty {selected.difficulty}/10 · Heat +{selected.heat_gain}</div>

        <div style={{ marginBottom: 20 }}>
          <div className="label-caps" style={{ marginBottom: 8 }}>SELECT CREW (min {selected.min_crew})</div>
          {user.hired_crew.length === 0 && <div style={{ color: "#EF4444", fontSize: 12 }}>No crew hired. Visit the Crew tab first.</div>}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 8 }}>
            {user.hired_crew.map(cid => {
              const n = catalog.npcs.find(x => x.id === cid); if (!n) return null;
              const sel = crewSel.includes(cid);
              const color = catalog.specializations.find(s => s.id === n.spec)?.color;
              return (
                <button data-testid={`select-crew-${cid}`} key={cid} onClick={() => toggleCrew(cid)} style={{ padding: 12, border: `1px solid ${sel ? color : "#1a2436"}`, background: sel ? `${color}15` : "transparent", textAlign: "left" }}>
                  <div className="font-display" style={{ color: "#fff", fontSize: 13 }}>{n.name}</div>
                  <div className="label-caps" style={{ color }}>{n.spec}</div>
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <div className="label-caps" style={{ marginBottom: 8 }}>GETAWAY VEHICLE</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 8 }}>
            {user.vehicles.map(v => {
              const meta = catalog.vehicles.find(x => x.id === v.id); if (!meta) return null;
              const sel = vehSel === v.id;
              return (
                <button data-testid={`select-veh-${v.id}`} key={v.instance_id || v.id} onClick={() => setVehSel(v.id)} style={{ padding: 12, border: `1px solid ${sel ? "#00F0FF" : "#1a2436"}`, background: sel ? "rgba(0,240,255,0.08)" : "transparent", textAlign: "left" }}>
                  <div className="font-display" style={{ color: "#fff", fontSize: 13 }}>{meta.name}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8" }}>ESC {meta.escape} · CND {v.condition}%</div>
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ padding: 12, background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.3)", fontSize: 12, color: "#F59E0B", marginBottom: 16 }}>
          ⚠ CREW WARNING · Crew specialization can affect operation outcome. Diverse teams reduce risk.
        </div>

        <button data-testid="run-operation" onClick={start} disabled={crewSel.length < selected.min_crew || cdLeft > 0} className="btn-primary" style={{ width: "100%", padding: 14, fontSize: 14 }}>{cdLeft > 0 ? `⏱ COOLDOWN ${Math.floor(cdLeft/60)}m ${cdLeft%60}s` : "▶ RUN OPERATION"}</button>
      </div>}

      {running && <div className="hologram-border card-glow" style={{ padding: 24 }} data-testid="operation-running">
        <div className="label-caps neon-cyan">OPERATION IN PROGRESS</div>
        <h2 className="font-display" style={{ fontSize: 24, color: "#fff", margin: "6px 0 16px", letterSpacing: "0.08em" }}>{selected?.name.toUpperCase()}</h2>
        <div style={{ maxHeight: 360, overflowY: "auto", padding: 16, background: "#04050a", border: "1px solid #1a2436", fontFamily: "IBM Plex Sans", fontSize: 13, display: "grid", gap: 6 }}>
          {events.map((e, i) => (
            <div key={i} className={`ticker-line event-${e.cat || "info"}`}><span style={{ color: "#64748B", fontFamily: "Orbitron", fontSize: 11 }}>{e.time}</span> · {e.msg}</div>
          ))}
          {events.length === 0 && <div style={{ color: "#64748B" }}>Initializing operation...</div>}
        </div>

        {outcome && <div style={{ marginTop: 20, padding: 24, border: `2px solid ${outcome.outcome === "PERFECT SUCCESS" ? "#F59E0B" : outcome.outcome === "SUCCESS" ? "#10B981" : outcome.outcome === "PARTIAL SUCCESS" ? "#38BDF8" : "#EF4444"}` }} data-testid="operation-outcome">
          <div className={`font-display ${outcomeClass[outcome.outcome]}`} style={{ fontSize: 30, fontWeight: 900, letterSpacing: "0.15em", textAlign: "center" }}>{outcome.outcome}</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(120px,1fr))", gap: 14, marginTop: 20 }}>
            <div><div className="label-caps">Cash</div><div className="font-display neon-gold" style={{ fontSize: 20 }}>+{fmtMoney(outcome.rewards.cash)}</div></div>
            <div><div className="label-caps">XP</div><div className="font-display neon-cyan" style={{ fontSize: 20 }}>+{outcome.rewards.xp}</div></div>
            <div><div className="label-caps">Rep</div><div className="font-display neon-purple" style={{ fontSize: 20 }}>{outcome.rewards.rep >= 0 ? "+" : ""}{outcome.rewards.rep}</div></div>
            <div><div className="label-caps">Heat</div><div className="font-display neon-red" style={{ fontSize: 20 }}>+{outcome.rewards.heat}</div></div>
            <div><div className="label-caps">HP Loss</div><div className="font-display" style={{ fontSize: 20, color: "#EF4444" }}>-{outcome.rewards.hp_loss}</div></div>
            <div><div className="label-caps">Enemies Killed</div><div className="font-display" style={{ fontSize: 20 }}>{outcome.rewards.enemies_killed}</div></div>
          </div>
          <button data-testid="close-outcome" onClick={closeOutcome} className="btn-primary" style={{ marginTop: 20, width: "100%", padding: 12 }}>CONTINUE</button>
        </div>}
      </div>}
    </div>
  );
}
