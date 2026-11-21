// Exact ART_BIBLE material palette (sRGB hex) + cel-shading surface properties.
// outline: 1.0 = normal crisp line, 0.3 = subtle terrain depth-only, 0.12 = foliage silhouette only, 0 = none

export const PALETTE = {
  // Walls
  wall_cream:       { color: '#F3E6CC', kind: 'wall',     spec: 0.04, shininess: 18, rim: 0.24, outline: 1.0 },
  wall_white:       { color: '#F6F2EA', kind: 'wall',     spec: 0.05, shininess: 20, rim: 0.24, outline: 1.0 },
  wall_peach:       { color: '#F2CBB0', kind: 'wall',     spec: 0.04, shininess: 18, rim: 0.25, outline: 1.0 },
  wall_mint:        { color: '#CFE6D6', kind: 'wall',     spec: 0.04, shininess: 18, rim: 0.25, outline: 1.0 },
  wall_sky:         { color: '#C9DDF0', kind: 'wall',     spec: 0.05, shininess: 20, rim: 0.26, outline: 1.0 },
  wood_dark:        { color: '#6B4A36', kind: 'wall',     spec: 0.08, shininess: 24, rim: 0.28, outline: 1.0 },
  wood_light:       { color: '#B88A5E', kind: 'wall',     spec: 0.06, shininess: 20, rim: 0.24, outline: 1.0 },
  wood_weathered:   { color: '#8E8173', kind: 'wall',     spec: 0.04, shininess: 16, rim: 0.22, outline: 0.9 },

  // Roofs (kawara tiles, slightly glossy)
  roof_blue:        { color: '#3F5F8C', kind: 'roof',     spec: 0.34, shininess: 46, rim: 0.42, outline: 1.0 },
  roof_teal:        { color: '#3E7D7A', kind: 'roof',     spec: 0.32, shininess: 44, rim: 0.40, outline: 1.0 },
  roof_terracotta:  { color: '#B5583F', kind: 'roof',     spec: 0.28, shininess: 38, rim: 0.36, outline: 1.0 },
  roof_charcoal:    { color: '#4A4E58', kind: 'roof',     spec: 0.34, shininess: 48, rim: 0.42, outline: 1.0 },
  roof_tin_red:     { color: '#A8453C', kind: 'roof',     spec: 0.38, shininess: 52, rim: 0.40, outline: 1.0 },

  // Trim & Glass
  trim_white:       { color: '#FAFAF5', kind: 'wall',     spec: 0.08, shininess: 24, rim: 0.24, outline: 0.9 },
  window_glass:     { color: '#8FB8D9', kind: 'glass',    spec: 0.85, shininess: 96, rim: 0.50, outline: 0.85 },
  window_frame:     { color: '#E9E3D6', kind: 'wall',     spec: 0.10, shininess: 28, rim: 0.22, outline: 0.9 },
  shoji:            { color: '#F4EBD8', kind: 'shoji',    spec: 0.05, shininess: 16, rim: 0.20, outline: 0.85 },
  door_wood:        { color: '#7A5233', kind: 'wall',     spec: 0.10, shininess: 28, rim: 0.25, outline: 1.0 },

  // Ground
  grass:            { color: '#8CC56A', kind: 'ground',   spec: 0.02, shininess: 12, rim: 0.16, outline: 0.22 },
  grass_dark:       { color: '#5E9E55', kind: 'ground',   spec: 0.02, shininess: 12, rim: 0.16, outline: 0.22 },
  dirt_path:        { color: '#D8C39A', kind: 'ground',   spec: 0.03, shininess: 12, rim: 0.12, outline: 0.20 },
  stone:            { color: '#BDB6A8', kind: 'ground',   spec: 0.06, shininess: 20, rim: 0.20, outline: 0.65 },
  stone_dark:       { color: '#8C877E', kind: 'ground',   spec: 0.06, shininess: 22, rim: 0.20, outline: 0.65 },
  asphalt:          { color: '#7C8088', kind: 'ground',   spec: 0.09, shininess: 26, rim: 0.14, outline: 0.25 },
  road_line:        { color: '#F5F2E8', kind: 'ground',   spec: 0.06, shininess: 18, rim: 0.10, outline: 0.05 },
  concrete:         { color: '#CFCAC0', kind: 'wet',      spec: 0.14, shininess: 28, rim: 0.20, outline: 0.72 },
  sand:             { color: '#EADBB2', kind: 'wet',      spec: 0.10, shininess: 24, rim: 0.14, outline: 0.15 },
  cliff_rock:       { color: '#A99C88', kind: 'ground',   spec: 0.05, shininess: 18, rim: 0.22, outline: 0.45 },

  // Nature (foliage skips interior outlines via low outline weight)
  leaf_green:       { color: '#6FB04F', kind: 'foliage',  spec: 0.06, shininess: 16, rim: 0.44, outline: 0.10 },
  leaf_light:       { color: '#A6D46A', kind: 'foliage',  spec: 0.06, shininess: 16, rim: 0.46, outline: 0.10 },
  leaf_dark:        { color: '#3F7E43', kind: 'foliage',  spec: 0.05, shininess: 14, rim: 0.36, outline: 0.10 },
  sakura:           { color: '#F7C6D4', kind: 'foliage',  spec: 0.06, shininess: 16, rim: 0.50, outline: 0.10 },
  sakura_deep:      { color: '#EE9DB5', kind: 'foliage',  spec: 0.06, shininess: 16, rim: 0.46, outline: 0.10 },
  bark:             { color: '#6E5444', kind: 'wall',     spec: 0.04, shininess: 14, rim: 0.22, outline: 0.75 },
  hydrangea_blue:   { color: '#8DA8E8', kind: 'foliage',  spec: 0.06, shininess: 16, rim: 0.40, outline: 0.12 },
  hydrangea_pink:   { color: '#E7A3C6', kind: 'foliage',  spec: 0.06, shininess: 16, rim: 0.40, outline: 0.12 },
  sunflower:        { color: '#F5C542', kind: 'foliage',  spec: 0.06, shininess: 16, rim: 0.36, outline: 0.18 },

  // Accents
  torii_red:        { color: '#D8443A', kind: 'roof',     spec: 0.22, shininess: 36, rim: 0.36, outline: 1.0 },
  lighthouse_white: { color: '#F7F7F2', kind: 'wall',     spec: 0.18, shininess: 32, rim: 0.30, outline: 1.0 },
  lighthouse_red:   { color: '#D84B3E', kind: 'roof',     spec: 0.24, shininess: 38, rim: 0.34, outline: 1.0 },
  boat_white:       { color: '#F4F4EF', kind: 'boat',     spec: 0.36, shininess: 52, rim: 0.34, outline: 1.0 },
  boat_blue:        { color: '#3C76B8', kind: 'boat',     spec: 0.38, shininess: 54, rim: 0.38, outline: 1.0 },
  boat_red:         { color: '#C9503F', kind: 'boat',     spec: 0.36, shininess: 52, rim: 0.36, outline: 1.0 },
  metal_grey:       { color: '#9AA1AA', kind: 'metal',    spec: 0.42, shininess: 56, rim: 0.36, outline: 0.9 },
  metal_dark:       { color: '#4F555E', kind: 'metal',    spec: 0.36, shininess: 48, rim: 0.34, outline: 0.9 },
  rail_steel:       { color: '#6E737A', kind: 'metal',    spec: 0.55, shininess: 68, rim: 0.40, outline: 0.75 },
  pole_wood:        { color: '#7D6A55', kind: 'wall',     spec: 0.05, shininess: 16, rim: 0.22, outline: 0.85 },
  wire_black:       { color: '#2E3036', kind: 'wire',     spec: 0.08, shininess: 20, rim: 0.10, outline: 0.0 },
  vending_red:      { color: '#D94A44', kind: 'metal',    spec: 0.44, shininess: 60, rim: 0.34, outline: 1.0 },
  vending_blue:     { color: '#3E79C7', kind: 'metal',    spec: 0.44, shininess: 60, rim: 0.34, outline: 1.0 },
  vending_white:    { color: '#F2F2F2', kind: 'metal',    spec: 0.35, shininess: 52, rim: 0.30, outline: 1.0 },
  noren_indigo:     { color: '#2F4A7A', kind: 'cloth',    spec: 0.04, shininess: 14, rim: 0.30, outline: 0.85 },
  noren_red:        { color: '#B8443C', kind: 'cloth',    spec: 0.04, shininess: 14, rim: 0.30, outline: 0.85 },
  awning_stripe:    { color: '#E46F5F', kind: 'cloth',    spec: 0.06, shininess: 16, rim: 0.26, outline: 0.9 },
  sign_yellow:      { color: '#F2C84B', kind: 'metal',    spec: 0.22, shininess: 36, rim: 0.25, outline: 0.95 },
  crossing_yellow:  { color: '#F2C230', kind: 'metal',    spec: 0.26, shininess: 40, rim: 0.28, outline: 0.95 },
  crossing_black:   { color: '#2B2B2B', kind: 'metal',    spec: 0.20, shininess: 36, rim: 0.22, outline: 0.6 },
  laundry_white:    { color: '#FBFBF7', kind: 'cloth',    spec: 0.05, shininess: 14, rim: 0.36, outline: 0.75 },
  laundry_blue:     { color: '#9FC3E8', kind: 'cloth',    spec: 0.05, shininess: 14, rim: 0.36, outline: 0.75 },
  laundry_pink:     { color: '#F3B9C5', kind: 'cloth',    spec: 0.05, shininess: 14, rim: 0.36, outline: 0.75 },
  tram_cream:       { color: '#F1E7CF', kind: 'metal',    spec: 0.40, shininess: 58, rim: 0.34, outline: 1.0 },
  tram_green:       { color: '#4F8F6B', kind: 'metal',    spec: 0.42, shininess: 58, rim: 0.36, outline: 1.0 },
  lamp_glow:        { color: '#FFF5D0', kind: 'emissive', spec: 0.0,  shininess: 1,  rim: 0.0,  outline: 0.0 },
  flower_red:       { color: '#E85D5D', kind: 'foliage',  spec: 0.05, shininess: 14, rim: 0.34, outline: 0.15 },
  flower_yellow:    { color: '#F6D365', kind: 'foliage',  spec: 0.05, shininess: 14, rim: 0.34, outline: 0.15 },
};

export function normalizeMatKey(name) {
  if (!name) return '';
  return name.trim().replace(/\.\d+$/, '').toLowerCase();
}

export function lookupMaterialSpec(name, fallbackHex) {
  const key = normalizeMatKey(name);
  if (PALETTE[key]) return { key, ...PALETTE[key] };
  return {
    key: key || 'default',
    color: fallbackHex || '#E8E0D4',
    kind: 'wall',
    spec: 0.08,
    shininess: 22,
    rim: 0.24,
    outline: 0.85,
  };
}
