# Uncut Gems v2 -- PCB Redesign

> Mixed-signal PCB redesign for a universal BCI analog front-end, compatible with OpenBCI Cyton/Daisy, Cognionics HD-72, and a new ultra-low-cost "ShitBCI" target.

> **NOTE: All component selections below (MCUs, ADCs, passives, connectors) are provisional starting points, not final picks. Final BOM will be determined by availability, pricing at order time, layout constraints, power budget, and hands-on eval. Treat every part number as TBD until schematic review is complete.**

---

## 1. Design Goals

| Goal | Detail |
|------|--------|
| **Multi-headset compatibility** | (1) OpenBCI Cyton 8/16ch ADS1299, (2) Cognionics HD-72 64ch dry EEG via USB/LSL, (3) ShitBCI ultra-cheap TBD |
| **Form factor improvement** | Smaller footprint, castellated edges, option for rigid-flex or flex-with-insertion-tabs |
| **Better MCU** | Upgrade from RFDuino-era to nRF5340 dual-core (Net + App) or RP2350 for cost tier |
| **Better ADC** | ADS1299 remains gold standard for OpenBCI tier; evaluate ADS1298 (lower power) or ADS131M08 for ShitBCI cost target |
| **GF(3) conservation** | Signal path preserves trit balance per `bci-colored-operad` skill: acquisition (-1), processing (0), broadcast (+1) |

---

## 2. Three Hardware Tiers

### Tier 1: OpenBCI-Compatible (ADS1299)
- **ADC**: TI ADS1299 (24-bit, 8ch, $30-45 qty 10)
- **MCU**: nRF5340 (BLE 5.4 + 128MHz app core) or existing RFDuino for backward compat
- **Channels**: 8 (single) / 16 (Daisy stacking)
- **Sample rate**: 250 Hz (standard), 500/1k/2k configurable
- **Interface**: SPI to ADC, UART to dongle, BLE optional
- **Reference design**: OpenBCI Cyton schematic + cyton-dongle skill for radio pairing protocol
- **Validation**: sheaf-cohomology-bci skill for local-to-global signal consistency checks

### Tier 2: Cognionics HD-72 Adapter
- **Not a replacement board** -- this tier is an interface/breakout
- **Purpose**: USB HID passthrough + LSL relay + DuckDB ingest
- **Pipeline**: Cognionics USB HID -> App-Cognionics (C++ LSL) -> pylsl -> nanoclj-zig brainfloj -> DuckDB
- **See**: `trees/bcf-0052.tree` in this repo for full acquisition pipeline
- **PCB role**: Optional signal conditioning / level shifting board if we bypass CGX software
- **Channel count**: 64 active channels @ 500 Hz

### Tier 3: ShitBCI (Ultra-Low-Cost)
- **Target BOM**: < $15 per board at qty 100
- **ADC**: ADS131M08 (24-bit, 8ch, ~$8) or ADS1298 (~$18, may bust budget) or even ADS1220 (single-ch, $3, multiplex with analog mux)
- **MCU**: RP2040 ($0.70) or RP2350 ($0.80) -- no BLE, USB-C direct
- **Channels**: 4-8 (reduced montage: Fp1, Fp2, C3, C4, O1, O2 minimum)
- **Compromise**: Lower CMRR, higher noise floor, no active shielding -- adequate for alpha/beta band demo
- **Scale path**: Rigid-flex single-shot design with insertion tabs for headband mount, designed for JLCPCB assembly
- **WorldPrime alignment**: See `~/Desktop/zig-syrup/tools/openbci_host/worldprime/` for nushell-based world A/B testing framework that this feeds into

---

## 3. KiCad Design Plan

### Schematic Blocks
1. **Power**: LDO 3.3V (analog) + 3.3V (digital), ferrite bead isolation, decoupling per ADS1299 spec
2. **ADC front-end**: ADS1299 (Tier 1) or ADS131M08 (Tier 3), SPI bus, DRDY interrupt
3. **Electrode interface**: ESD protection (TVS diodes), bias drive (SRB1/SRB2), impedance check circuit
4. **MCU**: nRF5340 (Tier 1) or RP2040/RP2350 (Tier 3)
5. **Comms**: USB-C (all tiers), BLE antenna (Tier 1 only), UART header for debug
6. **Aux**: 3-axis accelerometer (LSM6DSO or similar), GPIO header for expansion

### PCB Stack-up
- **Tier 1/3 rigid**: 4-layer, 1.6mm FR4, ENIG finish
  - L1: Signal + components
  - L2: Ground plane (continuous, no splits under ADC)
  - L3: Power plane (analog/digital split with single-point star ground)
  - L4: Signal + components
- **ShitBCI flex variant**: 2-layer flex (polyimide), stiffeners at connector tabs, 0.2mm trace/space

### Design Rules
- Analog traces: 8 mil minimum, matched length differential pairs for SPI clock
- Guard ring around ADC analog inputs
- No digital traces crossing analog ground plane boundary
- Component placement: ADC + passives on one side, MCU + digital on other (or opposite board face)

