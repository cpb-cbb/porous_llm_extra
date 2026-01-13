# CSV过滤功能使用说明

## 功能描述

该功能用于过滤评估CSV文件中不符合提示词要求的幻觉字段，并重新计算F1分数。

## 文件说明

- `servers/utils/field_template.py` - 核心模块，包含字段模版和过滤逻辑
- `filter_csv.py` - 命令行脚本，用于处理CSV文件

## 使用方法

### 方式1: 命令行使用

```bash
# 基本用法（输出文件名自动生成为 xxx_filtered.csv）
python filter_csv.py evaluation_results/combined_detailed_report.csv

# 指定输出文件路径
python filter_csv.py evaluation_results/combined_detailed_report.csv -o evaluation_results/filtered_report.csv
```

### 方式2: Python代码调用

```python
from servers.utils.field_template import filter_csv_and_recalculate

# 过滤CSV并重新计算指标
result = filter_csv_and_recalculate(
    input_csv_path="evaluation_results/combined_detailed_report.csv",
    output_csv_path="evaluation_results/filtered_report.csv"
)

print(f"F1提升: {result['improvement']['f1_gain']:.4f}")
print(f"移除的无效字段: {result['improvement']['invalid_keys_removed']}")
```

## CSV格式要求

输入CSV文件应包含以下列：

- `Key` - 字段路径（如 "Sample1.Synthesis.Components.Precursors"）
- `Extracted Value` - 提取的值
- `Ground Truth` - 标准答案
- `Status` - 状态（TP/FP/FN/TN/Mismatch）
- `Reason` - 原因说明
- `File` - 文件名（可选）

这是 `batch_envalue.py` 生成的 `combined_detailed_report.csv` 的标准格式。

## 输出说明

脚本会输出：

1. **过滤统计**

   - 原始行数
   - 检测到的不合法字段数量
   - 过滤后剩余行数
2. **指标对比**

   - 过滤前: TP, FP, FN, TN, Precision, Recall, F1
   - 过滤后: TP, FP, FN, TN, Precision, Recall, F1
   - 改善: FP减少数量和百分比，Precision提升，F1提升
3. **过滤后的CSV文件**

   - 移除了所有不合法字段的行
   - 保留了所有其他列的原始数据

## 字段合法性判断

字段是否合法由 `servers/utils/field_template.py` 中定义的模版决定：

### Synthesis（合成）

- Components: Precursors, Activator, Template, Ratios
- ProcessFlow: step_name, temperature, duration, heating_rate, atmosphere, flow_rate, details

### PhysicochemicalProperties（物化性质）

- Porosity: SpecificSurfaceArea_BET, MicroporeSurfaceArea, TotalPoreVolume, 等
- Composition: Elemental, HighResolution_XPS, QualitativeFunctionalGroups_FTIR
- Crystallinity: Graphitization_Raman_ID_IG

### ElectrochemicalPerformance（电化学）

- SystemType, Electrolyte, VoltageWindow, SpecificCapacitance, 等

详细字段列表请参考 `field_template.py` 中的模版定义。

## 示例输出

```
正在读取CSV文件: evaluation_results/combined_detailed_report.csv
成功读取 1234 行数据

原始数据统计:
  TP: 850
  FP: 384 (包括 120 个 Mismatch)
  FN: 170 (包括 120 个 Mismatch)
  TN: 50

发现 45 个不合法的字段:
  行 23: Sample1.Synthesis.Components.InvalidField
  行 56: Sample2.PhysicochemicalProperties.FakeProperty
  ...

过滤后剩余 1189 行 (移除了 45 行)

================================================================================
过滤前后指标对比:
================================================================================

过滤前:
  TP: 850, FP: 384, FN: 170, TN: 50
  Precision: 0.6887 (68.87%)
  Recall: 0.8333 (83.33%)
  F1 Score: 0.7540 (75.40%)

过滤后:
  TP: 850, FP: 339, FN: 170, TN: 50
  Precision: 0.7148 (71.48%)
  Recall: 0.8333 (83.33%)
  F1 Score: 0.7692 (76.92%)

改善:
  FP减少: 45 (11.72%)
  Precision提升: 0.0261 (3.79%)
  F1提升: 0.0152 (2.02%)

✅ 过滤后的CSV已保存到: evaluation_results/combined_detailed_report_filtered.csv
```

## 注意事项

1. 原始CSV文件不会被修改，所有结果保存到新文件
2. 动态键名（如元素符号C、O、N和XPS子物种）会被正确识别，不会被过滤
3. 只移除行，不修改Status列的值
4. 如果字段路径解析失败，该行会被保留
