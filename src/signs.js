import * as THREE from 'three';

const THEMES = [
  { bg: '#F7F1DF', border: '#2E4F7E', text: '#213452', accent: '#C84B3C' }, // retro cream & navy
  { bg: '#2C4976', border: '#E8DFC5', text: '#F9F5E8', accent: '#E8B84B' }, // indigo noren sign
  { bg: '#F2CC57', border: '#5A3A24', text: '#3A2416', accent: '#C54636' }, // warm shop yellow
  { bg: '#EFE7D4', border: '#3E7A74', text: '#2A4E4B', accent: '#D8634B' }, // coastal teal trim
  { bg: '#B9463E', border: '#F6ECD8', text: '#FFF9EC', accent: '#F2C84B' }, // warm vermilion
];

function hashStr(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

export function createSignTexture(text, mesh) {
  const cleanText = String(text || '').trim();
  if (!cleanText) return null;

  // Inspect mesh geometry bounds to decide vertical vs horizontal signboard
  let vertical = false;
  if (mesh && mesh.geometry) {
    mesh.geometry.computeBoundingBox();
    const bb = mesh.geometry.boundingBox;
    if (bb) {
      const dx = bb.max.x - bb.min.x;
      const dy = bb.max.y - bb.min.y;
      const dz = bb.max.z - bb.min.z;
      const horiz = Math.max(dx, dz);
      vertical = dy > horiz * 1.15;
    }
  }

  const w = vertical ? 256 : 512;
  const h = vertical ? 512 : 200;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');

  const isStation = cleanText.includes('しおみ') || (mesh && /station/i.test(mesh.name));
  const theme = isStation
    ? { bg: '#FAFAF5', border: '#2E6B8A', text: '#1F3448', accent: '#3B8A7E' }
    : THEMES[hashStr(cleanText) % THEMES.length];

  // Background fill
  ctx.fillStyle = theme.bg;
  ctx.fillRect(0, 0, w, h);

  // Subtle hand-painted wood/enamel wash & grain strokes
  ctx.save();
  ctx.globalAlpha = 0.08;
  for (let i = 0; i < 28; i++) {
    ctx.fillStyle = i % 2 === 0 ? '#FFFFFF' : '#5B4636';
    if (vertical) {
      ctx.fillRect((i * 19) % w, 0, 5, h);
    } else {
      ctx.fillRect(0, (i * 13) % h, w, 4);
    }
  }
  ctx.restore();

  // Frame border
  const pad = 12;
  ctx.strokeStyle = theme.border;
  ctx.lineWidth = 7;
  ctx.strokeRect(pad, pad, w - pad * 2, h - pad * 2);
  ctx.strokeStyle = theme.accent;
  ctx.lineWidth = 2;
  ctx.strokeRect(pad + 7, pad + 7, w - (pad + 7) * 2, h - (pad + 7) * 2);

  // Station horizontal stripe decoration
  if (isStation && !vertical) {
    ctx.fillStyle = theme.accent;
    ctx.fillRect(pad + 8, h - 42, w - (pad + 8) * 2, 10);
    ctx.fillStyle = '#536D85';
    ctx.font = '600 18px "Hiragino Kaku Gothic ProN", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('SHIOMI', w * 0.5, h - 24);
  }

  // Hand-painted Japanese brush/serif lettering
  const chars = Array.from(cleanText);
  const fontStack = '"Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", "Hiragino Kaku Gothic ProN", serif';
  ctx.fillStyle = theme.text;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  if (vertical) {
    const availH = h - 76;
    const step = availH / Math.max(1, chars.length);
    const fontSize = Math.min(78, Math.floor(step * 0.84));
    ctx.font = `700 ${fontSize}px ${fontStack}`;
    const startY = (h - step * (chars.length - 1)) * 0.5;
    chars.forEach((ch, idx) => {
      const jitterX = (((idx * 37) % 5) - 2) * 0.8;
      ctx.fillText(ch, w * 0.5 + jitterX, startY + idx * step);
    });
  } else {
    const availW = w - 68;
    const maxSize = isStation ? 74 : 84;
    const fontSize = Math.min(maxSize, Math.floor(availW / Math.max(1.5, chars.length * 1.05)));
    ctx.font = `700 ${fontSize}px ${fontStack}`;
    const cy = isStation ? h * 0.41 : h * 0.52;
    // Slight warm ink shadow for crisp readability
    ctx.save();
    ctx.globalAlpha = 0.16;
    ctx.fillStyle = '#000000';
    ctx.fillText(cleanText, w * 0.5 + 2, cy + 2);
    ctx.restore();
    ctx.fillText(cleanText, w * 0.5, cy);
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.flipY = false; // glTF 2.0 UV origin is top-left
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  tex.needsUpdate = true;
  return tex;
}
