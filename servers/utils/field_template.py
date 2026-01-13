"""
字段模版定义模块
用于验证提取结果是否符合提示词要求，过滤掉幻觉字段
"""

from typing import Any, Dict, List, Set


# Synthesis 部分的合法字段模版
SYNTHESIS_TEMPLATE = {
    "Components": {
        "Precursors": list,  # List[str]
        "Activator": (str, type(None)),  # Optional[str]
        "Template": (str, type(None)),  # Optional[str]
        "Ratios": list  # List[Dict] with keys: component_A, component_B, ratio, type
    },
    "ProcessFlow": list  # List[Dict] with keys: step_name, temperature, duration, heating_rate, atmosphere, details
}

# Synthesis.Components.Ratios 中每个元素的合法字段
SYNTHESIS_RATIO_FIELDS = {
    "component_A",
    "component_B",
    "ratio",
    "type"
}

# Synthesis.ProcessFlow 中每个步骤的合法字段
SYNTHESIS_PROCESS_FIELDS = {
    "step_name",
    "temperature",
    "duration",
    "heating_rate",
    "atmosphere",
    "flow_rate",
    "details"
}

# PhysicochemicalProperties 部分的合法字段模版
PROPERTIES_TEMPLATE = {
    "Porosity": {
        "SpecificSurfaceArea_BET": dict,  # {"value": float, "unit": str}
        "MicroporeSurfaceArea": dict,  # {"value": float, "unit": str}
        "TotalPoreVolume": dict,  # {"value": float, "unit": str}
        "MicroporeVolume": dict,  # {"value": float, "unit": str, "method": str}
        "MesoporeVolume": dict,  # {"value": float, "unit": str}
        "AveragePoreDiameter": dict,  # {"value": float, "unit": str}
        "PoreSizeDistribution": (str, type(None))  # Optional[str]
    },
    "Composition": {
        "Elemental": dict,  # Dict with element symbols as keys
        "HighResolution_XPS": dict,  # Dict with species types as keys
        "QualitativeFunctionalGroups_FTIR": (list, str, type(None))  # Optional[list or str]
    },
    "Crystallinity": {
        "Graphitization_Raman_ID_IG": (float, int, type(None))
    }
}

# Properties.Porosity 下值字段的合法键
PROPERTIES_POROSITY_VALUE_FIELDS = {
    "value",
    "unit",
    "method"
}

# Properties.Composition.Elemental 中元素值的合法字段
PROPERTIES_ELEMENTAL_VALUE_FIELDS = {
    "value",
    "unit"
}

# Properties.Composition.HighResolution_XPS 的已知物种类型
PROPERTIES_XPS_SPECIES_TYPES = {
    "N_Species",
    "C_Species",
    "O_Species",
    "S_Species"
}

# ElectrochemicalPerformance 部分的合法字段模版（列表中的每个测试配置）
PERFORMANCE_TEST_FIELDS = {
    "SystemType",
    "Electrolyte",
    "VoltageWindow",
    "SpecificCapacitance",
    "RateCapability",
    "Impedance",
    "MaxEnergyDensity",
    "MaxPowerDensity",
    "CycleStability"
}

# Performance.SpecificCapacitance 中每个元素的合法字段
PERFORMANCE_CAPACITANCE_FIELDS = {
    "method",
    "value",
    "unit",
    "condition",
    "mass_loading"
}

# Performance.Impedance 的合法字段
PERFORMANCE_IMPEDANCE_FIELDS = {
    "ESR",
    "Rct",
    "unit"
}

# Unified Results 的顶层合法字段
UNIFIED_RESULT_TOP_FIELDS = {
    "Synthesis",
    "PhysicochemicalProperties",
    "ElectrochemicalPerformance"
}


