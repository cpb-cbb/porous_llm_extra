# -*- coding: utf-8 -*-
"""
This script stores the optimized prompts for the multi-step information extraction
process for porous carbon material literature for supercapacitors.
Version 4.0 (Streamlined for performance prediction modeling)
"""

# --- Step 1.1: Document Relevance & Sample Identification ---
prompt_1_1 = """
Role Setting: Literature Screening and Sample Identification Expert
Task: Strictly analyze the literature step-by-step to determine relevance and extract key sample information.
Extraction Process:
1.  **Document Relevance Judgment**:
    * Carefully read the abstract, introduction, and experimental sections of the literature.
    * Does this literature study or synthesize **porous carbon materials for supercapacitors**?
    * If not, return directly: "This document does not meet the requirements."
2.  **Sample Identification**:
    * If yes, please identify **all** porous carbon material samples explicitly synthesized and characterized in the literature.
    * List the **exact names** of these samples (e.g., PC-800, NPC-2, AC-KOH-900).
3.  **Output Format**:
    * If relevant, output a list containing the names of all identified samples.
    * Format: `Sample List: [Sample Name 1, Sample Name 2, ...]`

Notes:
    * Only identify samples **experimentally synthesized** in the literature.
    * Ensure sample names are accurate and consistent with the literature.
"""

# --- Step 1.2: Synthesis & Preparation Conditions Extraction (Refined) ---
prompt_1_2 = """
Role Setting: Material Synthesis Information Extraction Expert
Task: For each sample identified in the previous step, accurately extract its synthesis and preparation conditions from the literature.
Input:
    * Full text of the literature (including supporting information).
    * The sample list from the previous step: `[Sample Name 1, Sample Name 2, ...]`
Extraction Process:
1.  **Locate Information**: For **each** sample name in the list, find its detailed preparation process in the literature (especially the experimental methods section and supporting information).
2.  **Extract Key Parameters**: Extract the following information for each sample:
    * **Precursor**: Must list all components (e.g., phenolic resin, sucrose, soybean dregs, polymer name).
    * **Activator**: Specify the type (e.g., KOH, ZnCl₂, CO₂, H₂O). If none, state "None".
    * **Activator/Precursor Ratio**: e.g., 1:1, 4:1.
    * **Pyrolysis/Carbonization Temp.**: Unit in °C. If multi-step, specify the temperature of the key step.
    * **Activation Temp.**: Unit in °C.
    * **Activation Time**: Unit in h (hours).
    * **Heating Rate**: Unit in °C/min or K/min.
    * **Gas Atmosphere & Flow Rate**: Extract gas type and flow rate separately. e.g., {Gas Type: "N₂", Flow Rate: "200 mL/min"}.
    * **Template**: e.g., SiO₂, MOF, SBA-15. If not used, state "None".
    * **Other Process**: e.g., pre-oxidation, acid washing, doping steps, plasma treatment, etc., and describe key parameters.
3.  **Output Format**:
    * Generate an information record for each sample.
    * Format:
        Sample Name 1: {Precursor: ${value}$, Activator: ${value}$, Activator/Precursor Ratio: ${value}$, Pyrolysis/Carbonization Temp.: ${value}$°C, Activation Temp.: ${value}$°C, Activation Time: ${value}$h, Heating Rate: ${value}$°C/min, Gas Atmosphere & Flow Rate: {Gas Type: "${value}$", Flow Rate: "${value}$"}, Template: ${value}$, Other Process: ${value}$};
        Sample Name 2: {Precursor: ${value}$, Activator: ${value}$, ...};
        ...

Notes:
    * Ensure information corresponds to the correct sample name.
    * If a specific piece of information is not mentioned in the literature, use "Not mentioned".
    * **Be sure to check the Supporting Information (SI)**.
"""

