// vote-agg Worker — see ../HANDOFF.md. Skeleton: GET /items, POST /vote, GET /health.
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' };
const json = (d, s = 200) => new Response(JSON.stringify(d, null, 2), { status: s, headers: { 'Content-Type': 'application/json', ...CORS } });
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
    if (url.pathname === '/health') return json({ status: 'healthy', service: 'vote-agg' });
    if (url.pathname === '/items') { const p = await env.VOTES.get('today', 'json'); return p ? json(p) : json({ error: 'no pair yet; cron not run' }, 503); }
    if (url.pathname === '/vote' && req.method === 'POST') {
      const v = await req.json();
      if (!v.pair_id || !['red', 'blue'].includes(v.side)) return json({ error: 'bad payload' }, 400);
      const key = `tally:${v.pair_id}`; const t = (await env.VOTES.get(key, 'json')) || { red: 0, blue: 0 };
      t[v.side]++; await env.VOTES.put(key, JSON.stringify(t)); return json({ ok: true, tally: t });
    }
    return json({ error: 'not found', endpoints: ['GET /items', 'POST /vote', 'GET /health'] }, 404);
  },
  async scheduled(_e, env) {
    // TODO: read device ledger, pick 2 want/aspirational items with cost overlap <=1.5x, seed=date, store as 'today'.
    // Placeholder so the cron is wired; replace with real selection against the forest's device JSON.
    await env.VOTES.put('today', JSON.stringify({ pair_id: 'TODO', note: 'implement selection from ledger' }));
  },
};
