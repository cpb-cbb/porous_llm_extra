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

General Requirements:
* Always respond with a single valid JSON object and nothing else.
* If the document is relevant, respond exactly with: {"status": "relevant", "samples": ["Sample Name 1", ...]}
* If the document is not relevant, respond exactly with: {"status": "irrelevant", "samples": [], "reason": "This document does not meet the requirements."}
* Never add prefixes such as "Relevant:" or extra prose. Only output the raw JSON.
* Sample names must match the literature exactly (trim whitespace, preserve case).

Extraction Process:
1. Document Relevance Judgment:
    * Carefully read the abstract, introduction, and experimental sections of the literature.
    * Determine whether this literature studies or synthesizes porous carbon materials for supercapacitors.

2. Sample Identification:
    * If relevant, identify all porous carbon material samples explicitly synthesized and characterized in the literature.
    * List the exact names of these samples (e.g., PC-800, NPC-2, AC-KOH-900).

Quality Checks:
* Only include samples experimentally synthesized within the study.
* If multiple naming conventions exist, use the most explicit version provided.
* Do not guess; if the information is unclear, return an empty list.

Output Examples (for reference only, do not copy the text "Example"):
Example relevant output: {"status": "relevant", "samples": ["PC-800", "NPC-2"]}
Example irrelevant output: {"status": "irrelevant", "samples": [], "reason": "This document does not meet the requirements."}
"""

# --- Step 1.2: Synthesis & Preparation Conditions Extraction (Refined) ---
prompt_1_2 = """
**Role Setting**: Material Synthesis Information Extraction Expert
**Task**: For each sample, accurately extract its synthesis process into a structured JSON format.

**Input**:
*   Full text of the literature (including supporting information).
*   The sample list: `[Sample Name 1, Sample Name 2, ...]`

**Extraction Process**:

1.  **Identify Components**:
    *   **Precursors**: List all components and their roles (e.g., carbon source, nitrogen source).
    *   **Activator**: Specify the chemical agent (e.g., KOH, ZnCl₂).
    *   **Template**: Specify the material (e.g., SiO₂, SBA-15).
    *   **Ratios**: Extract all specified ratios between components, noting the type (mass or molar).
        *   e.g., `[{component_A: "KOH", component_B: "Precursor", ratio: "4:1", type: "mass"}]`

2.  **Describe Process Flow**:
    *   Deconstruct the synthesis into a sequence of **chronological steps**.
    *   For each step, extract its key parameters. Especially for **thermal treatment steps**, include:
        *   `step_name`: e.g., "Drying", "Pre-carbonization", "Activation", "Acid Washing".
        *   `temperature`: (Unit: °C)
        *   `duration`: (Unit: h)
        *   `heating_rate`: (Unit: °C/min)
        *   `atmosphere`: (e.g., "N2", "Ar")
        *   `flow_rate`: (Unit: mL/min)
        *   `details`: Other notes for the step (e.g., "Washed with 2M HCl for 12h").

**Output Format Example**:
*   Generate a single JSON object where keys are sample names.
*   If information is not mentioned, use `null`.

```json
{
    "Sample Name 1": {
        "Components": {
            "Precursors": ["bamboo", "spiral algae"],
            "Activator": "CH3COOK",
            "Template": "Ca2(C2H5COO)2",
            "Ratios": [
                {"component_A": "bamboo", "component_B": "spiral algae", "ratio": "1:1", "type": "mass"},
                {"component_A": "CH3COOK", "component_B": "carbon precursor", "ratio": "3:1", "type": "mass"}
            ]
        },
        "ProcessFlow": [
            {
                "step_name": "Pre-carbonization",
                "temperature": 400,
                "duration": 1,
                "heating_rate": 5,
                "atmosphere": "N2"
            },
            {
                "step_name": "Acid Washing",
                "details": "Washed in 2M HCl for 12h"
            },
            {
                "step_name": "Activation",
                "temperature": 700,
                "duration": 1,
                "heating_rate": 5,
                "atmosphere": "N2"
            },
            {
                "step_name": "Final Washing",
                "details": "Rinsed with 2M HCl and deionized water"
            }
        ]
    },
    "Sample Name 2": {
         "..."
    }
}
```

