# -*- coding: utf-8 -*-
"""
This script stores the optimized prompts for the multi-step information extraction
process for porous carbon material literature for supercapacitors.
Version 3.0 (Refined based on discussion)
"""

# --- Step 1.1: Document Relevance & Sample Identification ---
# --- 步骤 1.1: 文献筛选与样本识别 ---
# This prompt remains unchanged as its function is well-defined and effective.
prompt_1_1 = """
角色设定：文献筛选与样本识别专家
任务：严格按步骤分析文献，判断相关性并提取关键样本信息。
提取流程：
1.  **文献相关性判断**：
    * 仔细阅读文献摘要、引言和实验部分。
    * 该文献是否研究或合成了**用于超级电容器的多孔碳材料**？
    * 如果否，直接返回：“该文献不符合要求。”
2.  **样本识别**：
    * 如果是，请识别文献中明确合成并表征的**所有**多孔碳材料样本。
    * 列出这些样本的**确切名称**（例如：PC-800, NPC-2, AC-KOH-900）。
3.  **输出格式**：
    * 如果相关，输出一个包含所有识别出的样本名称的列表。
    * 格式：`样本列表：[样本名称1, 样本名称2, ...]`

注意事项：
    * 仅识别文献中**实验研究合成**的样本。
    * 确保样本名称准确无误，与文献保持一致。
"""

# --- Step 1.2: Synthesis & Preparation Conditions Extraction (Refined) ---
# --- 步骤 1.2: 合成与制备条件提取 (优化) ---
prompt_1_2 = """
角色设定：材料合成信息提取专家
任务：针对上一步识别出的每个样本，从文献中精准提取其合成与制备条件。
输入：
    * 文献全文（包括支撑信息）。
    * 上一步输出的样本列表：`[样本名称1, 样本名称2, ...]`
提取流程：
1.  **定位信息**：对于列表中的**每一个**样本名称，在文献（特别是实验方法部分和支撑信息）中查找其详细制备过程。
2.  **提取关键参数**：为每个样本提取以下信息：
    * **前驱体 (Precursor)**：必须列出所有组分（例如：酚醛树脂、蔗糖、豆渣、聚合物名称）。
    * **活化剂 (Activator)**：注明种类（例如：KOH, ZnCl₂, CO₂, H₂O）。如果未用，注明“无”。
    * **活化剂/前驱体质量比 (Activator/Precursor Ratio)**：例如 1:1, 4:1。
    * **热解/碳化温度 (Pyrolysis/Carbonization Temp.)**：单位 ℃。如果是多步，注明关键步骤温度。
    * **活化温度 (Activation Temp.)**：单位 ℃。
    * **活化时间 (Activation Time)**：单位 h (小时)。
    * **升温速率 (Heating Rate)**：单位 ℃/min 或 K/min。
    * **气体气氛与流速 (Gas Atmosphere & Flow Rate)**：分别提取气体类型和流速。例如：{气体类型: "N₂", 流速: "200 mL/min"}。
    * **模板剂 (Template)**：例如 SiO₂, MOF, SBA-15。如果未使用，注明“无”。
    * **其他特殊工艺 (Other Process)**：例如 预氧化、酸洗、掺杂步骤、等离子体处理等，并描述关键参数。
3.  **输出格式**：
    * 为每个样本生成一个信息记录。
    * 格式：
        样本名称1: {前驱体: ${值}$, 活化剂: ${值}$, 活化剂/前驱体质量比: ${值}$, 热解/碳化温度: ${值}$℃, 活化温度: ${值}$℃, 活化时间: ${值}$h, 升温速率: ${值}$℃/min, 气体气氛与流速: {气体类型: "${值}$", 流速: "${值}$"}, 模板剂: ${值}$, 其他工艺: ${值}$};
        样本名称2: {前驱体: ${值}$, 活化剂: ${值}$, ...};
        ...

注意事项：
    * 确保信息与正确的样本名称对应。
    * 如果文献中未提及某个特定信息，使用“未提及”。
    * **务必检查支撑信息 (SI)**。
"""

