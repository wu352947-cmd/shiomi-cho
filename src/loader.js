import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { createSignTexture } from './signs.js';

function findNamedAncestor(obj, prefix) {
  let cur = obj;
  while (cur) {
    if (cur.name && cur.name.toLowerCase().startsWith(prefix)) return cur;
    cur = cur.parent;
  }
  return null;
}

function findSignText(obj) {
  let cur = obj;
  while (cur) {
    if (cur.userData && typeof cur.userData.text === 'string' && cur.userData.text.trim()) {
      return cur.userData.text.trim();
    }
    cur = cur.parent;
  }
  return null;
}

async function resolveModelUrl(override) {
  if (override) {
    const clean = override.replace(/[^a-zA-Z0-9._-]/g, '');
    return clean.endsWith('.glb') ? `./public/models/${clean}` : `./public/models/${clean}.glb`;
  }
  const townUrl = './public/models/town.glb';
  try {
    const res = await fetch(townUrl, { method: 'HEAD', cache: 'no-store' });
    if (res.ok) return townUrl;
  } catch {
    // Fallback to stand-in stub
  }
  return './public/models/stub.glb';
}

export async function loadTownModel(materialSystem, onProgress, modelOverride = '') {
  const url = await resolveModelUrl(modelOverride);

  const loader = new GLTFLoader();
  const draco = new DRACOLoader();
  draco.setDecoderPath('./vendor/three/addons/libs/draco/gltf/');
  loader.setDRACOLoader(draco);
  loader.setMeshoptDecoder(MeshoptDecoder);

  const gltf = await new Promise((resolve, reject) => {
    loader.load(
      url,
      resolve,
      (xhr) => {
        if (onProgress && xhr && xhr.total > 0) {
          onProgress(Math.min(0.95, xhr.loaded / xhr.total));
        }
      },
      reject
    );
  });

  const root = gltf.scene;
  root.name = 'TownRoot';

  const boatSet = new Set();
  const tramSet = new Set();
  const solidMeshes = [];
  let lighthouseLamp = null;
  let totalTris = 0;

  root.traverse((obj) => {
    const lname = (obj.name || '').toLowerCase();
    if (lname.startsWith('anim_boat_')) {
      // Only push top-most boat object (avoid double-bobbing child trim meshes)
      const parentBoat = findNamedAncestor(obj.parent, 'anim_boat_');
      if (!parentBoat) boatSet.add(obj);
    }
    if (lname.startsWith('tram') || lname.includes('_tram')) {
      const parentTram = findNamedAncestor(obj.parent, 'tram');
      if (!parentTram) tramSet.add(obj);
    }
    if (lname === 'lighthouse_lamp' || lname.startsWith('lighthouse_lamp')) {
      lighthouseLamp = obj;
    }

    if (!obj.isMesh) return;

    const geo = obj.geometry;
    if (geo) {
      if (!geo.attributes.normal) geo.computeVertexNormals();
      const idx = geo.index;
      totalTris += idx ? idx.count / 3 : (geo.attributes.position ? geo.attributes.position.count / 3 : 0);
    }

    const hasAO = Boolean(geo && geo.attributes && geo.attributes.color);
    const isTree = Boolean(findNamedAncestor(obj, 'anim_tree_'));
    const isFlag = Boolean(findNamedAncestor(obj, 'anim_flag_'));
    const animMode = isTree ? 1 : (isFlag ? 2 : 0);

    // Check for sign_* mesh with extras.text
    const signObj = findNamedAncestor(obj, 'sign_');
    const signText = signObj ? findSignText(obj) : null;
    const signMap = signText ? createSignTexture(signText, obj) : null;

    const replaceMat = (orig) => {
      const matName = orig ? orig.name : '';
      const fallbackCol = orig && orig.color ? orig.color : null;
      const ds = orig ? orig.side === THREE.DoubleSide : false;
      return materialSystem.makeToonMaterial(matName, fallbackCol, {
        animMode,
        hasAO,
        doubleSided: ds || Boolean(signMap),
        signMap,
      });
    };

    if (Array.isArray(obj.material)) {
      obj.material = obj.material.map(replaceMat);
    } else {
      obj.material = replaceMat(obj.material);
    }

    const primaryMat = Array.isArray(obj.material) ? obj.material[0] : obj.material;
    const spec = primaryMat?.userData?.spec;
    const outlineWeight = spec ? spec.outline : 0.85;
    const isBg = lname.startsWith('bg_') || lname.includes('mountain') || lname.includes('island');
    const isWire = spec && spec.kind === 'wire';
    const isEmissive = spec && spec.kind === 'emissive';

    obj.castShadow = !isBg && !isWire && !isEmissive;
    obj.receiveShadow = !isBg && !isWire && !isEmissive;

    // Attach prepass material for depth+normal outline & ocean depth buffer
    obj.userData.toonMaterial = obj.material;
    obj.userData.normalMaskMaterial = materialSystem.makeNormalMaskMaterial(
      isBg ? 0.0 : outlineWeight,
      animMode,
      primaryMat && primaryMat.side === THREE.DoubleSide
    );
    solidMeshes.push(obj);
  });

  if (onProgress) onProgress(1.0);
  draco.dispose();

  return {
    root,
    url,
    solidMeshes,
    boats: Array.from(boatSet),
    trams: Array.from(tramSet),
    lighthouseLamp,
    totalTris: Math.round(totalTris),
  };
}
