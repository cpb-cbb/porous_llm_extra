# -*- coding: utf-8 -*-
"""
This script stores the prompts for the multi-step information extraction
process for porous carbon material literature.
"""

# --- Step 1.1: Document Relevance & Sample Identification ---
# --- 步骤 1.1: 文献筛选与样本识别 ---
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

# --- Step 1.2: Synthesis Details Extraction ---
# --- 步骤 1.2: 合成细节提取 ---
prompt_1_2 = """
角色设定：材料合成信息提取专家
任务：针对上一步识别出的每个样本，从文献中精准提取其制备信息。确保包含所有前驱体组分和特殊处理步骤。
输入：
    * 文献全文（包括支撑信息）。
    * 上一步输出的样本列表：`[样本名称1, 样本名称2, ...]`
提取流程：
1.  **定位信息**：对于列表中的**每一个**样本名称，在文献（特别是实验方法部分和支撑信息）中查找其详细制备过程。
2.  **提取关键参数**：为每个样本提取以下信息：
    * **前驱体**：（例如：酚醛树脂、蔗糖、生物质名称、聚合物名称、复合材料组分如 "石墨烯/Fe3O4 混合物"）。**必须列出所有组分**。
    * **活化剂**：（例如：KOH, ZnCl₂, H₃PO₄, CO₂, H₂O；注明种类和可能的状态/浓度）。
    * **碳化温度**：（单位：℃；可能是多步，注明关键步骤温度或范围）。
    * **模板剂**：（例如：SiO₂ 纳米球, MOF, SBA-15；如果未使用，注明“无”）。
    * **其他特殊工艺**：（例如：预氧化、酸洗、碱蚀刻、二次活化、掺杂步骤、等离子体处理、球磨、表面官能化等）。**详细描述方法和关键参数（温度、时间、气氛等）**。
3.  **输出格式**：
    * 为每个样本生成一个信息记录。
    * 格式：
        样本名称1: {前驱体: ${值}$, 活化剂: ${值}$, 碳化温度: ${值}$℃, 模板剂: ${值}$, 其他工艺: ${值}$};
        样本名称2: {前驱体: ${值}$, 活化剂: ${值}$, 碳化温度: ${值}$℃, 模板剂: ${值}$, 其他工艺: ${值}$};
        ...

注意事项：
    * 确保信息与正确的样本名称对应。
    * 如果文献中未提及某个特定信息，使用“未提及”或“N/A”。
    * 碳化温度可能涉及多个步骤，提取最关键的温度或范围。
    * **务必检查支撑信息 (SI)**。
"""

# --- Step 1.3: Physical & Chemical Properties Extraction ---
# --- 步骤 1.3: 物化性质提取 ---
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
    * **总孔体积**：（单位：cm³/g；通常来自 N₂ 吸附在高 P/P₀ 处）
    * **微孔体积**：（单位：cm³/g；注明计算方法，如 DFT, t-plot）
    * **介孔体积**：（单位：cm³/g；可通过总量减微孔或由 BJH/DFT 计算得到）
    * **主孔径范围/分布描述**：（nm；例如 "主要分布在 0.5-2 nm"，"存在 <2 nm 和 2-5 nm 的双峰"）
    * **平均孔径**：（nm；如果文献提供）
3.  **提取表面化学与晶体结构参数**：
    * **掺杂元素含量分析 (XPS)**：（列出检测到的**所有元素**及其原子百分比(at%)或质量百分比(wt%)，如 C: 85 at%, O: 10 at%, N: 5 at%, Fe: 0.5 wt%）。**必须注明是at%还是wt%（如果文献提供）**。
    * **官能团 (FTIR)**：（列出识别出的主要官能团，如 -COOH, -OH, C=O, C-N）。如果提供定量信息，也一并提取。
    * **石墨化程度 (Raman)**：（提取 ID/IG 比值）
    * **XRD (002) 层间距**：（提取 d₀₀₂ 值，单位：nm）
4.  **输出格式**：
    * 为每个样本生成一个信息记录。
    * 格式：
        样本名称1: {BET总比表面积: ${值}$ m²/g, 微孔比表面积: ${值}$ m²/g (${方法}$), 总孔体积: ${值}$ cm³/g, 微孔体积: ${值}$ cm³/g (${方法}$), 介孔体积: ${值}$ cm³/g, 孔径分布: ${描述}$, 平均孔径: ${值}$ nm, 元素含量: {C:${值}$%, O:${值}$%, N:${值}$%, Fe:${值}$%, ...}, 官能团: [${团1}$, ${团2}$, ...], ID/IG: ${值}$, d002间距: ${值}$ nm};
        样本名称2: {BET总比表面积: ...};
        ...

