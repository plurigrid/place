# Manual missing-location list to canonical parts

Evidence target: prove the forest location diagrams are driven by the same manual missing-location list, then map each handwritten location against source PCB/BOM data and local history substitution decisions.

## Manual prompt anchor

The handwritten list is in Codex history at `/Users/alice/.codex/history.jsonl:4361`, session `019eba31-d56a-7a53-86a5-fb1d4b561ab9`, `ts=1781262383` (`2026-06-12 04:06:23 PDT`).

> 1. the ecu missng parts map needs improvement -- in wrong locations&incomplete - i would say sensor groups (j10 ,8,6,4,11,9,7,5), u6,?,5,1 (rightmost next to y axis sensors- cant see label due to light) , 'reset' , u8,4,7,3  , u15 , u16 , '5v input' , u17 , usb port , j2 , sd1 , every tp(n) are missing -- theres 2 photos of stlink -- there should be a diagram of the adaptor boards this is also a pcb -- in the uncut gem this is lies + misid of images [Image #1], remove entirely -- based on my eyes gem is missing j4 j3 j2 j1, u3 u2 r7 r6 d3 d2 r24 oled 5v_supp1 pwr1 en1 boot1 r27 r29 r28 led1 tp1 c35 j6 d4 gnd pd 2.5v and has sma holes and maybe d6 d5 missing

The current goal prompt tying this list to `openfnirs-build.xml` and `uncut-gems-build.xml` is `/Users/alice/.codex/history.jsonl:4395`.

## OpenFNIRS mapping

Current forest provenance:

- `p/place/bci/devices/openfnirs-build.tree:58` says the ECU map is generated from original OpenNIRScap GitHub KiCad source `tonykim07/fNIRS/hardware/fNIRS_ECU/fNIRS_PCB-PcbDoc.kicad_pcb`.
- `p/place/bci/devices/openfnirs-build.tree:72` says the ST-LINK adapter map is generated from `tonykim07/fNIRS/hardware/STLINK_Breakout/STLINK_Breakout-PcbDoc.kicad_pcb`.
- `p/place/bci/devices/openfnirs-build.tree:131` preserves the no-substitution rule for bci.place-furnished material.

| Manual token | Canonical source mapping | Purchased-photo / current evidence | History substitution decision |
|---|---|---|---|
| `sensor groups (j10,8,6,4,11,9,7,5)` | Source map has `J10/J8/J6/J4`, an unnumbered KiCad `J`, and `J9/J7/J5`, all `SAMTEC_T1M-10-F-SH-L-K` (`p/place/assets/hardware-builds/generated/openfnirs-ecu-unfilled-locations.svg:139-146`). Current tree names that same set and avoids adding photo-invented headers (`p/place/bci/devices/openfnirs-build.tree:88`). | T1M-10 stock photo is in the packet (`p/place/bci/devices/openfnirs-build.tree:110`). | `/Users/alice/.codex/sessions/2026/06/11/rollout-2026-06-11T21-58-08-019eba31-d56a-7a53-86a5-fb1d4b561ab9.jsonl:5647` records that invented `J11` rows were removed; source designators only. |
| `u6,?,5,1` | `U6` is LMV324A (`openfnirs-ecu-unfilled-locations.svg:147-149`; ECU BOM `i/openfnirs-pcb-2026-05/pcb-verify-2026-04-18/order_ready/ecu/BOM.csv:21`). `U5` is repeated analog switch footprints (`openfnirs-ecu-unfilled-locations.svg:150-157`). `U1` is STM32L476 (`BOM.csv:18`; SVG `:158`). The `?` remains glare-obscured inspection hold (`openfnirs-build.tree:89`). | No placement image until microscope/designator confirmation (`openfnirs-build.tree:89`). TMUX1104 stock is verify-only (`openfnirs-build.tree:111`). | No approved substitution found. Do not back-fill by shape; inspect first. |
| `reset` | `SW1` tactile switch (`BOM.csv:24`; SVG `:159`). | FSM1LP tactile switch stock photo exists (`openfnirs-build.tree:90`, `:109`). | Fit-check only; no substitute found. |
| `u8,4,7,3` | `U8` ADUM4160 USB isolator (`BOM.csv:23`; SVG `:160`), `U4` MCP73831 charger (`BOM.csv:20`; SVG `:161`), `U7` TCA9535 I/O expander (`BOM.csv:22`; SVG `:162-163`), `U3` regulator (`BOM.csv:19`; SVG `:164`). | Current tree shows LM1085 3.3 V stock for ECU U3 and requires fit-check/proving the 3.3 V rail (`openfnirs-build.tree:91`, `:107`). | Current history and tree treat LM1085 as the U3 replacement candidate for the original AMS1117 site; fit-check TO-263 and prove rail before downstream population. |
| `u15`, `u16`, `u17` | Not present in current canonical source-map rows. | No purchased-photo placement evidence. | `/Users/alice/.codex/sessions/2026/06/11/rollout-2026-06-11T21-58-08-019eba31-d56a-7a53-86a5-fb1d4b561ab9.jsonl:5647` records these invented/photo-callout rows were removed; treat as manual/photo mis-ID until cross-probed. |
| `5v input` | Silkscreen near `J2/U3`, not a component (`openfnirs-ecu-unfilled-locations.svg:183`; `openfnirs-build.tree:93`). | No part image because it is not a part. | No substitution; use as orientation/power proof label only. |
| `usb port`, `j2` | `J2` USB Mini-B connector (`BOM.csv:11`; SVG `:166`). | Molex 67503-1020 Mini-B stock photo exists (`openfnirs-build.tree:93`, `:108`). | Install matched USB connector only; prove +5 V and USB enumeration. |
| `sd1` | `SD1` Micro SD connector (`openfnirs-ecu-unfilled-locations.svg:167`). | Current tree includes `SD1` in the source map but no dedicated part photo (`openfnirs-build.tree:93`). | No approved substitute found; bin-check exact storage connector before place. |
| `every tp(n)` | Test pads, not components (`openfnirs-ecu-unfilled-locations.svg:168-179`; note at `openfnirs-build.tree:94`). | No part image. | No substitution; use for continuity, power, SWD, and bring-up evidence. |
| ST-LINK adapter boards | `J1` is `HTSW-107-07-G-D`; `J2` is `FTSH-107-01-L-DV-K` (`p/place/assets/hardware-builds/generated/openfnirs-stlink-adapter-unfilled-locations.svg:26-27`; `openfnirs-build.tree:95`). | Bare adapter board photo and FTSH stock image exist; HTSW image is not in saved packet (`openfnirs-build.tree:95`, `:112-113`). | Buy HTSW and one extra FTSH if no spare (`openfnirs-build.tree:127`). |
| Sensor module `J1` | Samtec `T1M-06-F-SH-L-K` bottom-edge 1 mm connector (`openfnirs-build.tree:84`, `:106`). | Five T1M-06 in hand for eight boards (`openfnirs-build.tree:84`, `:124`). | Buy three more T1M-06 if completing all eight. No substitute found. |
| Sensor module source/detector | `D1` VSMD66694 dual LED, `D2` VBPW34S photodiode, `D3` green LED (`i/openfnirs-pcb-2026-05/pcb-verify-2026-04-18/order_ready/sensor_module/BOM.csv:4-6`). | Current tree says optical/electrical verification before any diode claim (`openfnirs-build.tree:87`). | No purchase/substitution task unless bench evidence contradicts current board. |
| Sensor module `U1` | Current sensor `U1` is AD8616 SOIC-8 in source map; AD8618ARUZ is not the current placement instruction (`openfnirs-build.tree:86`). | AD8618ARUZ is set aside (`openfnirs-build.tree:128`). | History verified the `AD8618ARUZ` correction on localhost; keep it as spare, do not place (`/Users/alice/.codex/sessions/2026/06/11/rollout-2026-06-11T21-58-08-019eba31-d56a-7a53-86a5-fb1d4b561ab9.jsonl:1687`, `:1707`). |

## Uncut Gem mapping

Current forest provenance:

- `p/place/bci/devices/uncut-gems-build.tree:66` says the map is generated from original GitHub KiCad/BOM sources `plurigrid/UncutGem/hardware/PCB/Uncut Gem.kicad_pcb` and `Uncut Gem-BOM.csv`.
- `p/place/bci/devices/uncut-gems-build.tree:136` preserves the no-substitution rule for CFM parts.

| Manual token | Canonical source mapping | Purchased-photo / current evidence | History substitution decision |
|---|---|---|---|
| `j4 j3 j2 j1`, `sma holes` | Original BOM maps `J1/J2/J3/J4` to Molex `73251-2120` edge-mount SMA (`scratch/public_codebase_intake/git_cache/plurigrid/UncutGem/hardware/PCB/Uncut Gem-BOM.csv:16-19`); source SVG repeats locations (`p/place/assets/hardware-builds/generated/uncut-gem-main-pcb-unfilled-locations.svg:71-74`). | Correct edge-mount SMA photo is not in the packet; BOOBRIE vertical SMA is explicitly no-fit warning (`uncut-gems-build.tree:84`, `:103`, `:125`). | Claude history says original PCB connectors are SMA Molex 73251-2120, not BNC (`/Users/alice/.claude/history.jsonl:4961`). Do not use BNC or BOOBRIE vertical as substitutes. |
| `j6` | `J6` ADC_SIGNAL, Molex `73251-2200` horizontal (`Uncut Gem-BOM.csv:21`; prod CSV `scratch/public_codebase_intake/git_cache/plurigrid/UncutGem/hardware/PCB/ProdFiles/Uncut Gem3.csv:24`; SVG `:75`). | Current production marks it DNP (`Uncut Gem3.csv:24`). | Only populate if ADC/INA333 rework requires it; no substitution found. |
| `u3 u2` | Original BOM says `U2/U3` are `GALI-84` SOT-89 (`Uncut Gem-BOM.csv:47`; SVG `:76-77`). Current prod CSV says `NXP-MMG3014NT1` (`Uncut Gem3.csv:50`). | MMG3014 stock photo is mismatch evidence only (`uncut-gems-build.tree:85`, `:108`). | `/Users/alice/.claude/history.jsonl:4952` includes the GALI-84 source; `/Users/alice/.codex/sessions/2026/06/11/rollout-2026-06-11T21-58-08-019eba31-d56a-7a53-86a5-fb1d4b561ab9.jsonl:5647` records `MMG3014` as mismatch/substitution evidence only, not approved. |
| `r7 r6` | `R6/R7` are 50 ohm (`Uncut Gem-BOM.csv:34`; prod CSV `Uncut Gem3.csv:35`; SVG `:78-79`). | Current prod marks DNP (`Uncut Gem3.csv:35`). | Do not auto-populate; confirm missing state and RF plan. |
| `d3 d2` | `D2/D3` are `D_Small` 0603 (`Uncut Gem-BOM.csv:13`; `Uncut Gem3.csv:17`; SVG `:80-81`). | No dedicated placement photo. | No substitution found. |
| `r24` | `R24` is `0R` (`Uncut Gem-BOM.csv:44`; SVG `:82`); current prod says `0`, DNP (`Uncut Gem3.csv:44`). | No dedicated placement photo. | No substitution found; DNP until rework requires it. |
| `oled` | Manual `oled` maps to current `OLED1`; original BOM calls the interface `J5` (`Uncut Gem-BOM.csv:20`; prod CSV `Uncut Gem3.csv:28`; SVG `:83`). | 1x4 header and candidate OLED module photos exist (`uncut-gems-build.tree:86`, `:104`, `:114`). | Candidate stock exists; verify pin order before connecting. |
| `5v_supp1` | `5V_SUPP1`, 2x3 power connector (`Uncut Gem-BOM.csv:2`; `Uncut Gem3.csv:2`; SVG `:84`). | 2x3 socket stock photo exists (`uncut-gems-build.tree:86`, `:106`). | Populate only if selected power plan uses it; prove protected 5 V and 3.3 V rails. |
| `pwr1`, `led1` | `PWR1` and `LED1` LEDs (`Uncut Gem-BOM.csv:29`; `Uncut Gem3.csv:26`; SVG `:85`, `:91`). | No dedicated placement image until LED intent confirmed (`uncut-gems-build.tree:87`). | No substitution found. |
| `en1 boot1` | Current prod names `BOOT1,EN1` as push switches (`Uncut Gem3.csv:3`; SVG `:86-87`). Original BOM old names are `SW1,SW2` (`Uncut Gem-BOM.csv:45`). | Included in source footprint map (`uncut-gems-build.tree:86`). | Rename between original and prod files; no substitute found. |
| `r27 r29 r28` | `R27/R28/R29` are 10k, DNP in current prod (`Uncut Gem3.csv:45`; SVG `:88-90`). | No placement image until intent confirmed (`uncut-gems-build.tree:87`). | Do not populate without new rework instruction. |
| `tp1` | `TP1` is a `TestPoint_Probe` (`Uncut Gem3.csv:47`; SVG `:92`). | Current tree says confirm whether TP1 is an access pad or fitted post (`uncut-gems-build.tree:87`). | No substitution; treat as access/probe point. |
| `c35` | Original BOM `C35` is `104`; current prod `C35` is `100nF`, DNP (`Uncut Gem-BOM.csv:9`; `Uncut Gem3.csv:12`; SVG `:93`). | No placement image until value/intent confirmed (`uncut-gems-build.tree:87`). | No substitution found; DNP unless rework says otherwise. |
| `d4` | `D4` is BPW34 (`Uncut Gem-BOM.csv:14`; current prod DNP at `Uncut Gem3.csv:18`; SVG `:94`). | BPW34-style photodiode stock is for prism/detector path, not OpenFNIRS substitution (`uncut-gems-build.tree:90`, `:109`). | Claude history identifies BPW34 as correct photodiode for this build path (`/Users/alice/.claude/history.jsonl:4961`). Verify detector socket pinout. |
| `gnd pd 2.5v` | Detector-side labels/pads, not component designators; tied to `D4` / `PHOTODIODE1` area (`uncut-gems-build.tree:88`; `Uncut Gem-BOM.csv:28`; prod CSV `Uncut Gem3.csv:30`; SVG note `:95`). | 1x3 PHOTODIODE1 socket stock photo exists (`uncut-gems-build.tree:88`, `:107`). | Map to detector socket/pads; do not add fake BOM parts. |
| `d6 d5` | `D5/D6` are `ESD9B5.0ST5G` ESD footprints (`Uncut Gem-BOM.csv:12`; `Uncut Gem3.csv:16`; SVG `:96-99`). Original GitHub BOM also groups `D1` with the same ESD part, so the manual `D5/D6` note is not the full ESD set. | No saved part image in packet (`uncut-gems-build.tree:89`). | No substitution found; inspection hold before buy/place task. |

## Current substitution summary

- OpenFNIRS `U15/U16/U17`: removed as invented/photo-callout rows; no canonical part or substitution.
- OpenFNIRS `U3`: original order-ready ECU BOM names AMS1117, but current assembly evidence uses LM1085 stock for the regulator site; treat as fit-check/prove-rail substitution candidate, not blind placement.
- OpenFNIRS `AD8618ARUZ`: explicitly not a current sensor `U1` placement; keep as spare.
- OpenFNIRS `HTSW`: no saved purchased-photo evidence; buy exact `HTSW-107-07-G-D`.
- Uncut Gem `U2/U3`: canonical original BOM is `GALI-84`; `MMG3014` stock is mismatch/substitution evidence only and not approved.
- Uncut Gem SMA: canonical original connectors are Molex `73251-2120` edge-mount SMA; BNC and BOOBRIE vertical SMA are rejected substitutes.
- Uncut Gem `D1/D5/D6`: canonical `ESD9B5.0ST5G`; manual only called out maybe `D5/D6`, but original GitHub BOM shows all three ESD footprints.
- Uncut Gem DNP passives/connectors (`R6/R7`, `R24`, `R27/R28/R29`, `C35`, `J2-J4`, `J6`, often `D4`): empty footprints can be intentional, not missing-parts proof.
