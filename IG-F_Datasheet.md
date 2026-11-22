# IG-F Series — Datasheet
## Fiberglass Core Wirewound Suppression Resistor

**HXO Resistor / 华星欧电子**
**Ignition Coil Suppression Resistor — Economy Series**
**Rev:** v1.0 | **Date:** 2026-07-22

---

## 1. Product Overview

The IG-F series is HXO Resistor's economy-grade ignition coil suppression resistor, featuring a fiberglass core wirewound construction. It is designed for cost-sensitive applications and high-vibration environments where reliability and affordability are paramount.

Key advantages:
- **Vibration resistance**: 30% better than ceramic core types
- **Cost**: ~30% lower than IG-C series
- **Reliability**: stable in standard ignition systems
- **Target**: motorcycles, small engines, aftermarket replacement

---

## 2. Detailed Specifications

### 2.1 Power Rating

| Parameter | Specification |
|-----------|---------------|
| Rated Power Range | 1W ~ 10W (at 25°C ambient) |
| Common Power Grades | 2W (scooter), 3W (motorcycle), 5W (general), 8W (heavy duty) |
| Derating Recommendation | Actual power ≤ 70% of rated power |
| Derating Curve | Start derating above 70°C ambient |
| Short-term Overload | 1.5× rated power for 5 seconds |

### 2.2 Resistance Range

| Parameter | Specification |
|-----------|---------------|
| Nominal Range | 1kΩ ~ 15kΩ |
| E-Series Standard Values | 1k, 2.2k, 3.3k, 4.7k, 5.1k, 5.6k, 6.8k, 10k, 15k |
| Most Common Values | 3.3kΩ (small engine), 4.7kΩ (general), 10kΩ (EFI economy) |
| Custom Values | Available upon request within 1kΩ~15kΩ |

### 2.3 Pulse Withstand Voltage

| Parameter | Specification |
|-----------|---------------|
| Max Pulse Withstand Voltage | 25kV (peak) |
| Test Waveform | 1.2/50μs standard lightning impulse |
| Continuous Working Voltage | Up to 20kV (AC/DC) |
| Safety Margin | System peak voltage ≤ 80% of rating (≤20kV) |
| Test Standard | IEC 60060-1 |

### 2.4 Temperature Characteristics

| Parameter | Specification |
|-----------|---------------|
| Operating Temperature Range | -55°C ~ +155°C |
| Storage Temperature Range | -55°C ~ +185°C |
| Temperature Coefficient (TCR) | ±200 ~ ±500 ppm/°C |
| TCR Test Condition | 25°C ~ +125°C |
| High Temp Load Life | 155°C, 1000h, ΔR ≤ ±3% |

### 2.5 TCR by Resistance Range

| Resistance Range | Typical TCR | Note |
|------------------|-------------|------|
| 1kΩ ~ 3.3kΩ | ±350 ppm/°C | Larger drift at low end |
| 4.7kΩ ~ 10kΩ | ±250 ppm/°C | Most stable range |
| 12kΩ ~ 15kΩ | ±450 ppm/°C | Largest drift at high end |

### 2.6 Tolerance

| Grade | Code | Deviation | Application | Price Factor |
|-------|------|-----------|-------------|--------------|
| K | K | ±10% | Recommended (general purpose) | 1.0× |
| M | M | ±20% | Economy / aftermarket | 0.9× |

### 2.7 Insulation Resistance & Inductance

| Parameter | Specification |
|-----------|---------------|
| Insulation Resistance (Standard) | ≥500 MΩ (500V DC) |
| Insulation Resistance (After Humidity) | ≥50 MΩ (40°C/95%RH/48h) |
| Dielectric Strength | 1.5× rated voltage for 1s, no breakdown |
| Insulation Material | Epoxy resin, UL 94 V-0 |
| Parasitic Inductance | 1~5 μH (wirewound structure) |
| Frequency Range | DC ~ 1MHz |

---

## 3. Physical Structure

The IG-F series consists of: fiberglass core (GFRP) as the insulating substrate, NiCr alloy resistance wire wound around the core, brass/nickel-plated end caps for electrical connection, and flame-retardant epoxy resin encapsulation.

### 3.1 Component Details

| Component | Material | Function | Key Requirement |
|-----------|----------|----------|-----------------|
| Fiberglass Core | GFRP (Glass Fiber Reinforced Polymer) | Insulating support, flexibility | Flexural strength ≥200MPa |
| Resistance Wire | NiCr 80/20 Alloy | Generate resistance, current limiting | High resistivity, oxidation resistant |
| End Cap | Brass, Nickel-plated | Electrical connection, mechanical fixing | Contact resistance low, pull force ≥40N |
| Encapsulation | Epoxy Resin (UL 94 V-0) | Insulation, moisture proof, vibration proof | Temp rating ≥155°C |

### 3.2 Fiberglass vs Ceramic Core Comparison

