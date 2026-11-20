/**
 * Wheelchair accessible-area raster (bookmark trick #21).
 * Twin of interior/accessible_area.py — same grid, disk, dilation, flood.
 *
 * 2bed.json has no floor polyline (#18). Layout is interior/accessible_layout.json
 * (v4 outline + partitions + furniture footprints). Label: indicative.
 * ADM Vol 1 (2015/2016 amendments):
 *   https://www.gov.uk/government/publications/access-to-and-use-of-buildings-approved-document-m
 *   https://assets.publishing.service.gov.uk/media/5a7f8a82ed915d74e622b17b/BR_PDF_AD_M1_2015_with_2016_amendments_V3.pdf
 * Wheelchair *passage* width 750 mm = M4(2) 2.22.b (ADM does not state a body width).
 * 1500 mm turning circle: M4(3) 3.14.d, 3.22.d, 3.43.e.
 */
export const CELL = 0.05;
export const WHEELCHAIR_WIDTH = 0.75;
export const ERODE_R = WHEELCHAIR_WIDTH / 2;
export const TURN_D = 1.5;
export const TURN_R = TURN_D / 2;
export const SOURCED_AREA = 63.0;

function disk(radiusM) {
  const r = Math.ceil(radiusM / CELL);
  const r2 = (radiusM / CELL) ** 2;
  const out = [];
  for (let di = -r; di <= r; di++) {
    for (let dj = -r; dj <= r; dj++) {
      if (di * di + dj * dj <= r2 + 1e-9) out.push([di, dj]);
    }
  }
  return out;
}
const DISK_ERODE = disk(ERODE_R);
const DISK_TURN = disk(TURN_R);

function pip(x, z, poly) {
  let c = false, j = poly.length - 1;
  for (let i = 0; i < poly.length; i++) {
    const xi = poly[i][0], zi = poly[i][1], xj = poly[j][0], zj = poly[j][1];
    if (((zi > z) !== (zj > z)) && (x < (xj - xi) * (z - zi) / (zj - zi) + xi)) c = !c;
    j = i;
  }
  return c;
}

function rot(px, pz, ang) {
  const c = Math.cos(ang), s = Math.sin(ang);
  return [px * c - pz * s, px * s + pz * c];
}

function wallHit(x, z, walls) {
  for (const w of walls) {
    const ax = w.a[0], az = w.a[1], bx = w.b[0], bz = w.b[1];
    const dx = bx - ax, dz = bz - az;
    const L2 = dx * dx + dz * dz;
    if (L2 < 1e-18) continue;
    const t = ((x - ax) * dx + (z - az) * dz) / L2;
    if (t < 0 || t > 1) continue;
    const s = t * Math.sqrt(L2);
    let blocked = true;
    for (const g of w.gaps || []) {
      if (g[0] <= s && s <= g[1]) { blocked = false; break; }
    }
    if (!blocked) continue;
    const px = ax + t * dx, pz = az + t * dz;
    const half = w.t / 2;
    if ((x - px) ** 2 + (z - pz) ** 2 <= half * half) return true;
  }
  return false;
}

function dilate(obs, w, h, diskOff) {
  const out = obs.slice();
  for (const [di, dj] of diskOff) {
    if (di === 0 && dj === 0) continue;
    for (let i = 0; i < w; i++) {
      const ii = i + di;
      if (ii < 0 || ii >= w) continue;
      const iOff = i * h, iiOff = ii * h;
      for (let j = 0; j < h; j++) {
        const jj = j + dj;
        if (jj < 0 || jj >= h) continue;
        if (obs[iOff + j]) out[iiOff + jj] = 1;
      }
    }
  }
  return out;
}

const cache = new WeakMap();

