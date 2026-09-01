// Direct local image references, no CSS slicing.
import { WEAPON_IMG, VEHICLE_IMG, CHARACTER_IMG } from "./images";

export function weaponArt(cat) {
  const url = WEAPON_IMG[cat] || WEAPON_IMG.pistol;
  return { backgroundImage: `url("${url}")`, backgroundSize: "cover", backgroundPosition: "center", backgroundRepeat: "no-repeat" };
}

export function vehicleArt(cat) {
  const url = VEHICLE_IMG[cat] || VEHICLE_IMG.compact;
  return { backgroundImage: `url("${url}")`, backgroundSize: "cover", backgroundPosition: "center", backgroundRepeat: "no-repeat" };
}

export function characterArt(avatarId) {
  const url = CHARACTER_IMG[avatarId] || CHARACTER_IMG.av_1;
  return { backgroundImage: `url("${url}")`, backgroundSize: "cover", backgroundPosition: "center top", backgroundRepeat: "no-repeat" };
}
