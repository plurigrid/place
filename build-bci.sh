#!/bin/bash
# Build the bci.horse forester site
# Rooted at horse-0001 (BCI Factory), combining:
#   - trees/bci-* (categorical BCI theory)
#   - localcharts/forest/trees/horse-* (production pipeline)
#   - bci/stages/* (factory stage trees)
#   - trees/dbl-*, dct-*, thy-*, mdt-* (CatColab math foundations)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use bci-forest.toml as the config
export FORESTER_CONFIG="bci-forest.toml"

echo "Building bci.horse forest..."
echo "  Root: horse-0001 (BCI Factory)"
echo "  Trees: $(find trees localcharts/forest/trees bci/stages -name '*.tree' 2>/dev/null | wc -l | tr -d ' ') total"
echo "  BCI trees: $(find trees -name 'bci-*.tree' | wc -l | tr -d ' ')"
echo "  Horse trees: $(find localcharts/forest/trees -name 'horse-*.tree' | wc -l | tr -d ' ')"

# Build with forester
./forester build "$FORESTER_CONFIG"

echo "Output in output/"
echo "Deploy: rsync -avz output/ bci.horse:/var/www/bci.horse/"
