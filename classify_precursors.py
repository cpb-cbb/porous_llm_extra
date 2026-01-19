"""
前驱体分类脚本
用于对all_synthesis.csv中的precursors列进行自动分类
"""

import pandas as pd
import json
from typing import Dict, List
import time
from pathlib import Path
import sys
import json_repair
sys.path.append('/Users/caopengbo/Documents/code/porous_llm_extra')

from servers.agents.generic import StandardExtractionAgent
from core.config import settings

# Classification System Prompt (English Version)
CLASSIFICATION_SYSTEM_PROMPT = """You are a materials science expert specializing in classifying precursor materials for porous carbon synthesis.

Your task is to classify the given precursor material into appropriate categories.

## Main Category (choose ONE from the following):
- Biomass
- Synthetic_Polymer
- Small_Molecule
- MOF
- Carbon_Material
- Composite
- Coal_Based
- Industrial_Waste
- Other

## Detail Categories (choose ONE or MORE from the following):

### Biomass subcategories:
- Biomass-Agricultural_Waste (e.g., rice husk, straw, bagasse, corn cob)
- Biomass-Wood_Material (e.g., sawdust, bark, bamboo, wood)
- Biomass-Fruit_Shell_Seed (e.g., coconut shell, walnut shell, peanut shell, fruit pit)
- Biomass-Plant_Tissue (e.g., leaves, petals, stems, peels)
- Biomass-Food_Waste (e.g., coffee grounds, tea waste, bean dregs, food residue)
- Biomass-Animal_Source (e.g., eggshell, bone, hair, leather waste)
- Biomass-Algae_Microorganism (e.g., spirulina, seaweed, bacterial cellulose)

### Synthetic_Polymer subcategories:
- Polymer-Nitrogen_Containing (e.g., PAN, polyimide, polyaniline)
- Polymer-Natural_Derivative (e.g., chitosan, sodium alginate, cellulose derivatives)
- Polymer-Resin (e.g., phenolic resin, melamine resin, epoxy resin)

### Small_Molecule subcategories:
- Small_Molecule-Carbohydrate (e.g., glucose, sucrose, starch)
- Small_Molecule-Aromatic (e.g., resorcinol, aniline, naphthalene)
- Small_Molecule-Nitrogen_Compound (e.g., melamine, urea, dicyandiamide)
- Small_Molecule-Alcohol_Aldehyde (e.g., furfuryl alcohol, formaldehyde, ethylene glycol)

### MOF subcategories:
- MOF-ZIF_Series (e.g., ZIF-8, ZIF-67)
- MOF-Other (e.g., MOF-5, UiO-66)

### Carbon_Material subcategories:
- Carbon-Activated_Carbon
- Carbon-Graphene
- Carbon-Carbon_Nanotube
- Carbon-Biochar

### Composite subcategories:
- Composite-Biomass_Nitrogen (biomass mixed with melamine, urea, etc.)
- Composite-Biomass_Metal (biomass mixed with metal salts)
- Composite-Multi_Component (three or more components)

### Coal_Based subcategories:
- Coal-Coal_Tar
- Coal-Coal
- Coal-Pitch

### Industrial_Waste subcategories:
- Waste-Sludge
- Waste-Waste_Oil
- Waste-Industrial_Residue

### Other subcategories:
- Other-Special_Material

## Output Format:
Return the result in JSON format with the following structure:
{
    "main_category": "one of the main categories listed above",
    "detail_categories": ["one or more detail categories"],
    "reason": "brief explanation for the classification"
}

IMPORTANT RULES:
1. main_category must be ONE of: Biomass, Synthetic_Polymer, Small_Molecule, MOF, Carbon_Material, Composite, Coal_Based, Industrial_Waste, Other
2. detail_categories must be a list containing one or more valid detail category names from above
3. Use underscore (_) instead of spaces in category names
4. Keep the reason concise and informative
"""

# User Message Template (note: StandardExtractionAgent expects parameter name 'text_input')
CLASSIFICATION_USER_TEMPLATE = """Please classify the following precursor material:

Precursor name: {text_input}

Return the classification result in JSON format."""