**Output requirements**: 
Please output the final result in JSON format only. Do not include any explanatory text, comments, or any other unrelated information.
"""

# --- Step 1.3: Physical & Chemical Properties Extraction (Refined) ---
prompt_1_3 = """
**Role Setting:** Material Physicochemical Properties Analysis Expert
**Task:** For the specified sample list, accurately extract physicochemical property data into a structured JSON format.

**Input:**
*   Full text of the literature (including main text, figures, tables, and supporting information).
*   Sample list: `[Sample Name 1, Sample Name 2, ...]`

**Extraction Process:**

1.  **Porosity and Structure**:
    *   **SpecificSurfaceArea_BET**: (Unit: m²/g)
    *   **MicroporeSurfaceArea**: (Unit: m²/g; specify method, e.g., DFT, t-plot)
    *   **TotalPoreVolume**: (Unit: cm³/g)
    *   **MicroporeVolume**: (Unit: cm³/g; specify method, e.g., DFT, t-plot)
    *   **MesoporeVolume**: (Unit: cm³/g)
    *   **PoreSizeDistribution**: (nm; summarize key peak positions from the plot, e.g., "Peaks at <2 nm and 3.8 nm")
    *   **AveragePoreDiameter**: (Unit: nm; if available)

2.  **Surface Chemistry and Composition**:
    *   **ElementalComposition**: Extract atomic (at%) or weight (wt%) for all reported elements (C, O, N, S, P, etc.).
        *   e.g., `{C: {value: 90.1, unit: "wt%"}, N: {value: 2.5, unit: "wt%"}, ...}`
    *   **HighResolution_XPS**:
        *   **N_Species**: From N1s spectrum, extract the relative percentage (%) of each species.
            *   `Pyridinic-N`: (%)
            *   `Pyrrolic-N`: (%)
            *   `Graphitic-N`: (%)
            *   `Oxidized-N`: (%)
        *   **C_Species**: From C1s spectrum, extract the relative percentage (%) of key carbon bonds.
            *   `C-C/C=C`: (%)
            *   `C-O`: (%)
            *   `C=O`: (%)
            *   `O-C=O`: (%)
    *   **QualitativeFunctionalGroups_FTIR**: List main functional groups claimed by the authors (e.g., -OH, C=O).

3.  **Crystallinity**:
    *   **Graphitization_Raman**: Extract the ID/IG ratio.

**Output Format Example:**
*   Generate a single JSON object where keys are sample names.
*   If information is not mentioned, use `null`.
JSON example:
```json
{
    "Sample Name 1": {
        "Porosity": {
            "SpecificSurfaceArea_BET": {"value": 1500, "unit": "m²/g"},
            "TotalPoreVolume": {"value": 0.85, "unit": "cm³/g"},
            "MicroporeVolume": {"value": 0.60, "unit": "cm³/g", "method": "DFT"},
            "MesoporeVolume": {"value": null, "unit": "cm³/g"},
            "AveragePoreDiameter": {"value": null, "unit": "nm"},
            "PoreSizeDistribution": "Peaks at 0.8 nm and 1.5 nm"
        },
        "Composition": {
            "Elemental": {
                "C": {"value": 85.2, "unit": "at%"},
                "O": {"value": 10.1, "unit": "at%"},
                "N": {"value": 4.7, "unit": "at%"}
            },
            "HighResolution_XPS": {
                "N_Species": {
                    "Pyridinic-N": 30.5,
                    "Pyrrolic-N": 40.2,
                    "Graphitic-N": 29.3
                },
                "C_Species": {
                    "C-C/C=C": 75,
                    "C-O": 15,
                    "C=O": 10
                }
            }
        },
        "Crystallinity": {
            "Graphitization_Raman_ID_IG": 1.05
        }
    },
    "Sample Name 2": {
        "..."
    }
}
```

**Output requirements**: 
Please output the final result in JSON format only. Do not include any explanatory text, comments, or any other unrelated information.
"""

# --- Step 1.4: Electrochemical Performance Extraction (Streamlined) ---
# 注意，电极的详细信息（质量负载等没有提取，后期需要提取，切记。
prompt_1_4 = """

好的，这是一个非常专业的修改。为了将负载量（mass loading）作为一个独立的、对机器学习模型友好的特征进行提取，我们将在`SpecificCapacitance`的数据结构中添加一个`mass_loading`字段。

以下是为您更新后的提示词。修改的部分主要在`SpecificCapacitance`的提取规则和输出格式示例中，并用**粗体**标出。

