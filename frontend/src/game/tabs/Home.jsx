import { useAuth } from "../../AuthContext";
import { fmtMoney } from "../../api";
import { ArrowRight, Target, ShoppingBag, Users, Home, Building2, DollarSign, Swords } from "lucide-react";

const HERO_IMG = "https://images.unsplash.com/photo-1518709414768-a88981a4515d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80";

export default function HomeTab({ setTab }) {
  const { user, catalog } = useAuth();
  const spec = catalog?.specializations.find(s => s.id === user.specialization);
  const nextOp = (catalog?.heists || []).filter(h => user.level >= h.min_level).slice(-1)[0];

  const cards = [
    { id: "character", label: "CHARACTER", val: `LVL ${user.level}`, sub: spec?.name || "—", Icon: Users, color: spec?.color },
    { id: "inventory", label: "INVENTORY", val: `${user.weapons.length + (user.armors?.length || 0)}`, sub: "ITEMS", Icon: ShoppingBag, color: "#00F0FF" },
    { id: "arsenal", label: "ARSENAL", val: user.weapons.length, sub: "WEAPONS", Icon: Target, color: "#38BDF8" },
    { id: "garage", label: "GARAGE", val: user.vehicles.length, sub: "VEHICLES", Icon: Target, color: "#F59E0B" },
    { id: "crew", label: "CREW", val: user.hired_crew.length, sub: "MEMBERS", Icon: Users, color: "#EC4899" },
    { id: "heists", label: "HEISTS", val: user.stats.ops_completed, sub: "COMPLETED", Icon: Target, color: "#A855F7" },
    { id: "assets", label: "PROPERTIES", val: (user.properties || []).length, sub: `${(user.businesses || []).length} BIZ`, Icon: Home, color: "#10B981" },
    { id: "pvp", label: "PVP", val: user.stats.raids_survived || 0, sub: "SURVIVED", Icon: Swords, color: "#EF4444" },
  ];

  const dailyIncome = (user.businesses || []).reduce((acc, b) => { const m = (catalog?.businesses || []).find(x => x.id === b.id); return acc + (m?.daily_income || 0); }, 0);

  return (
    <div style={{ display: "grid", gap: 22 }}>
      <div className="hologram-border" style={{ position: "relative", overflow: "hidden", minHeight: 320 }}>
        <img src={HERO_IMG} alt="" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.6 }} />
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(90deg, rgba(2,2,4,0.95) 0%, rgba(2,2,4,0.55) 50%, rgba(2,2,4,0.85) 100%)" }} />
        <div style={{ position: "relative", padding: "36px 32px", display: "flex", flexDirection: "column", justifyContent: "space-between", minHeight: 320 }}>
          <div>
            <div className="label-caps neon-cyan">SECTOR 07 · NEON CITY</div>
            <h1 className="font-display" style={{ fontSize: 42, color: "#fff", letterSpacing: "0.1em", margin: "6px 0", fontWeight: 900 }}>WELCOME BACK, <span style={{ color: spec?.color }}>{user.username.toUpperCase()}</span></h1>
            <div style={{ color: "#cbd5e1", fontSize: 14, maxWidth: 620 }}>The city is yours. Build your criminal empire — one operation at a time.</div>
          </div>
          {nextOp && <div style={{ background: "rgba(2,2,6,0.85)", border: "1px solid rgba(168,85,247,0.5)", padding: 18, maxWidth: 380 }}>
            <div className="label-caps neon-purple">NEXT OPERATION</div>
            <div className="font-display" style={{ fontSize: 20, color: "#fff", letterSpacing: "0.06em", marginTop: 4 }}>{nextOp.name.toUpperCase()}</div>
            <div style={{ marginTop: 8, fontSize: 12, color: "#94a3b8" }}>Reward: <span className="neon-gold">{fmtMoney(nextOp.reward_min)} – {fmtMoney(nextOp.reward_max)}</span></div>
            <button data-testid="cta-heists" onClick={() => setTab("heists")} className="btn-primary" style={{ marginTop: 12, width: "100%", padding: 10, fontSize: 12 }}>PREPARE HEIST <ArrowRight size={12} style={{ display: "inline", marginLeft: 4 }} /></button>
          </div>}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 12 }}>
        {cards.map(c => {
          const Icon = c.Icon;
          return (
            <button data-testid={`home-card-${c.id}`} key={c.id} onClick={() => setTab(c.id)} className="card-glow" style={{ padding: 16, textAlign: "left", borderColor: `${c.color}44`, minHeight: 130 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div className="label-caps" style={{ color: c.color, letterSpacing: "0.18em" }}>{c.label}</div>
                <Icon size={16} color={c.color} />
              </div>
              <div className="font-display" style={{ fontSize: 28, color: "#fff", fontWeight: 800, marginTop: 12 }}>{c.val}</div>
              <div style={{ fontSize: 10, color: "#64748B", letterSpacing: "0.15em", marginTop: 2 }}>{c.sub}</div>
            </button>
          );
        })}
      </div>

      {dailyIncome > 0 && <div className="card-glow" style={{ padding: 18, borderColor: "rgba(16,185,129,0.4)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div>
          <div className="label-caps neon-green">PASSIVE INCOME</div>
          <div className="font-display neon-green" style={{ fontSize: 22 }}>{fmtMoney(dailyIncome)}/day</div>
        </div>
        <button data-testid="cta-assets" onClick={() => setTab("assets")} className="btn-outline" style={{ padding: "8px 14px" }}><DollarSign size={12} style={{ display: "inline", marginRight: 4 }} /> COLLECT</button>
      </div>}
    </div>
  );
}
