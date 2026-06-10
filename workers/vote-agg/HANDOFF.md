# Handoff: vote-agg Worker (votes.bci.place) — currently DOWN

## Status (verified 2026-06-10)
- `https://bci.red` → 200 (live UI)  ·  `https://bci.blue` → 200 (live UI)
- `https://votes.bci.place/items` → **HTTP 000 (not responding)**
- No Worker source exists in `plurigrid/place` (this repo). Either it lives in another
  repo (e.g. plurigrid/asi) or was never shipped. The device ledger (`bci/devices/bcf-devices.tree`,
  `trees/bcf-INV-MASTER.tree`) describes it in present tense regardless.

## What the Worker must do (extracted from the ledger)
1. **Daily rotation** (cron `0 0 * * *`, 00:00 UTC): from the device ledger, take items with
   `status ∈ {want, aspirational}` (NOTE: `building` was removed from rotation 2026-06-10),
   pick 2 whose `cost_usd` ranges overlap within 1.5×. Deterministic: seed = date.
2. **`GET /items`** → today's pair as JSON: `{pair_id, seed, a:{id,name,cost,...}, b:{...}}`.
   bci.red renders side A, bci.blue side B.
3. **`POST /vote`** ← payload `{pair_id, side, final_state_hash, seed}`. `side ∈ {red,blue}`.
   `final_state_hash` commits to the in-browser simulation state the voter reached.
   Tally per pair_id; persist in KV.
4. **`GET /health`** → status JSON.

## Deploy recipe (Cloudflare Workers)
- `wrangler.jsonc` here sets name=`vote-agg`, a `[triggers] crons=["0 0 * * *"]`, KV binding `VOTES`,
  and custom domain route `votes.bci.place/*`.
- `export CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=...` then `npx wrangler deploy`.
- Custom domain `votes.bci.place` must be a zone on the account; add as `custom_domain` route.
- `src/index.js` here is a working skeleton implementing the 4 endpoints + KV tally.

## Open questions for the human
- Which repo/account currently owns the deployment? (so this doesn't duplicate it)
- Source of the device list at request time: read the forest's built JSON, or a KV snapshot?
