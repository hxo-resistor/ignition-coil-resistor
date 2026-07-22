#!/usr/bin/env python3
"""Generate IG-F, IG-S Datasheets, Product Catalog, and Application Notes PDFs"""

from fpdf import FPDF
import os

OUTPUT_DIR = "/app/data/所有对话/主对话/github_pages"
FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

class HXOPDF(FPDF):
    def __init__(self, title="HXO Resistor"):
        super().__init__()
        self.add_font("cjk", "", FONT_REGULAR, uni=True)
        self.add_font("cjk", "B", FONT_BOLD, uni=True)
        self._title = title
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() > 1:
            self.set_font("cjk", "", 7)
            self.set_text_color(153, 153, 153)
            self.cell(0, 8, f"HXO Resistor | {self._title}", align="L")
            self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(233, 69, 96)
            self.line(10, 13, 200, 13)
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("cjk", "", 7)
        self.set_text_color(153, 153, 153)
        if self.page_no() == 1:
            self.cell(0, 10, "HXO Resistor | resistor@hxo-lcr.cn | +86 135 1020 0650", align="C")

    def section_title(self, title):
        self.set_font("cjk", "B", 14)
        self.set_text_color(26, 26, 46)
        self.set_draw_color(233, 69, 96)
        self.ln(4)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def sub_title(self, title):
        self.set_font("cjk", "B", 11)
        self.set_text_color(15, 52, 96)
        self.ln(2)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("cjk", "", 9)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def make_table(self, headers, data, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)
        # Header row
        self.set_font("cjk", "B", 8)
        self.set_fill_color(26, 26, 46)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align="C", fill=True)
        self.ln()
        # Data rows
        self.set_font("cjk", "", 7.5)
        self.set_text_color(51, 51, 51)
        fill = False
        for row in data:
            if self.get_y() > 255:
                self.add_page()
                # Repeat header
                self.set_font("cjk", "B", 8)
                self.set_fill_color(26, 26, 46)
                self.set_text_color(255, 255, 255)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], 7, h, border=1, align="C", fill=True)
                self.ln()
                self.set_font("cjk", "", 7.5)
                self.set_text_color(51, 51, 51)
            if fill:
                self.set_fill_color(248, 249, 250)
            else:
                self.set_fill_color(255, 255, 255)
            for i, d in enumerate(row):
                self.cell(col_widths[i], 6, str(d), border=1, align="C", fill=True)
            self.ln()
            fill = not fill
        self.ln(2)