export function prepare(layout) {
  let g = cache.get(layout);
  if (g) return g;
  const floor = layout.floor;
  const xs = floor.map(p => p[0]), zs = floor.map(p => p[1]);
  const pad = 0.80;
  const xmin = Math.min(...xs) - pad, xmax = Math.max(...xs) + pad;
  const zmin = Math.min(...zs) - pad, zmax = Math.max(...zs) + pad;
  const origin_x = Math.floor(xmin / CELL) * CELL;
  const origin_z = Math.floor(zmin / CELL) * CELL;
  const w = Math.ceil((xmax - origin_x) / CELL);
  const h = Math.ceil((zmax - origin_z) / CELL);
  const inFloor = new Uint8Array(w * h);
  const wall = new Uint8Array(w * h);
  const room = new Int16Array(w * h);
  room.fill(-1);
  const ids = layout.rooms.map(r => r.id);
  const idIndex = Object.fromEntries(ids.map((id, i) => [id, i]));
  for (let i = 0; i < w; i++) {
    const x = origin_x + (i + 0.5) * CELL;
    for (let j = 0; j < h; j++) {
      const z = origin_z + (j + 0.5) * CELL;
      const k = i * h + j;
      if (!pip(x, z, floor)) continue;
      inFloor[k] = 1;
      if (wallHit(x, z, layout.walls)) { wall[k] = 1; continue; }
      for (const r of layout.rooms) {
        if (pip(x, z, r.poly)) { room[k] = idIndex[r.id]; break; }
      }
    }
  }
  let changed = true;
  while (changed) {
    changed = false;
    for (let i = 0; i < w; i++) {
      for (let j = 0; j < h; j++) {
        const k = i * h + j;
        if (!inFloor[k] || wall[k] || room[k] >= 0) continue;
        const votes = new Map();
        for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const ii = i + di, jj = j + dj;
          if (ii < 0 || jj < 0 || ii >= w || jj >= h) continue;
          const rr = room[ii * h + jj];
          if (rr >= 0) votes.set(rr, (votes.get(rr) || 0) + 1);
        }
        if (votes.size) {
          let best = -1, n = -1;
          for (const [id, c] of votes) if (c > n) { best = id; n = c; }
          room[k] = best;
          changed = true;
        }
      }
    }
  }
  const staticClear = new Uint8Array(w * h);
  for (let k = 0; k < w * h; k++) staticClear[k] = inFloor[k] && !wall[k] ? 1 : 0;
  g = { origin_x, origin_z, w, h, inFloor, wall, room, ids, staticClear };
  cache.set(layout, g);
  return g;
}