class PrecursorClassifier:
    """前驱体分类器"""
    
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None, 
                 temperature: float = 0.3, top_p: float = 1.0, max_tokens: int = 5000):
        """
        初始化分类器
        
        Args:
            model: 使用的模型名称（如果为None，从settings读取）
            api_key: API密钥（如果为None，从settings读取）
            base_url: API基础URL（如果为None，从settings读取）
            temperature: 温度参数
            top_p: top_p参数
            max_tokens: 最大token数
        """
        self.agent = StandardExtractionAgent(
            system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
            model=model or settings.llm_model,
            api_key=api_key or settings.llm_api_key,
            base_url=base_url or settings.llm_base_url,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            message_template=CLASSIFICATION_USER_TEMPLATE
        )
        print(f"初始化分类器，使用模型: {self.agent.model}")
        
    def classify_single(self, precursor: str) -> Dict:
        """
        对单个前驱体进行分类
        
        Args:
            precursor: 前驱体名称
            
        Returns:
            包含分类结果的字典
        """
        try:
            # 使用agent进行分类（注意：参数名必须是text_input）
            response = self.agent.run(text_input=precursor)
            
            # 使用 json_repair 自动修复并解析返回的JSON结果
            if isinstance(response, str):
                result = json_repair.loads(response)
            elif isinstance(response, dict):
                result = response
            else:
                raise ValueError(f"Unexpected response type: {type(response)}")
            
            result['precursor'] = precursor
            result['success'] = True
            
            return result
            
        except Exception as e:
            print(f"分类失败: {precursor}, 错误: {str(e)}")
            # 尝试打印原始响应以便调试
            try:
                if 'response' in locals():
                    print(f"原始响应: {response[:300] if isinstance(response, str) else response}")
            except:
                pass
            
            return {
                'precursor': precursor,
                'main_category': 'Other',
                'detail_categories': ['Other-Special_Material'],
                'reason': f'Error: {str(e)}',
                'success': False
            }
    
    def classify_batch(self, precursors: List[str], batch_size: int = 10, 
                      delay: float = 1.0, save_interval: int = 50, 
                      resume_file: str = "classification_checkpoint.json") -> List[Dict]:
        """
        批量分类前驱体（支持断点续传）
        
        Args:
            precursors: 前驱体列表
            batch_size: 批处理大小
            delay: 每次请求之间的延迟（秒）
            save_interval: 每处理多少条保存一次中间结果
            resume_file: 断点续传文件路径
            
        Returns:
            分类结果列表
        """
        results = []
        processed_precursors = set()
        start_index = 0
        
        # 尝试加载断点续传数据
        if Path(resume_file).exists():
            try:
                with open(resume_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    results = checkpoint_data.get('results', [])
                    processed_precursors = set(r['precursor'] for r in results)
                    start_index = len(results)
                print(f"✓ 加载断点续传数据：已完成 {start_index} 条，继续处理...")
            except Exception as e:
                print(f"⚠ 无法加载断点文件，将从头开始: {e}")
                results = []
                processed_precursors = set()
                start_index = 0
        
        total = len(precursors)
        remaining = total - start_index
        
        print(f"开始分类 {total} 个前驱体 (剩余 {remaining} 条)...")
        
        for i, precursor in enumerate(precursors, 1):
            # 跳过已处理的
            if precursor in processed_precursors:
                continue
            
            print(f"进度: {i}/{total} - 正在分类: {precursor[:50]}...")
            
            result = self.classify_single(precursor)
            results.append(result)
            processed_precursors.add(precursor)
            
            # 定期保存断点
            if len(results) % save_interval == 0:
                self._save_checkpoint(results, resume_file)
                print(f"✓ 已保存断点: {len(results)} 条")
            
            # 延迟以避免API限流
            if i < total:
                time.sleep(delay)
        
        # 保存最终断点
        self._save_checkpoint(results, resume_file)
        print("分类完成！")
        return results
    
    def _save_checkpoint(self, results: List[Dict], checkpoint_file: str):
        """保存断点数据"""
        checkpoint_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_processed': len(results),
            'results': results
        }
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    
    def _save_intermediate_results(self, results: List[Dict], filename: str):
        """保存中间结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


def load_precursors_from_csv(csv_path: str) -> pd.DataFrame:
    """
    从CSV文件加载前驱体数据
    
    Args:
        csv_path: CSV文件路径
        
    Returns:
        包含前驱体的DataFrame
    """
    df = pd.read_csv(csv_path)
    print(f"加载CSV文件: {csv_path}")
    print(f"总行数: {len(df)}")
    print(f"包含precursors的行数: {df['precursors'].notna().sum()}")
    
    return df


def get_unique_precursors(df: pd.DataFrame) -> List[str]:
    """
    获取唯一的前驱体列表
    
    Args:
        df: DataFrame
        
    Returns:
        唯一前驱体列表
    """
    unique_precursors = df['precursors'].dropna().unique().tolist()
    print(f"唯一前驱体数量: {len(unique_precursors)}")
    
    return unique_precursors


def save_classification_results(results: List[Dict], output_path: str):
    """
    保存分类结果
    
    Args:
        results: 分类结果列表
        output_path: 输出文件路径
    """
    # 保存JSON格式
    json_path = output_path.replace('.csv', '_full.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"保存完整结果: {json_path}")
    
    # 转换为DataFrame并保存CSV
    df_results = pd.DataFrame([
        {
            'precursor': r['precursor'],
            'main_category': r.get('main_category', ''),
            'detail_categories': '|'.join(r.get('detail_categories', [])),
            'reason': r.get('reason', ''),
            'success': r.get('success', False)
        }
        for r in results
    ])
    
    df_results.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"保存分类结果CSV: {output_path}")
    
    # 打印统计信息
    print("\n=== 分类统计 ===")
    print(f"成功分类: {df_results['success'].sum()}")
    print(f"分类失败: {(~df_results['success']).sum()}")
    print("\n主要类别分布:")
    print(df_results['main_category'].value_counts().head(15))


def merge_classification_to_original(original_csv: str, classification_csv: str, 
                                     output_csv: str):
    """
    将分类结果合并回原始CSV
    
    Args:
        original_csv: 原始CSV文件路径
        classification_csv: 分类结果CSV路径
        output_csv: 输出CSV路径
    """
    df_original = pd.read_csv(original_csv)
    df_classification = pd.read_csv(classification_csv)
    
    # 创建precursor到分类的映射
    classification_map = df_classification.set_index('precursor').to_dict('index')
    
    # 添加分类列
    df_original['precursor_main_category'] = df_original['precursors'].map(
        lambda x: classification_map.get(x, {}).get('main_category', '') if pd.notna(x) else ''
    )
    df_original['precursor_detail_categories'] = df_original['precursors'].map(
        lambda x: classification_map.get(x, {}).get('detail_categories', '') if pd.notna(x) else ''
    )
    
    df_original.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"已保存合并后的文件: {output_csv}")


def main():
    """主函数"""
    # 配置参数
    CSV_PATH = "/Volumes/mac_outstore/毕业/jsol文献/biomass_super_2000/filtered_json/zhipu/csv_output/all_synthesis.csv"
    OUTPUT_DIR = "/Volumes/mac_outstore/毕业/jsol文献/biomass_super_2000/filtered_json/zhipu/csv_output"
    CHECKPOINT_FILE = f"{OUTPUT_DIR}/classification_checkpoint.json"
    
    # 创建输出目录
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # 初始化分类器（使用项目配置）
    classifier = PrecursorClassifier()
    
    # 如果需要覆盖配置，可以传入参数：
    # classifier = PrecursorClassifier(
    #     model="gpt-4o-mini",
    #     temperature=0.3
    # )
    
    # 加载数据
    df = load_precursors_from_csv(CSV_PATH)
    unique_precursors = get_unique_precursors(df)
    
    # 可选：只对前N个进行测试
    # unique_precursors = unique_precursors[:10]
    # print(f"测试模式：只分类前 {len(unique_precursors)} 个前驱体")
    
    # 执行分类（支持断点续传）
    results = classifier.classify_batch(
        unique_precursors,
        batch_size=10,
        delay=1.0,  # API请求间隔
        save_interval=10,  # 每10条保存一次断点
        resume_file=CHECKPOINT_FILE  # 断点文件路径
    )
    
    # 保存结果
    output_path = f"{OUTPUT_DIR}/precursor_classification.csv"
    save_classification_results(results, output_path)
    
    # 合并回原始文件
    merged_output = f"{OUTPUT_DIR}/all_synthesis_with_classification.csv"
    merge_classification_to_original(CSV_PATH, output_path, merged_output)
    
    # 清理断点文件（可选，如果想保留则注释掉）
    # if Path(CHECKPOINT_FILE).exists():
    #     Path(CHECKPOINT_FILE).unlink()
    #     print(f"✓ 已删除断点文件")
    
    print("\n所有任务完成！")


if __name__ == "__main__":
    main()
