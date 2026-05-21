# Indoor Plants for Lab/Office Setup

> Plant selection guide for team members setting up large indoor plants in their workspace.

---

## Hosted Plant Catalog

**Plant photo gallery and procurement list**: [To be hosted]

Recommended hosting location (per ASI skill survey -- `cloudflare` and `coolify-deployment` skills):
- **Cloudflare R2** (S3-compatible object storage, free egress): Upload plant photos + care sheets as a static site via Cloudflare Pages with R2 backend. Zero egress cost, generous free tier (10 GB storage, 10M reads/month).
  - Setup: `wrangler r2 bucket create bci-horse-plants` then `wrangler pages deploy ./plants-site`
- **Alternative**: Coolify self-hosted instance if the team already runs one (see `coolify-deployment` skill) -- deploy a simple static file server.
- **Quick option**: GitHub repo subfolder with LFS for images, served via GitHub Pages.

Once hosting is set up, update this link:
```
PLANT_CATALOG_URL=https://plants.bci.horse  # or whatever domain
```

---

## Selection Criteria

For a BCI lab / hacking space in SF:

| Criterion | Why It Matters |
|-----------|----------------|
| **Low maintenance** | Lab people forget to water; pick drought-tolerant species |
| **Air purifying** | Closed lab with soldering fumes, reflow oven -- VOC absorption helps |
| **Low light tolerant** | Many SF apartments/offices have limited natural light |
| **Large statement size** | Request was specifically for large indoor plants |
| **Non-toxic** | Safety if anyone has pets visiting the space |
| **Humidity tolerant** | SF fog = variable humidity; avoid species that need precise RH |

---

## Recommended Species

### Tier 1: Hard to Kill, Large, Air-Purifying

| Plant | Size | Light | Water | Air Purify | Notes |
|-------|------|-------|-------|------------|-------|
| **Monstera deliciosa** (Swiss Cheese) | 4-8 ft | Medium indirect | Weekly | Yes (formaldehyde) | Iconic. Loves neglect. Gets huge. |
| **Ficus lyrata** (Fiddle Leaf Fig) | 5-10 ft | Bright indirect | When top 2" dry | Moderate | Dramatic but slightly fussy about drafts |
| **Dracaena marginata** (Dragon Tree) | 5-8 ft | Low-medium | Every 2 weeks | Yes (benzene, xylene) | Almost indestructible. Thin profile. |
| **Strelitzia nicolai** (Giant Bird of Paradise) | 6-10 ft | Bright | Weekly | Moderate | Architectural. Needs space. |
| **Sansevieria trifasciata** (Snake Plant) | 2-4 ft | Any | Monthly | Yes (multiple VOCs) | NASA-certified air cleaner. Zero maintenance. |

### Tier 2: Medium Effort, High Impact

| Plant | Size | Light | Water | Notes |
|-------|------|-------|-------|-------|
| **Ficus elastica** (Rubber Plant) | 4-8 ft | Medium | Every 10 days | Dark glossy leaves. Handles low light. |
| **Philodendron bipinnatifidum** (Tree Philodendron) | 4-6 ft | Medium indirect | Weekly | Tropical look. Very forgiving. |
| **Areca Palm** (Dypsis lutescens) | 6-8 ft | Bright indirect | When top inch dry | Best air humidifier per NASA study. |
| **Pachira aquatica** (Money Tree) | 4-6 ft | Medium | Every 10 days | Braided trunk version is common. |
| **Yucca elephantipes** | 4-8 ft | Bright | Every 2-3 weeks | Drought champion. Sculptural. |

### Tier 3: Statement Pieces (If You Have Good Light)

| Plant | Size | Light | Water | Notes |
|-------|------|-------|-------|-------|
| **Ficus benghalensis** (Banyan / Audrey) | 5-10 ft | Bright | Weekly | Trendier than fiddle leaf, more forgiving |
| **Euphorbia trigona** (African Milk Tree) | 4-6 ft | Bright | Every 2 weeks | Cactus-like, very architectural |
| **Caryota mitis** (Fishtail Palm) | 6-8 ft | Bright indirect | Keep moist | Unusual frond shape |

---

## Where to Buy in SF

| Source | Type | Notes |
|--------|------|-------|
| **Flora Grubb Gardens** | Nursery (Bayview) | Best selection of large specimens in SF. Worth the trip. |
| **Sloat Garden Center** | Chain nursery (multiple SF locations) | Reliable, good prices, staff knows local conditions |
| **The Plant Foundry** | Shop (Inner Sunset) | Curated selection, slightly premium pricing |
| **Home Depot / Lowe's** | Big box | Cheapest large plants but inspect carefully for pests |
| **Facebook Marketplace / Craigslist** | Used | People moving out of SF constantly sell large plants cheap |
| **Floom / The Sill** (delivery) | Online | Convenient but expensive for large plants |

---

## Care Quick-Reference

```
GENERAL RULE FOR LARGE INDOOR PLANTS:
  - Water when top 2 inches of soil are dry (stick your finger in)
  - Fertilize monthly during spring/summer with diluted liquid fert
  - Wipe leaves with damp cloth monthly (dust blocks photosynthesis)
  - Rotate pot 90 degrees weekly for even growth
  - Repot when roots circle the bottom (usually every 1-2 years)

SOLDERING LAB SPECIFIC:
  - Keep plants away from reflow oven heat exhaust
  - Fume extractor helps but plants add supplementary VOC absorption
  - Snake plants and dracaenas are best for overnight air cleaning (CAM photosynthesis)
```

---

## Starter Pack Suggestion

For a BCI lab setup, grab these three from Flora Grubb:

1. **1x Monstera deliciosa** (6ft, ~$80-120) -- the main showpiece
2. **2x Sansevieria trifasciata** (3ft, ~$30-50 each) -- air purifiers, put near solder station
3. **1x Dracaena marginata** (5ft, ~$60-80) -- fills a corner, zero maintenance

Total: ~$200-300 for immediate visual + air quality impact.