---

## 4. Timeline

| Week | Dates | Milestone |
|------|-------|-----------|
| **W1** | Apr 7-13 | Schematic capture in KiCad. Component selection finalized. Order critical long-lead parts from DigiKey (ADS1299, nRF5340 module, connectors). Set up reflow oven + solder station. |
| **W2** | Apr 14-18 | PCB layout complete. DRC/ERC clean. Generate Gerbers + BOM + CPL for JLCPCB. **Order PCBs from JLCPCB with SMT assembly** (10 boards). Simultaneously order all DigiKey parts for local hand-soldering of remaining components. |
| **W2-3** | Apr 14-25 | **Lead time: PCB fab + pick-and-place in China (~2 weeks)**. During this window: |
| | | - Finalize reflow oven calibration (thermal profile for lead-free SAC305) |
| | | - Set up solder station (JBC or Hakko FX-951 equivalent) |
| | | - Acquire test equipment (see section 5) |
| | | - Prepare firmware skeleton (nRF5340 SDK or RP2040 SDK) |
| | | - Set up gayOS TUI/GUI for BCI data display (see `gayOS/` submodule) |
| **W4** | Apr 28 - May 2 | Boards arrive. Hand-solder remaining through-hole/connectors. Reflow any QFN rework. |
| **W5-6** | May 5-16 | **Extensive testing phase** (see section 6) |
| **W7+** | May 19+ | Iterate: fix issues found in testing, spin v2.1 if needed |

---

## 5. Lab Equipment Needed

### Must-Have
| Equipment | Purpose | Approx Cost |
|-----------|---------|-------------|
| **Oscilloscope** (4ch, 100MHz+) | Verify SPI timing, check ADC clock integrity, debug analog noise | $400-800 (Rigol DS1104Z or Siglent SDS1104X-E) |
| **Reference 24-bit ADC** | Baseline comparison for ADC output accuracy | Use existing ADS1299 eval board (TI ADS1299EVM, ~$500) or build minimal breakout |
| **Multimeter** (bench, 6.5 digit) | Voltage reference accuracy, current consumption | $200-400 (Siglent SDM3065X) |
| **Reflow oven** | Solder paste reflow for QFN/BGA rework | Already have -- needs thermal profile calibration |
| **Solder station** | Hand soldering, rework | Already have -- verify tip inventory |
| **Logic analyzer** | SPI/UART/I2C protocol debugging | $15-150 (Saleae Logic 8 clone or genuine) |

### Nice-to-Have
| Equipment | Purpose |
|-----------|---------|
| **Spectrum analyzer** or **FFT on scope** | Verify 50/60 Hz rejection, check ADC noise floor in frequency domain |
| **LCR meter** | Verify decoupling capacitor values, check electrode impedance |
| **Thermal camera** | Spot hot components, verify power dissipation |
| **Signal generator** (function gen) | Inject known sine waves into ADC inputs for linearity testing |

---

## 6. Testing Protocol

### Phase 1: Board Bring-Up (Day 1-2)
- [ ] Visual inspection under magnification (solder bridges, tombstoning)
- [ ] Power rail verification (3.3V analog, 3.3V digital, current draw)
- [ ] MCU boot + UART debug output
- [ ] SPI communication to ADC (read device ID register)
- [ ] USB enumeration

### Phase 2: ADC Characterization (Day 3-5)
Using methodology from `bci-colored-operad` and `sheaf-cohomology-bci` skills:

- [ ] **Noise floor measurement**: Short all inputs, record 60s, compute RMS noise per channel
  - ADS1299 spec: 1 uVpp input-referred noise @ gain=24
  - Compare against reference ADC eval board output
- [ ] **CMRR test**: Apply common-mode 50Hz signal, measure rejection ratio
  - Target: >110 dB (ADS1299 datasheet typical)
- [ ] **Crosstalk**: Drive single channel with 10 Hz sine, measure bleed into adjacent channels
  - Target: <-100 dB channel isolation
- [ ] **Linearity**: Sweep DC input, verify DNL/INL within spec
- [ ] **Sample rate verification**: Confirm 250 Hz DRDY interrupt timing on scope

### Phase 3: Signal Quality (Day 6-10)
Per the 5-probe protocol from `trees/bcf-0052.tree`:

1. **Eyes closed rest** (10s) -- verify occipital alpha (8-12 Hz) at O1/O2
2. **Jaw clench 3x** (5s) -- verify temporal EMG artifact at T7/T8
3. **Eye blinks 5x** (5s) -- verify frontal artifact at Fp1/Fp2
4. **Left hand squeeze imagery** (10s) -- verify mu desynchronization at C3/C4
5. **Mental arithmetic** (10s) -- verify frontal theta increase at Fz/F3/F4

Each probe compared against:
- OpenBCI Cyton (known-good reference)
- Cognionics HD-72 (if available, for high-channel-count reference)
- Literature values for each paradigm

