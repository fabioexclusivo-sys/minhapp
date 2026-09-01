import { useEffect, useState } from "react";
import { useAuth } from "../AuthContext";
import { LayoutDashboard, User, Briefcase, Crosshair, Car, Users, Target, Home, Building2, Map, Trophy, LogOut, ShoppingCart, Skull } from "lucide-react";

const TABS = [
  { id: "home", label: "DASHBOARD", icon: LayoutDashboard },
  { id: "character", label: "CHARACTER", icon: User },
  { id: "inventory", label: "INVENTORY", icon: Briefcase },
  { id: "arsenal", label: "ARSENAL", icon: Crosshair },
  { id: "garage", label: "GARAGE", icon: Car },
  { id: "crew", label: "CREW", icon: Users },
  { id: "heists", label: "HEISTS", icon: Target },
  { id: "assets", label: "PROPERTIES", icon: Home },
  { id: "businesses", label: "BUSINESSES", icon: Building2 },
  { id: "map", label: "MAP", icon: Map },
  { id: "progress", label: "PROGRESS", icon: Trophy },
  { id: "market", label: "MARKET", icon: ShoppingCart },
  { id: "pvp", label: "BLACK MARKET", icon: Skull },
];

export default function Sidebar({ tab, setTab }) {
  const { logout } = useAuth();
  const [now, setNow] = useState(new Date());
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(t); }, []);

  const time = now.toTimeString().slice(0, 5);
  const dd = String(now.getDate()).padStart(2, "0");
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const yy = now.getFullYear() + 51;

  return (
    <aside style={{ position: "fixed", left: 0, top: 96, bottom: 0, width: 240, zIndex: 50, background: "#030307", borderRight: "1px solid #14141f", display: "flex", flexDirection: "column" }} data-testid="sidebar">
      <div style={{ padding: "18px 20px 14px", borderBottom: "1px solid #14141f" }}>
        <div className="font-display" style={{ fontSize: 22, fontWeight: 900, letterSpacing: "0.16em", background: "linear-gradient(90deg, #EC4899 0%, #A855F7 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", lineHeight: 1, filter: "drop-shadow(0 0 10px rgba(236,72,153,0.45))" }}>NEON CITY</div>
        <div className="label-caps" style={{ fontSize: 8, color: "#94a3b8", letterSpacing: "0.4em", marginTop: 4 }}>— THE LAW OF SILENCE —</div>
      </div>
      <nav style={{ flex: 1, overflowY: "auto", padding: "14px 12px" }}>
        {TABS.map(t => {
          const Icon = t.icon;
          const active = tab === t.id;
          return (
            <button key={t.id} data-testid={`nav-${t.id}`} onClick={() => setTab(t.id)} style={{ display: "flex", alignItems: "center", gap: 12, width: "100%", padding: "11px 16px", marginBottom: 1, background: active ? "linear-gradient(90deg, rgba(236,72,153,0.14) 0%, transparent 100%)" : "transparent", borderLeft: active ? "3px solid #EC4899" : "3px solid transparent", color: active ? "#fff" : "#64748B", transition: "all 0.15s", fontFamily: "Orbitron", fontSize: 11, letterSpacing: "0.14em", fontWeight: 700, textAlign: "left" }}>
              <Icon size={15} strokeWidth={active ? 2.2 : 1.6} color={active ? "#EC4899" : undefined} />
              <span>{t.label}</span>
            </button>
          );
        })}
        <button data-testid="logout-btn" onClick={logout} style={{ display: "flex", alignItems: "center", gap: 12, width: "100%", padding: "11px 16px", marginTop: 12, borderTop: "1px solid #14141f", color: "#EF4444", fontFamily: "Orbitron", fontSize: 11, letterSpacing: "0.14em", fontWeight: 700, textAlign: "left" }}>
          <LogOut size={15} /> LOG OUT
        </button>
      </nav>

      <div style={{ padding: "16px 20px 20px", borderTop: "1px solid #14141f", background: "#020205" }}>
        <div className="font-display" style={{ fontSize: 24, color: "#EC4899", fontWeight: 800, letterSpacing: "0.06em", filter: "drop-shadow(0 0 8px rgba(236,72,153,0.5))" }}>{time}</div>
        <div style={{ fontSize: 11, color: "#64748B", letterSpacing: "0.1em", marginTop: 2 }}>{dd}/{mm}/{yy}</div>
        <div style={{ marginTop: 12, fontSize: 10, color: "#94a3b8", letterSpacing: "0.18em", fontFamily: "Orbitron", fontWeight: 700 }}>NEON CITY</div>
        <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.24em", marginTop: 1 }}>SECTOR 07</div>
      </div>
    </aside>
  );
}