| Property | IG-F (Fiberglass) | IG-C (Ceramic) |
|----------|-------------------|----------------|
| Core Density | 2.0 g/cm³ | 3.8 g/cm³ |
| Flexural Strength | ≥200MPa | ≥300MPa |
| Elastic Modulus | 20GPa | 300GPa |
| Fracture Elongation | 2-3% | 0.1% |
| Thermal Conductivity | 0.3-0.5 W/m·K | 20-30 W/m·K |
| CTE | 10-15 ppm/°C | 6-8 ppm/°C |

The fiberglass core's low elastic modulus and high fracture elongation provide natural advantages in vibration environments — absorbing vibration energy without brittle fracture.

### 3.3 Dimensions

| Power Rating | Typical Size (D×L) | Lead Diameter | Package Options |
|--------------|--------------------|---------------|-----------------|
| 1W~3W | 8×25mm ~ 10×35mm | 1.0~1.5mm | IG-A (Cylindrical plug) |
| 5W~8W | 10×35mm ~ 12×45mm | 1.5~2.0mm | IG-A / IG-B (Cap type) |
| 10W | 12×45mm ~ 14×50mm | 2.0mm | IG-A / Custom |

---

## 4. Process Characteristics

- **Fiberglass Core Manufacturing**: Pultrusion forming — glass fiber strands impregnated with resin, cured at 150°C~180°C. Glass fiber content 60%~70% by volume. Surface treatment with coupling agent to enhance resin bonding.
- **Winding Process**: Tension-controlled winding — (1) low tension to prevent fiberglass core deformation; (2) uniform pitch for consistent resistance; (3) dual fixation (adhesive + crimping) at wire ends.
- **Encapsulation**: Dipping process — uniform epoxy coating. Curing 120°C, 1.5 hours. Coating thickness 0.3~0.5mm.

---

## 5. Performance Curves

### 5.1 Power Derating Curve

| Ambient Temperature | Allowable Power Ratio |
|---------------------|----------------------|
| 25°C | 100% |
| 70°C | 80% |
| 100°C | 60% |
| 125°C | 40% |
| 145°C | 20% |
| 155°C | 0% |

### 5.2 Resistance vs Temperature (Typical, 4.7kΩ/±250ppm)

| Temperature | Resistance Value | Change |
|-------------|------------------|--------|
| -55°C | ~4.60kΩ | -2.1% |
| 25°C | 4.70kΩ (Reference) | 0% |
| 85°C | ~4.77kΩ | +1.5% |
| 125°C | ~4.82kΩ | +2.6% |
| 155°C | ~4.85kΩ | +3.3% |

### 5.3 Pulse Life Curve

| Pulse Voltage | Expected Life (Cycles) | Note |
|---------------|------------------------|------|
| 15kV | >1,000,000 | Typical condition, very long life |
| 20kV | >500,000 | Within normal margin |
| 22kV | >200,000 | Near rated value |
| 25kV | >50,000 | Limit, avoid prolonged use |

---

## 6. Lifetime Estimation

### 6.1 Expected Lifetime by Application

| Application | Estimated Life | Notes |
|-------------|----------------|-------|
| Motorcycle (city commuting) | 20,000~40,000 km | ~2-4 years |
| Small scooter (≤125cc) | 15,000~25,000 km | Lower engine bay temp |
| General purpose engine | 10,000~20,000 hours | Low load continuous |
| Aftermarket replacement | Varies by original condition | Usually improves OEM |

### 6.2 Failure Mode Analysis

| Failure Mode | Probability | Cause | Prevention |
|--------------|-------------|-------|------------|
| Resistance drift | 45% | Long-term high temp aging | Keep temp ≤125°C |
| Open circuit (wire melt) | 30% | Overload / pulse exceeded | Adequate derating |
| Insulation breakdown | 15% | Pulse voltage exceeded | Don't use >20kV systems |
| Core aging | 10% | Resin degradation at high temp | Avoid >155°C |

---

## 7. Selection Guide

### 7.1 Quick Selection

| Application | Recommended Model | Notes |
|-------------|-------------------|-------|
| Economy motorcycle | IG-F-A-3W-4K7-M | Lowest cost, ±20% |
| Small scooter (≤125cc) | IG-F-A-2W-3K3-K | Cost sensitive, ignition priority |
| General gasoline engine | IG-F-A-3W-5K6-K | Best value for money |
| Aftermarket replacement | IG-F-A-3W-4K7-M | Universal, wide compatibility |
| High vibration environment | IG-F-A-5W-4K7-K | Leverage fiberglass advantage |

### 7.2 Ordering Information

**Part Number Format:** IG-F-A-3W-4K7-K
- IG = Ignition Series
- F = Fiberglass Core
- A = Package Type (Cylindrical Plug)
- 3W = Power Rating
- 4K7 = 4.7kΩ Resistance
- K = ±10% Tolerance

---

**HXO Resistor / 华星欧电子**
Email: resistor@hxo-lcr.cn | Tel: +86 135 1020 0650 | Web: www.hxo-lcr.cn
