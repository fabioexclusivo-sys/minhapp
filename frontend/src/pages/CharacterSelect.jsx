import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { api, fmtDetail } from "../api";
import { toast } from "sonner";
import { User, Ghost, Skull, Wrench, Crown, EyeOff } from "lucide-react";
import { characterArt } from "../game/artwork";

const AVATARS = [
  { id: "av_1", name: "Street Thug", tag: "The Survivor", color: "#A855F7", Icon: User },
  { id: "av_2", name: "Netrunner", tag: "The Ghost", color: "#00F0FF", Icon: Ghost },
  { id: "av_3", name: "Solo", tag: "The Merc", color: "#EF4444", Icon: Skull },
  { id: "av_4", name: "Techie", tag: "The Engineer", color: "#10B981", Icon: Wrench },
  { id: "av_5", name: "Kingpin", tag: "The Empire", color: "#F59E0B", Icon: Crown },
  { id: "av_6", name: "Wraith", tag: "The Shadow", color: "#EC4899", Icon: EyeOff },
];

const REF_IMG = "https://customer-assets-jai6qajn.emergentagent.net/job_84f7bbbd-916b-4aca-81f7-c910c1459d12/artifacts/mrgjk9cj_ee3fffa1-6aee-464d-bb69-b4de291e2c7e.png";

export default function CharacterSelect() {
  const { catalog, setUser } = useAuth();
  const nav = useNavigate();
  const [avatar, setAvatar] = useState(null);
  const [spec, setSpec] = useState(null);
  const [loading, setLoading] = useState(false);

  const specs = catalog?.specializations || [];

  const create = async () => {
    if (!avatar || !spec) { toast.error("Choose avatar and specialization."); return; }
    setLoading(true);
    try {
      const { data } = await api.post("/character/create", { avatar_id: avatar, specialization: spec });
      setUser(data);
      toast.success("Character created. Entering Neon City...");
      nav("/game");
    } catch (err) { toast.error(fmtDetail(err.response?.data?.detail) || err.message); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#020204" }}>
      <div style={{ position: "relative", height: 280, overflow: "hidden", borderBottom: "1px solid rgba(0,240,255,0.2)" }}>
        <img src={REF_IMG} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center top", opacity: 0.55 }} />
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, transparent 0%, transparent 45%, #020204 100%)" }} />
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "flex-end", padding: "0 40px 30px" }}>
          <div>
            <div className="label-caps neon-cyan" style={{ fontSize: 11 }}>STEP 1 · CHOOSE YOUR START</div>
            <h1 className="font-display" style={{ fontSize: 44, margin: "6px 0", color: "#fff", letterSpacing: "0.12em", fontWeight: 900 }}>CHARACTER <span style={{ color: "#00F0FF" }}>SELECT</span></h1>
            <div style={{ color: "#94a3b8", fontSize: 14, maxWidth: 620 }}>Pick your fighter. Every path is different. Every choice matters. No one owns you. The city is yours.</div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1240, margin: "0 auto", padding: "32px 20px 80px" }} className="fade-in-up">
        <div style={{ marginBottom: 36 }}>
          <div className="label-caps" style={{ marginBottom: 14 }}>AVATAR · APPEARANCE</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 14 }}>
            {AVATARS.map(a => {
              const Icon = a.Icon;
              const selected = avatar === a.id;
              return (
                <button data-testid={`avatar-${a.id}`} key={a.id} onClick={() => setAvatar(a.id)} className="card-glow" style={{ padding: 0, textAlign: "left", borderColor: selected ? a.color : undefined, boxShadow: selected ? `0 0 24px ${a.color}66` : undefined, overflow: "hidden" }}>
                  <div style={{ height: 180, position: "relative", overflow: "hidden", borderBottom: `1px solid ${a.color}33`, ...characterArt(a.id) }}>
                    <div style={{ position: "absolute", inset: 0, background: `linear-gradient(180deg, transparent 50%, rgba(3,3,8,0.6) 100%)` }} />
                    <div style={{ position: "absolute", inset: 0, background: `linear-gradient(135deg, ${a.color}22 0%, transparent 60%)` }} />
                  </div>
                  <div style={{ padding: 14 }}>
                    <div className="font-display" style={{ fontSize: 15, color: "#fff", fontWeight: 800, letterSpacing: "0.08em" }}>{a.name.toUpperCase()}</div>
                    <div style={{ fontSize: 11, color: a.color, letterSpacing: "0.18em", marginTop: 2 }}>{a.tag.toUpperCase()}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <div className="label-caps" style={{ marginBottom: 14 }}>SPECIALIZATION · YOUR EDGE</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 14 }}>
            {specs.map(s => (
              <button data-testid={`spec-${s.id}`} key={s.id} onClick={() => setSpec(s.id)} className="card-glow" style={{ padding: 24, textAlign: "left", borderColor: spec === s.id ? s.color : undefined, boxShadow: spec === s.id ? `0 0 24px ${s.color}55` : undefined, minHeight: 180 }}>
                <div className="font-display" style={{ fontSize: 24, fontWeight: 900, color: s.color, letterSpacing: "0.12em", marginBottom: 8 }}>{s.name.toUpperCase()}</div>
                <div style={{ height: 2, width: 42, background: s.color, marginBottom: 14, boxShadow: `0 0 12px ${s.color}` }}></div>
                <div style={{ color: "#cbd5e1", fontSize: 13, lineHeight: 1.55 }}>{s.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 44, display: "flex", justifyContent: "center" }}>
          <button data-testid="create-character" onClick={create} disabled={!avatar || !spec || loading} className="btn-primary" style={{ padding: "18px 56px", fontSize: 14 }}>
            {loading ? "..." : "ENTER NEON CITY →"}
          </button>
        </div>
      </div>
    </div>
  );
}