def get_valid_keys_for_path(path: List[str]) -> Set[str]:
    """
    根据路径返回该位置的合法字段集合
    
    Args:
        path: 字段路径列表，例如 ["Synthesis", "Components"]
    
    Returns:
        该路径下的合法字段名称集合
    """
    if not path:
        return UNIFIED_RESULT_TOP_FIELDS
    
    # Synthesis 路径
    if path[0] == "Synthesis":
        if len(path) == 1:
            return set(SYNTHESIS_TEMPLATE.keys())
        elif path[1] == "Components":
            if len(path) == 2:
                return set(SYNTHESIS_TEMPLATE["Components"].keys())
            elif path[2] == "Ratios" and len(path) == 3:
                return SYNTHESIS_RATIO_FIELDS
        elif path[1] == "ProcessFlow" and len(path) == 2:
            return SYNTHESIS_PROCESS_FIELDS
    
    # PhysicochemicalProperties 路径
    elif path[0] == "PhysicochemicalProperties":
        if len(path) == 1:
            return set(PROPERTIES_TEMPLATE.keys())
        elif path[1] == "Porosity":
            if len(path) == 2:
                return set(PROPERTIES_TEMPLATE["Porosity"].keys())
            elif len(path) == 3:
                return PROPERTIES_POROSITY_VALUE_FIELDS
        elif path[1] == "Composition":
            if len(path) == 2:
                return set(PROPERTIES_TEMPLATE["Composition"].keys())
            elif path[2] == "Elemental" and len(path) == 4:
                # 元素符号下的值字段
                return PROPERTIES_ELEMENTAL_VALUE_FIELDS
            elif path[2] == "HighResolution_XPS":
                if len(path) == 3:
                    return PROPERTIES_XPS_SPECIES_TYPES
                # XPS 物种类型下可以有任意命名的子物种，不限制
        elif path[1] == "Crystallinity":
            if len(path) == 2:
                return set(PROPERTIES_TEMPLATE["Crystallinity"].keys())
    
    # ElectrochemicalPerformance 路径
    elif path[0] == "ElectrochemicalPerformance":
        if len(path) == 1:
            return PERFORMANCE_TEST_FIELDS
        elif path[1] == "SpecificCapacitance" and len(path) == 2:
            return PERFORMANCE_CAPACITANCE_FIELDS
        elif path[1] == "Impedance" and len(path) == 2:
            return PERFORMANCE_IMPEDANCE_FIELDS
    
    # 未定义路径返回空集合（表示该路径下不应有更多字段）
    return set()


def validate_and_filter_dict(data: Dict[str, Any], path: List[str] = None) -> Dict[str, Any]:
    """
    递归验证并过滤字典，移除不在模版中的字段
    
    Args:
        data: 要验证和过滤的数据字典
        path: 当前路径（用于递归）
    
    Returns:
        过滤后的字典
    """
    if path is None:
        path = []
    
    valid_keys = get_valid_keys_for_path(path)
    filtered_data = {}
    
    for key, value in data.items():
        # 特殊处理：某些位置允许动态键名
        is_dynamic_key = False
        
        # Composition.Elemental 下的元素符号（C, O, N 等）
        if len(path) >= 2 and path[0] == "PhysicochemicalProperties" and \
           path[1] == "Composition" and len(path) == 3 and path[2] == "Elemental":
            is_dynamic_key = True
        
        # HighResolution_XPS 下的物种子类型（Pyridinic-N, Pyrrolic-N 等）
        if len(path) >= 3 and path[0] == "PhysicochemicalProperties" and \
           path[1] == "Composition" and path[2] == "HighResolution_XPS" and len(path) == 4:
            is_dynamic_key = True
        
        # 检查键是否合法
        if not valid_keys or key in valid_keys or is_dynamic_key:
            # 递归处理嵌套字典
            if isinstance(value, dict):
                filtered_value = validate_and_filter_dict(value, path + [key])
                filtered_data[key] = filtered_value
            # 处理列表
            elif isinstance(value, list):
                filtered_list = []
                for item in value:
                    if isinstance(item, dict):
                        filtered_item = validate_and_filter_dict(item, path + [key])
                        filtered_list.append(filtered_item)
                    else:
                        filtered_list.append(item)
                filtered_data[key] = filtered_list
            else:
                filtered_data[key] = value
    
    return filtered_data