# ============ IG-F DATASHEET ============
def generate_igf_datasheet():
    pdf = HXOPDF("IG-F Datasheet")
    # Cover page
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("cjk", "B", 28)
    pdf.set_text_color(233, 69, 96)
    pdf.cell(0, 14, "IG-F Series", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("cjk", "B", 16)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 10, "Fiberglass Core Wirewound Suppression Resistor", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("cjk", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Ignition Coil Suppression Resistor - Economy Series", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(233, 69, 96)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("cjk", "", 9)
    pdf.set_text_color(80, 80, 80)
    specs = [
        "Pulse Withstand Voltage: 25kV (Peak)",
        "Operating Temperature: -55°C ~ +155°C",
        "Resistance Range: 1kΩ ~ 15kΩ",
        "Power Range: 1W ~ 10W",
        "Tolerance: ±10% (K) / ±20% (M)",
        "TCR: ±200 ~ ±500 ppm/°C",
        "Insulation Resistance: ≥500 MΩ",
        "Vibration Resistance: Enhanced (+30% vs Ceramic Core)",
    ]
    for s in specs:
        pdf.cell(0, 7, s, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("cjk", "", 8)
    pdf.set_text_color(153, 153, 153)
    pdf.cell(0, 6, "HXO Resistor | resistor@hxo-lcr.cn | +86 135 1020 0650", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "www.hxo-lcr.cn", align="C", new_x="LMARGIN", new_y="NEXT")

    # Page 1: Product Overview
    pdf.add_page()
    pdf.section_title("1. Product Overview")
    pdf.body_text(
        "The IG-F series is HXO Resistor's economy-grade ignition coil suppression resistor, "
        "featuring a fiberglass core wirewound construction. It is designed for cost-sensitive "
        "applications and high-vibration environments where reliability and affordability are paramount."
    )
    pdf.body_text(
        "Key advantages of the IG-F series include: exceptional vibration resistance (30% better "
        "than ceramic core types), cost-effective pricing (approximately 30% lower than IG-C series), "
        "and reliable performance in standard ignition systems. The fiberglass core's inherent "
        "flexibility and high fracture elongation make it ideal for motorcycles, small engines, "
        "and aftermarket replacement applications."
    )

    pdf.section_title("2. Detailed Specifications")
    pdf.sub_title("2.1 Power Rating")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Rated Power Range", "1W ~ 10W (at 25°C ambient)"],
            ["Common Power Grades", "2W (scooter), 3W (motorcycle), 5W (general), 8W (heavy duty)"],
            ["Derating Recommendation", "Actual power ≤ 70% of rated power"],
            ["Derating Curve", "Start derating above 70°C ambient"],
            ["Short-term Overload", "1.5x rated power for 5 seconds"],
        ],
        [60, 130]
    )
    pdf.sub_title("2.2 Resistance Range")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Nominal Range", "1kΩ ~ 15kΩ"],
            ["E-Series Standard Values", "1k, 2.2k, 3.3k, 4.7k, 5.1k, 5.6k, 6.8k, 10k, 15k"],
            ["Most Common Values", "3.3kΩ (small engine), 4.7kΩ (general), 10kΩ (EFI economy)"],
            ["Custom Values", "Available upon request within 1kΩ~15kΩ"],
        ],
        [60, 130]
    )
    pdf.sub_title("2.3 Pulse Withstand Voltage")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Max Pulse Withstand Voltage", "25kV (peak)"],
            ["Test Waveform", "1.2/50μs standard lightning impulse"],
            ["Continuous Working Voltage", "Up to 20kV (AC/DC)"],
            ["Safety Margin", "System peak voltage ≤ 80% of rating (≤20kV)"],
            ["Test Standard", "IEC 60060-1"],
        ],
        [60, 130]
    )
    pdf.sub_title("2.4 Temperature Characteristics")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Operating Temperature Range", "-55°C ~ +155°C"],
            ["Storage Temperature Range", "-55°C ~ +185°C"],
            ["Temperature Coefficient (TCR)", "±200 ~ ±500 ppm/°C"],
            ["TCR Test Condition", "25°C ~ +125°C"],
            ["High Temp Load Life", "155°C, 1000h, ΔR ≤ ±3%"],
        ],
        [60, 130]
    )
    pdf.sub_title("2.5 TCR by Resistance Range")
    pdf.make_table(
        ["Resistance Range", "Typical TCR", "Note"],
        [
            ["1kΩ ~ 3.3kΩ", "±350 ppm/°C", "Larger drift at low end"],
            ["4.7kΩ ~ 10kΩ", "±250 ppm/°C", "Most stable range"],
            ["12kΩ ~ 15kΩ", "±450 ppm/°C", "Largest drift at high end"],
        ],
        [63, 63, 64]
    )
    pdf.sub_title("2.6 Tolerance")
    pdf.make_table(
        ["Grade", "Code", "Deviation", "Application", "Price Factor"],
        [
            ["K", "K", "±10%", "Recommended (general purpose)", "1.0x"],
            ["M", "M", "±20%", "Economy / aftermarket", "0.9x"],
        ],
        [20, 20, 30, 80, 40]
    )
    pdf.sub_title("2.7 Insulation Resistance & Inductance")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Insulation Resistance (Standard)", "≥500 MΩ (500V DC)"],
            ["Insulation Resistance (After Humidity)", "≥50 MΩ (40°C/95%RH/48h)"],
            ["Dielectric Strength", "1.5x rated voltage for 1s, no breakdown"],
            ["Insulation Material", "Epoxy resin, UL 94 V-0"],
            ["Parasitic Inductance", "1~5 μH (wirewound structure)"],
            ["Frequency Range", "DC ~ 1MHz"],
        ],
        [60, 130]
    )

    # Page 2: Physical Structure
    pdf.add_page()
    pdf.section_title("3. Physical Structure")
    pdf.sub_title("3.1 Structure Diagram")
    pdf.body_text(
        "The IG-F series consists of: fiberglass core (GFRP) as the insulating substrate, "
        "NiCr alloy resistance wire wound around the core, brass/nickel-plated end caps for "
        "electrical connection, and flame-retardant epoxy resin encapsulation."
    )
    pdf.sub_title("3.2 Component Details")
    pdf.make_table(
        ["Component", "Material", "Function", "Key Requirement"],
        [
            ["Fiberglass Core", "GFRP (Glass Fiber Reinforced Polymer)", "Insulating support, flexibility", "Flexural strength ≥200MPa"],
            ["Resistance Wire", "NiCr 80/20 Alloy", "Generate resistance, current limiting", "High resistivity, oxidation resistant"],
            ["End Cap", "Brass, Nickel-plated", "Electrical connection, mechanical fixing", "Contact resistance low, pull force ≥40N"],
            ["Encapsulation", "Epoxy Resin (UL 94 V-0)", "Insulation, moisture proof, vibration proof", "Temp rating ≥155°C"],
        ],
        [35, 50, 55, 50]
    )
    pdf.sub_title("3.3 Fiberglass vs Ceramic Core Comparison")
    pdf.make_table(
        ["Property", "IG-F (Fiberglass)", "IG-C (Ceramic)"],
        [
            ["Core Density", "2.0 g/cm³", "3.8 g/cm³"],
            ["Flexural Strength", "≥200MPa", "≥300MPa"],
            ["Elastic Modulus", "20GPa", "300GPa"],
            ["Fracture Elongation", "2-3%", "0.1%"],
            ["Thermal Conductivity", "0.3-0.5 W/m·K", "20-30 W/m·K"],
            ["CTE", "10-15 ppm/°C", "6-8 ppm/°C"],
        ],
        [63, 63, 64]
    )
    pdf.body_text(
        "The fiberglass core's low elastic modulus and high fracture elongation provide natural "
        "advantages in vibration environments - absorbing vibration energy without brittle fracture."
    )
    pdf.sub_title("3.4 Dimensions")
    pdf.make_table(
        ["Power Rating", "Typical Size (D×L)", "Lead Diameter", "Package Options"],
        [
            ["1W~3W", "8×25mm ~ 10×35mm", "1.0~1.5mm", "IG-A (Cylindrical plug)"],
            ["5W~8W", "10×35mm ~ 12×45mm", "1.5~2.0mm", "IG-A / IG-B (Cap type)"],
            ["10W", "12×45mm ~ 14×50mm", "2.0mm", "IG-A / Custom"],
        ],
        [35, 55, 50, 50]
    )

    pdf.section_title("4. Process Characteristics")
    pdf.sub_title("4.1 Fiberglass Core Manufacturing")
    pdf.body_text(
        "Process: Pultrusion forming - glass fiber strands impregnated with resin, cured at "
        "150°C~180°C. Glass fiber content: 60%~70% by volume. Surface treatment with coupling "
        "agent to enhance resin bonding."
    )
    pdf.sub_title("4.2 Winding Process")
    pdf.body_text(
        "IG-F series uses tension-controlled winding: (1) Low tension winding to prevent "
        "fiberglass core deformation; (2) Uniform pitch for consistent resistance; (3) Dual "
        "fixation (adhesive + crimping) at wire ends."
    )
    pdf.sub_title("4.3 Encapsulation")
    pdf.body_text(
        "Dipping process: uniform epoxy coating. Curing: 120°C, 1.5 hours. Coating thickness: "
        "0.3~0.5mm. (Lower curing temperature vs ceramic core due to fiberglass temp limit.)"
    )

    # Performance Curves
    pdf.add_page()
    pdf.section_title("5. Performance Curves")
    pdf.sub_title("5.1 Power Derating Curve")
    pdf.make_table(
        ["Ambient Temperature", "Allowable Power Ratio"],
        [
            ["25°C", "100%"],
            ["70°C", "80%"],
            ["100°C", "60%"],
            ["125°C", "40%"],
            ["145°C", "20%"],
            ["155°C", "0%"],
        ],
        [95, 95]
    )
    pdf.sub_title("5.2 Resistance vs Temperature (Typical, 4.7kΩ/±250ppm)")
    pdf.make_table(
        ["Temperature", "Resistance Value", "Change"],
        [
            ["-55°C", "~4.60kΩ", "-2.1%"],
            ["25°C", "4.70kΩ (Reference)", "0%"],
            ["85°C", "~4.77kΩ", "+1.5%"],
            ["125°C", "~4.82kΩ", "+2.6%"],
            ["155°C", "~4.85kΩ", "+3.3%"],
        ],
        [63, 63, 64]
    )
    pdf.sub_title("5.3 Pulse Life Curve")
    pdf.make_table(
        ["Pulse Voltage", "Expected Life (Cycles)", "Note"],
        [
            ["15kV", ">1,000,000", "Typical condition, very long life"],
            ["20kV", ">500,000", "Within normal margin"],
            ["22kV", ">200,000", "Near rated value"],
            ["25kV", ">50,000", "Limit, avoid prolonged use"],
        ],
        [50, 70, 70]
    )

    pdf.section_title("6. Lifetime Estimation")
    pdf.sub_title("6.1 Expected Lifetime by Application")
    pdf.make_table(
        ["Application", "Estimated Life", "Notes"],
        [
            ["Motorcycle (city commuting)", "20,000~40,000 km", "~2-4 years"],
            ["Small scooter (≤125cc)", "15,000~25,000 km", "Lower engine bay temp"],
            ["General purpose engine", "10,000~20,000 hours", "Low load continuous"],
            ["Aftermarket replacement", "Varies by original condition", "Usually improves OEM"],
        ],
        [65, 65, 60]
    )
    pdf.sub_title("6.2 Failure Mode Analysis")
    pdf.make_table(
        ["Failure Mode", "Probability", "Cause", "Prevention"],
        [
            ["Resistance drift", "45%", "Long-term high temp aging", "Keep temp ≤125°C"],
            ["Open circuit (wire melt)", "30%", "Overload / pulse exceeded", "Adequate derating"],
            ["Insulation breakdown", "15%", "Pulse voltage exceeded", "Don't use >20kV systems"],
            ["Core aging", "10%", "Resin degradation at high temp", "Avoid >155°C"],
        ],
        [40, 30, 50, 70]
    )

    pdf.section_title("7. Selection Guide")
    pdf.sub_title("7.1 Quick Selection")
    pdf.make_table(
        ["Application", "Recommended Model", "Notes"],
        [
            ["Economy motorcycle", "IG-F-A-3W-4K7-M", "Lowest cost, ±20%"],
            ["Small scooter (≤125cc)", "IG-F-A-2W-3K3-K", "Cost sensitive, ignition priority"],
            ["General gasoline engine", "IG-F-A-3W-5K6-K", "Best value for money"],
            ["Aftermarket replacement", "IG-F-A-3W-4K7-M", "Universal, wide compatibility"],
            ["High vibration environment", "IG-F-A-5W-4K7-K", "Leverage fiberglass advantage"],
        ],
        [65, 65, 60]
    )
    pdf.sub_title("7.2 Ordering Information")
    pdf.body_text(
        "Example: IG-F-A-3W-4K7-K\n"
        "IG = Ignition Series | F = Fiberglass Core | A = Package Type (Cylindrical Plug) | "
        "3W = Power Rating | 4K7 = 4.7kΩ Resistance | K = ±10% Tolerance"
    )

    pdf_path = os.path.join(OUTPUT_DIR, "IG-F_Datasheet.pdf")
    pdf.output(pdf_path)
    print(f"Generated: {pdf_path}")
    return pdf_path