export function compute(layout, hidden) {
  hidden = new Set(hidden || []);
  const t0 = (typeof performance !== 'undefined' ? performance.now() : Date.now());
  const g = prepare(layout);
  const { origin_x, origin_z, w, h, inFloor, room, ids, staticClear } = g;
  const furn = new Uint8Array(w * h);
  for (const it of layout.furniture) {
    if (hidden.has(it.name)) continue;
    const cx = it.c[0], cz = it.c[1], sx = it.s[0], sz = it.s[1];
    const rotA = it.rot || 0;
    const rad = 0.5 * Math.hypot(sx, sz);
    const i0 = Math.max(0, Math.floor((cx - rad - origin_x) / CELL) - 1);
    const i1 = Math.min(w, Math.floor((cx + rad - origin_x) / CELL) + 2);
    const j0 = Math.max(0, Math.floor((cz - rad - origin_z) / CELL) - 1);
    const j1 = Math.min(h, Math.floor((cz + rad - origin_z) / CELL) + 2);
    const isCirc = it.shape === 'circle';
    const hx = sx / 2, hz = sz / 2;
    for (let i = i0; i < i1; i++) {
      const x = origin_x + (i + 0.5) * CELL;
      for (let j = j0; j < j1; j++) {
        const z = origin_z + (j + 0.5) * CELL;
        const [lx, lz] = rot(x - cx, z - cz, -rotA);
        if (isCirc) {
          if (lx * lx + lz * lz <= hx * hx) furn[i * h + j] = 1;
        } else if (Math.abs(lx) <= hx && Math.abs(lz) <= hz) {
          furn[i * h + j] = 1;
        }
      }
    }
  }
  const N = w * h;
  const free = new Uint8Array(N);
  const obst = new Uint8Array(N);
  for (let k = 0; k < N; k++) {
    const f = staticClear[k] && !furn[k] ? 1 : 0;
    free[k] = f;
    obst[k] = f ? 0 : 1;
  }
  const nav = new Uint8Array(N);
  for (let i = 0; i < w; i++) {
    for (let j = 0; j < h; j++) {
      const k = i * h + j;
      if (!free[k]) continue;
      let ok = true;
      for (const [di, dj] of DISK_ERODE) {
        const ii = i + di, jj = j + dj;
        if (ii < 0 || jj < 0 || ii >= w || jj >= h || !free[ii * h + jj]) { ok = false; break; }
      }
      if (ok) nav[k] = 1;
    }
  }

  const sx = layout.entrance.seed[0], sz = layout.entrance.seed[1];
  let si = Math.floor((sx - origin_x) / CELL);
  let sj = Math.floor((sz - origin_z) / CELL);
  if (!(si >= 0 && sj >= 0 && si < w && sj < h && nav[si * h + sj])) {
    let found = false;
    for (let r = 0; r < 30 && !found; r++) {
      for (let di = -r; di <= r && !found; di++) {
        for (let dj = -r; dj <= r; dj++) {
          const ii = si + di, jj = sj + dj;
          if (ii >= 0 && jj >= 0 && ii < w && jj < h && nav[ii * h + jj]) {
            si = ii; sj = jj; found = true; break;
          }
        }
      }
    }
  }
  const reach = new Uint8Array(N);
  const stack = [];
  if (si >= 0 && sj >= 0 && si < w && sj < h && nav[si * h + sj]) {
    stack.push(si, sj);
    reach[si * h + sj] = 1;
  }
  while (stack.length) {
    const j = stack.pop(), i = stack.pop();
    const nbs = [i + 1, j, i - 1, j, i, j + 1, i, j - 1];
    for (let n = 0; n < 8; n += 2) {
      const ii = nbs[n], jj = nbs[n + 1];
      if (ii < 0 || jj < 0 || ii >= w || jj >= h) continue;
      const k = ii * h + jj;
      if (nav[k] && !reach[k]) { reach[k] = 1; stack.push(ii, jj); }
    }
  }

  const cellA = CELL * CELL;
  const rooms = {};
  for (let ridI = 0; ridI < ids.length; ridI++) {
    let nClear = 0, nReach = 0, turn = false;
    for (let i = 0; i < w; i++) {
      for (let j = 0; j < h; j++) {
        const k = i * h + j;
        if (room[k] !== ridI) continue;
        if (free[k]) nClear++;
        if (reach[k]) nReach++;
        if (!turn && free[k]) {
          let ok = true;
          for (const [di, dj] of DISK_TURN) {
            const ii = i + di, jj = j + dj;
            if (ii < 0 || jj < 0 || ii >= w || jj >= h || !free[ii * h + jj] || room[ii * h + jj] !== ridI) {
              ok = false; break;
            }
          }
          if (ok) turn = true;
        }
      }
    }
    rooms[ids[ridI]] = {
      reachable_m2: Math.round(nReach * cellA * 10000) / 10000,
      clear_m2: Math.round(nClear * cellA * 10000) / 10000,
      turning_circle: turn,
    };
  }
  let nFree = 0, nNav = 0, nReach = 0;
  for (let k = 0; k < N; k++) {
    if (free[k]) nFree++;
    if (nav[k]) nNav++;
    if (reach[k]) nReach++;
  }
  const grid = new Uint8Array(w * h);
  for (let i = 0; i < w; i++) {
    for (let j = 0; j < h; j++) {
      const k = i * h + j;
      grid[j * w + i] = !inFloor[k] ? 0 : (reach[k] ? 2 : 1);
    }
  }
  const ms = (typeof performance !== 'undefined' ? performance.now() : Date.now()) - t0;
  const reachable = nReach * cellA;
  return {
    label: 'indicative',
    approximate_layout: true,
    cell_m: CELL,
    wheelchair_width_m: WHEELCHAIR_WIDTH,
    erode_radius_m: ERODE_R,
    turning_circle_diameter_m: TURN_D,
    hidden: [...hidden].sort(),
    clear_floor_m2: Math.round(nFree * cellA * 10000) / 10000,
    navigable_m2: Math.round(nNav * cellA * 10000) / 10000,
    reachable_m2: Math.round(reachable * 10000) / 10000,
    sourced_floor_m2: SOURCED_AREA,
    reachable_le_sourced: reachable <= SOURCED_AREA + 1e-9,
    rooms,
    seed_cell: [si, sj],
    recompute_ms: Math.round(ms * 1000) / 1000,
    overlay: { origin: [origin_x, origin_z], cell: CELL, w, h, grid },
  };
}

export function dropOverlay(result) {
  const { overlay, ...rest } = result;
  return rest;
}
