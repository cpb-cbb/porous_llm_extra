"""
一步式完整提取 Prompt
用于对比分步+验证工作流的准确率和召回率
Version 1.0
"""

ONE_STEP_EXTRACTION_PROMPT = """
**Role Setting**: Comprehensive Porous Carbon Material Information Extraction Expert

**Task**: Perform a complete, one-shot extraction of ALL relevant information from a porous carbon supercapacitor literature, including sample identification, synthesis details, physicochemical properties, and electrochemical performance.

**Input**: Full text of the literature (including abstract, main text, figures, tables, and supporting information).

**Overall Requirements**:
* Read the entire document carefully and extract ALL information in a single pass.
* Output a single, comprehensive JSON object.
* Ensure accuracy and completeness - do not miss any samples or data points.
* If information is not mentioned, use `null`.
* Output ONLY the JSON object, no additional text.

---

## PART 1: Document Relevance & Sample Identification

**Step 1.1 - Relevance Check**:
1. Determine if this literature studies porous carbon materials for supercapacitors.
2. If NOT relevant, output: `{"status": "irrelevant", "reason": "...", "samples": []}`
3. If relevant, proceed to identify ALL samples.

**Step 1.2 - Sample Identification**:
* Identify ALL porous carbon material samples explicitly synthesized and characterized.
* Use exact sample names from the literature (e.g., PC-800, NPC-2, AC-KOH-900).
* Only include samples experimentally synthesized within this study.

---

## PART 2: Comprehensive Data Extraction (For Each Sample)

For **each identified sample**, extract the following four categories of information:

### Category A: Synthesis Process

**A1. Components**:
* **Precursors**: List all components and their roles (carbon source, nitrogen source, etc.)
* **Activator**: Chemical agent (e.g., KOH, ZnCl₂)
* **Template**: Material (e.g., SiO₂, SBA-15)
* **Ratios**: All specified ratios between components
  - Format: `[{component_A: "KOH", component_B: "Precursor", ratio: "4:1", type: "mass"}]`

**A2. Process Flow**:
* Deconstruct synthesis into chronological steps
* For each step (especially thermal treatments), extract:
  - `step_name`: e.g., "Drying", "Pre-carbonization", "Activation"
  - `temperature`: (°C)
  - `duration`: (h)
  - `heating_rate`: (°C/min)
  - `atmosphere`: (e.g., "N2", "Ar")
  - `flow_rate`: (mL/min)
  - `details`: Other notes

### Category B: Physicochemical Properties

**B1. Porosity and Structure**:
* `SpecificSurfaceArea_BET`: (m²/g)
* `MicroporeSurfaceArea`: (m²/g, specify method)
* `TotalPoreVolume`: (cm³/g)
* `MicroporeVolume`: (cm³/g, specify method)
* `MesoporeVolume`: (cm³/g)
* `PoreSizeDistribution`: Summarize key peaks (nm)
* `AveragePoreDiameter`: (nm)

**B2. Composition**:
* **Elemental**: All elements (C, O, N, S, P) in at% or wt%
  - Format: `{C: {value: 90.1, unit: "wt%"}, N: {value: 2.5, unit: "wt%"}}`
* **HighResolution_XPS**:
  - **N_Species** (from N1s): Pyridinic-N (%), Pyrrolic-N (%), Graphitic-N (%), Oxidized-N (%)
  - **C_Species** (from C1s): C-C/C=C (%), C-O (%), C=O (%), O-C=O (%)
* **QualitativeFunctionalGroups_FTIR**: Main functional groups (e.g., -OH, C=O)

**B3. Crystallinity**:
* `Graphitization_Raman_ID_IG`: ID/IG ratio

### Category C: Electrochemical Performance

For **each test system** (defined by SystemType + Electrolyte):

**C1. System Configuration**:
* `SystemType`: "Three-electrode" / "Two-electrode symmetric" / "Two-electrode asymmetric"
* `Electrolyte`: e.g., "6M KOH", "1M H2SO4"
* `VoltageWindow`: e.g., "[-1, 0] V", "[0, 1.8] V"

**C2. Performance Metrics**:

**For Three-electrode Systems**:
* **SpecificCapacitance**: Extract ALL data points
  - Format: `[{method: "GCD", value: 350, unit: "F/g", condition: "1 A/g", mass_loading: "1.2 mg/cm²"}, ...]`
  - **CRITICAL**: Extract mass_loading for each data point (use `null` if not mentioned)
* **RateCapability**: Format: "85% (from 1 A/g to 20 A/g)"
* **Impedance**: `{ESR: value, Rct: value, unit: "Ω"}`

**For Two-electrode Systems**:
* **MaxEnergyDensity**: "25 Wh/kg @ 500 W/kg"
* **MaxPowerDensity**: "10000 W/kg @ 15 Wh/kg"
* **CycleStability**: "10000 cycles, 95% retention @ 10 A/g"
* **Impedance**: `{ESR: value, Rct: value, unit: "Ω"}`

---

## Output Format

Generate a **single JSON object** with the following structure:

```json
{
  "status": "relevant",
  "samples": ["Sample-1", "Sample-2"],
  "data": {
    "Sample-1": {
      "synthesis": {
        "Components": {
          "Precursors": ["bamboo", "spiral algae"],
          "Activator": "KOH",
          "Template": null,
          "Ratios": [
            {"component_A": "KOH", "component_B": "Precursor", "ratio": "3:1", "type": "mass"}
          ]
        },
        "ProcessFlow": [
          {
            "step_name": "Pre-carbonization",
            "temperature": 400,
            "duration": 1,
            "heating_rate": 5,
            "atmosphere": "N2",
            "flow_rate": null,
            "details": null
          },
          {
            "step_name": "Activation",
            "temperature": 800,
            "duration": 2,
            "heating_rate": 5,
            "atmosphere": "N2",
            "flow_rate": null,
            "details": null
          }
        ]
      },
      "properties": {
        "Porosity": {
          "SpecificSurfaceArea_BET": {"value": 2500, "unit": "m²/g"},
          "MicroporeSurfaceArea": {"value": 1800, "unit": "m²/g", "method": "DFT"},
          "TotalPoreVolume": {"value": 1.2, "unit": "cm³/g"},
          "MicroporeVolume": {"value": 0.85, "unit": "cm³/g", "method": "DFT"},
          "MesoporeVolume": {"value": 0.35, "unit": "cm³/g"},
          "PoreSizeDistribution": "Peaks at 0.7 nm, 1.2 nm, and 3.5 nm",
          "AveragePoreDiameter": {"value": 2.1, "unit": "nm"}
        },
        "Composition": {
          "Elemental": {
            "C": {"value": 88.5, "unit": "at%"},
            "O": {"value": 8.2, "unit": "at%"},
            "N": {"value": 3.3, "unit": "at%"}
          },
          "HighResolution_XPS": {
            "N_Species": {
              "Pyridinic-N": 35.2,
              "Pyrrolic-N": 38.5,
              "Graphitic-N": 26.3,
              "Oxidized-N": null
            },
            "C_Species": {
              "C-C/C=C": 78.5,
              "C-O": 12.3,
              "C=O": 6.2,
              "O-C=O": 3.0
            }
          },
          "QualitativeFunctionalGroups_FTIR": ["-OH", "C=O", "C-N"]
        },
        "Crystallinity": {
          "Graphitization_Raman_ID_IG": 1.08
        }
      },
      "performance": [
        {
          "SystemType": "Three-electrode",
          "Electrolyte": "6M KOH",
          "VoltageWindow": "[-1, 0] V",
          "SpecificCapacitance": [
            {"method": "GCD", "value": 380, "unit": "F/g", "condition": "0.5 A/g", "mass_loading": "1.0 mg/cm²"},
            {"method": "GCD", "value": 350, "unit": "F/g", "condition": "1 A/g", "mass_loading": "1.0 mg/cm²"},
            {"method": "GCD", "value": 280, "unit": "F/g", "condition": "20 A/g", "mass_loading": "1.0 mg/cm²"},
            {"method": "CV", "value": 360, "unit": "F/g", "condition": "5 mV/s", "mass_loading": "1.0 mg/cm²"}
          ],
          "RateCapability": "73.7% (from 0.5 A/g to 20 A/g)",
          "Impedance": {"ESR": 0.42, "Rct": 0.85, "unit": "Ω"}
        },
        {
          "SystemType": "Two-electrode symmetric",
          "Electrolyte": "6M KOH",
          "VoltageWindow": "[0, 1.0] V",
          "MaxEnergyDensity": "28.5 Wh/kg @ 450 W/kg",
          "MaxPowerDensity": "12000 W/kg @ 12 Wh/kg",
          "CycleStability": "10000 cycles, 96.5% retention @ 10 A/g",
          "Impedance": {"ESR": 0.65, "Rct": null, "unit": "Ω"}
        }
      ]
    },
    "Sample-2": {
      "synthesis": {...},
      "properties": {...},
      "performance": [...]
    }
  }
}
```

---

## Critical Reminders

1. **Completeness**: Extract ALL samples and ALL data points mentioned in the literature.
2. **Accuracy**: Double-check numbers, units, and sample-data associations.
3. **System Separation**: Keep three-electrode and two-electrode data strictly separated.
4. **Mass Loading**: For three-electrode specific capacitance, ALWAYS try to extract mass_loading.
5. **Multiple Test Conditions**: If a sample is tested under different electrolytes or voltage windows, create separate system objects.
6. **Supporting Information**: Check SI thoroughly - critical data is often there.
7. **No Hallucination**: If information is not mentioned, use `null`. Do not invent data.

**Final Output**: Return ONLY the JSON object above, with no additional text, comments, or explanations.
"""