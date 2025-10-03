import json
from typing import Any, Dict, List, Optional


def merge_agent_outputs_simple(
    synthesis_data: Optional[Dict[str, Any]],
    properties_data: Optional[Dict[str, Any]],
    performance_data: Optional[Dict[str, Any]],
    sample_list: List[str]
) -> Dict[str, Any]:
    """
    Merges outputs from different agents into a unified structure without schema validation.

    This function directly copies the data for each sample from the source dictionaries.
    It's faster and more flexible but does not enforce any data structure rules.

    Args:
        synthesis_data (Dict[str, Any]): Output from the synthesis extraction agent.
        properties_data (Dict[str, Any]): Output from the properties extraction agent.
        performance_data (Dict[str, Any]): Output from the performance extraction agent.
        sample_list (List[str]): The list of sample names to process.

    Returns:
        Dict[str, Any]: A unified dictionary with sample names as keys.
    """
    unified_results = {}

    synthesis_data = synthesis_data or {}
    properties_data = properties_data or {}
    performance_data = performance_data or {}

    for sample_name in sample_list:
        # Initialize an entry for the current sample
        unified_results[sample_name] = {}

        # Check if synthesis data exists for this sample and add it if so.
        if sample_name in synthesis_data:
            unified_results[sample_name]["Synthesis"] = synthesis_data.get(sample_name, {})

        # Check if physicochemical properties data exists and add it.
        if sample_name in properties_data:
            unified_results[sample_name]["PhysicochemicalProperties"] = properties_data.get(sample_name, {})

        # Check if electrochemical performance data exists and add it.
        if sample_name in performance_data:
            unified_results[sample_name]["ElectrochemicalPerformance"] = performance_data.get(sample_name, {})

    return unified_results

# --- Main Execution Block ---

if __name__ == "__main__":
    # 1. Define the list of samples to process
    SAMPLES = ["HPC-800", "HPC-900"]

    # 2. Simulate the outputs from your three agents
    # This data is the same as the previous example.

    # Agent 1.2 Output: Synthesis Data
    synthesis_agent_output = {
        "HPC-800": {
            "Components": {
                "Precursors": ["pomelo peel"],
                "Activator": "KOH",
                "Template": None,
                "Ratios": [{"component_A": "KOH", "component_B": "Precursor", "ratio": "4:1", "type": "mass"}]
            },
            "ProcessFlow": [
                {"step_name": "Pre-carbonization", "temperature": 500, "duration": 2, "heating_rate": 5, "atmosphere": "N2"},
                {"step_name": "Activation", "temperature": 800, "duration": 1, "heating_rate": 5, "atmosphere": "N2"},
                {"step_name": "Acid Washing", "details": "Washed with 1M HCl then deionized water to neutral."}
            ]
        },
        "HPC-900": {
            "Components": {
                "Precursors": ["pomelo peel"],
                "Activator": "KOH",
                "Template": None,
                "Ratios": [{"component_A": "KOH", "component_B": "Precursor", "ratio": "4:1", "type": "mass"}]
            },
            "ProcessFlow": [
                {"step_name": "Pre-carbonization", "temperature": 500, "duration": 2, "heating_rate": 5, "atmosphere": "N2"},
                {"step_name": "Activation", "temperature": 900, "duration": 1, "heating_rate": 5, "atmosphere": "N2"},
                {"step_name": "Acid Washing", "details": "Washed with 1M HCl then deionized water to neutral."}
            ]
        }
    }

    # Agent 1.3 Output: Properties Data
    properties_agent_output = {
        "HPC-800": {
            "Porosity": {
                "SpecificSurfaceArea_BET": {"value": 2097, "unit": "m²/g"},
                "TotalPoreVolume": {"value": 1.05, "unit": "cm³/g"},
                "MicroporeVolume": {"value": 0.82, "unit": "cm³/g", "method": "t-plot"},
                "PoreSizeDistribution": "Peaks centered at < 2 nm"
            },
            "Composition": {
                "Elemental": {"C": {"value": 89.75, "unit": "at%"}, "O": {"value": 9.21, "unit": "at%"}, "N": {"value": 1.04, "unit": "at%"}},
                "HighResolution_XPS": {"N_Species": {"Pyridinic-N": 45.1, "Pyrrolic-N": 33.5, "Graphitic-N": 21.4}}
            },
            "Crystallinity": {"Graphitization_Raman_ID_IG": 1.02}
        },
        "HPC-900": {
            "Porosity": {
                "SpecificSurfaceArea_BET": {"value": 1856, "unit": "m²/g"},
                "TotalPoreVolume": {"value": 1.12, "unit": "cm³/g"},
                "MicroporeVolume": {"value": 0.58, "unit": "cm³/g", "method": "t-plot"},
                "PoreSizeDistribution": "Bimodal peaks at < 2 nm and ~3.8 nm"
            },
            "Composition": {"Elemental": {"C": {"value": 91.33, "unit": "at%"}, "O": {"value": 7.85, "unit": "at%"}, "N": {"value": 0.82, "unit": "at%"}}},
            "Crystallinity": {"Graphitization_Raman_ID_IG": 0.98}
        }
    }

    # Agent 1.4 Output: Performance Data
    performance_agent_output = {
        "HPC-800": [
            {
                "SystemType": "Three-electrode", "Electrolyte": "6M KOH", "VoltageWindow": "[-1, 0] V",
                "SpecificCapacitance": [
                    {"method": "GCD", "value": 381, "unit": "F/g", "condition": "0.5 A/g"},
                    {"method": "GCD", "value": 325, "unit": "F/g", "condition": "20 A/g"}
                ],
                "RateCapability": "85.3% (from 0.5 A/g to 20 A/g)",
                "Impedance": {"ESR": 0.35, "Rct": 0.08, "unit": "Ω"}
            },
            {
                "SystemType": "Two-electrode symmetric", "Electrolyte": "1M Na2SO4", "VoltageWindow": "[0, 1.8] V",
                "MaxEnergyDensity": "23.4 Wh/kg @ 450 W/kg",
                "MaxPowerDensity": "18000 W/kg @ 15.1 Wh/kg",
                "CycleStability": "10000 cycles, 90.2% retention @ 10 A/g"
            }
        ]
        # HPC-900 data is intentionally omitted to show how the function handles missing data.
    }

    # 3. Call the simplified merging function
    final_structured_data = merge_agent_outputs_simple(
        synthesis_agent_output,
        properties_agent_output,
        performance_agent_output,
        SAMPLES
    )

    # 4. Print the final unified JSON
    print(json.dumps(final_structured_data, indent=4))