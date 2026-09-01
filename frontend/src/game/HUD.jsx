import { useAuth } from "../AuthContext";
import { fmtMoney } from "../api";
import { LogOut } from "lucide-react";

function Bar({ value, max = 100, color, label, testid }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div data-testid={testid} style={{ minWidth: 90 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, letterSpacing: "0.25em", color: "#64748B", marginBottom: 3 }}><span>{label}</span><span style={{ color: "#dbe4ee" }}>{Math.round(value)}{max === 100 ? "%" : `/${max}`}</span></div>
      <div className="bar"><div className="bar-fill" style={{ width: `${pct}%`, background: color, boxShadow: `0 0 8px ${color}` }}></div></div>
    </div>
  );
}

export default function HUD() {
  const { user, catalog, logout } = useAuth();
  const spec = catalog?.specializations.find(s => s.id === user.specialization);
  const xpMax = 1000 + (user.level - 1) * 500;

  return (
    <div style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 50, background: "rgba(3,3,8,0.92)", backdropFilter: "blur(10px)", borderBottom: "1px solid rgba(0,240,255,0.2)", padding: "12px 20px" }} data-testid="hud">
      <div style={{ maxWidth: 1280, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div className="font-display" style={{ fontSize: 14, fontWeight: 900, color: "#fff", letterSpacing: "0.2em" }}>
            LAW OF <span style={{ background: "linear-gradient(90deg,#00F0FF,#EC4899)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>SILENCE</span>
          </div>
          <div style={{ borderLeft: "1px solid #1a2436", paddingLeft: 14, fontSize: 11, letterSpacing: "0.15em" }} data-testid="hud-user">
            <div className="font-display" style={{ color: spec?.color || "#00F0FF", fontWeight: 700 }}>{user.username.toUpperCase()}</div>
            <div style={{ color: "#64748B", fontSize: 10 }}>LVL {user.level} · {spec?.name.toUpperCase()}</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap" }}>
          <div data-testid="hud-money" className="font-display neon-green" style={{ fontSize: 18, fontWeight: 800 }}>{fmtMoney(user.money)}</div>
          <Bar testid="hud-xp" value={user.xp} max={xpMax} color="#38BDF8" label="XP" />
          <Bar testid="hud-hp" value={user.health} color={user.health < 30 ? "#EF4444" : "#22C55E"} label="HP" />
          <Bar testid="hud-heat" value={user.heat} color="#EF4444" label="HEAT" />
          <div style={{ fontSize: 11, textAlign: "right" }} data-testid="hud-rep"><div className="label-caps">REP</div><div className="font-display neon-purple" style={{ fontSize: 16 }}>{user.reputation}</div></div>
          <button data-testid="logout-btn" onClick={logout} className="btn-outline" style={{ padding: "6px 12px", fontSize: 10 }} title="Log out"><LogOut size={14} /></button>
        </div>
      </div>
    </div>
  );
}