# --- Step 1.3: Physical & Chemical Properties Extraction (Refined) ---
# --- 步骤 1.3: 物化性质提取 (优化) ---
prompt_1_3 = """
角色设定：材料物化性质分析专家
任务：针对指定的样本列表，从文献（包括正文、图表、表格、支撑信息）中精准提取物理化学性质数据。
输入：
    * 文献全文（包括图表、表格、支撑信息）。
    * 样本列表：`[样本名称1, 样本名称2, ...]`
提取流程：
1.  **定位信息**：对于列表中的**每一个**样本名称，在文献（结果与讨论、图表、表格、支撑信息）中查找其物理化学性质数据。
2.  **提取结构与孔隙参数**：
    * **BET 总比表面积**：（单位：m²/g）
    * **微孔比表面积**：（单位：m²/g；注明计算方法，如 DFT, t-plot）
    * **总孔体积**：（单位：cm³/g）
    * **微孔体积**：（单位：cm³/g；注明计算方法，如 DFT, t-plot）
    * **介孔体积**：（单位：cm³/g）
    * **孔径分布描述**：（nm；从孔径分布图中总结。例如 "主要分布在 0.5-2 nm"，"存在 <2 nm 和 2-5 nm 的双峰"）
3.  **提取表面化学与晶体结构参数**：
    * **掺杂元素含量分析 (XPS)**：列出检测到的**所有元素**及其原子百分比(at%)或质量百分比(wt%)。**如果文献提供了具体成键状态的含量（例如 Pyridinic-N/N-6, Pyrrolic-N/N-5, Graphitic-N/N-Q, Oxidized-N/N-X），也必须一并提取并使用标准名称（N_PYRIDINIC, N_PYRROLIC, N_GRAPHITIC, N_OXIDIZED）进行记录**。例如：{N: 5 at% (其中 N_PYRIDINIC: 60%, N_PYRROLIC: 30%, N_GRAPHITIC: 10%), O: 10 at%, C: 85 at%}。
    * **官能团 (FTIR)**：列出识别出的主要官能团，如 -COOH, -OH, C=O, C-N。
    * **石墨化程度 (Raman)**：提取 ID/IG 比值。
4.  **输出格式**：
    * 为每个样本生成一个信息记录。
    * 格式：
        样本名称1: {BET总比表面积: ${值}$ m²/g, 微孔比表面积: ${值}$ m²/g (${方法}$), 总孔体积: ${值}$ cm³/g, 微孔体积: ${值}$ cm³/g (${方法}$), 介孔体积: ${值}$ cm³/g, 孔径分布: ${描述}$, 元素含量: {C:${值}$%, O:${值}$%, N:${值}$% (N_PYRIDINIC:${...}$%, N_PYRROLIC:${...}$%)}, 官能团: [${团1}$, ${团2}$], ID/IG: ${值}$};
        样本名称2: {BET总比表面积: ...};
        ...

注意事项：
    * 确保数据与正确的样本名称对应。
    * 单位必须提取。
    * 如果文献中未提及某个特定信息，使用“未提及”。
    * **务必检查支撑信息 (SI) 和图表**。
"""

# --- Step 1.4: Electrochemical Performance Extraction (Major Overhaul) ---
# --- 步骤 1.4: 电化学性能提取 (重大修改) ---
prompt_1_4 = """
角色设定：电化学性能数据提取专家
任务：为每个样本提取在**不同测试体系**下的电化学性能。这是一个关键步骤，要求将性能数据与其特定的测试条件严格绑定。

输入：
* 文献全文（包括图表、表格、支撑信息）。
* 样本列表：`[样本名称1, 样本名称2, ...]`

提取流程：
1.  **识别测试体系 (Identify Test Systems)**：
    * 对于列表中的**每一个**样本，识别文献中所有独立的电化学测试体系。
    * 一个独立的“测试体系”由 **【系统类型】**、**【电解液】** 和 **【电压窗口】** 共同定义。
    * 例如："三电极, 6M KOH, [-1, 0] V" 和 "二电极对称器件, 1M Na₂SO₄, [0, 2] V" 是两个独立的测试体系。

2.  **提取体系内数据 (Extract Data within Each System)**：
    * 对于你识别出的**每一个测试体系**，提取以下所有相关信息：
    * **系统类型 (SystemType)**：例如 "Three-electrode", "Two-electrode symmetric", "Two-electrode asymmetric"。
    * **电解液 (Electrolyte)**：例如 "6M KOH", "1M H2SO4", "EMIMBF4"。
    * **电压窗口 (VoltageWindow)**：例如 "[-1, 0] V", "[0, 1.8] V"。
    * **电极信息 (Electrode Info)**：
        * **活性物质负载 (MassLoading)**：单位 mg/cm²。务必尽力查找。
        * **电极组分 (Composition)**：提取活性物质(Active Material)、粘合剂(Binder)、导电剂(Conductive Agent)的**具体名称和质量百分比(wt%)**。例如：{ActiveMaterial: 80 wt%, Binder: {name: "PTFE", value: 10 wt%}, ConductiveAgent: {name: "Super P", value: 10 wt%}}。
    * **比电容 (SpecificCapacitance)**：**仅在三电极体系中提取**。必须包含类型(gravimetric/areal)、计算方法(GCD/CV)和对应的条件(电流密度 A/g 或扫描速率 mV/s)。以列表形式提供所有报道的数据点。
    * **能量/功率密度 (Energy/Power Density)**：**仅在二电极（器件）体系中提取**。从Ragone图中提取**最大能量密度 (MaxEnergyDensity)** 和 **最大功率密度 (MaxPowerDensity)**，并注明其对应的功率或能量密度条件。
    * **循环稳定性 (CycleStability)**：提取圈数、容量保持率，并注明测试时的电流密度或扫描速率。
    * **阻抗 (Impedance)**：从奈奎斯特图(Nyquist plot)的图表或正文中提取等效串联电阻(ESR)和电荷转移电阻(Rct)，单位 Ω。

3.  **输出格式 (Output Format)**：
    * 为每个样本生成一个包含其所有测试体系的列表。
    * 格式：
        样本名称1: [
            {
                SystemType: "Three-electrode",
                Electrolyte: "6M KOH",
                VoltageWindow: "[-1, 0] V",
                MassLoading: "${值}$ mg/cm²",
                Composition: {ActiveMaterial: ${80}$ wt%, Binder: {name: "${名称}$", value: ${10}$ wt%}, ConductiveAgent: {name: "${名称}$", value: ${10}$ wt%}},
                SpecificCapacitance: [{type: "gravimetric", method: "GCD", value: ${值1}$, unit: "F/g", condition: "${值}$ A/g"}, {type: "gravimetric", method: "CV", value: ${值2}$, unit: "F/g", condition: "${值}$ mV/s"}],
                CycleStability: "${圈数}$次, ${保持率}$% @ ${条件}$",
                Impedance: {ESR: ${值}$ Ω, Rct: ${值}$ Ω}
            },
            {
                SystemType: "Two-electrode symmetric",
                Electrolyte: "1M Na2SO4",
                VoltageWindow: "[0, 2] V",
                MassLoading: "未提及",
                Composition: "未提及",
                MaxEnergyDensity: "${值}$ Wh/kg @ ${功率密度}$ W/kg",
                MaxPowerDensity: "${值}$ W/kg @ ${能量密度}$ Wh/kg",
                CycleStability: "未提及"
            }
        ];
        样本名称2: [ ... ];
        ...
注意事项：
* 严格区分三电极和二电极体系的数据。
* 如果文献未提及某个信息，使用“未提及”。
* **务必检查支撑信息(SI)和所有图表以获取详细参数。**
"""