注意事项：
    * 确保数据与正确的样本名称对应。
    * 如果数据来自图表，需准确读图。
    * 单位必须提取。
    * 如果文献中未提及某个特定信息，使用“未提及”或“N/A”。
    * 注意区分不同计算方法得出的孔隙参数。
    * **务必检查支撑信息 (SI)**。
    * 注意提取比较性描述中的数值（例如，“样本B是样本A的两倍，后者为X”）。
"""

# --- Step 1.4: Electrochemical Performance Extraction ---
# --- 步骤 1.4: 电化学性能提取 ---
prompt_1_4 = """
角色设定：电化学性能数据提取专家
任务：针对指定的样本列表，从文献（包括正文、图表、表格、支撑信息）中精准提取电化学性能数据及其测试条件。
输入：
    * 文献全文（包括图表、表格、支撑信息）。
    * 样本列表：`[样本名称1, 样本名称2, ...]`
提取流程：
1.  **定位信息**：对于列表中的**每一个**样本名称，在文献（电化学测试、结果与讨论、图表、表格、支撑信息）中查找其电化学性能数据。同时，查找通用的测试条件。
2.  **提取通用测试条件**：（这些条件通常对一组实验或所有实验适用）
    * **电极系统类型**：（例如 “三电极”, “二电极/对称器件/全电池”）
    * **电解液**：（例如 “6M KOH”, “1M H₂SO₄”, “EMIMBF₄”）
    * **电压窗口**：（V；区分三电极和二电极的窗口，如果不同）
3.  **提取特定性能指标**：为每个样本提取以下性能数据，并**注明关键测试条件**（如电流密度、扫描速率或功率/能量密度）：
    * **比电容**：（单位：F/g；必须包含对应的电流密度或扫描速率，例如 "320 F/g @ 1 A/g", "250 F/g @ 10 mV/s"）。可能报告多个值，提取代表性值（如最低电流密度下的值，或文献强调的值，或一个范围）。
    * **最高能量密度**：（单位：Wh/kg；通常针对二电极体系报告，需注明对应的功率密度或计算条件）。
    * **最高密度**：（单位：W/kg；通常针对二电极体系报告，需注明对应的能量密度）。
    * **循环稳定性**：（提供循环圈数和容量保持率%，例如 "10000次循环后保持率95%"）。
    * **EIS（交流阻抗）**：
        * **ESR（等效串联电阻）**：（单位：Ω；通常是奈奎斯特图在高频区与实轴的截距）。
        * **Rct（电荷转移电阻）**：（单位：Ω；通常是奈奎斯特图中半圆的直径）。
    * **（可选）电导率**：（单位：S/cm 或 S/m；如果文献提供）。
4.  **输出格式**：
    * 先输出通用测试条件，然后为每个样本生成一个信息记录。
    * 格式：
        通用测试条件: {电极系统: ${类型}$, 电解液: ${值}$, 三电极电压窗口: ${值}$ V, 二电极电压窗口: ${值}$ V};
        样本名称1: {比电容: ["${值1}$ F/g @ ${条件1}$", "${值2}$ F/g @ ${条件2}$"], 能量密度: "${值}$ Wh/kg @ ${条件}$", 功率密度: "${值}$ W/kg @ ${条件}$", 循环稳定性: "${圈数}$次, ${保持率}$%", ESR: ${值}$ Ω, Rct: ${值}$ Ω, 电导率: ${值}$ S/cm};
        样本名称2: {比电容: ..., 能量密度: ..., ...};
        ...

注意事项：
    * 确保数据与正确的样本名称对应。
    * 性能指标必须与其测试条件关联。
    * 区分三电极和二电极（器件）的测试结果和条件。
    * 如果文献中未提及某个特定信息，使用“未提及”或“N/A”。
    * **务必检查支撑信息 (SI)**。
"""

# --- Step 2: Data Structuring ---
# --- 步骤 2: 数据结构化 ---
prompt_2 = """
Role Setting
You are a database construction expert responsible for consolidating and structuring extracted material science data into a JSON format.
Task Steps
1.  **Input Consolidation**: Receive structured information pieces about samples covering:
    * Sample names (from Step 1.1 output)
    * Synthesis details (structured text/dict from Step 1.2 output)
    * Physical/Chemical properties (structured text/dict from Step 1.3 output)
    * Electrochemical performance and general conditions (structured text/dict from Step 1.4 output)
