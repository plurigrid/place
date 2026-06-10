var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// src/index.js
var CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type"
};
var json = /* @__PURE__ */ __name((d, s = 200) => new Response(JSON.stringify(d, null, 2), {
  status: s,
  headers: { "Content-Type": "application/json", ...CORS }
}), "json");
function parseCostRange(str) {
  if (!str) return null;
  const cleanStr = str.replace(/,/g, "");
  const rangeMatch = cleanStr.match(/(\d+)\s*-\s*(\d+)/);
  if (rangeMatch) {
    const min = parseFloat(rangeMatch[1]);
    const max = parseFloat(rangeMatch[2]);
    if (!isNaN(min) && !isNaN(max)) {
      return [min, max];
    }
  }
  const singleMatch = cleanStr.match(/(\d+)/);
  if (singleMatch) {
    const multMatch = cleanStr.match(/(\d+)\s*(?:USD)?\s*[xX]\s*(\d+)/);
    if (multMatch) {
      const val2 = parseFloat(multMatch[1]) * parseFloat(multMatch[2]);
      return [val2, val2];
    }
    const val = parseFloat(singleMatch[1]);
    if (!isNaN(val)) {
      return [val, val];
    }
  }
  return null;
}
__name(parseCostRange, "parseCostRange");
function doesOverlap(rangeA, rangeB) {
  return Math.max(rangeA[0], rangeB[0]) <= 1.5 * Math.min(rangeA[1], rangeB[1]);
}
__name(doesOverlap, "doesOverlap");
function getSeededRandom(seedStr) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < seedStr.length; i++) {
    h = Math.imul(h ^ seedStr.charCodeAt(i), 16777619);
  }
  let seed = h >>> 0;
  let t = seed + 1831565813;
  t = Math.imul(t ^ t >>> 15, t | 1);
  t ^= t + Math.imul(t ^ t >>> 7, t | 61);
  return ((t ^ t >>> 14) >>> 0) / 4294967296;
}
__name(getSeededRandom, "getSeededRandom");
async function generatePairForDate(env, dateStr) {
  const url = env.FOREST_JSON_URL || "https://bci.red/forest.json";
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch forest.json from ${url}: ${res.status}`);
  }
  const data = await res.json();
  const candidates = [];
  for (const [key, val] of Object.entries(data)) {
    if (val.taxon === "Inventory-item") {
      const status = (val.metas.status || "").toLowerCase();
      if (status === "want" || status === "aspirational") {
        const costStr = val.metas["cost-range"];
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
    throw new Error("No overlapping pairs found in inventory items");
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
__name(generatePairForDate, "generatePairForDate");
async function getTodayPair(env, forceDate) {
  const d = forceDate ? new Date(forceDate) : /* @__PURE__ */ new Date();
  if (isNaN(d.getTime())) {
    throw new Error("Invalid date format");
  }
  const year = d.getUTCFullYear();
  const month = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  const dateStr = `${year}-${month}-${day}`;
  if (!forceDate) {
    const cached = await env.VOTES.get("today", "json");
    if (cached && cached.seed === dateStr) {
      return cached;
    }
  }
  const pair = await generatePairForDate(env, dateStr);
  if (!forceDate) {
    await env.VOTES.put("today", JSON.stringify(pair));
  }
  return pair;
}
__name(getTodayPair, "getTodayPair");
var src_default = {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    if (url.pathname === "/health") {
      return json({ status: "healthy", service: "vote-agg" });
    }
    if (url.pathname === "/items") {
      try {
        const forceDate = url.searchParams.get("date");
        const p = await getTodayPair(env, forceDate);
        return json(p);
      } catch (err) {
        return json({ error: err.message }, 500);
      }
    }
    if (url.pathname === "/vote" && req.method === "POST") {
      try {
        const v = await req.json();
        if (!v.pair_id || !["red", "blue"].includes(v.side)) {
          return json({ error: "bad payload" }, 400);
        }
        const key = `tally:${v.pair_id}`;
        const t = await env.VOTES.get(key, "json") || { red: 0, blue: 0 };
        t[v.side]++;
        await env.VOTES.put(key, JSON.stringify(t));
        return json({ ok: true, tally: t });
      } catch (err) {
        return json({ error: err.message }, 500);
      }
    }
    return json({
      error: "not found",
      endpoints: ["GET /items", "POST /vote", "GET /health"]
    }, 404);
  },
  async scheduled(event, env) {
    try {
      const d = event.scheduledTime ? new Date(event.scheduledTime) : /* @__PURE__ */ new Date();
      const year = d.getUTCFullYear();
      const month = String(d.getUTCMonth() + 1).padStart(2, "0");
      const day = String(d.getUTCDate()).padStart(2, "0");
      const dateStr = `${year}-${month}-${day}`;
      const pair = await generatePairForDate(env, dateStr);
      await env.VOTES.put("today", JSON.stringify(pair));
      console.log(`Cron: successfully rotated today's pair to ${pair.pair_id} for date ${dateStr}`);
    } catch (err) {
      console.error("Cron: failed to run daily rotation:", err);
    }
  }
};

// ../../../node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-drUXTT/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = src_default;

// ../../../node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-drUXTT/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=index.js.map