def filter_unified_results(unified_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    过滤 unified_results，移除所有不符合模版的幻觉字段
    
    Args:
        unified_results: 合并后的完整结果字典
    
    Returns:
        过滤后的结果字典
    """
    filtered_results = {}
    
    for sample_name, sample_data in unified_results.items():
        filtered_sample = {}
        
        for section_name, section_data in sample_data.items():
            if section_name in UNIFIED_RESULT_TOP_FIELDS:
                # 对于 ElectrochemicalPerformance，它是一个列表
                if section_name == "ElectrochemicalPerformance" and isinstance(section_data, list):
                    filtered_list = []
                    for test_config in section_data:
                        if isinstance(test_config, dict):
                            filtered_config = validate_and_filter_dict(
                                test_config,
                                [section_name]
                            )
                            filtered_list.append(filtered_config)
                    filtered_sample[section_name] = filtered_list
                
                # 对于其他部分（Synthesis, PhysicochemicalProperties）
                elif isinstance(section_data, dict):
                    filtered_sample[section_name] = validate_and_filter_dict(
                        section_data,
                        [section_name]
                    )
        
        filtered_results[sample_name] = filtered_sample
    
    return filtered_results


def get_all_invalid_keys(data: Dict[str, Any], path: List[str] = None) -> List[tuple]:
    """
    递归查找所有不合法的字段路径
    
    Args:
        data: 要检查的数据字典
        path: 当前路径
    
    Returns:
        不合法的字段路径列表，格式为 [(path, key), ...]
    """
    if path is None:
        path = []
    
    valid_keys = get_valid_keys_for_path(path)
    invalid_keys = []
    
    for key, value in data.items():
        # 特殊处理动态键名
        is_dynamic_key = False
        
        if len(path) >= 2 and path[0] == "PhysicochemicalProperties" and \
           path[1] == "Composition" and len(path) == 3 and path[2] == "Elemental":
            is_dynamic_key = True
        
        if len(path) >= 3 and path[0] == "PhysicochemicalProperties" and \
           path[1] == "Composition" and path[2] == "HighResolution_XPS" and len(path) == 4:
            is_dynamic_key = True
        
        # 检查键是否合法
        if valid_keys and key not in valid_keys and not is_dynamic_key:
            invalid_keys.append((path.copy(), key))
        
        # 递归检查
        if isinstance(value, dict):
            invalid_keys.extend(get_all_invalid_keys(value, path + [key]))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    invalid_keys.extend(get_all_invalid_keys(item, path + [key]))
    
    return invalid_keys

def filter_csv_and_recalculate(
    input_csv_path: str,
    output_csv_path: str = None
) -> Dict[str, Any]:
    """
    读取详细报告CSV文件(combined_detailed_report.csv格式)，
    过滤掉不合法字段的行，重新计算F1分数
    
    CSV格式应包含: Key, Extracted Value, Ground Truth, Status, Reason, File
    
    Args:
        input_csv_path: 输入CSV文件路径
        output_csv_path: 输出CSV文件路径（可选，默认为输入文件名_filtered.csv）
    
    Returns:
        包含过滤后指标的字典
    """
    import pandas as pd
    
    # 读取CSV
    print(f"正在读取CSV文件: {input_csv_path}")
    df = pd.read_csv(input_csv_path)
    print(f"成功读取 {len(df)} 行数据")
    
    # 如果没有指定输出路径，生成默认路径
    if output_csv_path is None:
        base_name = input_csv_path.rsplit('.', 1)[0]
        output_csv_path = f"{base_name}_filtered.csv"
    
    # 统计原始指标
    tp_before = len(df[df['Status'] == 'TP'])
    fp_before = len(df[df['Status'] == 'Mismatch']) + len(df[df['Status'] == 'FP'])
    fn_before = len(df[(df['Status'] == 'Mismatch') | (df['Status'] == 'FN')])
    tn_before = len(df[df['Status'] == 'TN'])
    
    # Mismatch会同时计入FP和FN
    mismatch_count = len(df[df['Status'] == 'Mismatch'])
    
    print(f"\n原始数据统计:")
    print(f"  TP: {tp_before}")
    print(f"  FP: {fp_before} (包括 {mismatch_count} 个 Mismatch)")
    print(f"  FN: {fn_before} (包括 {mismatch_count} 个 Mismatch)")
    print(f"  TN: {tn_before}")
    
    # 检查每个Key是否合法
    invalid_keys = []
    for idx, row in df.iterrows():
        key = row.get('Key', '')
        if not key:
            continue
        
        # 解析Key路径 (格式如: "Sample.Synthesis.Components.Precursors")
        # 移除样本名，只保留字段路径
        parts = key.split('.')
        if len(parts) < 2:
            continue
        
        # 第一部分是样本名，从第二部分开始是实际路径
        sample_name = parts[0]
        field_path = parts[1:]
        
        # 检查字段路径是否合法
        valid_keys = get_valid_keys_for_path(field_path[:-1])  # 父路径的合法键
        last_key = field_path[-1] if field_path else ''
        
        # 特殊处理动态键名
        is_dynamic = False
        if len(field_path) >= 3 and field_path[0] == "PhysicochemicalProperties":
            # Elemental下的元素符号
            if len(field_path) >= 4 and field_path[1] == "Composition" and field_path[2] == "Elemental":
                is_dynamic = True
            # XPS子物种
            if len(field_path) >= 4 and field_path[1] == "Composition" and field_path[2] == "HighResolution_XPS":
                is_dynamic = True
        
        # 如果不是动态键名且不在合法键集合中，标记为无效
        if not is_dynamic and valid_keys and last_key not in valid_keys:
            invalid_keys.append((idx, key))
    
    print(f"\n发现 {len(invalid_keys)} 个不合法的字段:")
    for idx, key in invalid_keys[:10]:  # 只打印前10个
        print(f"  行 {idx}: {key}")
    if len(invalid_keys) > 10:
        print(f"  ... 还有 {len(invalid_keys) - 10} 个")
    
    # 过滤掉不合法的行
    invalid_indices = [idx for idx, _ in invalid_keys]
    filtered_df = df.drop(invalid_indices)
    
    print(f"\n过滤后剩余 {len(filtered_df)} 行 (移除了 {len(invalid_keys)} 行)")
    
    # 重新统计指标
    tp_after = len(filtered_df[filtered_df['Status'] == 'TP'])
    mismatch_after = len(filtered_df[filtered_df['Status'] == 'Mismatch'])
    fp_after = mismatch_after + len(filtered_df[filtered_df['Status'] == 'FP'])
    fn_after = mismatch_after + len(filtered_df[filtered_df['Status'] == 'FN'])
    tn_after = len(filtered_df[filtered_df['Status'] == 'TN'])
    
    # 计算指标
    precision_before = tp_before / (tp_before + fp_before) if (tp_before + fp_before) > 0 else 0
    recall_before = tp_before / (tp_before + fn_before) if (tp_before + fn_before) > 0 else 0
    f1_before = 2 * precision_before * recall_before / (precision_before + recall_before) if (precision_before + recall_before) > 0 else 0
    
    precision_after = tp_after / (tp_after + fp_after) if (tp_after + fp_after) > 0 else 0
    recall_after = tp_after / (tp_after + fn_after) if (tp_after + fn_after) > 0 else 0
    f1_after = 2 * precision_after * recall_after / (precision_after + recall_after) if (precision_after + recall_after) > 0 else 0
    
    # 保存过滤后的CSV
    filtered_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ 过滤后的CSV已保存到: {output_csv_path}")
    
    # 打印对比结果
    print("\n" + "=" * 80)
    print("过滤前后指标对比:")
    print("=" * 80)
    print(f"\n过滤前:")
    print(f"  TP: {tp_before}, FP: {fp_before}, FN: {fn_before}, TN: {tn_before}")
    print(f"  Precision: {precision_before:.4f} ({precision_before*100:.2f}%)")
    print(f"  Recall: {recall_before:.4f} ({recall_before*100:.2f}%)")
    print(f"  F1 Score: {f1_before:.4f} ({f1_before*100:.2f}%)")
    
    print(f"\n过滤后:")
    print(f"  TP: {tp_after}, FP: {fp_after}, FN: {fn_after}, TN: {tn_after}")
    print(f"  Precision: {precision_after:.4f} ({precision_after*100:.2f}%)")
    print(f"  Recall: {recall_after:.4f} ({recall_after*100:.2f}%)")
    print(f"  F1 Score: {f1_after:.4f} ({f1_after*100:.2f}%)")
    
    print(f"\n改善:")
    fp_reduced = fp_before - fp_after
    print(f"  FP减少: {fp_reduced} ({(fp_reduced / fp_before * 100) if fp_before > 0 else 0:.2f}%)")
    print(f"  Precision提升: {(precision_after - precision_before):.4f} ({((precision_after - precision_before) / precision_before * 100) if precision_before > 0 else 0:.2f}%)")
    print(f"  F1提升: {(f1_after - f1_before):.4f} ({((f1_after - f1_before) / f1_before * 100) if f1_before > 0 else 0:.2f}%)")
    
    return {
        "before": {
            "TP": tp_before,
            "FP": fp_before,
            "FN": fn_before,
            "TN": tn_before,
            "precision": precision_before,
            "recall": recall_before,
            "f1_score": f1_before
        },
        "after": {
            "TP": tp_after,
            "FP": fp_after,
            "FN": fn_after,
            "TN": tn_after,
            "precision": precision_after,
            "recall": recall_after,
            "f1_score": f1_after
        },
        "improvement": {
            "fp_reduced": fp_reduced,
            "invalid_keys_removed": len(invalid_keys),
            "precision_gain": precision_after - precision_before,
            "f1_gain": f1_after - f1_before
        }
    }


if __name__ == "__main__":
    import json
    
    # 测试用例：包含一些幻觉字段的数据
    test_data = {
        "STGPC-1": {
            "Synthesis": {
                "Components": {
                    "Precursors": [
                        "Sargassum thunbergii (as bio-char, NDPCs-700)"
                    ],
                    "Activator": "K2FeO4",
                    "Template": 'null',
                    "Ratios": [
                        {
                            "component_A": "K2FeO4",
                            "component_B": "bio-char (NDPCs-700)",
                            "ratio": "2:1",
                            "type": "mass"
                        }
                    ]
                },
                "ProcessFlow": [
                    {
                        "step_name": "Mixing and Drying",
                        "temperature": 80,
                        "duration": 6,
                        "heating_rate": 'null',
                        "atmosphere": 'null',
                        "flow_rate": 'null',
                        "details": "Mixed with 50 mL deionized water, stirred for 6 h."
                    },
                    {
                        "step_name": "Activation",
                        "temperature": 600,
                        "duration": 2,
                        "heating_rate": 5,
                        "atmosphere": "N2",
                        "flow_rate": 'null',
                        "details": 'null'
                    },
                    {
                        "step_name": "Acid Washing",
                        "temperature": 'null',
                        "duration": 'null',
                        "heating_rate": 'null',
                        "atmosphere": 'null',
                        "flow_rate": 'null',
                        "details": "Washed with 6 M HCl to remove residual inorganic impurities."
                    },
                    {
                        "step_name": "Final Washing and Drying",
                        "temperature": 110,
                        "duration": 'null',
                        "heating_rate": 'null',
                        "atmosphere": 'null',
                        "flow_rate": 'null',
                        "details": "Washed with deionized water."
                    }
                ]
            },
            "PhysicochemicalProperties": {
                "Porosity": {
                    "SpecificSurfaceArea_BET": {
                        "value": 1044.1,
                        "unit": "m²/g"
                    },
                    "MicroporeSurfaceArea": {
                        "value": 808.26,
                        "unit": "m²/g"
                    },
                    "TotalPoreVolume": {
                        "value": 0.62,
                        "unit": "cm³/g"
                    },
                    "MicroporeVolume": {
                        "value": 0.43,
                        "unit": "cm³/g"
                    },
                    "MesoporeVolume": {
                        "value": 0.19,
                        "unit": "cm³/g"
                    },
                    "AveragePoreDiameter": {
                        "value": 2.41,
                        "unit": "nm"
                    },
                    "PoreSizeDistribution": "mostly around 0.6–10 nm"
                },
                "Composition": {
                    "Elemental": {
                        "C": {
                            "value": 78.2,
                            "unit": "wt%"
                        },
                        "N": {
                            "value": 6.1,
                            "unit": "wt%"
                        },
                        "O": {
                            "value": 10.8,
                            "unit": "wt%"
                        }
                    },
                    "HighResolution_XPS": {
                        "N_Species": {
                            "Pyridinic-N": 21.7,
                            "Pyrrolic-N": 51.6,
                            "Graphitic-N": 26.7,
                            "Oxidized-N": 'null'
                        },
                        "C_Species": 'null'
                    },
                    "QualitativeFunctionalGroups_FTIR": 'null'
                },
                "Crystallinity": {
                    "Graphitization_Raman_ID_IG": 0.98
                }
            },
            "ElectrochemicalPerformance": [
                {
                    "SystemType": "Three-electrode",
                    "Electrolyte": "6M KOH",
                    "VoltageWindow": "[-1.0, 0] V",
                    "SpecificCapacitance": [
                        {
                            "method": "GCD",
                            "value": 167.4,
                            "unit": "F/g",
                            "condition": "0.5 A/g",
                            "mass_loading": "2.0 mg/cm^2"
                        }
                    ],
                    "RateCapability": 'null',
                    "Impedance": {
                        "ESR": 'null',
                        "Rct": 'null',
                        "unit": "Ω"
                    }
                }
            ]
        },
        
    }
    print("=" * 80)
    print("原始数据（包含幻觉字段）:")
    print("=" * 80)
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("检测到的不合法字段:")
    print("=" * 80)
    for sample_name, sample_data in test_data.items():
        invalid = get_all_invalid_keys(sample_data)
        if invalid:
            print(f"\n样本 {sample_name}:")
            for path, key in invalid:
                path_str = " -> ".join(path) if path else "root"
                print(f"  {path_str} -> [{key}]")
    
    print("\n" + "=" * 80)
    print("过滤后的数据（移除幻觉字段）:")
    print("=" * 80)
    filtered = filter_unified_results(test_data)
    print(json.dumps(filtered, indent=2, ensure_ascii=False))


