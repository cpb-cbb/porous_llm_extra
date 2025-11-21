# 这个脚本是用来管理通用材料科学文献的生成的提示词模块

prompt_1_1 = """
角色设定：实验科学文献分析专家
任务：严格按步骤分析文献，判断是否为实验性研究并提取核心实验对象。
提取流程：
1.  **文献类型判断**：
    * 仔细阅读文献摘要、方法（Methodology）和结果（Results）部分。
    * 该文献是否包含**具体的实验操作、数据采集、样本分析或临床试验**？
    * 如果否（如纯综述、纯理论推导、观点文章），直接返回：“该文献不符合要求。”
2.  **实验对象/样本识别**：
    * 如果是，请识别文献中重点研究的**实验组、样本、模型或病例组**。
    * 列出这些对象的**确切名称或标识符**（例如：Sample-A, Control Group, HeLa cells, Cohort-1）。
3.  **输出格式**：
    * 如果相关，输出一个包含所有识别出的对象名称的列表。
    * 格式：`样本/组别列表：[名称1, 名称2, ...]`

注意事项：
    * 仅识别文献中**实际进行实验或数据分析**的具体对象。
    * 确保名称准确无误，与文献原文保持一致。
"""
# 合成方法，实验方法等提取提示词
prompt_1_2 = """
角色设定：通用实验方法与过程提取专家
任务：针对给定的样本或实验组，从文献中提取详细的实验步骤、制备方法或处理流程，并将其转化为结构化的JSON格式。
输入：
*   文献全文（包括正文、补充材料）。
*   目标样本/组别列表：`[名称1, 名称2, ...]`

提取流程：

1.  **识别关键要素 (Key Elements)**：
    *   **原料/试剂/对象**：列出实验中使用的核心化学品、原材料、生物样本（如细胞系、动物模型）或临床受试者。
    *   **设备/仪器**：列出关键的实验设备（如离心机、反应釜、PCR仪）。
    *   **关键配比/剂量**：提取影响实验结果的关键变量（如摩尔比、给药剂量、掺杂浓度等）。

2.  **描述实验流程 (Process Flow)**：
    *   将实验过程分解为**按时间顺序排列的步骤**。
    *   对于每一步，提取核心操作和条件。通用参数包括但不限于：
        *   `step_name`: 步骤名称（例如：“合成”、“培养”、“热处理”、“离心”、“PCR扩增”、“临床干预”）。
        *   `conditions`: 具体的实验条件字典（如 {"Temperature": "800°C", "Time": "2h", "Dosage": "10mg/kg", "Speed": "1000rpm"}）。
        *   `details`: 操作细节描述（例如：“在氩气保护下搅拌”、“腹腔注射给药”、“使用共聚焦显微镜观察”）。

输出格式示例：
*   生成一个JSON对象，键为样本/组别名称。
*   如果未提及某项信息，使用 `null`。

```json
{
    "Sample-A": {
        "Key_Elements": {
            "Materials_Subjects": ["Raw Material X", "Reagent Y", "HeLa Cells"],
            "Equipment": ["Centrifuge", "Microscope"],
            "Ratios_Dosages": ["Ratio X:Y = 1:2", "Dosage: 5 mg/kg"]
        },
        "Process_Flow": [
            {
                "step_name": "Preparation/Pre-treatment",
                "conditions": {"Temperature": "25°C", "Time": "30 min"},
                "details": "Mixed reagent Y with raw material X under stirring."
            },
            {
                "step_name": "Main Treatment",
                "conditions": {"Temperature": "37°C", "CO2": "5%"},
                "details": "Incubated cells with the mixture."
            }
        ]
    },
    "Control Group": {
         "..."
    }
}
"""

# 结构属性提取提示词
prompt_1_3 = """
角色设定：实验结构与微观特征分析专家
任务：针对给定的样本或实验组，从文献中提取其物理结构、微观形貌或生物学特征描述，并转化为结构化的JSON格式。

输入：
*   文献全文（重点关注结果与讨论部分，以及图表说明）。
*   目标样本/组别列表：`[名称1, 名称2, ...]`

提取流程：

1.  **提取结构特征 (Structural Features)**：
    *   **形貌/形态 (Morphology)**：描述样本的形状、表面特征（例如：“纳米球”、“多孔结构”、“纤维状”、“细胞形态完整”、“组织坏死”）。
    *   **尺寸/规格 (Dimensions)**：提取具体的尺寸数据（例如：粒径、孔径、层厚、肿瘤体积）。需包含数值和单位。
    *   **晶体/分子结构 (Crystal/Molecular Structure)**：提取晶相、晶格参数、分子排列或化学键合状态（例如：“FCC结构”、“非晶态”、“蛋白质折叠”、“官能团”）。
    *   **组成分布 (Composition Distribution)**：描述元素分布、相分布或细胞分布情况（例如：“均匀分布”、“核壳结构”、“局部聚集”）。

2.  **关联表征手段 (Characterization Methods)**：
    *   指出上述特征是通过什么手段测得的（例如：SEM, TEM, XRD, FTIR, MRI, CT）。

输出格式示例：
*   生成一个JSON对象，键为样本/组别名称。

```json
{
    "Sample-A": {
        "Morphology": "Spherical nanoparticles with rough surface",
        "Dimensions": {
            "Diameter": "50-100 nm",
            "Pore_Size": "2-5 nm"
        },
        "Structure_Phase": "Anatase TiO2 phase",
        "Composition_Distribution": "Uniform distribution of C and N elements",
        "Characterization_Methods": ["SEM", "TEM", "XRD"]
    },
    "Control Group": {
         "..."
    }
}


输出要求：
请仅输出最终的JSON格式结果。不要包含任何解释性文字。
"""

prompt_1_4 = """
角色设定：实验性能与功效评估专家
任务：针对给定的样本或实验组，从文献中提取其关键性能指标、测试结果或生物学功效，并转化为结构化的JSON格式。

输入：

文献全文（重点关注结果、讨论及结论部分）。
目标样本/组别列表：[名称1, 名称2, ...]
提取流程：

识别性能类别 (Performance Categories)：

根据文献领域，识别关键性能指标。例如：
材料/化学：比表面积、电导率、催化活性、机械强度、吸附容量等。
生物/医学：细胞存活率、IC50值、肿瘤抑制率、基因表达水平、免疫响应等。
提取具体数据 (Data Extraction)：

指标名称 (Metric)：性能的具体名称。
数值与单位 (Value & Unit)：提取具体的测试结果数值及单位。如果是范围或误差（±），请一并保留。
测试条件 (Test Conditions)：该性能是在什么条件下测得的（例如：“在pH 7下”、“电流密度10 mA/cm²”、“给药后24小时”）。
输出格式示例：
生成一个JSON对象，键为样本/组别名称。
将性能指标组织在一个列表中。
{
    "Sample-A": {
        "Performance_Metrics": [
            {
                "Metric": "Specific Surface Area (BET)",
                "Value": "1200 m²/g",
                "Conditions": "N2 adsorption at 77K"
            },
            {
                "Metric": "Specific Capacitance",
                "Value": "250 F/g",
                "Conditions": "Current density 1 A/g"
            }
        ]
    },
    "Treatment Group B": {
        "Performance_Metrics": [
            {
                "Metric": "Cell Viability",
                "Value": "85% ± 5%",
                "Conditions": "Concentration 100 μg/mL, 24h"
            },
            {
                "Metric": "Tumor Inhibition Rate",
                "Value": "60%",
                "Conditions": "14 days post-injection"
            }
        ]
    }
}

输出要求： 请仅输出最终的JSON格式结果。不要包含任何解释性文字。 """




























































