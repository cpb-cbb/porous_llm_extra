import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from tqdm import tqdm
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def safe_get(data: Any, *keys, default=None):
    """
    安全地从嵌套字典中获取值
    
    Args:
        data: 数据源
        *keys: 键的路径
        default: 默认值
    
    Returns:
        提取的值或默认值
    """
    try:
        result = data
        for key in keys:
            if result is None:
                return default
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return default
        return result if result is not None else default
    except (KeyError, TypeError, AttributeError):
        return default


def filename_to_doi(filename: str) -> str:
    """
    将文件名转换为DOI格式
    
    Args:
        filename: 文件名,如 "10.1016_j.jallcom.2023.170452_extracted.json"
    
    Returns:
        DOI字符串,如 "10.1016/j.jallcom.2023.170452"
    """
    try:
        # 移除后缀
        base_name = filename.replace('_extracted.json', '').replace('.json', '')
        
        # 将第一个下划线替换为斜杠,其余替换为点
        doi = base_name.replace('_', '/', 1).replace('_', '.')
        
        return doi
    except Exception as e:
        logger.warning(f"转换DOI失败 {filename}: {e}")
        return filename


def extract_synthesis_data(sample_name: str, data: Dict, doi: str) -> Dict:
    """提取合成信息 - 增强鲁棒性版本"""
    result = {
        'doi': doi,
        'sample_name': sample_name,
        'precursors': None,
        'activator': None,
        'template': None,
        'ratios': None,
        'max_temperature': None,
        'total_duration': None,
        'atmospheres': None
    }
    
    if data is None:
        return result
    
    try:
        synthesis = safe_get(data, 'Synthesis', default={})
        components = safe_get(synthesis, 'Components', default={})
        
        # 提取前驱体
        precursors = safe_get(components, 'Precursors', default=[])
        if precursors and isinstance(precursors, list):
            result['precursors'] = ', '.join(str(p) for p in precursors if p)
        
        # 提取活化剂
        result['activator'] = safe_get(components, 'Activator')
        
        # 提取模板
        result['template'] = safe_get(components, 'Template')
        
        # 提取比例信息
        ratios = safe_get(components, 'Ratios', default=[])
        if ratios and isinstance(ratios, list):
            ratio_parts = []
            for r in ratios:
                if isinstance(r, dict):
                    comp_a = safe_get(r, 'component_A', default='?')
                    comp_b = safe_get(r, 'component_B', default='?')
                    ratio = safe_get(r, 'ratio', default='?')
                    ratio_type = safe_get(r, 'type', default='')
                    ratio_parts.append(f"{comp_a}:{comp_b}={ratio} ({ratio_type})")
            if ratio_parts:
                result['ratios'] = '; '.join(ratio_parts)
        
        # 提取工艺流程关键参数
        process_flow = safe_get(synthesis, 'ProcessFlow', default=[])
        if process_flow and isinstance(process_flow, list):
            max_temp = None
            total_duration = 0
            atmospheres = []
            
            for step in process_flow:
                if not isinstance(step, dict):
                    continue
                
                # 温度
                temp = safe_get(step, 'temperature')
                if temp is not None:
                    try:
                        temp = float(temp)
                        if max_temp is None or temp > max_temp:
                            max_temp = temp
                    except (ValueError, TypeError):
                        pass
                
                # 时长
                duration = safe_get(step, 'duration')
                if duration is not None:
                    try:
                        total_duration += float(duration)
                    except (ValueError, TypeError):
                        pass
                
                # 气氛
                atmosphere = safe_get(step, 'atmosphere')
                if atmosphere and atmosphere not in atmospheres:
                    atmospheres.append(str(atmosphere))
            
            result['max_temperature'] = max_temp
            result['total_duration'] = total_duration if total_duration > 0 else None
            result['atmospheres'] = ', '.join(atmospheres) if atmospheres else None
    
    except Exception as e:
        logger.warning(f"提取样品 {sample_name} 的合成数据时出错: {e}")
    
    return result


