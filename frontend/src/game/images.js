// Local image slices from the user's dashboard reference art.
// Files live in /app/frontend/public/dashboard/
const BASE = "/dashboard";

export const HERO_BG = `${BASE}/hero.png`;
export const PORTRAIT_BG = `${BASE}/portrait.png`;

// Dashboard section cards (used by Home.jsx BigCard image={CARD_BG.xxx})
export const CARD_BG = {
  inventory:  `${BASE}/inventory.png`,
  arsenal:    `${BASE}/arsenal.png`,
  garage:     `${BASE}/garage.png`,
  crew:       `${BASE}/crew.png`,
  heists:     `${BASE}/heists.png`,
  properties: `${BASE}/properties.png`,
  businesses: `${BASE}/businesses.png`,
  map:        `${BASE}/map.png`,
  progress:   `${BASE}/progress.png`,
};

// Featured art (weapon/vehicle/contract) - clean artwork
export const FEATURED_ART = {
  weapon:   `${BASE}/featured_weapon_art.png`,
  vehicle:  `${BASE}/featured_vehicle_art.png`,
  contract: `${BASE}/daily_contract_art.png`,
};

// Full city map artworks (used by MapView)
export const CITY_MAP_BG = `${BASE}/citymap_full2.png`;

// Per-item artwork keyed by weapon category
export const WEAPON_IMG = {
  melee:   `${BASE}/weapon_melee.png`,
  pistol:  `${BASE}/weapon_pistol.png`,
  smg:     `${BASE}/weapon_smg.png`,
  rifle:   `${BASE}/weapon_rifle.png`,
  shotgun: `${BASE}/weapon_shotgun.png`,
  sniper:  `${BASE}/weapon_sniper.png`,
  special: `${BASE}/weapon_special.png`,
};

export const VEHICLE_IMG = {
  compact: `${BASE}/vehicle_compact.png`,
  sport:   `${BASE}/vehicle_sport.png`,
  muscle:  `${BASE}/vehicle_muscle.png`,
  super:   `${BASE}/vehicle_super.png`,
  bike:    `${BASE}/vehicle_bike.png`,
  armored: `${BASE}/vehicle_armored.png`,
  utility: `${BASE}/vehicle_compact.png`,
};

// Character portraits keyed by avatar id (see CharacterSelect.jsx AVATARS)
export const CHARACTER_IMG = {
  av_1: `${BASE}/char_street_thug.png`, // Street Thug
  av_2: `${BASE}/char_netrunner.png`,   // Netrunner
  av_3: `${BASE}/char_solo.png`,        // Solo
  av_4: `${BASE}/char_techie.png`,      // Techie
  av_5: `${BASE}/char_kingpin.png`,     // Kingpin
  av_6: `${BASE}/char_legend.png`,      // Wraith → Legend art
};

// Legacy placeholders kept for compatibility
export const PROPERTY_IMG = {};
export const BUSINESS_IMG = {};
