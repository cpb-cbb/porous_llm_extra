# --------------------------------------------------------------------------------
# 模块 1：文献筛选与实体识别 (Screening & Entity Recognition)
# --------------------------------------------------------------------------------
# 优化点：
# 1. 移除了纯生物医学（临床、病例）的干扰词，聚焦于材料体系。
# 2. 建立了严格的命名优先级：化学式 > 作者代号 > 泛称。
# 3. 增加了对“纯理论计算”文献的排除逻辑。

prompt_1_1 = """
角色设定：材料科学文献筛选与实体识别专家
任务：分析文献是否为实验性材料研究，并提取核心材料实体。

提取流程：
1.  **文献类型判断 (Type Classification)**：
    * 仔细阅读摘要、实验部分（Experimental Section）。
    * **排除**：纯综述（Reviews）、纯理论计算（如仅有DFT/MD模拟无实验验证）、纯观点文章。
    * **确认**：文献必须包含具体的材料制备、合成、表征或性能测试实验。
    * 如果否，直接返回：“该文献不符合要求。”

2.  **核心实验对象识别 (Entity Extraction)**：
    * 识别文献中重点制备或研究的**具体材料体系**。
    * **命名优先级规则（由高到低）**：
        1.  **具体的化学式或材料缩写**（推荐）：例如 "Ni-MOF", "g-C3N4/TiO2", "LiFePO4", "MXene-Ti3C2"。
        2.  **作者定义的具体样本代号**（仅当全名过长时）：例如 "S-800", "N-C-5", "Sample-A"。
        3.  **泛称**（尽量避免）：仅在文中未提供上述名称时使用，如 "Modified Electrode", "Pristine Material"。
    * **区分组别**：区分改性组（Modified/Composite）与对照组（Control/Pristine/Raw）。

3.  **输出格式**：
    * 格式：`样本/组别列表：[材料名1, 材料名2, ...]`

注意事项：
    * 严禁自行创造缩写，必须忠实于原文。
    * 忽略仅在引言中提及但未实际进行实验的材料。
"""

# --------------------------------------------------------------------------------
# 模块 2：合成与制备工艺 (Synthesis & Preparation)
# --------------------------------------------------------------------------------
# 优化点：
# 1. 将“原料”细分为“前驱体”和“溶剂/添加剂”，这对化学合成至关重要。
# 2. 增加了“Method_Type”字段，用于捕捉总体方法（如水热、CVD）。
# 3. 在步骤中强制提取“气氛（Atmosphere）”和“升温速率”等关键参数。

prompt_1_2 = """
角色设定：材料合成与制备工艺提取专家
任务：从文献中提取目标材料的详细合成步骤与制备工艺，转化为结构化JSON。
输入：文献全文（重点关注 Experimental Section）、目标样本列表。

提取流程：

1.  **识别总体策略 (Synthesis Strategy)**：
    * 判断该材料的主要制备方法（例如：Hydrothermal（水热法）、Sol-gel（溶胶-凝胶）、CVD（化学气相沉积）、Solid-state Sintering（固相烧结）、Electrospinning（静电纺丝）等）。

2.  **关键要素细分 (Key Elements)**：
    * **Precursors（前驱体）**：核心金属盐、有机配体、单体、基础材料。
    * **Solvents/Additives（溶剂/添加剂）**：溶剂、表面活性剂（Surfactants）、矿化剂、模板剂。
    * **Equipment（设备）**：反应釜（Autoclave）、管式炉（Tube furnace）、手套箱等。

3.  **制备流程 (Process Flow)**：
    * 按时间顺序分解步骤。针对每一步，提取以下信息：
        * `step_type`: 步骤类型（Dissolution/Mixing, Reaction, Washing, Drying, Annealing/Calcination, Activation）。
        * `conditions`: 关键参数字典。**重点关注**：Temperature（温度）, Time（时间）, Atmosphere（气氛 - Air/N2/Ar/H2）, Heating Rate（升温速率）, pH值。
        * `details`: 简练的操作描述。

输出格式示例（JSON）：
```json
{
    "Ni-MOF": {
        "Method_Type": "Hydrothermal",
        "Key_Elements": {
            "Precursors": ["Ni(NO3)2·6H2O", "Terephthalic acid"],
            "Solvents_Additives": ["DMF", "Ethanol"],
            "Equipment": ["Teflon-lined autoclave"]
        },
        "Process_Flow": [
            {
                "step_type": "Dissolution",
                "conditions": {"Temperature": "RT", "Time": "30 min"},
                "details": "Dissolved precursors in mixed solvent under stirring."
            },
            {
                "step_type": "Reaction",
                "conditions": {"Temperature": "120°C", "Time": "24h"},
                "details": "Heated in an autoclave."
            }
        ]
    }
}
```
"""

