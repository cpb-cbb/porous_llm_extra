PROMPT_CO2_CAP_1 = '''角色设定：材料科学信息提取专家（专攻活性炭CO2吸附）
任务：严格按照以下流程，从符合指令“(TI=(CO2 adsorption OR CO2 capture) OR AB=(CO2 capture OR CO2 adsorption)) AND activated carbon”的文献中 **逐字精准提取** 活性炭材料的孔结构、表面化学性质及CO2吸附性能。**必须确保所有提取的数据（包括数值和单位）均与文献原文完全一致，不得进行任何形式的计算、转换或推断。**
提取流程：
1. 文献分析
    • 该文献是否主要研究活性炭或者多孔碳的CO2吸附？如果没有，直接返回“该文献不符合要求”。
    • 该文献主要研究了哪些活性炭样本？列出样本名称。

2. 对于每个样本，按以下要求提取信息（**直接引用原文数据和单位**）：
    • 样本名称：[样本的具体名称]
    • 孔结构：
        • 比表面积 ([单位]): [数值] (例如: 1500 m2/g)
        • 总孔体积 ([单位]): [数值] (例如: 0.8 cm3/g)
        • 微孔体积 ([单位]): [数值] (例如: 0.6 cm3/g)
        • 平均孔径 ([单位]): [数值] (例如: 1.5 nm)
    • 表面化学：
        • 元素含量 (注明 wt% 或 at%，**以原文为准**):
            • C: [数值]%
            • H: [数值]%
            • O: [数值]%
            • N: [数值]%
            • S: [数值]%
            • 其他元素: [元素名称: 数值%] (若有)
        • 官能团种类与数量 (注明单位，**以原文为准**):
            • -OH (羟基): [数值] [单位]
            • -COOH (羧基): [数值] [单位]
            • -C=O (羰基): [数值] [单位]
            • -C-O-C- (醚基): [数值] [单位]
            • N6 (吡啶氮): [数值] [单位]
            • N5 (吡咯氮): [数值] [单位]
            • NQ (季氮): [数值] [单位]
            • amine (胺): [数值] [单位]
            • 其他官能团: [官能团名称: 数值 单位] (若有)
    • CO2吸附性能 (**必须包含原文的吸附量、温度和压力及其单位**):
        • 吸附量 ([单位]): [数值]
        • 吸附温度 ([单位]): [数值]
        • 吸附压力 ([单位]): [数值]
        • (如果文献提供多个条件下的吸附量，请**分别、完整地**列出)

3. 输出格式：
    • 采用键值对形式清晰列出每个样本的信息，样本间用分号";"隔开。
    • 示例（**注意保留原文单位**）：
        样本一：样本名称: AC-1; 比表面积: 1500 m2/g; 总孔体积: 0.8 cm3/g; 微孔体积: 0.6 cm3/g; 平均孔径: 1.5 nm; 元素含量: C: 85 wt%, O: 10 wt%, N: 5 wt%; 官能团: -COOH: 1.2 wt%; CO2吸附量: 4.5 mmol/g @ 25 ℃ & 1 bar;
        样本二：样本名称: NAC-2; 比表面积: 2100 m2/g; 总孔体积: 1.1 cm3/g; 微孔体积: 0.9 cm3/g; 平均孔径: 1.1 nm; 元素含量: C: 80 wt%, O: 8 wt%, N: 12 at%; 官能团: N6: 3 wt%, N5: 2 wt%; CO2吸附量: 5.8 mmol/g @ 273.15 K & 101.3 kPa; CO2吸附量: 3.0 mmol/g @ 298.15 K & 1 atm;
    • ... 其他样本

注意事项：
    • **严格忠于原文**：如果文献中没有明确提到某个样本的某个信息，请在该项后标注“无”，**严禁自行推断或填补**。
    • **单位准确性**：确保提取的单位与文献原文完全一致。
    • **CO2吸附条件完整性**：对于CO2吸附量，必须同时记录原文提供的对应吸附温度和压力及其单位。
    • **百分比类型**：元素含量和官能团含量的百分比类型（wt% 或 at%）需按原文记录。
'''


