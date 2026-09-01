import { useState } from "react";
import { useAuth } from "../AuthContext";
import HUD from "../game/HUD";
import BottomNav from "../game/BottomNav";
import Home from "../game/tabs/Home";
import Character from "../game/tabs/Character";
import Inventory from "../game/tabs/Inventory";
import Arsenal from "../game/tabs/Arsenal";
import Garage from "../game/tabs/Garage";
import Crew from "../game/tabs/Crew";
import Heists from "../game/tabs/Heists";
import MapView from "../game/tabs/MapView";
import Progress from "../game/tabs/Progress";
import Assets from "../game/tabs/Assets";
import PvP from "../game/tabs/PvP";

export default function Game() {
  const { user } = useAuth();
  const [tab, setTab] = useState("home");
  if (!user) return null;

  const Tab = { home: Home, character: Character, inventory: Inventory, arsenal: Arsenal, garage: Garage, crew: Crew, heists: Heists, map: MapView, progress: Progress, assets: Assets, pvp: PvP }[tab] || Home;

  return (
    <div style={{ minHeight: "100vh", paddingTop: 96, paddingBottom: 110 }} className="grid-bg">
      <HUD />
      <main style={{ maxWidth: 1280, margin: "0 auto", padding: "0 16px" }} data-testid="game-main">
        <div className="fade-in-up" key={tab}>
          <Tab setTab={setTab} />
        </div>
      </main>
      <BottomNav tab={tab} setTab={setTab} />
    </div>
  );
}
