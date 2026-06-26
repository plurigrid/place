# BCI Build Recovered Prompts and Desiderata

Status: recovered after repeated context compaction, 2026-06-12.

This file preserves the human prompts that materially constrain the BCI hardware build task. It excludes injected AGENTS/environment/developer wrappers and keeps the prompt ledger tied to the local session evidence so future edits do not drift back to stale assumptions.

## Source Evidence

- History index: `/Users/alice/.codex/history.jsonl`
- Primary rollout: `/Users/alice/.codex/sessions/2026/06/11/rollout-2026-06-11T21-58-08-019eba31-d56a-7a53-86a5-fb1d4b561ab9.jsonl`
- Session id: `019eba31-d56a-7a53-86a5-fb1d4b561ab9`

## Prompt Ledger

| Rollout line | Prompt constraint |
|---:|---|
| 7 | Incorporate the prior-session paste and PR30 context instead of losing continuity. |
| 147 | Produce PDFs for both hardware builds with embedded images. |
| 233 | Produce both Forester trees and Markdown/PDF artifacts with embedded images for PR30. |
| 275 | Use the Forester skill/site model. |
| 418 | Keep localhost Forester trees visible while editing. |
| 572 | Final trees must be direct text copies of the approved/sent Markdown, not alternate two-per-item trees. |
| 788 | Main goal: design, assemble, and purchase the whole BCI device set from the most recent canonical state; itemize missing pieces, compare against the tree Markdown, embed images, create DuckDB records, and separate spare or indeterminate parts into their own tree. |
| 820 | Do not discard or assume images are unnecessary. |
| 822 | Include every relevant image, including the chip image missing from the tree. |
| 836 | Incorporate the single supplied image. |
| 1066 | Incorporate the 35-image purchase packet; transclude purchase reasons from Forester trees; duplicate images are not duplicate parts; save images to the workfile for subagents; create an org record; omit only retaken images of the same part when they add no new information. |
| 1070 | Incorporate the 3-image follow-up. |
| 1080 | Verify images survived the session reopen. |
| 1096 | Post-compaction full objective: build a source-backed, visually informative BCI design/assembly/purchasing bill-of-work update; reconstruct relevant `.claude`/`.codex`/Gemini history into DuckDB; identify missing or indeterminate parts and board locations from best available images; compare against existing trees/Markdown; produce inline-image Markdown, PDFs, Forester trees, and durable records; verify rendered output and keep the broader scope intact. |
| 1183 | Treat the Barton-sent Markdown as canonical likely truth; examine counterfactuals through DuckDB/history; central goal is to populate visibly unpopulated board parts in an electronically acceptable way equivalent or better than the original GitHub designs. |
| 1311 | The goal is not complete until the final trees are visible. |
| 1335 | Trees were not visible because they were not open in localhost. |
| 1388 | Use the skill://forester localhost path; no workarounds. |
| 1519 | Rebuilding the whole forest is acceptable. |
| 1714 | Major correction: do not say "Barton approved"; the material was approved only for Barton to view and that meta does not belong in the tree. Include MOX station details. Replace "customer" with `bci.place`. Use more and better images. Verify missing parts against images and Markdown. Exclude rotation-only screenshots. Generate diagrams of unfilled locations per board with labels. Human verification determines spare or unnecessary parts. Double-check every missing-part claim. Exclude cross-probe, JLCPCB-placed, Diamond Geezer, and previous-version images from assembler-facing instructions. Inline images and table links. Use DuckDB as a relevance filter/open-question record, not an irrelevant dump. Verify DuckDB contains the work. For Uncut Gem, include the current electronic issue and improvement plan. |
| 1872 | Red-tinted images are wrong; OpenNIRS bill of work was cut off to sensors and must cover the whole stack; Uncut Gem should use better images; every tree must contain everything needed. |
| 2022 | Review `.codex/history.jsonl` to recover prompts before compaction so the full goal and invariants can be recalled and a more accurate desiderata can replace critique. |
| 2107 | Ensure every previous prompt from this conversation is included because multiple high-impact prompts matter. |
| 2109 | Continue in the context of a conversation compacted several times. |

History file anchors for the same prompt family:

- `/Users/alice/.codex/history.jsonl:4313` and `:4321`: full `/goal` BCI design/assembly/purchasing objective.
- `/Users/alice/.codex/history.jsonl:4324`: Barton-sent Markdown is canonical likely truth and counterfactuals go through DuckDB/history.
- `/Users/alice/.codex/history.jsonl:4329`: final trees must be visible.
- `/Users/alice/.codex/history.jsonl:4331`: skill://forester localhost/no workarounds.
- `/Users/alice/.codex/history.jsonl:4334`: long 10-image correction.
- `/Users/alice/.codex/history.jsonl:4335`: red-tinted image complaint and OpenNIRS cut-off correction.
- `/Users/alice/.codex/history.jsonl:4336`: prompt-history review request.

## Corrected Desiderata

1. The deliverables are assembler-facing build records for the current hardware, not a critique of earlier output.
2. Use the Barton-sent Markdown as canonical likely truth unless direct board/photo/BOM/history evidence contradicts it.
3. Use DuckDB/history for relevance filtering, counterfactual tracking, and open questions; do not turn it into an undifferentiated dump.
4. Include all materially distinct supplied images. Retakes can collapse only when they show the same part with no additional evidence.
5. Use clear current images as assembler-facing evidence. Do not rely on red-tinted photos, rotation-only screenshots, cross-probe captures, JLCPCB placed-part review images, Diamond Geezer renders, or previous-version device images as final assembly instructions.
6. Replace "customer" language with `bci.place` or neutral kit-owner language.
7. Do not write "Barton approved" or similar approval metadata in the tree/docs. The relevant fact is that the material was approved for Barton to view.
8. Include MOX station details: MOX, 1618 Mission Street, San Francisco, with fan, air filter, soldering bench, and ESD wrist straps available.
9. OpenNIRS scope is the whole OpenNIRScap unit: sensors, ECU, ST-LINK adapter, cap, cabling, firmware, USB frame contract, host MBLL/CBSI output, optical proof, safety, and isolation.
10. Uncut Gem scope is the current DEF CON 33/current-board instrument: power, ESP32/USB, PLL/RF, optomechanics, detector path, ADC baseline, ODMR trace, and the reversible INA333 measurement-integrity improvement plan.
11. Missing-part claims must come from physical board/photo/BOM agreement. Empty footprints can be populate-now, leave-empty-by-design, blocked-by-fit, blocked-by-schematic-uncertainty, damaged, spare, or unnecessary.
12. Human verification determines spare and unnecessary parts. Do not hide or discard indeterminate pieces.
13. Produce diagrams of visibly unpopulated board locations per board with labels.
14. Images and table links must be inline in the tree/docs where they guide action.
15. Final Forester trees must be visible through localhost Forester output, not merely written to disk.