PROMPT_CO2_CAP_2 = '''角色设定：数据库构建专家
任务：将第一步提取的关于活性炭CO2吸附的 **原文文本信息**，严格按照指定的JSON结构进行转换，用于数据集构建。**重点在于结构化映射的准确性，不进行任何数据内容的修改或单位转换。**

任务步骤：
1. 数据格式标准化：
    • 所有从第一步提取的包含数值和单位的数据，统一使用以下结构表示：
      {"value": number | null, "unit": "original_unit_string"}
      例如：{"value": 1500, "unit": "m2/g"}, {"value": 25, "unit": "℃"}, {"value": 101.3, "unit": "kPa"}
    • **保留所有原始单位**，不执行任何单位转换（例如，温度保留℃或K，压力保留bar、kPa、atm等）。
    • 缺失数据（在第一步中标注为“无”的信息）在JSON中用 `null` 表示对应字段的 `value`，`unit` 也可为 `null` 或省略。

2. 信息结构化：
    • 严格按照以下JSON格式组织数据，每个样本一个JSON对象，所有样本组成一个JSON数组：
[
  {
    "Sample Name": "Sample Name", // 直接从第一步提取
    "Pore Structure": {
      "Specific Surface Area": {"value": number | null, "unit": "original_unit_string"},
      "Total Pore Volume": {"value": number | null, "unit": "original_unit_string"},
      "Micropore Volume": {"value": number | null, "unit": "original_unit_string"},
      "Average Pore Diameter": {"value": number | null, "unit": "original_unit_string"}
    },
    "Surface Chemistry": {
      "Elemental Content Unit": "wt% or at%", // 指明第一步提取的主要单位类型
      "Elemental Content": {
        "C": {"value": number | null, "unit": "%"}, // 单位通常是 %
        "H": {"value": number | null, "unit": "%"},
        "O": {"value": number | null, "unit": "%"},
        "N": {"value": number | null, "unit": "%"},
        "S": {"value": number | null, "unit": "%"},
        "Others": [{"element": "name", "value": number | null, "unit": "%"}] // 列表
      },
      "Functional Group Unit": "original_unit_string", // 指明第一步提取的主要单位类型
      "Functional Groups": {
        "-OH": {"value": number | null, "unit": "original_unit_string"},
        "-COOH": {"value": number | null, "unit": "original_unit_string"},
        "-C=O": {"value": number | null, "unit": "original_unit_string"},
        "-C-O-C-": {"value": number | null, "unit": "original_unit_string"},
        "N6": {"value": number | null, "unit": "original_unit_string"},
        "N5": {"value": number | null, "unit": "original_unit_string"},
        "NQ": {"value": number | null, "unit": "original_unit_string"},
        "amine": {"value": number | null, "unit": "original_unit_string"},
        "Others": [{"group": "name", "value": number | null, "unit": "original_unit_string"}] // 列表
      }
    },
    "CO2 Adsorption Performance": [ // 包含所有原文数据点的列表
      {
        "Adsorption Capacity": {"value": number | null, "unit": "original_unit_string"}, // 保留原文单位
        "Temperature": {"value": number | null, "unit": "original_unit_string"}, // 保留原文单位 (℃, K, etc.)
        "Pressure": {"value": number | null, "unit": "original_unit_string"} // 保留原文单位 (bar, kPa, atm, etc.)
      }
      // ... 可能有更多的数据点对象
    ]
  }
  // ... 更多样本对象
]

直接输出要求：
    • **仅输出JSON结果**，不包含任何解释性文字或标记。
    • 将所有样本的数据组织在一个JSON数组中。
    • **确保所有数值和单位均来自第一步提取的原文信息，不进行任何转换。**
    • 准确将第一步提取的键值对信息映射到指定的JSON结构中。
    • 在 "Elemental Content Unit" 和 "Functional Group Unit" 字段中注明第一步提取的主要百分比或单位类型。
    • 对于列表字段（如 "Others" 元素/官能团，"CO2 Adsorption Performance"），如果无数据，则输出空列表 `[]`。
    • 对于缺失的单个数据点，其 `value` 应为 `null`。
'''

#存在的问题，幻觉还是较高