# --- Step 1.3: Physical & Chemical Properties Extraction (Refined) ---
prompt_1_3 = """
**Role Setting:** Material Physicochemical Properties Analysis Expert

**Task:** For the specified sample list, accurately extract physicochemical property data from the literature (including main text, figures, tables, and supporting information).

**Input:**
*   Full text of the literature (including figures, tables, supporting information).
*   Sample list: `[Sample Name 1, Sample Name 2, ...]`

**Extraction Process:**

1.  **Locate Information**: For **each** sample name in the list, find its physicochemical property data in the literature (results and discussion, figures, tables, supporting information).

2.  **Extract Structural and Porosity Parameters**:
    *   **BET Specific Surface Area**: (Unit: m²/g)
    *   **Micropore Surface Area**: (Unit: m²/g; specify calculation method, e.g., DFT, t-plot)
    *   **Total Pore Volume**: (Unit: cm³/g)
    *   **Micropore Volume**: (Unit: cm³/g; specify calculation method, e.g., DFT, t-plot)
    *   **Mesopore Volume**: (Unit: cm³/g)
    *   **Pore Size Distribution Description**: (nm; summarize from the pore size distribution plot. e.g., "Mainly distributed at 0.5-2 nm", "Bimodal peaks at <2 nm and 2-5 nm")

3.  **Extract Surface Chemistry and Crystal Structure Parameters**:
    *   **Overall Element Content (XPS or Elemental Analysis)**: Extract the atomic percentage (at%) or weight percentage (wt%) for the following primary elements.
        *   **Carbon (C)**: (Unit: % at or % wt)
        *   **Oxygen (O)**: (Unit: % at or % wt)
        *   **Nitrogen (N)**: (Unit: % at or % wt)
    *   **Nitrogen Species Content (High-Resolution N1s XPS)**: For the total Nitrogen content, extract the relative percentage (%) of its specific bonding states. Use the standard names below. The sum of these species should ideally be close to 100%.
        *   **Pyridinic-N (N_PYRIDINIC)**: (Unit: %)
        *   **Pyrrolic-N (N_PYRROLIC)**: (Unit: %)
        *   **Graphitic-N (N_GRAPHITIC)**: (Unit: %)
        *   **Oxidized-N (N_OXIDIZED)**: (Unit: %)
    *   **Functional Groups (FTIR)**: List the main identified functional groups, such as -COOH, -OH, C=O, C-N.
    *   **Degree of Graphitization (Raman)**: Extract the ID/IG ratio.

4.  **Output Format**:
    *   Generate an information record for each sample.
    *   Format:
        `Sample Name 1: {BET Specific Surface Area: ${value}$ m²/g, Micropore Surface Area: ${value}$ m²/g (${method}$), Total Pore Volume: ${value}$ cm³/g, Micropore Volume: ${value}$ cm³/g (${method}$), Mesopore Volume: ${value}$ cm³/g, Pore Size Distribution: ${description}$, Element Content: {C: ${value}$%, O: ${value}$%, N: ${value}$% (N_PYRIDINIC: ${value}$%, N_PYRROLIC: ${value}$%, N_GRAPHITIC: ${value}$%, N_OXIDIZED: ${value}$%)}, Functional Groups: [${group1}$, ${group2}$], ID/IG: ${value}$};`
        `Sample Name 2: {BET Specific Surface Area: ...};`
        `...`

**Notes:**
*   Ensure data corresponds to the correct sample name.
*   Units must be extracted.
*   If a specific piece of information is not mentioned in the literature, use "Not mentioned".
"""

