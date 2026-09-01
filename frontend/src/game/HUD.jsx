import { useAuth } from "../AuthContext";
import { Bell, Mail, Settings, Power, DollarSign, Landmark, Flame, Crown, User as UserIcon } from "lucide-react";

function CornerFrame({ color }) {
  const s = { position: "absolute", width: 10, height: 10, borderColor: color };
  return (
    <>
      <span style={{ ...s, top: -2, left: -2, borderTop: `2px solid ${color}`, borderLeft: `2px solid ${color}` }} />
      <span style={{ ...s, top: -2, right: -2, borderTop: `2px solid ${color}`, borderRight: `2px solid ${color}` }} />
      <span style={{ ...s, bottom: -2, left: -2, borderBottom: `2px solid ${color}`, borderLeft: `2px solid ${color}` }} />
      <span style={{ ...s, bottom: -2, right: -2, borderBottom: `2px solid ${color}`, borderRight: `2px solid ${color}` }} />
    </>
  );
}

function StatBlock({ Icon, iconColor, label, value, valueColor, testid }) {
  return (
    <div data-testid={testid} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 18px", background: "#08080f", border: "1px solid #14141f", minWidth: 0 }}>
      <div style={{ width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center", background: `${iconColor}18`, border: `1px solid ${iconColor}55` }}>
        <Icon size={16} color={iconColor} style={{ filter: `drop-shadow(0 0 4px ${iconColor}aa)` }} />
      </div>
      <div style={{ minWidth: 0 }}>
        <div className="label-caps" style={{ color: iconColor, fontSize: 9, letterSpacing: "0.25em" }}>{label}</div>
        <div className="font-display" style={{ fontSize: 18, color: valueColor, fontWeight: 800, letterSpacing: "0.02em", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{value}</div>
      </div>
    </div>
  );
}

function IconBtn({ Icon, badge, onClick, color = "#94a3b8", testid }) {
  return (
    <button data-testid={testid} onClick={onClick} style={{ position: "relative", width: 40, height: 40, border: "1px solid #14141f", background: "#08080f", display: "flex", alignItems: "center", justifyContent: "center", color, transition: "all 0.15s" }} onMouseEnter={e => e.currentTarget.style.borderColor = color} onMouseLeave={e => e.currentTarget.style.borderColor = "#14141f"}>
      <Icon size={16} />
      {badge && <span style={{ position: "absolute", top: 4, right: 4, minWidth: 12, height: 12, background: "#EF4444", borderRadius: 6, boxShadow: "0 0 6px #EF4444", fontSize: 8, color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", padding: "0 3px", fontWeight: 800 }}>{typeof badge === "number" ? badge : ""}</span>}
    </button>
  );
}

export default function HUD() {
  const { user, catalog, logout } = useAuth();
  const spec = catalog?.specializations.find(s => s.id === user.specialization);
  const xpMax = 1000 + (user.level - 1) * 500;
  const xpPct = Math.min(100, (user.xp / xpMax) * 100);
  const heatSegs = 20;
  const heatFilled = Math.round((user.heat / 100) * heatSegs);
  const specColor = spec?.color || "#EC4899";

  return (
    <header style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 60, background: "#030307", borderBottom: "1px solid #14141f", height: 96, display: "grid", gridTemplateColumns: "270px 1fr auto", alignItems: "center", gap: 14, padding: "0 18px" }} data-testid="hud">
      <div style={{ display: "flex", alignItems: "center", gap: 14 }} data-testid="hud-user">
        <div style={{ position: "relative", width: 62, height: 62, border: `1px solid ${specColor}55`, background: `linear-gradient(135deg, ${specColor}33 0%, #050508 100%)`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <UserIcon size={30} color={specColor} strokeWidth={1.2} style={{ filter: `drop-shadow(0 0 6px ${specColor}bb)` }} />
          <CornerFrame color={specColor} />
        </div>
        <div style={{ minWidth: 0 }}>
          <div className="font-display" style={{ fontSize: 20, color: "#fff", letterSpacing: "0.08em", fontWeight: 900, lineHeight: 1, textShadow: `0 0 10px ${specColor}66`, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{user.username.toUpperCase()}</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginTop: 6 }}>
            <span className="label-caps" style={{ fontSize: 10, color: specColor, letterSpacing: "0.28em", fontWeight: 800 }}>LEVEL {user.level}</span>
            <span style={{ fontSize: 10, color: "#94a3b8", letterSpacing: "0.05em" }}>{user.xp.toLocaleString()} / {xpMax.toLocaleString()} XP</span>
          </div>
          <div style={{ marginTop: 5, width: 200, height: 4, background: "#0a0a12", overflow: "hidden" }}>
            <div style={{ width: `${xpPct}%`, height: "100%", background: `linear-gradient(90deg, ${specColor} 0%, #A855F7 100%)`, boxShadow: `0 0 6px ${specColor}` }} />
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.5fr 1fr", gap: 10 }}>
        <StatBlock testid="hud-cash" Icon={DollarSign} iconColor="#10B981" label="CASH" value={`$ ${user.money.toLocaleString()}`} valueColor="#10B981" />
        <StatBlock testid="hud-bank" Icon={Landmark} iconColor="#38BDF8" label="BANK" value={`$ ${(user.bank || 0).toLocaleString()}`} valueColor="#38BDF8" />
        <div data-testid="hud-heat" style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 18px", background: "#08080f", border: "1px solid #14141f", minWidth: 0 }}>
          <div style={{ width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)" }}>
            <Flame size={16} color="#EF4444" style={{ filter: "drop-shadow(0 0 4px #EF4444aa)" }} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="label-caps" style={{ color: "#EF4444", fontSize: 9, letterSpacing: "0.25em" }}>HEAT</div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 5 }}>
              <div style={{ display: "flex", gap: 2, flex: 1 }}>
                {Array.from({ length: heatSegs }).map((_, i) => (
                  <div key={i} style={{ flex: 1, height: 8, background: i < heatFilled ? (i < 8 ? "#F59E0B" : i < 15 ? "#EF4444" : "#7f1d1d") : "#1a1a26", boxShadow: i < heatFilled ? "0 0 3px #EF4444" : "none" }} />
                ))}
              </div>
              <div className="font-display" style={{ fontSize: 12, color: "#fff", fontWeight: 800, whiteSpace: "nowrap" }}>{user.heat} / 100</div>
            </div>
          </div>
        </div>
        <StatBlock testid="hud-rep" Icon={Crown} iconColor="#A855F7" label="REPUTATION" value={user.reputation.toLocaleString()} valueColor="#fff" />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <IconBtn testid="hud-bell" Icon={Bell} badge={true} />
        <IconBtn testid="hud-mail" Icon={Mail} badge={6} />
        <IconBtn testid="hud-settings" Icon={Settings} />
        <IconBtn testid="hud-logout" Icon={Power} onClick={logout} color="#EF4444" />
      </div>
    </header>
  );
}
