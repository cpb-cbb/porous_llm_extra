import os
import json
import csv
from pathlib import Path

def read_json_file(file_path):
    """Reads a JSON file and returns the data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        structured_data = data.get('structured_result','不存在')
        return structured_data

def flatten_property(data, prefix, row_dict):
    """
    Flattens a property dictionary (often containing 'value', 'unit', 'method', 'condition')
    into a row_dict with prefixed keys.
    """
    if not isinstance(data, dict):
        row_dict[prefix] = data # Handle cases where the property might be a direct value
        return

    if 'value' in data:
        row_dict[f"{prefix}_value"] = data.get('value')
    if 'unit' in data:
        row_dict[f"{prefix}_unit"] = data.get('unit')
    if 'method' in data:
        row_dict[f"{prefix}_method"] = data.get('method')
    if 'condition' in data:
        condition = data.get('condition')
        if isinstance(condition, dict): # e.g., Specific Capacitance condition
            if 'value' in condition:
                 row_dict[f"{prefix}_condition_value"] = condition.get('value')
            if 'unit' in condition:
                 row_dict[f"{prefix}_condition_unit"] = condition.get('unit')
        else: # e.g., Energy Density condition (string)
            row_dict[f"{prefix}_condition"] = condition

def extract_preparation_data(prep_dict):
    """Extracts and flattens preparation data."""
    row = {}
    if not isinstance(prep_dict, dict): return row

    precursors = prep_dict.get("Precursors")
    if isinstance(precursors, list):
        row["Preparation_Precursors"] = ", ".join(map(str, precursors))
    elif precursors is not None:
        row["Preparation_Precursors"] = str(precursors)

    activator = prep_dict.get("Activator")
    if isinstance(activator, list):
        row["Preparation_Activator"] = ", ".join(map(str, activator))
    elif activator is not None:
        row["Preparation_Activator"] = str(activator)

    carb_temp = prep_dict.get("Carbonization Temperature")
    if isinstance(carb_temp, dict):
        carb_temp_val = carb_temp.get("value")
        if isinstance(carb_temp_val, list) and len(carb_temp_val) == 2:
            row["Preparation_Carbonization Temperature_value_min"] = carb_temp_val[0]
            row["Preparation_Carbonization Temperature_value_max"] = carb_temp_val[1]
        elif carb_temp_val is not None:
            row["Preparation_Carbonization Temperature_value"] = carb_temp_val
        if "unit" in carb_temp:
            row["Preparation_Carbonization Temperature_unit"] = carb_temp.get("unit")

    row["Preparation_Template"] = prep_dict.get("Template")
    row["Preparation_Other Process"] = prep_dict.get("Other Process")
    return row

def extract_phys_chem_properties(phys_chem_dict):
    """Extracts and flattens physical chemical properties."""
    row = {}
    if not isinstance(phys_chem_dict, dict): return row

    flatten_property(phys_chem_dict.get("Specific Surface Area (BET)"), "PCP_Specific Surface Area (BET)", row)
    flatten_property(phys_chem_dict.get("Micropore Specific Surface Area"), "PCP_Micropore Specific Surface Area", row)
    flatten_property(phys_chem_dict.get("Total Pore Volume"), "PCP_Total Pore Volume", row)
    flatten_property(phys_chem_dict.get("Micropore Volume"), "PCP_Micropore Volume", row)
    flatten_property(phys_chem_dict.get("Mesopore Volume"), "PCP_Mesopore Volume", row)
    row["PCP_Pore Size Distribution Description"] = phys_chem_dict.get("Pore Size Distribution Description")
    flatten_property(phys_chem_dict.get("Average Pore Diameter"), "PCP_Average Pore Diameter", row)

    element_content = phys_chem_dict.get("Element Content (XPS)")
    if isinstance(element_content, dict):
        for element, details in element_content.items():
            if isinstance(details, dict):
                row[f"PCP_Element Content_{element}_value"] = details.get("value")
                row[f"PCP_Element Content_{element}_unit"] = details.get("unit")

    functional_groups = phys_chem_dict.get("Surface Functional Groups (FTIR)")
    if isinstance(functional_groups, list):
        row["PCP_Surface Functional Groups (FTIR)"] = ", ".join(map(str, functional_groups))
    elif functional_groups is not None:
         row["PCP_Surface Functional Groups (FTIR)"] = str(functional_groups)


    graph_degree = phys_chem_dict.get("Degree of Graphitization (Raman ID/IG)")
    if isinstance(graph_degree, dict):
        row["PCP_Degree of Graphitization (Raman ID_IG)_value"] = graph_degree.get("value")

    interlayer_spacing = phys_chem_dict.get("Interlayer Spacing (XRD d002)")
    flatten_property(interlayer_spacing, "PCP_Interlayer Spacing (XRD d002)", row)

    return row

def extract_electrochem_performance(electrochem_dict):
    """Extracts and flattens electrochemical performance data, excluding specific capacitance."""
    row = {}
    if not isinstance(electrochem_dict, dict): return row

    row["Electrochem_Electrode System Type"] = electrochem_dict.get("Electrode System Type")
    row["Electrochem_Electrolyte"] = electrochem_dict.get("Electrolyte")

    voltage_window = electrochem_dict.get("Voltage Window")
    if isinstance(voltage_window, dict):
        vw_val = voltage_window.get("value")
        if isinstance(vw_val, list) and len(vw_val) == 2:
            row["Electrochem_Voltage Window_value_min"] = vw_val[0]
            row["Electrochem_Voltage Window_value_max"] = vw_val[1]
        if "unit" in voltage_window:
            row["Electrochem_Voltage Window_unit"] = voltage_window.get("unit")

    flatten_property(electrochem_dict.get("Energy Density"), "Electrochem_Energy Density", row)
    flatten_property(electrochem_dict.get("Power Density"), "Electrochem_Power Density", row)

    cycle_stability = electrochem_dict.get("Cycle Stability")
    if isinstance(cycle_stability, dict):
        cn = cycle_stability.get("Cycle Number")
        if isinstance(cn, dict):
            row["Electrochem_Cycle Stability_Cycle Number_value"] = cn.get("value")
        cr = cycle_stability.get("Capacity Retention")
        if isinstance(cr, dict):
            row["Electrochem_Cycle Stability_Capacity Retention_value"] = cr.get("value")
            row["Electrochem_Cycle Stability_Capacity Retention_unit"] = cr.get("unit")

    flatten_property(electrochem_dict.get("Equivalent Series Resistance (ESR)"), "Electrochem_ESR", row)
    flatten_property(electrochem_dict.get("Charge Transfer Resistance (Rct)"), "Electrochem_Rct", row)
    flatten_property(electrochem_dict.get("Conductivity"), "Electrochem_Conductivity", row)
    
    if "notes" in electrochem_dict:
        row["Electrochem_notes"] = electrochem_dict.get("notes")
        
    return row

def process_json_data(json_data, file_name_stem):
    """Processes JSON data for multiple samples and returns a list of row dictionaries."""
    all_rows_for_file = []

    # Ensure json_data is a list of samples
    if not isinstance(json_data, list):
        print(f"Warning: Expected a list of samples in {file_name_stem}, but got {type(json_data)}. Skipping.")
        return []
        
    for sample in json_data:
        if not isinstance(sample, dict):
            print(f"Warning: Expected a sample dict in {file_name_stem}, but got {type(sample)}. Skipping sample.")
            continue

        base_row = {'doi': file_name_stem}
        base_row["Sample Name"] = sample.get("Sample Name", "")

        base_row.update(extract_preparation_data(sample.get("Preparation")))
        base_row.update(extract_phys_chem_properties(sample.get("Physical Chemical Properties")))
        base_row.update(extract_electrochem_performance(sample.get("Electrochemical Performance")))

        specific_capacitances = sample.get("Electrochemical Performance", {}).get("Specific Capacitance")

        if isinstance(specific_capacitances, list) and specific_capacitances:
            for sc_entry in specific_capacitances:
                row_with_sc = base_row.copy()
                if isinstance(sc_entry, dict):
                    flatten_property(sc_entry, "Electrochem_Specific Capacitance", row_with_sc)
                all_rows_for_file.append(row_with_sc)
        else:
            # Add a row even if there's no specific capacitance data or it's null
            all_rows_for_file.append(base_row)
            
    return all_rows_for_file

def main():
    """Main function to convert JSON files in a directory to a single CSV file."""
    # Adjust these paths as needed
    input_dir = Path('/Volumes/mac_outstore/毕业/jsol文献/biomass_super_2000/multi_step_extraction_output')  # Directory containing your JSON files
    output_file = Path('./output_data.csv') # Output CSV file path

    # Create input directory if it doesn't exist for easy testing
    input_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a dummy JSON file for testing if input_dir is empty
    # You should replace this with your actual JSON files.
    if not any(input_dir.iterdir()):
        print(f"Input directory '{input_dir}' is empty. Creating a dummy JSON file for testing.")
        dummy_json_path = input_dir / "dummy_sample.json"
        dummy_data = [
            {
                "Sample Name": "TestSample1",
                "Preparation": {
                    "Precursors": ["Biochar", "Component X"],
                    "Activator": "KOH",
                    "Carbonization Temperature": {"value": 800, "unit": "℃"},
                    "Template": None,
                    "Other Process": "Washing and drying"
                },
                "Physical Chemical Properties": {
                    "Specific Surface Area (BET)": {"value": 1500, "unit": "m²/g"},
                    "Micropore Specific Surface Area": {"value": 1200, "unit": "m²/g", "method": "t-plot"},
                    "Total Pore Volume": {"value": 0.75, "unit": "cm³/g"},
                    "Micropore Volume": {"value": 0.60, "unit": "cm³/g", "method": "DFT"},
                    "Mesopore Volume": {"value": 0.15, "unit": "cm³/g"},
                    "Pore Size Distribution Description": "Hierarchical pores",
                    "Average Pore Diameter": {"value": 2.1, "unit": "nm"},
                    "Element Content (XPS)": {
                        "C": {"value": 85.5, "unit": "at%"},
                        "O": {"value": 10.2, "unit": "at%"},
                        "N": {"value": 2.3, "unit": "at%"}
                    },
                    "Surface Functional Groups (FTIR)": ["-OH", "C=O"],
                    "Degree of Graphitization (Raman ID/IG)": {"value": 1.1},
                    "Interlayer Spacing (XRD d002)": {"value": 0.345, "unit": "nm"}
                },
                "Electrochemical Performance": {
                    "Electrode System Type": "Three-electrode",
                    "Electrolyte": "6M KOH",
                    "Voltage Window": {"value": [-0.1, 0.9], "unit": "V"},
                    "Specific Capacitance": [
                        {"value": 300, "unit": "F/g", "condition": {"value": 1, "unit": "A/g"}},
                        {"value": 250, "unit": "F/g", "condition": {"value": 10, "unit": "A/g"}},
                        {"value": 280, "unit": "F/g", "condition": {"value": 5, "unit": "mV/s"}}
                    ],
                    "Energy Density": {"value": 30, "unit": "Wh/kg", "condition": "@ 500 W/kg"},
                    "Power Density": {"value": 5000, "unit": "W/kg", "condition": "@ 15 Wh/kg"},
                    "Cycle Stability": {"Cycle Number": {"value": 10000}, "Capacity Retention": {"value": 95, "unit": "%"}},
                    "Equivalent Series Resistance (ESR)": {"value": 0.5, "unit": "Ω"},
                    "Charge Transfer Resistance (Rct)": {"value": 2.0, "unit": "Ω"},
                    "Conductivity": {"value": 5.5, "unit": "S/cm"}
                }
            }
        ]
        with open(dummy_json_path, 'w', encoding='utf-8') as f_dummy:
            json.dump(dummy_data, f_dummy, indent=2)
        print(f"Dummy file '{dummy_json_path}' created. Please replace or supplement with your actual files.")


    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory {input_dir} does not exist or is not a directory.")
        return

    json_files = [f for f in input_dir.glob('*.json') if f.is_file()]

    if not json_files:
        print(f"No JSON files found in directory {input_dir}.")
        return

    print(f"Found {len(json_files)} JSON files. Processing...")

    all_rows_across_files = []
    processed_files_count = 0

    for json_file_path in json_files:
        try:
            print(f"Processing file: {json_file_path.name}")
            raw_json_data = read_json_file(json_file_path)
            if raw_json_data == '不存在':
                print(f"Structured result not found in {json_file_path.name}. Skipping.")
                continue
            
            # Adapt if your JSON files have a specific structure like 'final_structured_result'
            # For instance, if the actual list of samples is under a key:
            # data_to_process = raw_json_data.get('final_structured_result', raw_json_data)
            # For now, assuming the file directly contains the list of samples or a single sample object that might be wrapped in a list by process_json_data
            data_to_process = raw_json_data # Use this if JSON file root is the list of samples

            file_stem = json_file_path.stem # To be used as 'doi' or file identifier
            rows_from_this_file = process_json_data(data_to_process, file_stem)
            all_rows_across_files.extend(rows_from_this_file)
            if rows_from_this_file:
                 processed_files_count +=1
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file {json_file_path.name}. Skipping.")
        except Exception as e:
            print(f"An error occurred while processing file {json_file_path.name}: {e}")

    if not all_rows_across_files:
        print("No data processed from any JSON files. Output CSV will not be created.")
        return

    # Determine all unique field names for the CSV header
    all_field_names = set()
    for row in all_rows_across_files:
        all_field_names.update(row.keys())
    
    # Ensure 'doi' and 'Sample Name' are first if they exist
    sorted_field_names = sorted(list(all_field_names))
    if "Sample Name" in sorted_field_names:
        sorted_field_names.insert(0, sorted_field_names.pop(sorted_field_names.index("Sample Name")))
    if "doi" in sorted_field_names:
        sorted_field_names.insert(0, sorted_field_names.pop(sorted_field_names.index("doi")))
        
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=sorted_field_names)
            writer.writeheader()
            writer.writerows(all_rows_across_files)
        print(f"Successfully converted {processed_files_count} JSON file(s) into {output_file}")
        print(f"Total records written: {len(all_rows_across_files)}")
    except IOError:
        print(f"Could not write to CSV file {output_file}. Check permissions or path.")
    except Exception as e:
        print(f"An unexpected error occurred during CSV writing: {e}")

if __name__ == "__main__":
    main()