# BCI Build Completion Audit

Status: current-state audit after Forester rebuild on 2026-06-12.

Scope boundary: this audit proves the documentation, evidence, and rendered-artifact objective for the BCI hardware build recovery thread. It does not claim physical assembly, soldering, purchase execution, firmware flashing, optical safety approval, or human-use readiness; those remain assembler/build tasks named in the bills of work.

## Requirement Matrix

| # | Requirement from recovered desiderata | Current evidence | Status |
|---:|---|---|---|
| 1 | Produce assembler-facing build records for the current hardware, not critique. | `openfnirs-assembly-bill-of-work.with-photo-references.md` sections 1-11; `uncut-gem-assembly-bill-of-work.with-photo-references.md` sections 1-11; `openfnirs-build.tree`; `uncut-gems-build.tree`; both Forester trees include verbatim copies of their current Markdown bills. | Proven for documentation deliverables. |
| 2 | Treat Barton-sent Markdown as canonical likely truth unless direct board/photo/BOM/history evidence contradicts it. | `bci-build-task-record.org` canonical decision rule and resolved claims; tree/history reconciliation tables in both Markdown bills. | Proven for current artifact policy. |
| 3 | Use DuckDB/history for relevance filtering, counterfactual tracking, and open questions, not as an undifferentiated dump. | `bci-build-history.duckdb` has `current_decision_principles`, `current_part_packet_claims`, `canonical_items`, `sources`, and mention indexes; `bci-parts-history.duckdb` has `history_sources`, `history_hits`, `part_claims`, `image_inventory`, and packet tables. | Proven for durable records. |
| 4 | Include all materially distinct supplied images; collapse only retakes with no added evidence. | `bci-build-task-record.org` pasted image packet has 39 rows, 29 retained/selected rows, 10 retake-disregard rows; `manifest.csv` has all 39 image files present and `contact-sheet.jpg` present. | Proven for packet custody and retake policy. |
| 5 | Use clear current images as assembler-facing evidence and exclude stale-image/source-provenance classes from active instructions. | Current Markdown bills and Forester trees use current clear photos and generated diagrams; active-source forbidden-token scan returned no matches across current Markdown, task record, trees, and XML. | Proven for active assembler surfaces. |
| 6 | Use `bci.place` or neutral kit-owner language instead of client/owner-generic language. | Active-source forbidden-token scan returned no owner-generic matches; Markdown bills and trees use `bci.place`. | Proven. |
| 7 | Do not write approval metadata in tree/docs. | Active-source forbidden-token scan returned no approval-metadata matches. | Proven. |
| 8 | Include MOX station details. | OpenFNIRS Markdown workmanship section and Forester tree include MOX, 1618 Mission Street, fan, air filter, soldering bench, and ESD wrist straps; Uncut Gem Markdown and Forester tree include the same. | Proven. |
| 9 | OpenNIRS scope is the whole OpenNIRScap unit: sensors, ECU, ST-LINK adapter, cap, cabling, firmware, USB frame contract, host MBLL/CBSI output, optical proof, safety, isolation. | OpenFNIRS Markdown scope, work items WI-1 through WI-9, acceptance criteria, software boundary, and Forester whole-stack state/bill-of-work sections. | Proven for documentation scope. |
| 10 | Uncut Gem scope is the current DEF CON 33/current-board instrument, including INA333 reversible improvement plan. | Uncut Gem Markdown scope, current photos, visual map, WI-1 through WI-11, known issue KI-1, acceptance criteria, and Forester current-state/rework sections. | Proven for documentation scope. |
| 11 | Missing-part claims must come from board/photo/BOM agreement and distinguish empty-needed, leave-empty, blocked, damaged, spare, or unnecessary. | OpenFNIRS visual location map and blockers B1-B4; Uncut Gem visual location map and open items KI-1/V-1/V-2/V-3; task record resolved claims and open inspection tasks. | Proven for current claims; physical verification remains an assembler exit proof. |
| 12 | Human verification determines spare/unnecessary parts; do not hide or discard indeterminate pieces. | `bci-indeterminate-spares.tree`; task record selected-indeterminate and selected-spare rows; Markdown instructions keep fit-check/probe-check gates before placement. | Proven for documentation and holding surfaces. |
| 13 | Produce diagrams of visibly unpopulated board locations per board with labels. | `assets/hardware-builds/generated/openfnirs-sensor-unfilled-locations.svg`; `assets/hardware-builds/generated/uncut-gem-main-pcb-unfilled-locations.svg`; both embedded in Markdown bills, PDFs, and Forester trees. | Proven. |
| 14 | Images and table links must be inline in tree/docs where they guide action. | Markdown image-link check: OpenFNIRS has 23 image refs / 16 unique and 0 missing; Uncut Gem has 29 image refs / 17 unique and 0 missing. Tree-native image check: `openfnirs-build.tree` has 19 image refs / 12 unique and 0 missing; `uncut-gems-build.tree` has 28 image refs / 17 unique and 0 missing. Both trees include current PCB photos, unfilled-location diagrams, and saved part-packet images next to the relevant fill decisions. | Proven. |
| 15 | Final Forester trees must be visible through localhost Forester output. | `./forester build forest.toml` completed; localhost HEAD checks returned HTTP 200 for `openfnirs-build.xml`, `uncut-gems-build.xml`, `bci-indeterminate-spares.xml`, and `bcf-devices.xml`. | Proven. |

Additional recovered constraint: final trees preserve direct text copies of the current Markdown bills rather than only alternate summaries. `openfnirs-build.tree` and `uncut-gems-build.tree` both contain a "Canonical Markdown bill text" subtree with the full Markdown bill copied in a rendered verbatim block. They are also quantifiably stronger than the Markdown as trees because each now has a tree-native "Inline part evidence for fill decisions" subtree before the canonical-copy block, pairing board-location rows with saved part-packet images or explicit no-photo/no-fit holds.

## Verification Commands Run

- `./forester build forest.toml`
- Active-source forbidden phrase scan across Markdown, task record, Forester trees, and rendered XML.
- DuckDB active-table forbidden phrase scan across both BCI databases.
- Markdown/Org local-reference existence checks.
- PDF extraction and image-XObject checks for both bills of work.
- Localhost HEAD checks for the four rendered Forester pages.

## Remaining Physical Work

- Build board-by-board population maps from microscope photos before soldering.
- Procure or confirm OpenNIRScap T1M-06 shortfall if all eight sensor modules are in scope.
- Fit-check and solder OpenNIRScap ECU/adapter headers and prove rail, reset, USB, mux, firmware, optical, host, cap, and safety gates.
- Verify Uncut Gem SMA fit, U2/U3 population, power/boot, PLL/RF, prism/laser/detector path, ODMR trace, and INA333 before/after measurement improvement if performed.

These are not missing documentation artifacts; they are the work orders and exit proofs intentionally assigned to the assembler/build process.