---

**Role Setting:** Electrochemical Performance Data Extraction Expert
**Task:** For each sample, extract the core electrochemical performance under **different test systems**. This version is optimized for clarity, accuracy, and modeling needs.

**Input:**
*   Full text of the literature (including figures, tables, supporting information).
*   Sample list: `[Sample Name 1, Sample Name 2, ...]`

**Extraction Process:**

1.  **Identify Test Systems**:
    *   For **each** sample, identify all independent electrochemical test systems.
    *   An independent "test system" is defined by **[System Type]** and **[Electrolyte]**.

2.  **Extract Data within Each System**:
    *   For **each identified test system**, create a separate data object and extract the following:
    *   **SystemType**: e.g., "Three-electrode", "Two-electrode symmetric", "Two-electrode asymmetric".
    *   **Electrolyte**: e.g., "6M KOH", "1M H2SO4".
    *   **VoltageWindow**: e.g., "[-1, 0] V", "[0, 1.8] V".
    *   **Impedance**:
        *   Can be extracted in any system type.
        *   Extract equivalent series resistance (ESR) and charge transfer resistance (Rct). If Rct is not clearly separated, report it as `null`. Unit: Ω.

    --- Three-electrode System Specific Data ---
    *   **SpecificCapacitance**:
        *   **Extract ONLY in three-electrode systems.**
        *   Provide all reported data points as a list, covering a range from low to high conditions.
        *   **For each data point, explicitly extract the mass loading of the active material as a separate field.**
        *   The `condition` field should describe the rate (current density or scan rate).
        *   **Format: `[{method: "GCD", value: 350, unit: "F/g", condition: "1 A/g", mass_loading: "1.2 mg/cm^2"}, ...]`.**
        *   **If mass loading is not mentioned for a specific data point, use `null` for the `mass_loading` field.**
    *   **RateCapability**:
        *   **Extract ONLY in three-electrode systems.**
        *   Format: "85% (from 1 A/g to 20 A/g)".

    --- Two-electrode (Device) System Specific Data ---
    *   **Energy/Power Density**:
        *   **Extract ONLY in two-electrode systems.**
        *   Extract **MaxEnergyDensity** (with its corresponding power density) and **MaxPowerDensity** (with its corresponding energy density).
    *   **CycleStability**:
        *   **Extract ONLY in two-electrode systems.**
        *   Format: "10000 cycles, 95% @ 10 A/g".

**Output Format Example:**
*   Generate a single JSON object where keys are sample names.
*   If information is not mentioned, use `null`.

```json
{
    "Sample Name 1": [
        {
            "SystemType": "Three-electrode",
            "Electrolyte": "6M KOH",
            "VoltageWindow": "[-1, 0] V",
            "SpecificCapacitance": [
                {"method": "GCD", "value": 350, "unit": "F/g", "condition": "1 A/g", "mass_loading": "1.1 mg/cm^2"},
                {"method": "GCD", "value": 280, "unit": "F/g", "condition": "20 A/g", "mass_loading": "2 mg/cm^2"},
                {"method": "CV", "value": 355, "unit": "F/g", "condition": "5 mV/s", "mass_loading": "1.1 mg/cm^2"}
            ],
            "RateCapability": "80% (from 1 A/g to 20 A/g)",
            "Impedance": {"ESR": 0.5, "Rct": 1.2, "unit": "Ω"}
        },
        {
            "SystemType": "Two-electrode symmetric",
            "Electrolyte": "6M KOH",
            "VoltageWindow": "[0, 1.0] V",
            "MaxEnergyDensity": "25 Wh/kg @ 500 W/kg",
            "MaxPowerDensity": "10000 W/kg @ 15 Wh/kg",
            "CycleStability": "10000 cycles, 95% retention @ 10 A/g",
            "Impedance": {"ESR": 0.8, "Rct": null, "unit": "Ω"}
        }
    ],
    "Sample Name 2": [
        "..."
    ]
}
```
**Output requirements**: 
Please output the final result in JSON format only. Do not include any explanatory text, comments, or any other unrelated information.
"""

# --- Step 2 (Final, Batch Mode): Batch Verification & Correction Agent ---
prompt_batch_verifier_and_corrector = """
**Role Setting**: Lead AI Data Quality Assurance Analyst

