import { useState } from "react";
import { useAuth } from "../AuthContext";
import HUD from "../game/HUD";
import Sidebar from "../game/Sidebar";
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
import Businesses from "../game/tabs/Businesses";
import PvP from "../game/tabs/PvP";

export default function Game() {
  const { user } = useAuth();
  const [tab, setTab] = useState("home");
  if (!user) return null;

  const Tab = {
    home: Home, character: Character, inventory: Inventory, arsenal: Arsenal, garage: Garage,
    crew: Crew, heists: Heists, map: MapView, progress: Progress,
    assets: Assets, businesses: Businesses, pvp: PvP,
    market: Arsenal, // MARKET = Arsenal (regular market)
  }[tab] || Home;

  return (
    <div style={{ minHeight: "100vh", background: "#020204" }}>
      <HUD />
      <Sidebar tab={tab} setTab={setTab} />
      <main style={{ marginLeft: 240, paddingTop: 96, paddingBottom: 30, minHeight: "100vh" }} data-testid="game-main">
        <div style={{ padding: "18px 18px 40px" }}>
          <div className="fade-in-up" key={tab}>
            <Tab setTab={setTab} />
          </div>
        </div>
      </main>
    </div>
  );
}
