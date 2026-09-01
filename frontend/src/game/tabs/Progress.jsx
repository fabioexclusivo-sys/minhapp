import { useEffect, useState } from "react";
import { useAuth } from "../../AuthContext";
import { api, fmtMoney } from "../../api";

export default function Progress() {
  const { user } = useAuth();
  const [rankings, setRankings] = useState([]);
  useEffect(() => { (async () => { try { const { data } = await api.get("/rankings"); setRankings(data); } catch {} })(); }, []);

  const s = user.stats;
  const stats = [
    { label: "Level", value: user.level },
    { label: "XP", value: user.xp },
    { label: "Money", value: fmtMoney(user.money) },
    { label: "Reputation", value: user.reputation },
    { label: "Heat", value: `${user.heat}%` },
    { label: "Ops Completed", value: s.ops_completed },
    { label: "Ops Failed", value: s.ops_failed },
    { label: "Enemies Killed", value: s.enemies_killed },
    { label: "Times Shot", value: s.times_shot },
    { label: "Crew Lost", value: s.crew_lost },
    { label: "Total Earnings", value: fmtMoney(s.total_earnings) },
    { label: "Total Spent", value: fmtMoney(s.total_spent) },
  ];

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div>
        <h2 className="font-display" style={{ fontSize: 24, color: "#fff", letterSpacing: "0.1em", marginBottom: 4 }}>PROGRESS</h2>
        <div style={{ color: "#64748B", fontSize: 13 }}>Your journey through Neon City. Every operation counts.</div>
      </div>

      <div className="card-glow" style={{ padding: 22 }}>
        <div className="label-caps neon-cyan" style={{ marginBottom: 12 }}>YOUR STATS</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 12 }}>
          {stats.map(x => (
            <div key={x.label} style={{ padding: 12, border: "1px solid #1a2436" }}>
              <div className="label-caps">{x.label}</div>
              <div className="font-display" style={{ fontSize: 18, color: "#fff", marginTop: 4 }}>{x.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card-glow" style={{ padding: 22 }}>
        <div className="label-caps neon-pink" style={{ marginBottom: 12 }}>GLOBAL RANKINGS</div>
        {rankings.length === 0 ? <div style={{ color: "#64748B", fontSize: 13 }}>Rankings will populate as operators level up.</div> :
          <div style={{ display: "grid", gap: 4 }}>
            <div style={{ display: "grid", gridTemplateColumns: "40px 1fr 80px 100px 120px", gap: 10, padding: "6px 8px", borderBottom: "1px solid #1a2436" }} className="label-caps">
              <span>#</span><span>Operator</span><span>Level</span><span>Rep</span><span>Earnings</span>
            </div>
            {rankings.map((r, i) => (
              <div key={i} data-testid={`rank-${i}`} style={{ display: "grid", gridTemplateColumns: "40px 1fr 80px 100px 120px", gap: 10, padding: "8px", background: r.username === user.username ? "rgba(0,240,255,0.08)" : "transparent", fontSize: 13 }}>
                <span className="font-display neon-gold">#{i + 1}</span>
                <span style={{ color: "#fff" }}>{r.username} <span style={{ color: "#64748B", fontSize: 10 }}>· {r.specialization}</span></span>
                <span className="font-display">{r.level}</span>
                <span className="neon-purple font-display">{r.reputation}</span>
                <span className="neon-gold font-display">{fmtMoney(r.total_earnings)}</span>
              </div>
            ))}
          </div>}
      </div>
    </div>
  );
}