2.  **Data Format Standardization**:
    * Numerical data: `{"value": number, "unit": "unit"}`. If unit is implicitly defined (e.g., ID/IG ratio), use `{"value": number}`. Handle percentages similarly. If unit is at% or wt%, include it in the unit field.
    * Range values: `{"value": [min_value, max_value], "unit": "unit"}` or describe textually if complex.
    * Data with conditions (like Specific Capacitance): Use a list if multiple values reported `[{"value": number, "unit": "F/g", "condition": {"value": number, "unit": "A/g or mV/s"}}, ...]`. Adapt unit in condition. Similar structure for Energy/Power density if conditions apply.
    * Cycle Stability: `{"Cycle Number": {"value": number}, "Capacity Retention": {"value": number, "unit": "%"}}`
    * Element Content: Format as a dictionary `{"ElementSymbol": {"value": number, "unit": "% or at% or wt%"}, ...}`. Use the unit provided in the input (at% or wt% if available, otherwise just %).
    * Functional Groups: List of strings `["-COOH", "-OH", ...]`.
    * Missing data or "未提及"/"N/A": Represent as `null`.
3.  **Information Structuring**: Organize data for *each sample* into a JSON object following this schema. Merge information from all previous steps for the corresponding sample. Incorporate general testing conditions into each relevant sample's record. Check for basic consistency if possible (e.g., pore volumes).

```json
[
  {
    "Sample Name": "Sample Name", // From 1.1
    "Preparation": { // From 1.2
        "Precursors": ["Material 1", "Composite Component 2", ...], // List
        "Activator": "Activator Name or List",
        "Carbonization Temperature": {"value": number or [num1, num2], "unit": "℃"},
        "Template": "Template Name or null",
        "Other Process": "Description of special treatments or null"
    },
    "Physical Chemical Properties": { // From 1.3
        "Specific Surface Area (BET)": {"value": number, "unit": "m²/g"},
        "Micropore Specific Surface Area": {"value": number, "unit": "m²/g", "method": "DFT/t-plot/etc or null"},
        "Total Pore Volume": {"value": number, "unit": "cm³/g"},
        "Micropore Volume": {"value": number, "unit": "cm³/g", "method": "DFT/t-plot/etc or null"},
        "Mesopore Volume": {"value": number, "unit": "cm³/g"}, // Can be null
        "Pore Size Distribution Description": "Textual description or range or null",
        "Average Pore Diameter": {"value": number, "unit": "nm"}, // Can be null
        "Element Content (XPS)": {"C": {"value": num, "unit": "%/at%/wt%"}, "O": {"value": num, "unit": "%/at%/wt%"}, /* ... other elements ... */}, // Use provided unit
        "Surface Functional Groups (FTIR)": ["-COOH", "-OH", ...] or null,
        "Degree of Graphitization (Raman ID/IG)": {"value": number} or null,
        "Interlayer Spacing (XRD d002)": {"value": number, "unit": "nm"} or null
    },
    "Electrochemical Performance": { // From 1.4
        "Electrode System Type": "Three-electrode / Two-electrode / etc.",
        "Electrolyte": "Electrolyte Name and Concentration",
        "Voltage Window": {"value": [min, max], "unit": "V"}, // Specify if 3-electrode or 2-electrode window if different and known
        "Specific Capacitance": [{"value": number, "unit": "F/g", "condition": {"value": number, "unit": "A/g or mV/s"}}, ... ] or null, // List format
        "Energy Density": {"value": number, "unit": "Wh/kg", "condition": "optional condition e.g. @ X W/kg"} or null,
        "Power Density": {"value": number, "unit": "W/kg", "condition": "optional condition e.g. @ Y Wh/kg"} or null,
        "Cycle Stability": {"Cycle Number": {"value": number}, "Capacity Retention": {"value": number, "unit": "%"}} or null,
        "Equivalent Series Resistance (ESR)": {"value": number, "unit": "Ω"} or null,
        "Charge Transfer Resistance (Rct)": {"value": number, "unit": "Ω"} or null,
        "Conductivity": {"value": number, "unit": "S/cm or S/m"} or null
        // Add optional "notes" field if needed for qualitative info or ambiguity
    }
  },
  // ... other samples
]
```
Direct Output Requirements:
    •   Output only the final JSON result, without any additional text.
    •   Separate multiple materials into individual JSON objects within the main list.
    •   Ensure clarity and completeness while avoiding unnecessary verbosity. Use `null` for missing data.
"""

# Example of how to access a prompt
# print("--- Prompt for Step 1.1 ---")
# print(prompt_1_1)

# You can add functions here to manage or select prompts if needed.
# For example:
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

# Example usage of the function:
# print(get_prompt("1.2"))