# ============ IG-S DATASHEET ============
def generate_igs_datasheet():
    pdf = HXOPDF("IG-S Datasheet")
    # Cover page
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("cjk", "B", 28)
    pdf.set_text_color(233, 69, 96)
    pdf.cell(0, 14, "IG-S Series", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("cjk", "B", 16)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 10, "Ceramic Solid Type Suppression Resistor", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("cjk", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Ignition Coil Suppression Resistor - Flagship Series", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(233, 69, 96)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("cjk", "B", 9)
    pdf.set_text_color(233, 69, 96)
    pdf.cell(0, 7, "Patent: CN 113016042 A - Ceramic Zone Conduction Technology", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("cjk", "", 9)
    pdf.set_text_color(80, 80, 80)
    specs = [
        "Pulse Withstand Voltage: 40kV (Peak) - Industry Highest",
        "Operating Temperature: -55°C ~ +350°C",
        "Resistance Range: 1kΩ ~ 20kΩ",
        "Power Range: 2W ~ 10W",
        "Tolerance: ±10% (K) / ±20% (M)",
        "TCR: -900±300 ppm/°C (NTC - Negative Temperature Coefficient)",
        "Insulation Resistance: ≥1,000 MΩ",
        "Parasitic Inductance: <0.1 μH (Non-Inductive)",
    ]
    for s in specs:
        pdf.cell(0, 7, s, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("cjk", "", 8)
    pdf.set_text_color(153, 153, 153)
    pdf.cell(0, 6, "HXO Resistor | resistor@hxo-lcr.cn | +86 135 1020 0650", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "www.hxo-lcr.cn", align="C", new_x="LMARGIN", new_y="NEXT")

    # Page 1: Overview
    pdf.add_page()
    pdf.section_title("1. Product Overview")
    pdf.body_text(
        "The IG-S series is HXO Resistor's flagship ignition coil suppression resistor, "
        "featuring a ceramic solid non-inductive construction with patented Ceramic Zone Conduction "
        "Technology (CN 113016042 A). It represents the pinnacle of HXO's resistor technology, "
        "delivering the highest pulse withstand voltage (40kV), extreme temperature tolerance (350°C), "
        "and virtually zero parasitic inductance (<0.1μH)."
    )
    pdf.body_text(
        "The IG-S series is designed for applications demanding the ultimate in performance and "
        "reliability: high-performance motorcycles, turbocharged engines, racing, military/aerospace, "
        "and industrial extreme environments. Its unique failure mode (gradual resistance drift rather "
        "than sudden open circuit) provides superior early warning in safety-critical applications."
    )

    pdf.section_title("2. Patented Ceramic Zone Conduction Technology")
    pdf.sub_title("2.1 Technology Overview")
    pdf.body_text(
        "Patent CN 113016042 A - 'Peeling Area Conduction Technology': Through a specialized "
        "sintering process, conductive zones and insulating zones are precisely distributed within "
        "the ceramic body. Unlike traditional ceramic solid resistors where conductive phases are "
        "uniformly distributed (leading to electric field concentration and breakdown at high voltage), "
        "HXO's patented technology creates multiple parallel conductive paths with a 'peeling' "
        "distribution pattern."
    )
    pdf.sub_title("2.2 Key Advantages")
    pdf.make_table(
        ["Advantage", "Description", "Benefit"],
        [
            ["Field Uniformity", "Eliminates local electric field concentration", "30% higher withstand voltage"],
            ["Redundant Paths", "Multiple parallel conductive paths", "Graceful failure mode"],
            ["Self-Healing", "Minor local breakdowns are non-catastrophic", "Higher reliability"],
            ["Non-Inductive", "Current flows uniformly through bulk ceramic", "<0.1μH inductance"],
        ],
        [40, 65, 85]
    )

    # Detailed Specs
    pdf.section_title("3. Detailed Specifications")
    pdf.sub_title("3.1 Power Rating")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Rated Power Range", "2W ~ 10W (at 25°C ambient)"],
            ["Common Power Grades", "3W (motorcycle), 5W (auto), 7~10W (racing/industrial)"],
            ["Derating Recommendation", "Actual power ≤ 70% of rated power"],
            ["Short-term Overload", "1.5x rated power for 10s, ΔR ≤ ±1%"],
            ["Note", "Ceramic solid has higher thermal capacity than wirewound"],
        ],
        [60, 130]
    )
    pdf.sub_title("3.2 Resistance Range")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Nominal Range", "1kΩ ~ 20kΩ"],
            ["E-Series Standard Values", "1k, 2.2k, 3.3k, 4.7k, 5.1k, 5.6k, 6.8k, 10k, 15k, 20k"],
            ["Most Common Values", "5kΩ~10kΩ (high perf), 10kΩ~15kΩ (industrial)"],
            ["Custom Values", "Available upon request within range"],
        ],
        [60, 130]
    )
    pdf.sub_title("3.3 Pulse Withstand Voltage")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Max Pulse Withstand Voltage", "40kV (peak) - Industry Highest"],
            ["Test Waveform", "1.2/50μs standard lightning impulse"],
            ["Continuous Working Voltage", "Up to 28kV (AC/DC)"],
            ["Safety Margin", "System peak voltage ≤ 80% of rating (≤32kV)"],
            ["Test Standard", "IEC 60060-1"],
        ],
        [60, 130]
    )
    pdf.sub_title("3.4 Voltage Withstand Comparison")
    pdf.make_table(
        ["Condition", "IG-C (Ceramic Wirewound)", "IG-F (Fiberglass)", "IG-S (Ceramic Solid)"],
        [
            ["Max Pulse Voltage", "30kV", "25kV", "40kV"],
            ["Recommended System", "≤24kV", "≤20kV", "≤32kV"],
            ["Application", "Standard auto/moto", "Economy", "High perf / extreme"],
        ],
        [40, 50, 50, 50]
    )
    pdf.sub_title("3.5 Temperature Characteristics")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Operating Temperature Range", "-55°C ~ +350°C"],
            ["Storage Temperature Range", "-55°C ~ +400°C"],
            ["Temperature Coefficient (TCR)", "-900 ± 300 ppm/°C (NTC)"],
            ["TCR Test Condition", "25°C ~ +125°C"],
            ["High Temp Load Life", "350°C, 1000h, ΔR ≤ ±3%"],
        ],
        [60, 130]
    )
    pdf.sub_title("3.6 NTC Characteristics (10kΩ @ 25°C Example)")
    pdf.make_table(
        ["Temperature", "Resistance Value", "Change"],
        [
            ["-55°C", "~16.5kΩ", "+65%"],
            ["25°C", "10.0kΩ (Reference)", "0%"],
            ["125°C", "~9.1kΩ", "-9%"],
            ["200°C", "~8.4kΩ", "-16%"],
            ["300°C", "~7.5kΩ", "-25%"],
            ["350°C", "~7.0kΩ", "-30%"],
        ],
        [63, 63, 64]
    )
    pdf.body_text(
        "NTC Benefit: Higher resistance at cold start provides better EMI suppression; "
        "lower resistance at operating temperature compensates for ignition energy loss, "
        "ensuring reliable ignition in extreme heat."
    )
    pdf.sub_title("3.7 Tolerance & Insulation")
    pdf.make_table(
        ["Parameter", "Specification"],
        [
            ["Tolerance", "K(±10%) / M(±20%) - J(±5%) available by screening"],
            ["Insulation Resistance (Standard)", "≥1,000 MΩ (500V DC)"],
            ["Insulation Resistance (After High Temp)", "≥500 MΩ (350°C, 1hr)"],
            ["Insulation Resistance (After Humidity)", "≥100 MΩ (40°C/95%RH/48h)"],
            ["Dielectric Strength", "1.5x rated voltage for 1s, no breakdown"],
        ],
        [60, 130]
    )
    pdf.sub_title("3.8 Inductance & Frequency Characteristics")
    pdf.make_table(
        ["Parameter", "IG-S (Ceramic Solid)", "IG-C (Wirewound)"],
        [
            ["Parasitic Inductance", "<0.1 μH (Non-Inductive)", "1~5 μH"],
            ["Frequency Range", "DC ~ 100MHz", "DC ~ 1MHz"],
            ["Impedance at 10MHz (10kΩ)", "~10.5kΩ", "~16kΩ"],
            ["Impedance at 50MHz (10kΩ)", "~12kΩ", "~35kΩ"],
            ["High Freq Behavior", "Purely resistive", "Inductive dominant"],
        ],
        [55, 67, 68]
    )

    # Physical Structure
    pdf.add_page()
    pdf.section_title("4. Physical Structure")
    pdf.sub_title("4.1 Structure Components")
    pdf.make_table(
        ["Component", "Material", "Function", "Key Requirement"],
        [
            ["Ceramic Body", "SiC-based conductive ceramic", "Resistance element, dual-phase distribution", "Uniform microstructure"],
            ["End Metallization", "Ag-Pd alloy (Silver-Palladium)", "Ohmic contact with electrode", "Low contact resistance, high temp stable"],
            ["Metal Electrode", "Cu/Ni-plated (standard) or Stainless Steel", "Electrical lead-out, mechanical connection", "Pull force ≥60N, corrosion resistant"],
        ],
        [35, 55, 55, 45]
    )
    pdf.sub_title("4.2 Dimensions")
    pdf.make_table(
        ["Power Rating", "Typical Size (D×L)", "Lead Diameter", "Package Options"],
        [
            ["2W~3W", "8×25mm ~ 10×35mm", "1.0~1.5mm", "IG-A (Cylindrical plug)"],
            ["5W~7W", "10×35mm ~ 12×45mm", "1.5~2.0mm", "IG-A / IG-B (Cap type)"],
            ["10W", "12×45mm ~ 14×50mm", "2.0mm", "IG-A / IG-B / Custom"],
        ],
        [35, 55, 50, 50]
    )

    pdf.section_title("5. Process Characteristics")
    pdf.sub_title("5.1 Ceramic Sintering Process")
    pdf.body_text(
        "Process flow: (1) Raw material mixing: SiC powder (0.5~5μm) + ceramic matrix powder "
        "at precise ratio; (2) Spray granulation + isostatic pressing (≥300MPa); (3) High temp "
        "sintering at 1600°C~1800°C for 2~4 hours; (4) End metallization: screen printing Ag-Pd "
        "paste, 800°C sintering; (5) Electrode installation: welding or brazing; (6) Sorting: "
        "resistance grading."
    )
    pdf.sub_title("5.2 Quality Control Key Points")
    pdf.make_table(
        ["Process", "Control Parameter", "Inspection Method"],
        [
            ["Raw material ratio", "Conductive phase content ±0.5%", "Weighing + ICP analysis"],
            ["Sintering temperature", "±5°C", "Thermocouple real-time monitoring"],
            ["Sintering atmosphere", "N₂ protection", "O₂ content <100ppm"],
            ["End face bonding", "Contact resistance <10mΩ", "4-wire measurement"],
            ["Final screening", "100% resistance + HV test", "Auto sorting machine"],
        ],
        [50, 65, 75]
    )

    # Performance Curves
    pdf.section_title("6. Performance Curves")
    pdf.sub_title("6.1 Power Derating Curve")
    pdf.make_table(
        ["Ambient Temperature", "Allowable Power Ratio"],
        [
            ["25°C", "100%"],
            ["100°C", "85%"],
            ["150°C", "70%"],
            ["200°C", "55%"],
            ["250°C", "40%"],
            ["300°C", "25%"],
            ["350°C", "10%"],
        ],
        [95, 95]
    )
    pdf.sub_title("6.2 Pulse Life Curve")
    pdf.make_table(
        ["Pulse Voltage", "Expected Life (Cycles)", "Note"],
        [
            ["25kV", ">2,000,000", "Typical, very long life"],
            ["30kV", ">1,000,000", "High performance"],
            ["35kV", ">500,000", "Extreme conditions"],
            ["40kV", ">100,000", "Maximum rating"],
        ],
        [50, 70, 70]
    )

    pdf.section_title("7. Lifetime Estimation")
    pdf.sub_title("7.1 Expected Lifetime by Application")
    pdf.make_table(
        ["Application", "Estimated Life", "Notes"],
        [
            ["High perf motorcycle", "50,000~80,000 km", "~5-8 years"],
            ["Turbocharged car", "8-10yrs / 120,000~150,000 km", "Extreme heat reliable"],
            ["Racing", "50-100 races", "Inspect per event"],
            ["Industrial ignition (continuous)", "30,000~50,000 hours", "Continuous high load"],
            ["Military / Aerospace", "Per military spec", "Extreme reliability"],
        ],
        [65, 65, 60]
    )
    pdf.sub_title("7.2 Failure Mode Analysis")
    pdf.make_table(
        ["Failure Mode", "Probability", "Cause", "Prevention"],
        [
            ["Gradual resistance drift", "50%", "Microstructure change at high temp", "Periodic monitoring"],
            ["End electrode aging", "25%", "High temp oxidation", "Choose stainless steel"],
            ["Thermal stress cracking", "15%", "Extreme thermal shock", "Control ramp rate"],
            ["Insulation degradation", "10%", "Surface contamination at high temp", "Keep clean"],
        ],
        [45, 25, 50, 70]
    )
    pdf.body_text(
        "Key Difference from Wirewound: IG-S failures are gradual (drift), not sudden open-circuit, "
        "providing superior early warning in safety-critical applications."
    )

    pdf.section_title("8. Selection Guide")
    pdf.sub_title("8.1 Quick Selection")
    pdf.make_table(
        ["Application", "Recommended Model", "Notes"],
        [
            ["High perf motorcycle", "IG-S-A-5W-5K6-K", "Non-inductive + high voltage"],
            ["Turbocharged car", "IG-S-A-7W-10K-K", "300°C+ temp rating"],
            ["Racing", "IG-S-A-10W-5K6-K", "Extreme conditions"],
            ["Industrial ignition", "IG-S-A-10W-15K-K", "Continuous operation"],
            ["High frequency multi-spark", "IG-S-A-5W-10K-K", "Must be non-inductive"],
            ["Extreme temp environment", "IG-S-A-5W-10K-K", "-55°C~+350°C coverage"],
        ],
        [65, 65, 60]
    )
    pdf.sub_title("8.2 Ordering Information")
    pdf.body_text(
        "Example: IG-S-A-5W-10K-K\n"
        "IG = Ignition Series | S = Ceramic Solid | A = Package Type | "
        "5W = Power Rating | 10K = 10kΩ Resistance | K = ±10% Tolerance"
    )

    pdf_path = os.path.join(OUTPUT_DIR, "IG-S_Datasheet.pdf")
    pdf.output(pdf_path)
    print(f"Generated: {pdf_path}")
    return pdf_path