def extract_physicochemical_data(sample_name: str, data: Dict, doi: str) -> Dict:
    """提取物理化学性质 - 增强鲁棒性版本"""
    result = {
        'doi': doi,
        'sample_name': sample_name,
        'BET_surface_area': None,
        'micropore_surface_area': None,
        'total_pore_volume': None,
        'micropore_volume': None,
        'mesopore_volume': None,
        'avg_pore_diameter': None,
        'pore_size_distribution': None,
        'functional_groups': None,
        'raman_ID_IG': None
    }
    
    if data is None:
        return result
    
    try:
        props = safe_get(data, 'PhysicochemicalProperties', default={})
        
        # 提取孔隙率数据
        porosity = safe_get(props, 'Porosity', default={})
        
        result['BET_surface_area'] = safe_get(porosity, 'SpecificSurfaceArea_BET', 'value')
        result['micropore_surface_area'] = safe_get(porosity, 'MicroporeSurfaceArea', 'value')
        result['total_pore_volume'] = safe_get(porosity, 'TotalPoreVolume', 'value')
        result['micropore_volume'] = safe_get(porosity, 'MicroporeVolume', 'value')
        result['mesopore_volume'] = safe_get(porosity, 'MesoporeVolume', 'value')
        result['avg_pore_diameter'] = safe_get(porosity, 'AveragePoreDiameter', 'value')
        result['pore_size_distribution'] = safe_get(porosity, 'PoreSizeDistribution')
        
        # 提取组成数据
        composition = safe_get(props, 'Composition', default={})
        
        # 元素组成
        elemental = safe_get(composition, 'Elemental', default={})
        if isinstance(elemental, dict):
            for element, info in elemental.items():
                value = None
                if isinstance(info, dict):
                    value = safe_get(info, 'value')
                elif isinstance(info, (int, float)):
                    value = info
                
                if value is not None:
                    result[f'element_{element}'] = value
        
        # XPS高分辨数据
        xps = safe_get(composition, 'HighResolution_XPS', default={})
        
        # N物种
        n_species = safe_get(xps, 'N_Species', default={})
        if isinstance(n_species, dict):
            for species, value in n_species.items():
                result[f'N_{species}'] = value
        
        # C物种
        c_species = safe_get(xps, 'C_Species', default={})
        if isinstance(c_species, dict):
            for species, value in c_species.items():
                result[f'C_{species}'] = value
        
        # 官能团
        ftir_groups = safe_get(composition, 'QualitativeFunctionalGroups_FTIR', default=[])
        if ftir_groups and isinstance(ftir_groups, list):
            result['functional_groups'] = ', '.join(str(g) for g in ftir_groups if g)
        
        # 结晶度
        crystallinity = safe_get(props, 'Crystallinity', default={})
        result['raman_ID_IG'] = safe_get(crystallinity, 'Graphitization_Raman_ID_IG')
    
    except Exception as e:
        logger.warning(f"提取样品 {sample_name} 的物理化学数据时出错: {e}")
    
    return result


def extract_electrochemical_data(sample_name: str, data: Dict, doi: str) -> List[Dict]:
    """提取电化学性能数据 - 增强鲁棒性版本"""
    results = []
    
    if data is None:
        return results
    
    try:
        performance = safe_get(data, 'ElectrochemicalPerformance', default=[])
        
        if not isinstance(performance, list):
            return results
        
        for i, test in enumerate(performance):
            if not isinstance(test, dict):
                continue
            
            try:
                result = {
                    'doi': doi,
                    'sample_name': sample_name,
                    'test_index': i,
                    'system_type': safe_get(test, 'SystemType'),
                    'electrolyte': safe_get(test, 'Electrolyte'),
                    'voltage_window': safe_get(test, 'VoltageWindow'),
                    'rate_capability': safe_get(test, 'RateCapability'),
                    'cycle_stability': safe_get(test, 'CycleStability'),
                    'max_energy_density': safe_get(test, 'MaxEnergyDensity'),
                    'max_power_density': safe_get(test, 'MaxPowerDensity'),
                    'ESR': None,
                    'Rct': None
                }
                
                # 提取电容数据
                capacitances = safe_get(test, 'SpecificCapacitance', default=[])
                if isinstance(capacitances, list):
                    for j, cap in enumerate(capacitances):
                        if isinstance(cap, dict):
                            result[f'capacitance_{j}_method'] = safe_get(cap, 'method')
                            result[f'capacitance_{j}_value'] = safe_get(cap, 'value')
                            result[f'capacitance_{j}_unit'] = safe_get(cap, 'unit')
                            result[f'capacitance_{j}_condition'] = safe_get(cap, 'condition')
                            result[f'capacitance_{j}_mass_loading'] = safe_get(cap, 'mass_loading')
                
                # 提取阻抗数据
                impedance = safe_get(test, 'Impedance', default={})
                if isinstance(impedance, dict):
                    result['ESR'] = safe_get(impedance, 'ESR')
                    result['Rct'] = safe_get(impedance, 'Rct')
                
                results.append(result)
            
            except Exception as e:
                logger.warning(f"提取样品 {sample_name} 测试 {i} 的电化学数据时出错: {e}")
                continue
    
    except Exception as e:
        logger.warning(f"提取样品 {sample_name} 的电化学数据时出错: {e}")
    
    return results


