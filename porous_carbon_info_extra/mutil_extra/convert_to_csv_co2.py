import os
import json
import csv
from pathlib import Path

def read_json_file(file_path):
    """读取JSON文件并返回数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_pore_structure(sample):
    """提取孔隙结构数据"""
    pore_structure = sample.get('Pore Structure', {})
    return {
        'Specific Surface Area': pore_structure.get('Specific Surface Area', {}).get('value'),
        'Specific Surface Area Unit': pore_structure.get('Specific Surface Area', {}).get('unit'),
        'Total Pore Volume': pore_structure.get('Total Pore Volume', {}).get('value'),
        'Total Pore Volume Unit': pore_structure.get('Total Pore Volume', {}).get('unit'),
        'Micropore Volume': pore_structure.get('Micropore Volume', {}).get('value'),
        'Micropore Volume Unit': pore_structure.get('Micropore Volume', {}).get('unit'),
        'Average Pore Diameter': pore_structure.get('Average Pore Diameter', {}).get('value'),
        'Average Pore Diameter Unit': pore_structure.get('Average Pore Diameter', {}).get('unit')
    }

def extract_elemental_content(sample):
    """提取元素含量数据"""
    surface_chemistry = sample.get('Surface Chemistry', {})
    elemental_content = surface_chemistry.get('Elemental Content', {})
    
    # 基本元素
    result = {
        'Elemental Content Unit': surface_chemistry.get('Elemental Content Unit'),
        'C': elemental_content.get('C', {}).get('value'),
        'H': elemental_content.get('H', {}).get('value'),
        'O': elemental_content.get('O', {}).get('value'),
        'N': elemental_content.get('N', {}).get('value'),
        'S': elemental_content.get('S', {}).get('value')
    }
    
    # 其它元素
    others = elemental_content.get('Others', [])
    for item in others:
        element_name = item.get('element')
        if element_name:
            result[f"Other_Element_{element_name}"] = item.get('value')
    
    return result

def extract_functional_groups(sample):
    """提取官能团数据"""
    surface_chemistry = sample.get('Surface Chemistry', {})
    functional_groups = surface_chemistry.get('Functional Groups', {})
    
    # 基本官能团
    result = {
        'Functional Group Unit': surface_chemistry.get('Functional Group Unit'),
        '-OH': functional_groups.get('-OH', {}).get('value'),
        '-COOH': functional_groups.get('-COOH', {}).get('value'),
        '-C=O': functional_groups.get('-C=O', {}).get('value'),
        '-C-O-C-': functional_groups.get('-C-O-C-', {}).get('value'),
        'N6': functional_groups.get('N6', {}).get('value'),
        'N5': functional_groups.get('N5', {}).get('value'),
        'NQ': functional_groups.get('NQ', {}).get('value'),
        'amine': functional_groups.get('amine', {}).get('value')
    }
    
    # 其它官能团
    others = functional_groups.get('Others', [])
    for item in others:
        group_name = item.get('group')
        if group_name:
            result[f"Other_Group_{group_name}"] = item.get('value')
    
    return result

def process_json_data(json_data, file_name):
    """处理JSON数据并返回行数据"""
    all_rows = []
    
    for sample in json_data:
        sample_name = sample.get('Sample Name', '')
        
        # 获取基本数据
        pore_structure = extract_pore_structure(sample)
        elemental_content = extract_elemental_content(sample)
        functional_groups = extract_functional_groups(sample)
        
        # 处理CO2吸附性能数据
        co2_performances = sample.get('CO2 Adsorption Performance', [])
        
        # 如果没有CO2数据，仍然添加一行基本信息
        if not co2_performances:
            row = {'doi': file_name, 'Sample Name': sample_name}
            row.update(pore_structure)
            row.update(elemental_content)
            row.update(functional_groups)
            all_rows.append(row)
        else:
            # 对每个CO2性能数据点创建一行，对于每个样本可能有多个性能数据
            for performance in co2_performances:
                row = {'doi': file_name, 'Sample Name': sample_name}
                row.update(pore_structure)
                row.update(elemental_content)
                row.update(functional_groups)
                
                adsorption = performance.get('Adsorption Capacity', {})
                temperature = performance.get('Temperature', {})
                pressure = performance.get('Pressure', {})
                
                row.update({
                    'CO2 Adsorption Capacity': adsorption.get('value'),
                    'CO2 Adsorption Unit': adsorption.get('unit'),
                    'Temperature': temperature.get('value'),
                    'Temperature Unit': temperature.get('unit'),
                    'Pressure': pressure.get('value'),
                    'Pressure Unit': pressure.get('unit')
                })
                
                all_rows.append(row)
    
    return all_rows

def main():
    # 设置输入文件夹和输出文件路径
    input_dir = Path('/Volumes/mac_outstore/毕业/jsol文献/biomass_co2_3000/co2_extraction_output')  # 请替换为实际的JSON文件夹路径
    output_file = Path('/Volumes/mac_outstore/毕业/源/combined_co2_data.csv')  # 输出CSV文件路径
    
    # 确保输入目录存在
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"输入目录 {input_dir} 不存在或不是一个目录")
        return
    
    # 获取所有JSON文件
    json_files = [f for f in input_dir.glob('*.json') if f.is_file()]
    
    if not json_files:
        print(f"目录 {input_dir} 中没有找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个JSON文件，开始处理...")
    
    # 收集所有数据行
    all_rows = []
    
    # 处理每个JSON文件
    for json_file in json_files:
        try:
            print(f"处理文件: {json_file.name}")
            json_data = read_json_file(json_file)
            
            # 检查状态
            if 'status' in json_data and json_data['status'] == 'Processed':
                json_data = json_data['final_structured_result']
            elif 'status' in json_data:
                # 如果状态不是processed，直接跳过
                print(f"文件 {json_file} 的状态为 {json_data['status']}，无法处理")
                continue
            
            file_name = json_file.stem
            rows = process_json_data(json_data, file_name)
            all_rows.extend(rows)
            
        except Exception as e:
            print(f"处理文件 {json_file} 时出错: {e}")
    
    # 如果没有有效数据，退出
    if not all_rows:
        print("没有找到有效数据，退出处理")
        return
    
    # 确定所有列
    all_fields = set()
    for row in all_rows:
        all_fields.update(row.keys())
    
    field_names = ['doi']  # 确保doi在第一列
    field_names.extend(sorted([f for f in all_fields if f != 'doi']))
    
    # 写入CSV文件
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"已完成所有数据合并到: {output_file}")
    print(f"共处理 {len(json_files)} 个文件，生成 {len(all_rows)} 条数据记录")

if __name__ == "__main__":
    main()