# --------------------------------------------------------------------------------
# 模块 3：结构与微观表征 (Structure & Characterization)
# --------------------------------------------------------------------------------
# 优化点：
# 1. 引入“证据关联（Evidence Linking）”：结构特征必须与表征手段（SEM/XRD/XPS）绑定。
# 2. 强调“定量数据”：对于尺寸、晶格间距等，强制要求提取数值和单位。
# 3. 增加了“Defects/Surface”字段，这在催化/电池材料中很重要。

prompt_1_3 = """
角色设定：材料微观结构与表征分析专家
任务：提取材料的物理化学结构特征，并将特征与相应的表征手段（Evidence）关联。
输入：文献全文（重点关注 Results & Discussion, Figure Captions）、目标样本列表。

提取流程：

1.  **形貌与尺寸 (Morphology & Dimensions)**：
    * 描述：形状（纳米线/片/球/管）、表面状态（粗糙/多孔/核壳结构）。
    * 定量：粒径、层厚、孔径、比表面积（BET）。**必须包含数值和单位**。
    * 证据：SEM, TEM, AFM, BET。

2.  **晶体与化学结构 (Crystal & Chemical Structure)**：
    * 晶相：物相组成（Phase）、晶格条纹间距（Lattice spacing）、晶面（Crystal plane）。
    * 化学环境：价态、官能团、化学键。
    * 证据：XRD, HRTEM, SAED, XPS, FTIR, Raman。

3.  **元素分布与缺陷 (Composition & Defects)**：
    * 分布：均匀分布、元素偏析、掺杂位置。
    * 缺陷：氧空位、晶格畸变。
    * 证据：EDS/Mapping, EPR, XAFS。

输出格式示例（JSON）：
```json
{
    "g-C3N4/TiO2": {
        "Morphology_Dimensions": {
            "Description": "2D nanosheets decorated with 0D nanoparticles",
            "Size_Data": ["TiO2 diameter: 20-30 nm", "g-C3N4 thickness: ~4 nm"],
            "Evidence": "TEM, AFM"
        },
        "Crystal_Structure": {
            "Phase": "Anatase TiO2 and Graphitic C3N4",
            "Lattice_Spacing": "0.35 nm (101 plane of TiO2)",
            "Evidence": "XRD, HRTEM"
        },
        "Chemical_State": {
            "Surface_Chemistry": "Formation of Ti-O-C bonds",
            "Evidence": "XPS (O 1s spectra)"
        }
    }
}
```
"""

# --------------------------------------------------------------------------------
# 模块 4：性能评估 (Performance Evaluation)
# --------------------------------------------------------------------------------
# 优化点：
# 1. 增加了“Application_Field”以明确上下文（是电池还是催化？）。
# 2. 增加了“Comparison”字段：明确要求提取该材料相对于对照组的性能提升。
# 3. 强制区分“Value”（数值）、“Unit”（单位）和“Error”（误差）。

prompt_1_4 = """
角色设定：材料性能评估与数据提取专家
任务：提取材料的关键性能指标（KPIs），并关联测试条件与对比数据。
输入：文献全文（关注 Results, Table, Conclusion）、目标样本列表。

提取流程：

1.  **应用领域识别 (Application)**：
    * 明确该材料的应用场景（如：Lithium-ion Battery, HER Electrocatalysis, Photodegradation, Tensile Strength）。

2.  **关键指标提取 (KPI Extraction)**：
    * 提取该领域的核心指标（如：比容量、循环寿命、过电势、降解率、杨氏模量）。
    * **格式要求**：
        * `Metric`: 指标名称。
        * `Value`: 具体数值。
        * `Unit`: 单位。
        * `Error`: 误差范围/标准差（如有，否则为 null）。

3.  **测试条件绑定 (Test Conditions)**：
    * 该数据是在何种条件下获得的？（如：电流密度 1 A/g, 光照 AM 1.5G, pH 7, 循环100圈后）。

4.  **性能对比 (Comparison)**：
    * 如果文中提及，提取该样本相对于对照组（Control）的性能提升描述（如 "2.5 times higher than pure TiO2"）。

输出格式示例（JSON）：
```json
{
    "Sample-Optimized": {
        "Application_Field": "Electrocatalysis (HER)",
        "Performance_Data": [
            {
                "Metric": "Overpotential",
                "Value": 120,
                "Unit": "mV",
                "Error": null,
                "Condition": "at 10 mA/cm², 0.5 M H2SO4",
                "Comparison_Ref": "50 mV lower than Control Group"
            },
            {
                "Metric": "Tafel Slope",
                "Value": 45,
                "Unit": "mV/dec",
                "Error": "± 2",
                "Condition": "Linear Sweep Voltammetry",
                "Comparison_Ref": null
            }
        ]
    }
}
"""

#markdown kv 可能是一种压缩的好方法