def convert_single_json_to_csv(json_file_path: str) -> tuple:
    """
    将单个JSON文件转换为DataFrame
    
    Returns:
        (df_synthesis, df_physicochemical, df_electrochemical, doi, success)
    """
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取文件名和DOI
        filename = Path(json_file_path).name
        doi = filename_to_doi(filename)
        
        # 提取final_result部分
        final_result = safe_get(data, 'final_result', default={})
        
        if not final_result or not isinstance(final_result, dict):
            logger.warning(f"{filename}: final_result为空或格式不正确")
            return None, None, None, doi, False
        
        # 创建三个数据集
        synthesis_data = []
        physicochemical_data = []
        electrochemical_data = []
        
        for sample_name, sample_data in final_result.items():
            if sample_data is None:
                logger.warning(f"{filename}: 样品 {sample_name} 的数据为None,跳过")
                continue
            
            try:
                synthesis_data.append(extract_synthesis_data(sample_name, sample_data, doi))
                physicochemical_data.append(extract_physicochemical_data(sample_name, sample_data, doi))
                electrochemical_data.extend(extract_electrochemical_data(sample_name, sample_data, doi))
            except Exception as e:
                logger.error(f"{filename}: 处理样品 {sample_name} 时出错: {e}")
                continue
        
        # 转换为DataFrame
        df_synthesis = pd.DataFrame(synthesis_data) if synthesis_data else pd.DataFrame()
        df_physicochemical = pd.DataFrame(physicochemical_data) if physicochemical_data else pd.DataFrame()
        df_electrochemical = pd.DataFrame(electrochemical_data) if electrochemical_data else pd.DataFrame()
        
        return df_synthesis, df_physicochemical, df_electrochemical, doi, True
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误 {Path(json_file_path).name}: {e}")
        return None, None, None, None, False
    except Exception as e:
        logger.error(f"处理文件 {Path(json_file_path).name} 时出错: {e}")
        return None, None, None, None, False


