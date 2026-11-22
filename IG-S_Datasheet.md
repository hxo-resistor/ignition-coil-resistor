# IG-S Series — Datasheet
## Ceramic Solid Type Suppression Resistor

**HXO Resistor / 华星欧电子**
**Ignition Coil Suppression Resistor — Flagship Series**
**Patent: CN 113016042 A — Ceramic Zone Conduction Technology**
**Rev:** v1.0 | **Date:** 2026-07-22

---

## 1. Product Overview

The IG-S series is HXO Resistor's flagship ignition coil suppression resistor, featuring a ceramic solid non-inductive construction with patented Ceramic Zone Conduction Technology (CN 113016042 A). It delivers the highest pulse withstand voltage (40kV), extreme temperature tolerance (350°C), and virtually zero parasitic inductance (<0.1μH).

Key advantages:
- **Pulse Withstand Voltage**: 40kV (Peak) — Industry Highest
- **Operating Temperature**: -55°C ~ +350°C
- **Parasitic Inductance**: <0.1 μH (Non-Inductive)
- **Failure Mode**: gradual resistance drift (not sudden open-circuit) → superior early warning

Target: high-performance motorcycles, turbocharged engines, racing, military/aerospace, industrial extreme environments.

---

## 2. Patented Ceramic Zone Conduction Technology

**Patent CN 113016042 A — "Peeling Area Conduction Technology"**: Through a specialized sintering process, conductive zones and insulating zones are precisely distributed within the ceramic body. Unlike traditional ceramic solid resistors (uniform conductive phase → electric field concentration → breakdown at high voltage), HXO's patented technology creates multiple parallel conductive paths with a "peeling" distribution pattern.

### Key Advantages

| Advantage | Description | Benefit |
|-----------|-------------|---------|
| Field Uniformity | Eliminates local electric field concentration | 30% higher withstand voltage |
| Redundant Paths | Multiple parallel conductive paths | Graceful failure mode |
| Self-Healing | Minor local breakdowns are non-catastrophic | Higher reliability |
| Non-Inductive | Current flows uniformly through bulk ceramic | <0.1μH inductance |

---

## 3. Detailed Specifications

### 3.1 Power Rating

| Parameter | Specification |
|-----------|---------------|
| Rated Power Range | 2W ~ 10W (at 25°C ambient) |
| Common Power Grades | 3W (motorcycle), 5W (auto), 7~10W (racing/industrial) |
| Derating Recommendation | Actual power ≤ 70% of rated power |
| Short-term Overload | 1.5× rated power for 10s, ΔR ≤ ±1% |
| Note | Ceramic solid has higher thermal capacity than wirewound |

### 3.2 Resistance Range

| Parameter | Specification |
|-----------|---------------|
| Nominal Range | 1kΩ ~ 20kΩ |
| E-Series Standard Values | 1k, 2.2k, 3.3k, 4.7k, 5.1k, 5.6k, 6.8k, 10k, 15k, 20k |
| Most Common Values | 5kΩ~10kΩ (high perf), 10kΩ~15kΩ (industrial) |
| Custom Values | Available upon request within range |

### 3.3 Pulse Withstand Voltage

| Parameter | Specification |
|-----------|---------------|
| Max Pulse Withstand Voltage | 40kV (peak) — Industry Highest |
| Test Waveform | 1.2/50μs standard lightning impulse |
| Continuous Working Voltage | Up to 28kV (AC/DC) |
| Safety Margin | System peak voltage ≤ 80% of rating (≤32kV) |
| Test Standard | IEC 60060-1 |

### 3.4 Voltage Withstand Comparison

| Condition | IG-C (Ceramic Wirewound) | IG-F (Fiberglass) | IG-S (Ceramic Solid) |
|-----------|--------------------------|-------------------|----------------------|
| Max Pulse Voltage | 30kV | 25kV | 40kV |
| Recommended System | ≤24kV | ≤20kV | ≤32kV |
| Application | Standard auto/moto | Economy | High perf / extreme |

### 3.5 Temperature Characteristics

| Parameter | Specification |
|-----------|---------------|
| Operating Temperature Range | -55°C ~ +350°C |
| Storage Temperature Range | -55°C ~ +400°C |
| Temperature Coefficient (TCR) | -900 ± 300 ppm/°C (NTC) |
| TCR Test Condition | 25°C ~ +125°C |
| High Temp Load Life | 350°C, 1000h, ΔR ≤ ±3% |

### 3.6 NTC Characteristics (10kΩ @ 25°C Example)

| Temperature | Resistance Value | Change |
|-------------|------------------|--------|
| -55°C | ~16.5kΩ | +65% |
| 25°C | 10.0kΩ (Reference) | 0% |
| 125°C | ~9.1kΩ | -9% |
| 200°C | ~8.4kΩ | -16% |
| 300°C | ~7.5kΩ | -25% |
| 350°C | ~7.0kΩ | -30% |

**NTC Benefit**: Higher resistance at cold start provides better EMI suppression; lower resistance at operating temperature compensates for ignition energy loss, ensuring reliable ignition in extreme heat.

### 3.7 Tolerance & Insulation

| Parameter | Specification |
|-----------|---------------|
| Tolerance | K(±10%) / M(±20%) — J(±5%) available by screening |
| Insulation Resistance (Standard) | ≥1,000 MΩ (500V DC) |
| Insulation Resistance (After High Temp) | ≥500 MΩ (350°C, 1hr) |
| Insulation Resistance (After Humidity) | ≥100 MΩ (40°C/95%RH/48h) |
| Dielectric Strength | 1.5× rated voltage for 1s, no breakdown |