# --- Step 1.4: Electrochemical Performance Extraction (Streamlined) ---
prompt_1_4 = """
Role Setting: Electrochemical Performance Data Extraction Expert
Task: For each sample, extract the core electrochemical performance under **different test systems**. This version has been streamlined for modeling needs.

Input:
* Full text of the literature (including figures, tables, supporting information).
* Sample list: `[Sample Name 1, Sample Name 2, ...]`

Extraction Process:
1.  **Identify Test Systems**:
    * For **each** sample in the list, identify all independent electrochemical test systems in the literature.
    * An independent "test system" is defined by **[System Type]** and **[Electrolyte]**.
    * e.g., "Three-electrode, 6M KOH" and "Two-electrode symmetric, 1M Na₂SO₄" are two independent test systems.

2.  **Extract Data within Each System**:
    * For **each test system** you identify, extract all the following relevant information:
    * **SystemType**: e.g., "Three-electrode", "Two-electrode symmetric", "Two-electrode asymmetric".
    * **Electrolyte**: e.g., "6M KOH", "1M H2SO4", "EMIMBF4".
    * **VoltageWindow**: e.g., "[-1, 0] V", "[0, 1.8] V".
    * **SpecificCapacitance**:
        * **Extract only in three-electrode systems**.
        * Must include the calculation method (GCD/CV) and the corresponding condition (current density A/g or scan rate mV/s).
        * Provide all reported data points as a list, **ensuring to cover a range from low to high conditions** to reflect rate performance.
    * **RateCapability**:
        * **Extract only in three-electrode systems**.
        * Extract the **capacitance retention** when changing from a low to a high current density.
        * Format example: "85% (from 1 A/g to 20 A/g)".
    * **Energy/Power Density**:
        * **Extract only in two-electrode (device) systems**.
        * Extract the **MaxEnergyDensity** and **MaxPowerDensity** from the Ragone plot, and note their corresponding power or energy density conditions.
    * **CycleStability**:
        * Extract the number of cycles, capacity retention, and note the current density or scan rate during the test.
    * **Impedance**:
        * Extract the equivalent series resistance (ESR) and charge transfer resistance (Rct) from the Nyquist plot, unit in Ω.

3.  **Output Format**:
    * Generate a list containing all test systems for each sample.
    * Format:
        Sample Name 1: [
            {
                SystemType: "Three-electrode",
                Electrolyte: "6M KOH",
                VoltageWindow: "[-1, 0] V",
                SpecificCapacitance: [{method: "GCD", value: 350, unit: "F/g", condition: "1 A/g"}, {method: "GCD", value: 280, unit: "F/g", condition: "20 A/g"}],
                RateCapability: "80% (from 1 A/g to 20 A/g)",
                CycleStability: "10000 cycles, 95% @ 10 A/g",
                Impedance: {ESR: 0.5 Ω, Rct: 1.2 Ω}
            },
            {
                SystemType: "Two-electrode symmetric",
                Electrolyte: "1M Na2SO4",
                VoltageWindow: "[0, 2] V",
                MaxEnergyDensity: "25 Wh/kg @ 500 W/kg",
                MaxPowerDensity: "10000 W/kg @ 15 Wh/kg"
            }
        ];
        Sample Name 2: [ ... ];
        ...
Notes:
* Strictly distinguish data between three-electrode and two-electrode systems.
* If a piece of information is not mentioned, use "Not mentioned".
* **Be sure to check the Supporting Information (SI) and all figures for detailed parameters.**
"""

