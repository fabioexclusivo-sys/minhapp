import { useAuth } from "../../AuthContext";
import { api, fmtDetail, fmtMoney } from "../../api";
import { toast } from "sonner";
import { DollarSign } from "lucide-react";
import { BUSINESS_IMG } from "../images";

export default function Businesses() {
  const { user, catalog, refresh } = useAuth();
  if (!catalog) return null;

  const buyBiz = async (b) => { try { await api.post("/business/buy", { item_id: b.id }); await refresh(); toast.success(`Acquired ${b.name}`); } catch (e) { toast.error(fmtDetail(e.response?.data?.detail)); } };
  const collect = async () => {
    try {
      const { data } = await api.post("/business/collect");
      await refresh();
      if (data.fines > 0) toast.error(`Collected $${data.income} but paid $${data.fines} in fines. Net: $${data.net}`);
      else toast.success(`+$${data.income} collected.`);
    } catch (e) { toast.error(fmtDetail(e.response?.data?.detail)); }
  };
  const dailyIncome = (user.businesses || []).reduce((acc, b) => { const m = catalog.businesses.find(x => x.id === b.id); return acc + (m?.daily_income || 0); }, 0);

  return (
    <div style={{ display: "grid", gap: 22 }}>
      <div>
        <h2 className="font-display" style={{ fontSize: 26, color: "#fff", letterSpacing: "0.1em", marginBottom: 4 }}>BUSINESSES</h2>
        <div style={{ color: "#64748B", fontSize: 13 }}>Legitimate fronts. Passive income — but higher-tier businesses attract inspectors.</div>
      </div>

      {(user.businesses || []).length > 0 && <div className="card-glow" style={{ padding: 20, borderColor: "rgba(16,185,129,0.4)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
          <div>
            <div className="label-caps neon-green">DAILY INCOME</div>
            <div className="font-display neon-green" style={{ fontSize: 26 }}>{fmtMoney(dailyIncome)}/day</div>
            <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>Income accrues hourly. Cap at 48h — collect before it locks.</div>
          </div>
          <button data-testid="collect-income" onClick={collect} className="btn-primary" style={{ padding: "12px 20px" }}><DollarSign size={14} style={{ display: "inline", marginRight: 4 }} /> COLLECT INCOME</button>
        </div>
      </div>}

      <div>
        <div className="label-caps neon-pink" style={{ marginBottom: 12 }}>BUSINESS OPPORTUNITIES</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 12 }}>
          {catalog.businesses.map(b => {
            const owned = (user.businesses || []).some(x => x.id === b.id);
            const riskPct = Math.round(b.inspection_risk * 100);
            return (
              <div key={b.id} className="card-glow" style={{ padding: 0, overflow: "hidden" }}>
                {BUSINESS_IMG[b.id] && <div style={{ position: "relative", height: 130, overflow: "hidden" }}>
                  <img src={BUSINESS_IMG[b.id]} alt="" loading="lazy" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.55 }} />
                  <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, transparent 0%, rgba(3,3,8,0.5) 60%, #08080f 100%)" }} />
                </div>}
                <div style={{ padding: 18 }}>
                  <div className="label-caps" style={{ color: "#EC4899" }}>{b.district.replace("_", " ").toUpperCase()}</div>
                  <div className="font-display" style={{ color: "#fff", fontSize: 16, marginTop: 4, letterSpacing: "0.06em" }}>{b.name.toUpperCase()}</div>
                  <div style={{ fontSize: 12, color: "#94a3b8", margin: "10px 0", minHeight: 34 }}>{b.desc}</div>
                  <div style={{ fontSize: 11, color: "#64748B", display: "grid", gap: 3 }}>
                    <div>DAILY: <span className="neon-green">{fmtMoney(b.daily_income)}</span></div>
                    <div>INSPECTION RISK: <span style={{ color: riskPct > 20 ? "#EF4444" : "#F59E0B" }}>{riskPct}%</span></div>
                    <div>FINE RANGE: <span style={{ color: "#EF4444" }}>{fmtMoney(b.fine_min)} – {fmtMoney(b.fine_max)}</span></div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 14 }}>
                    <div className="font-display neon-gold">{fmtMoney(b.price)}</div>
                    <button data-testid={`buy-biz-${b.id}`} onClick={() => buyBiz(b)} disabled={owned || user.money < b.price} className="btn-primary" style={{ padding: "8px 12px", fontSize: 11 }}>{owned ? "OWNED" : "BUY"}</button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