### 3.8 Inductance & Frequency Characteristics

| Parameter | IG-S (Ceramic Solid) | IG-C (Wirewound) |
|-----------|----------------------|------------------|
| Parasitic Inductance | <0.1 μH (Non-Inductive) | 1~5 μH |
| Frequency Range | DC ~ 100MHz | DC ~ 1MHz |
| Impedance at 10MHz (10kΩ) | ~10.5kΩ | ~16kΩ |
| Impedance at 50MHz (10kΩ) | ~12kΩ | ~35kΩ |
| High Freq Behavior | Purely resistive | Inductive dominant |

---

## 4. Physical Structure

### 4.1 Structure Components

| Component | Material | Function | Key Requirement |
|-----------|----------|----------|-----------------|
| Ceramic Body | SiC-based conductive ceramic | Resistance element, dual-phase distribution | Uniform microstructure |
| End Metallization | Ag-Pd alloy (Silver-Palladium) | Ohmic contact with electrode | Low contact resistance, high temp stable |
| Metal Electrode | Cu/Ni-plated or Stainless Steel | Electrical lead-out, mechanical connection | Pull force ≥60N, corrosion resistant |

### 4.2 Dimensions

| Power Rating | Typical Size (D×L) | Lead Diameter | Package Options |
|--------------|--------------------|---------------|-----------------|
| 2W~3W | 8×25mm ~ 10×35mm | 1.0~1.5mm | IG-A (Cylindrical plug) |
| 5W~7W | 10×35mm ~ 12×45mm | 1.5~2.0mm | IG-A / IG-B (Cap type) |
| 10W | 12×45mm ~ 14×50mm | 2.0mm | IG-A / IG-B / Custom |

---

## 5. Process Characteristics

### 5.1 Ceramic Sintering Process

1. Raw material mixing: SiC powder (0.5~5μm) + ceramic matrix powder at precise ratio
2. Spray granulation + isostatic pressing (≥300MPa)
3. High temp sintering at 1600°C~1800°C for 2~4 hours
4. End metallization: screen printing Ag-Pd paste, 800°C sintering
5. Electrode installation: welding or brazing
6. Sorting: resistance grading

### 5.2 Quality Control Key Points

| Process | Control Parameter | Inspection Method |
|---------|-------------------|-------------------|
| Raw material ratio | Conductive phase content ±0.5% | Weighing + ICP analysis |
| Sintering temperature | ±5°C | Thermocouple real-time monitoring |
| Sintering atmosphere | N₂ protection | O₂ content <100ppm |
| End face bonding | Contact resistance <10mΩ | 4-wire measurement |
| Final screening | 100% resistance + HV test | Auto sorting machine |

---

## 6. Performance Curves

### 6.1 Power Derating Curve

| Ambient Temperature | Allowable Power Ratio |
|---------------------|----------------------|
| 25°C | 100% |
| 100°C | 85% |
| 150°C | 70% |
| 200°C | 55% |
| 250°C | 40% |
| 300°C | 25% |
| 350°C | 10% |

### 6.2 Pulse Life Curve

| Pulse Voltage | Expected Life (Cycles) | Note |
|---------------|------------------------|------|
| 25kV | >2,000,000 | Typical, very long life |
| 30kV | >1,000,000 | High performance |
| 35kV | >500,000 | Extreme conditions |
| 40kV | >100,000 | Maximum rating |

---

## 7. Lifetime Estimation

### 7.1 Expected Lifetime by Application

| Application | Estimated Life | Notes |
|-------------|----------------|-------|
| High perf motorcycle | 50,000~80,000 km | ~5-8 years |
| Turbocharged car | 8-10yrs / 120,000~150,000 km | Extreme heat reliable |
| Racing | 50-100 races | Inspect per event |
| Industrial ignition (continuous) | 30,000~50,000 hours | Continuous high load |
| Military / Aerospace | Per military spec | Extreme reliability |

### 7.2 Failure Mode Analysis

| Failure Mode | Probability | Cause | Prevention |
|--------------|-------------|-------|------------|
| Gradual resistance drift | 50% | Microstructure change at high temp | Periodic monitoring |
| End electrode aging | 25% | High temp oxidation | Choose stainless steel |
| Thermal stress cracking | 15% | Extreme thermal shock | Control ramp rate |
| Insulation degradation | 10% | Surface contamination at high temp | Keep clean |

**Key Difference from Wirewound**: IG-S failures are gradual (drift), not sudden open-circuit, providing superior early warning in safety-critical applications.

---

## 8. Selection Guide

### 8.1 Quick Selection

| Application | Recommended Model | Notes |
|-------------|-------------------|-------|
| High perf motorcycle | IG-S-A-5W-5K6-K | Non-inductive + high voltage |
| Turbocharged car | IG-S-A-7W-10K-K | 300°C+ temp rating |
| Racing | IG-S-A-10W-5K6-K | Extreme conditions |
| Industrial ignition | IG-S-A-10W-15K-K | Continuous operation |
| High frequency multi-spark | IG-S-A-5W-10K-K | Must be non-inductive |
| Extreme temp environment | IG-S-A-5W-10K-K | -55°C~+350°C coverage |

### 8.2 Ordering Information

**Part Number Format:** IG-S-A-5W-10K-K
- IG = Ignition Series
- S = Ceramic Solid
- A = Package Type
- 5W = Power Rating
- 10K = 10kΩ Resistance
- K = ±10% Tolerance

---

**HXO Resistor / 华星欧电子**
Email: resistor@hxo-lcr.cn | Tel: +86 135 1020 0650 | Web: www.hxo-lcr.cn