### Phase 4: Sheaf Consistency Validation
From `sheaf-cohomology-bci` skill:
- [ ] Compute Cech cohomology H^0 (global sections) and H^1 (obstructions) across electrode montage
- [ ] Sheaf Laplacian Tr(L_F) should decrease as electrode contact improves
- [ ] Verify local-to-global gluing: per-channel signals must compose consistently

### Phase 5: Endurance + Environmental (Day 11-14)
- [ ] 8-hour continuous recording (check for drift, thermal effects)
- [ ] Movement artifact characterization (head turns, walking)
- [ ] Electrode impedance tracking over session duration
- [ ] Power consumption profiling (battery life estimation)

---

## 7. Form Factor Variants

### 7a. Rigid (Standard)
- 50mm x 35mm 4-layer FR4
- Castellated edges for board-to-board stacking (Daisy expansion)
- USB-C connector, SWD debug header, electrode header (2x10 or 2x5)

### 7b. Rigid-Flex (Medium-Term)
- Rigid section: MCU + power + USB-C
- Flex tail: ADC + electrode pads, wraps around headband
- Reduces cable length between electrodes and ADC (lower noise pickup)
- JLCPCB rigid-flex capability: 2+2 layer, polyimide flex, FR4 rigid

### 7c. ShitBCI One-Shot Flex (Scale Target)
- Full flex PCB with stiffener tabs at specific electrode nodes
- Pre-positioned electrode contacts at 10-20 system locations
- Snaps into 3D-printed headband frame
- Designed for JLCPCB pick-and-place at qty 100+
- **WorldPrime integration**: Each board gets a unique world-hash for A/B testing across subjects
- **Scale goal**: $25 all-in BOM at qty 1000, suitable for classroom/workshop deployment

---

## 8. Chip Selection Matrix (ALL TBD -- Starting Points Only)

> Every row below is a **placeholder** based on initial research. Final selection depends on: DigiKey/LCSC stock at order time, JLCPCB basic vs extended parts library, thermal/layout feasibility once schematic is drafted, actual noise measurements from eval boards, and budget. Prices are approximate and will shift.

| Component | Tier 1 (OpenBCI) | Tier 3 (ShitBCI) | Notes |
|-----------|-------------------|-------------------|-------|
| ADC | ADS1299 (~$35) | ADS131M08 (~$8) or ADS1220+mux (~$5) | Starting point -- need eval board noise comparison first |
| MCU | nRF5340 (~$7) | RP2040 (~$0.70) | BLE vs USB-only tradeoff; alternatives: ESP32-S3, STM32 |
| Power | TPS7A4901 (LDO) | AP2112K-3.3 (~$0.20) | Analog LDO choice heavily depends on ADC PSRR needs |
| ESD | TPD4E05U06 | TVS diode array | Specific parts TBD based on electrode interface design |
| Accel | LSM6DSO (~$2.50) | MMA8452Q (~$1) or omit | May swap for BMI270 or similar; may cut entirely |
| Crystal | 32.768 kHz + 8 MHz | 12 MHz (USB) | Frequency depends on final MCU choice |
| Connector | Samtec or Hirose electrode | 2.54mm pin header | Connector choice follows mechanical/form factor decisions |

---

## 9. Relevant ASI Skills

| Skill | Role in Redesign |
|-------|------------------|
| `bci-colored-operad` | Signal processing pipeline architecture, isolation boundaries, GF(3) trit assignment |
| `sheaf-cohomology-bci` | Signal validation: local-to-global consistency, Cech cohomology for gluing verification |
| `cyton-dongle` | OpenBCI radio protocol reference, ADS1299 register configuration, serial commands |
| `glamorous-moldable-multiplatform` | Moldable inspectors for EEG streams, data format parsing (OpenBCI/NWB/XDF/EDF) |
| `nrf5340-hardware` | nRF5340 DK reference, SWD probing, BLE integration patterns |
| `kscale-biomimetic-supply` | Supply chain risk awareness for China-sourced components, domestic sourcing strategy |
| `gay-mcp` | Deterministic color generation for channel visualization in gayOS |
| `worldprime` (zig-syrup) | World A/B testing framework for multi-board, multi-subject experiments |
| `gayOS` (submodule) | TUI/GUI for real-time BCI data display, 1-bit NoteCards interface with terminal cards |

---

## 10. Open Questions

- [ ] ADS131M08 noise floor acceptable for alpha/beta detection? Need eval board test.
- [ ] RP2040 USB latency: can it sustain 250 Hz x 8ch streaming without drops?
- [ ] Rigid-flex minimum order qty at JLCPCB? Last check was 5 pcs minimum.
- [ ] Cognionics HD-72 USB HID protocol: fully documented or need reverse engineering?
- [ ] ShitBCI electrode material: Ag/AgCl snap-on vs conductive fabric vs dry gold-plated spring?
- [ ] Battery vs USB-powered? Battery adds BOM cost + charging circuit complexity.