# --- Step 2: Data Structuring (Major Overhaul) ---
# --- 步骤 2: 数据结构化 (重大修改) ---
prompt_2 = """
Role Setting:
You are a database construction expert responsible for consolidating and structuring extracted material science data into a clean, machine-readable JSON format based on a strict schema.

Task Steps:
1.  **Input Consolidation**: You will receive multiple pieces of structured text about one or more material samples. These pieces cover:
    * Sample names (from Step 1.1)
    * Synthesis & Preparation Conditions (from Step 1.2)
    * Physical & Chemical Properties (from Step 1.3)
    * Electrochemical Performances, detailed across different test systems (from Step 1.4)

2.  **Data Structuring and Standardization**:
    * **Numerical Data**: For any value with a unit, structure it as `{"value": number, "unit": "unit_string"}`. For ratios or unitless values, use `{"value": number}`.
    * **Conditional Data**: Structure data points that depend on a condition (like Specific Capacitance) as a list of objects, where each object contains the value and its corresponding condition.
    * **Missing Data**: If a piece of information is marked as "未提及" or is not available, represent it as `null` in the final JSON.
    * **Consistency**: Ensure all placeholder keys (e.g., `MaxEnergyDensity`, `SpecificCapacitance`) are present in every test system object, even if their value is `null`. This maintains a consistent schema.

3.  **JSON Schema Application**:
    * For each sample, construct a single JSON object.
    * Combine all sample objects into a single JSON list `[...]`.
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
          {"type": "gravimetric", "method": "GCD", "value": 346, "unit": "F/g", "condition": {"value": 1, "unit": "A/g"}},
          {"type": "gravimetric", "method": "GCD", "value": 250, "unit": "F/g", "condition": {"value": 20, "unit": "A/g"}},
          {"type": "gravimetric", "method": "CV", "value": 350, "unit": "F/g", "condition": {"value": 5, "unit": "mV/s"}}
        ],
        "CycleStability": {"CycleNumber": {"value": 10000}, "CapacityRetention": {"value": 97.5, "unit": "%"}, "condition": {"value": 10, "unit": "A/g"}},
        "EquivalentSeriesResistance_ESR": {"value": 0.5, "unit": "Ω"},
        "ChargeTransferResistance_Rct": {"value": 1.2, "unit": "Ω"}
      },
      {
        "SystemType": "Two-electrode symmetric",
        "Electrolyte": "1M Na2SO4",
        "VoltageWindow": {"value": [0, 2], "unit": "V"},
        "Electrode": {"MassLoading": null, "Composition": null},
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
# print("--- Optimized Prompt for Step 1.4 ---")
# print(get_prompt("1.4"))
# print("\n--- Optimized Prompt for Step 2 ---")
# print(get_prompt("2"))
