porous_llm_extra
================

面向多孔炭超级电容文献的自动信息抽取与评估工具集，基于多 Agent 工作流完成样本预判、工艺/孔结构/电化学性能抽取，并提供指标计算与结果过滤脚本。

功能亮点
--------

- 工作流式抽取：预判相关性后并行抽取工艺流程、孔结构参数、电化学性能并合并结果。
- 灵活的 LLM 切换：支持智谱 GLM 及任意 OpenAI 兼容模型（Gemini、DeepSeek、Moonshot 等）。
- 评估与过滤：批量评估脚本、字段合法性过滤与 F1 复算工具。
- 数据转换：旧版 CSV/JSON 转换脚本保留，便于历史数据对齐。

目录速览
--------

- [main.py](main.py)：CLI 示例入口，可单文件或批量处理。
- [servers/work_flows/extract_por_super.py](servers/work_flows/extract_por_super.py)：核心抽取工作流。
- [servers/utils](servers/utils)：文本清洗、Prompt、合并等通用工具。
- [docs/architecture_overview.md](docs/architecture_overview.md)：架构与数据流示意。
- [filter_csv.py](filter_csv.py)：过滤幻觉字段并重算 F1 的脚本，详见 [docs/csv_filtering_guide.md](docs/csv_filtering_guide.md)。
- [evaluation_results](evaluation_results)：示例评估产物与汇总指标。

环境准备
--------

1) Python 版本：3.12.11（见 [pyproject.toml](pyproject.toml)）。
2) 安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

LLM 配置
--------

项目默认调用智谱 GLM，也支持任意 OpenAI 接口兼容的模型（如 Gemini、DeepSeek、Moonshot 等）。

复制 `.env.example` 为 `.env` 并配置以下变量：

```bash
# LLM 服务配置
LLM_API_KEY=your_api_key_here       # 必需：API 密钥
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4  # API 基础 URL
LLM_MODEL=openai/glm-4.7            # 可选：模型名称
```

**常用服务配置示例：**

```bash
# 智谱 GLM
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=openai/glm-4.7

# Gemini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=openai/gemini-2.5-pro

# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=openai/deepseek-chat
```

快速开始
--------

### 1. 单文件抽取

```bash
python - <<'PY'
from servers.work_flows.extract_por_super import run_extraction_workflow

input_path = "path/to/input.json"      # 文献 JSON 或清洗后的文本路径
output_path = "outputs/extracted.json"

run_extraction_workflow(input_path, output_path)
print("done", output_path)
PY
```

### 2. 批量处理目录

[main.py](main.py) 内置批处理示例，可传入目录并并发处理：

```bash
python - <<'PY'
from main import process_directory

process_directory(
		input_dir="datas/json_inputs",   # 目录需包含 .json 文件
		output_dir="datas/outputs",      # 输出将追加 _extracted.json 后缀
		max_workers=8
)
PY
```

### 3. 结果评估

项目提供两种评估模式，可根据场景选择：

#### 方式 A：基于规则的评估（Rule-Based）

快速、确定性强、无 LLM 成本，适合开发调试阶段。

```python
from envalue.rule_based_evaluator import RuleBasedEvaluator

evaluator = RuleBasedEvaluator(
    ground_truth_csv="datas/ground_truth.csv"  # 标准答案 CSV
)

# 评估单个文件
results = evaluator.evaluate_json_file("outputs/extracted.json")

# 批量评估目录
results_df = evaluator.evaluate_directory(
    json_dir="outputs",
    output_csv="evaluation_results/rule_based_results.csv"
)
```

**特点：**

- 直接对比数值、字符串精确匹配
- 自动计算权重（≥4 个数字时权重为数字个数）
- 输出 TP/FP/FN/TN 及 Precision/Recall/F1

#### 方式 B：基于 LLM 的评估（LLM-Based）

调用大模型作为"审计员"，对比提取结果与原文，发现语义不匹配和遗漏，更智能但成本较高。

```bash
# 批量 LLM 评估（支持断点续传）
python batch_envalue.py
```

或在代码中：

```python
from envalue.envalue_test import flatten_json, get_agent_audit, generate_evaluation_report_strict

# 1. 扁平化提取数据
flat_data = flatten_json(extracted_json)

# 2. LLM 审计（对比原文）
agent_issues = get_agent_audit(source_text, flat_data)

# 3. 生成评估报告
df_report, metrics = generate_evaluation_report_strict(extracted_json, agent_issues)

print(f"F1 Score: {metrics['F1_Score']}%")
df_report.to_csv("evaluation_report.csv", index=False)
```

**特点：**

- 理解上下文和语义，发现细微错误
- 自动识别 mismatch（值错误）和 missing（遗漏）
- 需配置 LLM API（支持 Gemini/DeepSeek 等）

#### 结果后处理：幻觉字段过滤

移除不符合字段模板的幻觉字段并重算 F1：

```bash
python filter_csv.py evaluation_results/combined_detailed_report.csv \
	-o evaluation_results/combined_detailed_report_filtered.csv
```

更多细节见 [docs/csv_filtering_guide.md](docs/csv_filtering_guide.md)。

数据与输出位置
--------------

- 输入/中间数据：datas/
- 抽取示例与评估产物：evaluation_results/
- 报告与指标汇总：evaluation_reports/

已知局限与提示
--------------

随着大模型能力的提升，在该框架下，幻觉程度大大降低，准确率在 98% 以上。但召回率仍待进一步提高，且当前项目抽取仅限于纯文本数据，未来需进一步扩展到多模态。

- **纯文本限制**：部分孔结构参数仅出现在图表或补充材料中，自动抽取存在缺口。
- **召回率挑战**：能量/功率密度等信息在文献中稀疏，召回有限，可优先聚焦实验数据与孔结构参数。
- **历史兼容**：旧版脚本位于 porous_carbon_info_extra/，如无兼容需求可忽略。

贡献与维护
----------

欢迎提交 Issue/PR 优化抽取流程、提示词与评估策略。建议为新增 Agent 和工具补充最小可复现示例与测试。
