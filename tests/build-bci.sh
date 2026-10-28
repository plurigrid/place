#!/usr/bin/env bash
# Exercise the wrapper without downloading Forester or rendering the forest.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

mkdir -p "$TEST_DIR/repo/trees" "$TEST_DIR/repo/localcharts/forest/trees" \
  "$TEST_DIR/repo/bci/stages"
cp "$REPO_DIR/build-bci.sh" "$TEST_DIR/repo/"
touch "$TEST_DIR/repo/bci-forest.toml"

cat > "$TEST_DIR/repo/forester" <<'FORESTER'
#!/usr/bin/env bash
set -euo pipefail
[[ "$#" -eq 2 && "$1" == build && "$2" == bci-forest.toml ]] || exit 99
[[ "${FORESTER_CONFIG:-}" == bci-forest.toml && -f "$2" ]] || exit 98
touch invoked
exit "${FORESTER_TEST_STATUS:-0}"
FORESTER
chmod +x "$TEST_DIR/repo/forester"

# Run outside the repository and with a conflicting inherited config.
cd "$TEST_DIR"
FORESTER_CONFIG=wrong.toml bash repo/build-bci.sh > success.log 2>&1
test -f repo/invoked
grep -Fxq 'Output in output/' success.log
grep -Fxq 'Deploy: rsync -avz output/ bci.horse:/var/www/bci.horse/' success.log

rm repo/invoked
status=0
FORESTER_TEST_STATUS=42 bash repo/build-bci.sh > failure.log 2>&1 || status=$?
test "$status" -eq 42
test -f repo/invoked
if grep -Eq '^(Output in|Deploy:)' failure.log; then
  echo 'Wrapper reported success after Forester failed' >&2
  exit 1
fi

echo 'build-bci.sh regression checks passed'
