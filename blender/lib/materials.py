"""Exact ART_BIBLE named materials for Shiomi-cho (汐見町).

All material names strictly match ART_BIBLE.md keys (65 materials total).
sRGB hex colors are converted to linear RGB for Blender Principled BSDF so
glTF 2.0 baseColorFactor values match the Art Bible sRGB palette accurately.
"""

import bpy


def srgb_channel_to_linear(c: float) -> float:
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear_rgba(hex_str: str) -> tuple[float, float, float, float]:
    h = hex_str.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (
        srgb_channel_to_linear(r),
        srgb_channel_to_linear(g),
        srgb_channel_to_linear(b),
        1.0,
    )


# (hex, roughness, metallic, emission_strength, emission_hex)
PALETTE: dict[str, tuple[str, float, float, float, str | None]] = {
    # Walls
    "wall_cream": ("#F3E6CC", 0.85, 0.0, 0.0, None),
    "wall_white": ("#F6F2EA", 0.84, 0.0, 0.0, None),
    "wall_peach": ("#F2CBB0", 0.85, 0.0, 0.0, None),
    "wall_mint": ("#CFE6D6", 0.85, 0.0, 0.0, None),
    "wall_sky": ("#C9DDF0", 0.85, 0.0, 0.0, None),
    "wood_dark": ("#6B4A36", 0.78, 0.0, 0.0, None),
    "wood_light": ("#B88A5E", 0.76, 0.0, 0.0, None),
    "wood_weathered": ("#8E8173", 0.88, 0.0, 0.0, None),
    # Roofs (kawara tiles, slightly glossy)
    "roof_blue": ("#3F5F8C", 0.36, 0.05, 0.0, None),
    "roof_teal": ("#3E7D7A", 0.36, 0.05, 0.0, None),
    "roof_terracotta": ("#B5583F", 0.42, 0.03, 0.0, None),
    "roof_charcoal": ("#4A4E58", 0.38, 0.06, 0.0, None),
    "roof_tin_red": ("#A8453C", 0.48, 0.35, 0.0, None),
    # Trim
    "trim_white": ("#FAFAF5", 0.65, 0.0, 0.0, None),
    "window_glass": ("#8FB8D9", 0.12, 0.15, 0.18, "#A6CEE8"),
    "window_frame": ("#E9E3D6", 0.60, 0.05, 0.0, None),
    "shoji": ("#F4EBD8", 0.82, 0.0, 0.04, "#FFF5DF"),
    "door_wood": ("#7A5233", 0.72, 0.0, 0.0, None),
    # Ground
    "grass": ("#8CC56A", 0.92, 0.0, 0.0, None),
    "grass_dark": ("#5E9E55", 0.92, 0.0, 0.0, None),
    "dirt_path": ("#D8C39A", 0.94, 0.0, 0.0, None),
    "stone": ("#BDB6A8", 0.88, 0.0, 0.0, None),
    "stone_dark": ("#8C877E", 0.90, 0.0, 0.0, None),
    "asphalt": ("#7C8088", 0.90, 0.0, 0.0, None),
    "road_line": ("#F5F2E8", 0.82, 0.0, 0.0, None),
    "concrete": ("#CFCAC0", 0.88, 0.0, 0.0, None),
    "sand": ("#EADBB2", 0.94, 0.0, 0.0, None),
    "cliff_rock": ("#A99C88", 0.92, 0.0, 0.0, None),
    # Nature
    "leaf_green": ("#6FB04F", 0.82, 0.0, 0.0, None),
    "leaf_light": ("#A6D46A", 0.80, 0.0, 0.0, None),
    "leaf_dark": ("#3F7E43", 0.84, 0.0, 0.0, None),
    "sakura": ("#F7C6D4", 0.78, 0.0, 0.0, None),
    "sakura_deep": ("#EE9DB5", 0.78, 0.0, 0.0, None),
    "bark": ("#6E5444", 0.90, 0.0, 0.0, None),
    "hydrangea_blue": ("#8DA8E8", 0.78, 0.0, 0.0, None),
    "hydrangea_pink": ("#E7A3C6", 0.78, 0.0, 0.0, None),
    "sunflower": ("#F5C542", 0.76, 0.0, 0.0, None),
    # Accent
    "torii_red": ("#D8443A", 0.45, 0.0, 0.0, None),
    "lighthouse_white": ("#F7F7F2", 0.55, 0.0, 0.0, None),
    "lighthouse_red": ("#D84B3E", 0.48, 0.0, 0.0, None),
    "boat_white": ("#F4F4EF", 0.42, 0.05, 0.0, None),
    "boat_blue": ("#3C76B8", 0.42, 0.05, 0.0, None),
    "boat_red": ("#C9503F", 0.45, 0.05, 0.0, None),
    "metal_grey": ("#9AA1AA", 0.42, 0.65, 0.0, None),
    "metal_dark": ("#4F555E", 0.45, 0.70, 0.0, None),
    "rail_steel": ("#6E737A", 0.35, 0.82, 0.0, None),
    "pole_wood": ("#7D6A55", 0.86, 0.0, 0.0, None),
    "wire_black": ("#2E3036", 0.60, 0.20, 0.0, None),
    "vending_red": ("#D94A44", 0.35, 0.15, 0.0, None),
    "vending_blue": ("#3E79C7", 0.35, 0.15, 0.0, None),
    "vending_white": ("#F2F2F2", 0.35, 0.10, 0.0, None),
    "noren_indigo": ("#2F4A7A", 0.88, 0.0, 0.0, None),
    "noren_red": ("#B8443C", 0.88, 0.0, 0.0, None),
    "awning_stripe": ("#E46F5F", 0.82, 0.0, 0.0, None),
    "sign_yellow": ("#F2C84B", 0.50, 0.05, 0.0, None),
    "crossing_yellow": ("#F2C230", 0.45, 0.10, 0.0, None),
    "crossing_black": ("#2B2B2B", 0.50, 0.10, 0.0, None),
    "laundry_white": ("#FBFBF7", 0.86, 0.0, 0.0, None),
    "laundry_blue": ("#9FC3E8", 0.86, 0.0, 0.0, None),
    "laundry_pink": ("#F3B9C5", 0.86, 0.0, 0.0, None),
    "tram_cream": ("#F1E7CF", 0.42, 0.15, 0.0, None),
    "tram_green": ("#4F8F6B", 0.42, 0.15, 0.0, None),
    "lamp_glow": ("#FFE8A8", 0.25, 0.0, 2.2, "#FFD984"),
    "flower_red": ("#E85D5D", 0.78, 0.0, 0.0, None),
    "flower_yellow": ("#F6D365", 0.78, 0.0, 0.0, None),
}

