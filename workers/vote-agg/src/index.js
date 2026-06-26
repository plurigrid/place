// vote-agg Worker — votes.bci.place
// Implements daily rotation triggers, GET /items, POST /vote, and GET /health.

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type'
};

const json = (d, s = 200) => new Response(JSON.stringify(d, null, 2), {
  status: s,
  headers: { 'Content-Type': 'application/json', ...CORS }
});

// Helper: parse min and max numeric cost from ranges like "500-1500 USD" or "1650 USD"
function parseCostRange(str) {
  if (!str) return null;
  const cleanStr = str.replace(/,/g, '');
  
  // check for a range: e.g. "500-1500"
  const rangeMatch = cleanStr.match(/(\d+)\s*-\s*(\d+)/);
  if (rangeMatch) {
    const min = parseFloat(rangeMatch[1]);
    const max = parseFloat(rangeMatch[2]);
    if (!isNaN(min) && !isNaN(max)) {
      return [min, max];
    }
  }
  
  // check for single number: e.g. "1650 USD"
  const singleMatch = cleanStr.match(/(\d+)/);
  if (singleMatch) {
    // support multiplier format if encountered (e.g. "130 USD x3")
    const multMatch = cleanStr.match(/(\d+)\s*(?:USD)?\s*[xX]\s*(\d+)/);
    if (multMatch) {
      const val = parseFloat(multMatch[1]) * parseFloat(multMatch[2]);
      return [val, val];
    }
    const val = parseFloat(singleMatch[1]);
    if (!isNaN(val)) {
      return [val, val];
    }
  }
  
  return null;
}

// Helper: checks if range A and B overlap within a 1.5x factor
function doesOverlap(rangeA, rangeB) {
  return Math.max(rangeA[0], rangeB[0]) <= 1.5 * Math.min(rangeA[1], rangeB[1]);
}

// Deterministic seed PRNG (FNV-1a + Mulberry32)
function getSeededRandom(seedStr) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < seedStr.length; i++) {
    h = Math.imul(h ^ seedStr.charCodeAt(i), 16777619);
  }
  let seed = h >>> 0;
  let t = seed + 0x6D2B79F5;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

// Fetch ledger and generate pair for a given date
async function generatePairForDate(env, dateStr) {
  const url = env.FOREST_JSON_URL || 'https://bci.red/forest.json';
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch forest.json from ${url}: ${res.status}`);
  }
  const data = await res.json();
  
  const candidates = [];
  for (const [key, val] of Object.entries(data)) {
    if (val.taxon === 'Inventory-item') {
      const status = (val.metas.status || '').toLowerCase();
      // want/aspirational filter (case-insensitive)
      if (status === 'want' || status === 'aspirational') {
        const costStr = val.metas['cost-range'];
        const range = parseCostRange(costStr);
        if (range) {
          candidates.push({
            id: key,
            name: val.title,
            cost: costStr,
            range,
            raw: val
          });
        }
      }
    }
  }

  // Deterministically sort candidates by ID to maintain stable pair ordering across engines
  candidates.sort((a, b) => a.id.localeCompare(b.id));

  const pairs = [];
  for (let i = 0; i < candidates.length; i++) {
    for (let j = i + 1; j < candidates.length; j++) {
      if (doesOverlap(candidates[i].range, candidates[j].range)) {
        pairs.push([candidates[i], candidates[j]]);
      }
    }
  }

  if (pairs.length === 0) {
    throw new Error('No overlapping pairs found in inventory items');
  }

  const rand = getSeededRandom(dateStr);
  const idx = Math.floor(rand * pairs.length);
  const chosen = pairs[idx];

  const ids = [chosen[0].id, chosen[1].id].sort();
  const pair_id = `${ids[0]}:${ids[1]}`;

  return {
    pair_id,
    seed: dateStr,
    a: {
      id: chosen[0].id,
      name: chosen[0].name,
      cost: chosen[0].cost,
      ...chosen[0].raw
    },
    b: {
      id: chosen[1].id,
      name: chosen[1].name,
      cost: chosen[1].cost,
      ...chosen[1].raw
    }
  };
}

// Retrieve pair for today with transparent on-the-fly generation & caching
async function getTodayPair(env, forceDate) {
  const d = forceDate ? new Date(forceDate) : new Date();
  if (isNaN(d.getTime())) {
    throw new Error('Invalid date format');
  }
  const year = d.getUTCFullYear();
  const month = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  const dateStr = `${year}-${month}-${day}`;

  if (!forceDate) {
    const cached = await env.VOTES.get('today', 'json');
    if (cached && cached.seed === dateStr) {
      return cached;
    }
  }

  const pair = await generatePairForDate(env, dateStr);

  if (!forceDate) {
    await env.VOTES.put('today', JSON.stringify(pair));
  }
  return pair;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
    
    if (url.pathname === '/health') {
      return json({ status: 'healthy', service: 'vote-agg' });
    }
    
    if (url.pathname === '/items') {
      try {
        const forceDate = url.searchParams.get('date');
        const p = await getTodayPair(env, forceDate);
        return json(p);
      } catch (err) {
        return json({ error: err.message }, 500);
      }
    }
    
    if (url.pathname === '/vote' && req.method === 'POST') {
      try {
        const v = await req.json();
        if (!v.pair_id || !['red', 'blue'].includes(v.side)) {
          return json({ error: 'bad payload' }, 400);
        }
        const key = `tally:${v.pair_id}`;
        const t = (await env.VOTES.get(key, 'json')) || { red: 0, blue: 0 };
        t[v.side]++;
        await env.VOTES.put(key, JSON.stringify(t));
        return json({ ok: true, tally: t });
      } catch (err) {
        return json({ error: err.message }, 500);
      }
    }
    
    return json({
      error: 'not found',
      endpoints: ['GET /items', 'POST /vote', 'GET /health']
    }, 404);
  },

  async scheduled(event, env) {
    try {
      const d = event.scheduledTime ? new Date(event.scheduledTime) : new Date();
      const year = d.getUTCFullYear();
      const month = String(d.getUTCMonth() + 1).padStart(2, '0');
      const day = String(d.getUTCDate()).padStart(2, '0');
      const dateStr = `${year}-${month}-${day}`;

      const pair = await generatePairForDate(env, dateStr);
      await env.VOTES.put('today', JSON.stringify(pair));
      console.log(`Cron: successfully rotated today's pair to ${pair.pair_id} for date ${dateStr}`);
    } catch (err) {
      console.error('Cron: failed to run daily rotation:', err);
    }
  }
};