# --- Step 2: Data Structuring (Streamlined) ---
prompt_2 = """
Role Setting:
You are a database construction expert responsible for consolidating and structuring extracted material science data into a clean, machine-readable JSON format based on a strict schema.

Task Steps:
1.  **Input Consolidation**: You will receive multiple pieces of structured text about one or more material samples. These pieces cover:
    * Sample names (from Step 1.1)
    * Synthesis & Preparation Conditions (from Step 1.2)
    * Physical & Chemical Properties (from Step 1.3)
    * Electrochemical Performances (Streamlined version from Step 1.4)

2.  **Data Structuring and Standardization**:
    * **Numerical Data**: For any value with a unit, structure it as `{"value": number, "unit": "unit_string"}`. For ratios or unitless values, use `{"value": number}`.
    * **Conditional Data**: Structure data points that depend on a condition as a list of objects.
    * **Missing Data**: If information is marked as "Not mentioned" or is not available, represent it as `null`.

3.  **JSON Schema Application**:
    * Adhere strictly to the detailed schema provided below.

```json
[
  {
    "SampleName": "Sample Name",
    "SynthesisAndPreparation": {
      "Precursors": ["Material 1", "Component 2"],
      "Activator": "Activator Name or null",
      "ActivatorToPrecursorRatio": {"value": 4},
      "PyrolysisTemperature": {"value": 800, "unit": "℃"},
      "ActivationTemperature": {"value": 800, "unit": "℃"},
      "ActivationTime": {"value": 2, "unit": "h"},
      "HeatingRate": {"value": 5, "unit": "℃/min"},
      "GasAtmosphere": {"Type": "N2", "FlowRate": {"value": 200, "unit": "mL/min"}},
      "Template": "Template Name or null",
      "OtherProcess": "Description of special treatments or null"
    },
    "PhysicalChemicalProperties": {
      "SpecificSurfaceArea_BET": {"value": 1500, "unit": "m²/g"},
      "MicroporeSurfaceArea": {"value": 1200, "unit": "m²/g", "method": "t-plot"},
      "TotalPoreVolume": {"value": 0.8, "unit": "cm³/g"},
      "MicroporeVolume": {"value": 0.6, "unit": "cm³/g", "method": "DFT"},
      "MesoporeVolume": {"value": 0.2, "unit": "cm³/g"},
      "PoreSizeDistribution": "Bimodal distribution with peaks at 0.8 nm and 3.5 nm",
      "ElementContent_XPS": {
        "C": {"value": 85, "unit": "at%"},
        "O": {"value": 10, "unit": "at%"},
        "N": {"value": 5, "unit": "at%", "species": {"N_PYRIDINIC": {"value": 60, "unit": "%"}, "N_PYRROLIC": {"value": 30, "unit": "%"}, "N_GRAPHITIC": {"value": 10, "unit": "%"}, "N_OXIDIZED": null}}
      },
      "FunctionalGroups_FTIR": ["-COOH", "-OH", "C=O"],
      "GraphitizationDegree_Raman_ID_IG": {"value": 0.95}
    },
    "ElectrochemicalPerformances": [
      {
        "SystemType": "Three-electrode",
        "Electrolyte": "6M KOH",
        "VoltageWindow": {"value": [-1, 0], "unit": "V"},
        "SpecificCapacitance": [
          {"method": "GCD", "value": 346, "unit": "F/g", "condition": {"value": 1, "unit": "A/g"}},
          {"method": "GCD", "value": 280, "unit": "F/g", "condition": {"value": 20, "unit": "A/g"}}
        ],
        "RateCapability": {"retention": {"value": 80.9, "unit": "%"}, "from_condition": {"value": 1, "unit": "A/g"}, "to_condition": {"value": 20, "unit": "A/g"}},
        "CycleStability": {"CycleNumber": {"value": 10000}, "CapacityRetention": {"value": 97.5, "unit": "%"}, "condition": {"value": 10, "unit": "A/g"}},
        "EquivalentSeriesResistance_ESR": {"value": 0.5, "unit": "Ω"},
        "ChargeTransferResistance_Rct": {"value": 1.2, "unit": "Ω"}
      },
      {
        "SystemType": "Two-electrode symmetric",
        "Electrolyte": "1M Na2SO4",
        "VoltageWindow": {"value": [0, 2], "unit": "V"},
        "MaxEnergyDensity": {"value": 25, "unit": "Wh/kg", "condition": {"value": 500, "unit": "W/kg"}},
        "MaxPowerDensity": {"value": 10000, "unit": "W/kg", "condition": {"value": 15, "unit": "Wh/kg"}}
      }
    ]
  }
]
```
Final Output Requirements:
* Output **only** the final, complete JSON list.
* Do not include any explanatory text, comments, or apologies. Just the raw JSON.
"""

def get_prompt(step_number):
    """Returns the prompt for the specified step."""
    if step_number == "1.1":
        return prompt_1_1
    elif step_number == "1.2":
        return prompt_1_2
    elif step_number == "1.3":
        return prompt_1_3
    elif step_number == "1.4":
        return prompt_1_4
    elif step_number == "2":
        return prompt_2
    else:
        return "Invalid step number."

# Example usage:
# print("--- Streamlined Prompt for Step 1.4 ---")
# print(get_prompt("1.4"))
# print("\n--- Streamlined Prompt for Step 2 ---")
# print(get_prompt("2"))