_CACHE: dict[str, bpy.types.Material] = {}


def reset_cache() -> None:
    _CACHE.clear()


def get_mat(name: str) -> bpy.types.Material:
    """Return (or create) an ART_BIBLE material by exact key name."""
    if name not in PALETTE:
        raise KeyError(f"Material '{name}' is not in ART_BIBLE PALETTE!")
    mat = _CACHE.get(name)
    if mat is not None and mat.name in bpy.data.materials:
        return mat
    existing = bpy.data.materials.get(name)
    if existing is not None:
        _CACHE[name] = existing
        return existing

    hex_col, rough, metal, em_strength, em_hex = PALETTE[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        nt.nodes.clear()
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    rgba = hex_to_linear_rgba(hex_col)
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.28 if rough > 0.7 else 0.55
    if em_strength > 0.0:
        em_rgba = hex_to_linear_rgba(em_hex or hex_col)
        bsdf.inputs["Emission Color"].default_value = em_rgba
        bsdf.inputs["Emission Strength"].default_value = em_strength
    mat.diffuse_color = rgba
    _CACHE[name] = mat
    return mat


def create_all_materials() -> dict[str, bpy.types.Material]:
    reset_cache()
    return {name: get_mat(name) for name in PALETTE}


def toggle_ao_preview(enable: bool, attr_name: str = "AO") -> None:
    """Wire vertex color AO multiply into Principled BSDF for Eevee preview only.

    Disable before glTF export so glTF keeps pure ART_BIBLE baseColorFactor
    alongside the COLOR_0 vertex attribute.
    """
    for name, mat in list(bpy.data.materials.items()):
        if name not in PALETTE or not mat.use_nodes:
            continue
        nt = mat.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        # Remove any existing AO preview nodes
        for node in list(nt.nodes):
            if node.name.startswith("_AO_"):
                nt.nodes.remove(node)
        rgba = hex_to_linear_rgba(PALETTE[name][0])
        bsdf.inputs["Base Color"].default_value = rgba
        if enable and name != "lamp_glow":
            attr = nt.nodes.new("ShaderNodeVertexColor")
            attr.name = "_AO_ATTR"
            attr.layer_name = attr_name
            mix = nt.nodes.new("ShaderNodeMix")
            mix.name = "_AO_MIX"
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 0.85
            mix.inputs["A"].default_value = rgba
            nt.links.new(attr.outputs["Color"], mix.inputs["B"])
            nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