# ============ PRODUCT CATALOG ============
def generate_product_catalog():
    pdf = HXOPDF("Product Catalog")
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("cjk", "B", 26)
    pdf.set_text_color(233, 69, 96)
    pdf.cell(0, 12, "HXO Resistor", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("cjk", "B", 18)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 10, "Product Catalog & Selection Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("cjk", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Ignition Coil Suppression Resistors - IG Series", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(233, 69, 96)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("cjk", "", 9)
    pdf.set_text_color(80, 80, 80)
    info = [
        "HXO Resistor - Specialized in Ignition Coil Suppression Resistors since 2018",
        "IG-C: Ceramic Core Wirewound | IG-F: Fiberglass Core Wirewound | IG-S: Ceramic Solid Type",
        "Pulse Voltage up to 40kV | Temp up to 350°C | Delivery 7-15 days",
        "Serving 500+ customers in 30+ countries",
    ]
    for line in info:
        pdf.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("cjk", "", 8)
    pdf.set_text_color(153, 153, 153)
    pdf.cell(0, 6, "HXO Resistor | resistor@hxo-lcr.cn | +86 135 1020 0650", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "www.hxo-lcr.cn", align="C", new_x="LMARGIN", new_y="NEXT")

    # Page 1: Series Overview
    pdf.add_page()
    pdf.section_title("1. Product Series Overview")
    pdf.sub_title("1.1 Three Series Comparison")
    pdf.make_table(
        ["Parameter", "IG-C (Ceramic Wirewound)", "IG-F (Fiberglass Wirewound)", "IG-S (Ceramic Solid)"],
        [
            ["Technology", "Ceramic Core Wirewound", "Fiberglass Core Wirewound", "Ceramic Solid (Non-Inductive)"],
            ["Pulse Voltage", "30kV", "25kV", "40kV (Highest)"],
            ["Working Voltage", "28kV", "20kV", "28kV"],
            ["Temp Range", "-55°C ~ +275°C", "-55°C ~ +155°C", "-55°C ~ +350°C"],
            ["Resistance", "1kΩ ~ 20kΩ", "1kΩ ~ 15kΩ", "1kΩ ~ 20kΩ"],
            ["Power Range", "1W ~ 15W", "1W ~ 10W", "2W ~ 10W"],
            ["Tolerance", "±5% / ±10% / ±20%", "±10% / ±20%", "±10% / ±20%"],
            ["TCR", "±100~±300 ppm/°C", "±200~±500 ppm/°C", "-900±300 ppm/°C (NTC)"],
            ["Insulation R", "≥1,000MΩ", "≥500MΩ", "≥1,000MΩ"],
            ["Inductance", "1~5 μH", "1~5 μH", "<0.1 μH (Non-Inductive)"],
            ["Vibration", "Standard", "Enhanced (+30%)", "Standard"],
            ["Patent", "—", "—", "CN 113016042 A"],
            ["Positioning", "Best Value, Standard Use", "Economy, High Vibration", "Flagship, Extreme Env."],
            ["Lead Time", "7-15 days", "7-15 days", "7-15 days"],
        ],
        [32, 52, 53, 53]
    )

    pdf.section_title("2. Selection Guide")
    pdf.sub_title("2.1 By Vehicle / Equipment Type")
    pdf.make_table(
        ["Application", "Recommended Series", "Recommended Model", "Reason"],
        [
            ["Small scooter (<125cc)", "IG-F", "IG-F-A-2W-3K3-K", "Best value, high vibration"],
            ["Mid motorcycle (125-400cc)", "IG-C", "IG-C-A-3W-4K7-K", "Stable, balanced performance"],
            ["Large motorcycle (>400cc)", "IG-C / IG-S", "IG-C-A-5W-5K6-K", "Higher power requirement"],
            ["Liter-class motorcycle", "IG-S", "IG-S-A-7W-10K-K", "High voltage, non-inductive"],
            ["Car (1.0-2.0L)", "IG-C / IG-S", "IG-C-A-5W-5K6-K", "Automotive grade required"],
            ["Car (>2.0L / Turbo)", "IG-S", "IG-S-A-7W-10K-K", "High temp & pressure"],
            ["Generator / Industrial", "IG-S / IG-C", "IG-S-A-10W-15K-K", "Continuous, high temp"],
            ["Lawn mower / Chainsaw", "IG-F", "IG-F-A-3W-4K7-K", "Light, vibration resistant"],
            ["Marine engine", "IG-S", "IG-S-A-7W-10K-K (Marine)", "Corrosion resistant"],
            ["Racing / High perf", "IG-S", "IG-S-A-5W-10K-K", "Non-inductive, high precision"],
        ],
        [40, 35, 55, 60]
    )

    pdf.sub_title("2.2 By Environmental Condition")
    pdf.make_table(
        ["Condition", "Recommended Series", "Notes"],
        [
            ["High temp (>150°C)", "IG-C / IG-S", "IG-C: 275°C, IG-S: 350°C"],
            ["High vibration (>5G)", "IG-F", "Fiberglass core, best vibration resistance"],
            ["High humidity (>85% RH)", "IG-S", "All-inorganic, non-hygroscopic"],
            ["Salt spray environment", "IG-S (Marine grade)", "Anti-corrosion coating"],
            ["Explosion-proof area", "IG-S", "All-inorganic, intrinsically safe"],
            ["High frequency application", "IG-S", "Non-inductive design, no resonance"],
        ],
        [60, 60, 70]
    )

    # Naming Rules
    pdf.add_page()
    pdf.section_title("3. Naming Rules & Ordering Codes")
    pdf.sub_title("3.1 Part Number Structure")
    pdf.body_text(
        "IG - [CORE] - [PACKAGE] - [POWER] - [RESISTANCE] - [TOLERANCE]\n\n"
        "Example: IG-C-A-3W-4K7-K\n"
        "IG = Ignition Series\n"
        "C = Core Type: C (Ceramic Wirewound) / F (Fiberglass Wirewound) / S (Ceramic Solid)\n"
        "A = Package Type: A (Cylindrical Plug) / B (Cap Type) / Custom\n"
        "3W = Power Rating: 2W, 3W, 5W, 7W, 10W, 15W\n"
        "4K7 = Resistance Code: 4K7=4.7kΩ, 5K6=5.6kΩ, 100=10kΩ, 150=15kΩ\n"
        "K = Tolerance: J(±5%), K(±10%), M(±20%)"
    )
    pdf.sub_title("3.2 Standard Part Numbers")
    pdf.make_table(
        ["Part Number", "Series", "Power", "Resistance", "Tolerance", "Application"],
        [
            ["IG-C-A-3W-4K7-K", "IG-C", "3W", "4.7kΩ", "±10%", "Motorcycle standard"],
            ["IG-C-A-5W-5K6-K", "IG-C", "5W", "5.6kΩ", "±10%", "Auto standard"],
            ["IG-C-A-10W-10K-K", "IG-C", "10W", "10kΩ", "±10%", "Industrial"],
            ["IG-F-A-2W-3K3-K", "IG-F", "2W", "3.3kΩ", "±10%", "Scooter economy"],
            ["IG-F-A-3W-4K7-M", "IG-F", "3W", "4.7kΩ", "±20%", "Aftermarket"],
            ["IG-F-A-5W-5K6-K", "IG-F", "5W", "5.6kΩ", "±10%", "General engine"],
            ["IG-S-A-5W-10K-K", "IG-S", "5W", "10kΩ", "±10%", "High perf motorcycle"],
            ["IG-S-A-7W-5K6-K", "IG-S", "7W", "5.6kΩ", "±10%", "Turbo car"],
            ["IG-S-A-10W-15K-K", "IG-S", "10W", "15kΩ", "±10%", "Industrial extreme"],
        ],
        [50, 20, 20, 25, 20, 55]
    )

    pdf.section_title("4. Packaging & Delivery")
    pdf.sub_title("4.1 Packaging Specifications")
    pdf.make_table(
        ["Packaging Type", "Quantity", "Application"],
        [
            ["Bulk (bag)", "1,000 pcs/bag", "Small batch / sample"],
            ["Tape & Reel", "2,000 pcs/reel", "Auto placement"],
            ["Carton (20 bags)", "20,000 pcs/carton", "Standard batch"],
            ["Custom packaging", "Per customer request", "OEM orders"],
        ],
        [55, 65, 70]
    )
    pdf.sub_title("4.2 Shipping Methods")
    pdf.make_table(
        ["Method", "Transit Time", "Min Quantity"],
        [
            ["International Express (DHL/FedEx/UPS)", "3-7 days", "From 1kg"],
            ["Air Freight", "5-10 days", "From 50kg"],
            ["Sea Freight (LCL)", "25-40 days", "From 1CBM"],
            ["Sea Freight (FCL)", "25-40 days", "From 20GP"],
        ],
        [65, 50, 75]
    )
    pdf.sub_title("4.3 Delivery Terms")
    pdf.body_text(
        "Standard Lead Time: 7-15 days (from order confirmation)\n"
        "Express Lead Time: 3-7 days (surcharge applies)\n"
        "MOQ: 20,000 pcs per model (standard), 10,000 pcs (trial order)\n"
        "Payment: T/T, L/C\n"
        "Trade Terms: EXW Shenzhen / FOB Shenzhen / CIF\n"
        "Free Samples: Up to 10 pcs per model for new customers (shipping at customer's cost)"
    )

    pdf.section_title("5. Contact Information")
    pdf.body_text(
        "HXO Resistor - Huaxingou Electronics (Shenzhen) Co., Ltd.\n"
        "Email: resistor@hxo-lcr.cn\n"
        "Phone: +86 135 1020 0650\n"
        "Website: www.hxo-lcr.cn\n"
        "Address: Shenzhen, Guangdong, China"
    )

    pdf_path = os.path.join(OUTPUT_DIR, "Product_Catalog.pdf")
    pdf.output(pdf_path)
    print(f"Generated: {pdf_path}")
    return pdf_path


# ============ APPLICATION NOTES ============
def generate_application_notes():
    pdf = HXOPDF("Application Notes")
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("cjk", "B", 24)
    pdf.set_text_color(233, 69, 96)
    pdf.cell(0, 12, "Application Notes", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("cjk", "B", 16)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 10, "Ignition Coil Suppression Resistor Selection Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("cjk", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "IG-C / IG-F / IG-S Series", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(233, 69, 96)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("cjk", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "Comprehensive guide for selecting the right ignition coil suppression resistor", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Covers: Automotive, Motorcycle, Generator, and Industrial applications", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("cjk", "", 8)
    pdf.set_text_color(153, 153, 153)
    pdf.cell(0, 6, "HXO Resistor | resistor@hxo-lcr.cn | +86 135 1020 0650", align="C", new_x="LMARGIN", new_y="NEXT")

    # Page 1: Selection by Application
    pdf.add_page()
    pdf.section_title("1. Selection by Application Scenario")
    pdf.sub_title("1.1 Automotive Ignition Systems")
    pdf.body_text(
        "Recommended Series: IG-C (Ceramic Core Wirewound) as main choice, "
        "IG-S (Ceramic Solid) for turbocharged/high-performance models."
    )
    pdf.body_text(
        "Key considerations:\n"
        "- Engine bay temperature: 120°C~150°C (normal), 200°C+ (turbo side)\n"
        "- IG-C series (275°C) and IG-S series (350°C) fully cover automotive requirements\n"
        "- EMC compliance: CISPR 25 standard - 10kΩ resistance recommended for better EMI suppression\n"
        "- Multi-cylinder consistency: ±5% (J grade) recommended for balanced ignition across cylinders\n"
        "- Recommended power: 5W for standard cars, 7W~10W for turbo/heavy duty"
    )
    pdf.body_text(
        "Common mistakes:\n"
        "❌ 'Car and motorcycle resistors are the same' - Car engine bay temps are much higher\n"
        "❌ 'Turbo cars must use IG-S' - IG-C (275°C) is sufficient for mild turbo applications\n"
        "❌ 'Higher power is always better' - 5W is typically sufficient for pulse mode operation"
    )

    pdf.sub_title("1.2 Motorcycle Ignition Systems")
    pdf.body_text(
        "Recommended Series: IG-F (Fiberglass) for economy, IG-C (Ceramic) for mid-range, "
        "IG-S (Ceramic Solid) for high-performance."
    )
    pdf.body_text(
        "Key considerations:\n"
        "- Vibration environment: Much higher than cars - IG-F's fiberglass core excels here\n"
        "- Cost sensitivity: IG-F is ~30% cheaper than IG-C, ideal for cost-sensitive markets\n"
        "- Small displacement needs low resistance: 1kΩ~3.3kΩ for 50-125cc scooters\n"
        "- Aftermarket replacement: IG-F series with ±20% tolerance offers widest compatibility"
    )
    pdf.body_text(
        "Common mistakes:\n"
        "❌ 'Ceramic solid is best for vibration' - Actually ceramic is brittle; fiberglass is better\n"
        "❌ 'EFI bikes need >10kΩ' - 4.7kΩ~5.6kΩ is usually sufficient\n"
        "❌ 'Higher resistance = better for aftermarket' - Match original OEM spec"
    )

    pdf.sub_title("1.3 Generator / Small Engine Applications")
    pdf.body_text(
        "Recommended Series: IG-F (Fiberglass) for economy, IG-C (Ceramic) for high reliability."
    )
    pdf.body_text(
        "Key considerations:\n"
        "- Continuous operation mode: Thermal accumulation effect requires adequate power derating\n"
        "- Small portable generators (≤2kW): IG-F-A-3W-4K7-K\n"
        "- Medium generators (2-10kW): IG-F-A-5W-5K6-K\n"
        "- Large generators (>10kW): IG-C-A-10W-10K-K\n"
        "- Power derating: ≥50% recommended for continuous operation"
    )

    pdf.sub_title("1.4 Industrial Equipment")
    pdf.body_text(
        "Recommended Series: IG-S (Ceramic Solid) as flagship, IG-C (Ceramic) as value choice."
    )
    pdf.body_text(
        "Key considerations:\n"
        "- Extreme temperatures: 200°C~350°C - IG-S's 350°C rating is the only option\n"
        "- 24/7 continuous operation: IG-S's gradual failure mode is superior to wirewound's sudden failure\n"
        "- High-frequency multi-spark: IG-S's non-inductive design (<0.1μH) ensures stable performance\n"
        "- Explosion-proof compliance: IG-S's all-ceramic structure is intrinsically safe\n"
        "- Recommended: IG-S-A-10W-15K-K for industrial burners"
    )

    # Common Mistakes
    pdf.add_page()
    pdf.section_title("2. Common Selection Mistakes")
    pdf.sub_title("2.1 Mistake: Lower Resistance = Better Performance")
    pdf.body_text(
        "Reality: Lower resistance increases EMI interference and reduces spark plug life.\n"
        "Recommended: Choose higher resistance (4.7kΩ~10kΩ) for better EMI suppression "
        "while maintaining reliable ignition. For EFI vehicles, ≥4.7kΩ is recommended."
    )

    pdf.sub_title("2.2 Mistake: Higher Power = Safer Choice")
    pdf.body_text(
        "Reality: Ignition coil resistors operate in pulse mode - average power is only 10-30% "
        "of rated power. Oversized resistors increase cost and size without benefit.\n"
        "Recommended: 2-3x actual average power is sufficient. Motorcycle: 2-3W, Car: 5W."
    )

    pdf.sub_title("2.3 Mistake: Only Compare Resistance Value, Ignore Technology Type")
    pdf.body_text(
        "Reality: Same 10kΩ resistance across different technologies delivers vastly different performance:\n"
        "- Pulse voltage: IG-F 25kV vs IG-C 30kV vs IG-S 40kV\n"
        "- Temperature: IG-F 155°C vs IG-C 275°C vs IG-S 350°C\n"
        "- Inductance: IG-F/IG-C 1-5μH vs IG-S <0.1μH\n"
        "- Life: IG-F 15Khrs vs IG-C 25Khrs vs IG-S 40Khrs"
    )

    pdf.sub_title("2.4 Mistake: Imported Brands Are Always Better")
    pdf.body_text(
        "Reality: HXO's patented technology (CN 113016042 A) achieves 40kV withstand voltage, "
        "matching or exceeding international brands. With 100% HV testing, 7-15 day delivery, "
        "and 30-50% lower pricing, HXO offers superior value."
    )

    pdf.sub_title("2.5 Mistake: Temperature Doesn't Affect Resistor Performance")
    pdf.body_text(
        "Reality: Temperature is the #1 factor affecting resistor life (Arrhenius law: each 10°C "
        "rise halves the life). Selection must start with determining operating temperature range, "
        "then choosing the appropriate series."
    )

    pdf.sub_title("2.6 Mistake: Pulse Voltage Isn't Important")
    pdf.body_text(
        "Reality: Transient peak voltages can reach 2-3x the nominal working voltage. "
        "Always maintain ≥20% safety margin above the system peak voltage. When in doubt, "
        "choose a higher voltage rating."
    )

    pdf.sub_title("2.7 Mistake: Installation Direction Doesn't Matter")
    pdf.body_text(
        "Reality: Proper installation extends resistor life by 20-30%:\n"
        "- Keep the resistor body away from metal parts (prevents short circuits)\n"
        "- Lead wire bending radius ≥ 2x lead diameter\n"
        "- Ensure good electrical contact between end cap and spark plug wire\n"
        "- Avoid mechanical stress on the resistor body"
    )

    pdf.sub_title("2.8 Mistake: Frequency Doesn't Matter")
    pdf.body_text(
        "Reality: In high-frequency systems (>1MHz), wirewound resistors' inductance causes "
        "impedance to increase significantly. For multi-spark and high-frequency systems, "
        "IG-S (non-inductive) is the only suitable choice."
    )

    # Installation Guide
    pdf.add_page()
    pdf.section_title("3. Installation Guidelines")
    pdf.sub_title("3.1 General Installation Rules")
    pdf.body_text(
        "1. Keep the resistor body away from direct contact with metal engine parts\n"
        "2. Ensure adequate clearance around the resistor for heat dissipation\n"
        "3. Use proper tools for lead bending - bend radius ≥ 2x lead diameter\n"
        "4. Do not apply excessive force to the resistor body during installation\n"
        "5. Ensure end caps are fully seated and making good electrical contact\n"
        "6. For cap-type (IG-B), ensure the cap completely covers the spark plug terminal\n"
        "7. Avoid sharp bends or kinks in the resistor leads"
    )
    pdf.sub_title("3.2 Heat Management")
    pdf.body_text(
        "1. Position the resistor away from exhaust manifolds and other heat sources\n"
        "2. Ensure adequate airflow around the resistor\n"
        "3. For continuous operation, maintain at least 50% power derating\n"
        "4. Consider using heat shields in extreme environments\n"
        "5. IG-S series can operate at up to 350°C - ideal for extreme heat locations"
    )
    pdf.sub_title("3.3 Vibration Management")
    pdf.body_text(
        "1. Secure the resistor and its leads to prevent vibration-induced fatigue\n"
        "2. Use cable ties or brackets to secure leads\n"
        "3. For high-vibration environments, choose IG-F (fiberglass core) series\n"
        "4. Allow some slack in the leads to prevent tension\n"
        "5. Avoid routing leads near moving engine parts"
    )

    pdf.section_title("4. Recommended Spare Parts")
    pdf.make_table(
        ["Application", "Model", "Cross Reference"],
        [
            ["125cc motorcycle (general)", "IG-F-A-3W-4K7-M", "Replaces most OEM 4.7kΩ"],
            ["250cc motorcycle", "IG-C-A-3W-4K7-K", "NGK, Denso equivalents"],
            ["Car (1.0-2.0L)", "IG-C-A-5W-5K6-K", "Standard automotive replacement"],
            ["Turbocharged car", "IG-S-A-7W-10K-K", "High performance replacement"],
            ["Generator", "IG-C-A-10W-10K-K", "Industrial continuous duty"],
            ["Racing", "IG-S-A-5W-10K-K", "Non-inductive, high precision"],
        ],
        [55, 55, 80]
    )

    pdf.section_title("5. Contact & Support")
    pdf.body_text(
        "For technical support, free samples, or bulk pricing inquiries:\n\n"
        "Email: resistor@hxo-lcr.cn\n"
        "Phone: +86 135 1020 0650\n"
        "Website: www.hxo-lcr.cn\n"
        "Free Samples: Up to 10 pcs per model for new customers\n"
        "Standard Lead Time: 7-15 days\n"
        "Express Lead Time: 3-7 days (surcharge applies)"
    )

    pdf_path = os.path.join(OUTPUT_DIR, "Application_Notes.pdf")
    pdf.output(pdf_path)
    print(f"Generated: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generate_igf_datasheet()
    generate_igs_datasheet()
    generate_product_catalog()
    generate_application_notes()
    print("\nAll PDFs generated successfully!")