def batch_convert_json_to_csv(input_dir: str, output_dir: str = None):
    """
    批量转换目录中的所有JSON文件为CSV
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径,默认为输入目录下的 'csv_output' 文件夹
    """
    input_path = Path(input_dir)
    
    # 设置输出目录
    if output_dir is None or output_dir == "":
        output_path = input_path / 'csv_output'
    else:
        output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 查找所有JSON文件
    json_files = list(input_path.glob('*_extracted.json'))
    
    if not json_files:
        logger.warning(f"在 {input_dir} 中未找到 *_extracted.json 文件")
        return None, None, None, None
    
    logger.info(f"找到 {len(json_files)} 个JSON文件,开始转换...")
    
    # 用于存储所有数据
    all_synthesis = []
    all_physicochemical = []
    all_electrochemical = []
    
    # 统计信息
    success_count = 0
    failed_count = 0
    
    # 使用tqdm显示进度
    for json_file in tqdm(json_files, desc="转换进度", unit="文件"):
        try:
            df_syn, df_phys, df_elec, doi, success = convert_single_json_to_csv(str(json_file))
            
            if success:
                if df_syn is not None and not df_syn.empty:
                    all_synthesis.append(df_syn)
                if df_phys is not None and not df_phys.empty:
                    all_physicochemical.append(df_phys)
                if df_elec is not None and not df_elec.empty:
                    all_electrochemical.append(df_elec)
                success_count += 1
            else:
                failed_count += 1
        
        except Exception as e:
            logger.error(f"处理文件 {json_file.name} 时出错: {e}")
            failed_count += 1
            continue
    
    # 合并所有数据
    if all_synthesis or all_physicochemical or all_electrochemical:
        combined_synthesis = pd.concat(all_synthesis, ignore_index=True) if all_synthesis else pd.DataFrame()
        combined_physicochemical = pd.concat(all_physicochemical, ignore_index=True) if all_physicochemical else pd.DataFrame()
        combined_electrochemical = pd.concat(all_electrochemical, ignore_index=True) if all_electrochemical else pd.DataFrame()
        
        # 创建合并数据集(通过doi和sample_name连接)
        if not combined_synthesis.empty and not combined_physicochemical.empty:
            combined_merged = combined_synthesis.merge(
                combined_physicochemical, 
                on=['doi', 'sample_name'], 
                how='outer'
            )
        elif not combined_synthesis.empty:
            combined_merged = combined_synthesis
        elif not combined_physicochemical.empty:
            combined_merged = combined_physicochemical
        else:
            combined_merged = pd.DataFrame()
        
        # 保存为CSV
        if not combined_synthesis.empty:
            combined_synthesis.to_csv(output_path / 'all_synthesis.csv', index=False, encoding='utf-8-sig')
        if not combined_physicochemical.empty:
            combined_physicochemical.to_csv(output_path / 'all_physicochemical.csv', index=False, encoding='utf-8-sig')
        if not combined_electrochemical.empty:
            combined_electrochemical.to_csv(output_path / 'all_electrochemical.csv', index=False, encoding='utf-8-sig')
        if not combined_merged.empty:
            combined_merged.to_csv(output_path / 'all_merged.csv', index=False, encoding='utf-8-sig')
        
        logger.info(f"\n{'='*60}")
        logger.info(f"转换完成!")
        logger.info(f"{'='*60}")
        logger.info(f"输出目录: {output_path}")
        logger.info(f"\n统计信息:")
        logger.info(f"  成功处理: {success_count} 个文件")
        logger.info(f"  失败: {failed_count} 个文件")
        logger.info(f"\n数据统计:")
        logger.info(f"  合成数据: {len(combined_synthesis)} 行, {len(combined_synthesis.columns)} 列")
        logger.info(f"  物理化学数据: {len(combined_physicochemical)} 行, {len(combined_physicochemical.columns)} 列")
        logger.info(f"  电化学数据: {len(combined_electrochemical)} 行, {len(combined_electrochemical.columns)} 列")
        logger.info(f"  合并数据: {len(combined_merged)} 行, {len(combined_merged.columns)} 列")
        logger.info(f"\n输出文件:")
        if not combined_synthesis.empty:
            logger.info(f"  ✓ all_synthesis.csv")
        if not combined_physicochemical.empty:
            logger.info(f"  ✓ all_physicochemical.csv")
        if not combined_electrochemical.empty:
            logger.info(f"  ✓ all_electrochemical.csv")
        if not combined_merged.empty:
            logger.info(f"  ✓ all_merged.csv")
        logger.info(f"{'='*60}\n")
        
        return combined_synthesis, combined_physicochemical, combined_electrochemical, combined_merged
    else:
        logger.warning("没有成功处理任何文件")
        return None, None, None, None


if __name__ == "__main__":
    # 批量处理示例
    input_directory = "/Volumes/mac_outstore/毕业/测试集文献/zhipu"
    output_directory = ""  # 空字符串表示使用默认目录
    
    # 批量转换
    df_syn, df_phys, df_elec, df_merged = batch_convert_json_to_csv(
        input_directory, 
        output_directory
    )
    
    # 显示部分数据
    if df_syn is not None and not df_syn.empty:
        print("\n合成数据预览:")
        print(df_syn.head())
        
        print("\nDOI列示例:")
        print(df_syn[['doi', 'sample_name']].head(10))