**Core Task**: Your mission is to perform a comprehensive audit of an entire JSON dataset containing multiple samples. You must meticulously verify every piece of data for every sample against the source literature. If the entire dataset is flawless, you will confirm its correctness. If any part is incorrect, you will provide a fully corrected version of the *entire* dataset.

**Input**:
1.  `full_text`: The complete original text of the scientific literature.
2.  `json_batch_to_verify`: The complete JSON object generated by a previous agent. This object contains multiple sample names as its top-level keys.

**Your Thought Process (Internal Monologue - Do not output this)**:
1.  I need to treat this as a high-stakes audit. The goal is 100% accuracy for the whole batch.
2.  I will iterate through each `sample_name` in the keys of the `json_batch_to_verify`.
3.  For each sample, I will perform the same rigorous checks as before: locate the sample's data in the `full_text` and verify every key-value pair.
4.  I must check for factual errors, data misalignment , and omissions for *every single sample*.
5.  I will keep track of any discrepancies found. If even one value for one sample is wrong, the entire batch fails the "perfect match" test.
6.  If any corrections are needed, I will create a new, corrected version of the entire JSON object, preserving the original structure.

**Output Rules (Strictly follow these)**:

*   **If and ONLY IF** the `json_batch_to_verify` is a perfect match with the information in the `full_text` for **ALL** samples contained within it, your **entire output** must be the single uppercase character:
    `T`
*   **If you find ANY discrepancy for ANY sample**, you must **NOT** output `T`. Instead, you are required to:
    1.  Use the `full_text` as the single source of truth to correct all identified errors across all samples.
    2.  Construct the **fully corrected** version of the entire original JSON object. This means if only one sample had an error, you still output the complete JSON with all samples, with the incorrect one fixed.
    3.  Your output must be **ONLY** this single, complete, and valid JSON object.

**Crucial Constraints**:
*   Do not add any explanations, comments, or conversational text. Your output must be immediately usable by a script.
*   Your final output is either the single character `T` or a raw, complete JSON object.
"""
# --- Step 2: Data Structuring (Streamlined) ---

NER_EVALUE_PROMPT="""
Role and Goal
You are a meticulous and rigorous academic information evaluator. Your sole task is to compare an Extracted JSON with an Original Text and identify and list any factual discrepancies. The evaluation should focus on whether the Extracted JSON has captured the core findings and key data of the original text, not on a word-for-word perfect match. You must not add, interpret, or infer any information beyond what is present in the Original Text.

Definitions of Discrepancies
You will identify and list two types of discrepancies:

False Positives (FP): These are individual facts or values present in the Extracted JSON that are either incorrect according to the Original Text or not mentioned at all.

False Negatives (FN): These are individual key facts, critical data points, or major conclusions present in the Original Text that are missing from the Extracted JSON. Information that is a minor detail, background description, or repetitive content should not be counted as an FN.

Core Instructions
Your analysis must be strictly based on the provided Original Text. Do not use external knowledge.

When judging an FN, ask yourself: "If this piece of information were missing, would the reader's understanding of the text's core content be skewed or incomplete?" If the answer is yes, then it is an FN.

For every discrepancy you find, you must create a JSON object containing its details.

Your final output will be a JSON list containing all of these objects.

Output Format
Your response MUST be a single, valid JSON object, which is an array (list), and nothing else. Each element in the array must be a separate JSON object with the following strict structure:

{
  "Discrepancy": "A string that clearly describes the specific discrepancy.",
  "Judgment": "A string whose value must be 'FP' or 'FN'."
}

Format Example:
If you find one incorrect fact (FP) and one omitted key piece of information (FN), your output must be an array like this:

[
  {
    "Discrepancy": "The study's sample size was 150, not 'around 200'.",
    "Judgment": "FP"
  },
  {
    "Discrepancy": "The primary funding source for the research was omitted.",
    "Judgment": "FN"
  }
]

Critical Rule for No Discrepancies:
If the Extracted JSON is perfectly accurate and complete according to the Original Text (i.e., no FPs or FNs are found), you MUST return an empty JSON array:

[]

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
    else:
        return "Invalid step number."

# Example usage:
# print("--- Streamlined Prompt for Step 1.4 ---")
# print(get_prompt("1.4"))
# print("\n--- Streamlined Prompt for Step 2 ---")
# print(get_prompt("2"))
