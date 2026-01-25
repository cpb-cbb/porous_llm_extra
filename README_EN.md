# porous_llm_extra

[中文](README.md) | English

An automatic information extraction and evaluation toolkit for porous carbon supercapacitor literature, based on multi-agent workflows to perform sample prejudgment, synthesis/pore structure/electrochemical performance extraction, and provides metric calculation and result filtering scripts.

## Features

- **Workflow-Based Extraction**: Prejudge relevance and then extract synthesis process, pore structure parameters, and electrochemical performance in parallel, merging results.
- **Flexible LLM Switching**: Supports Zhipu GLM and any OpenAI-compatible models (Gemini, DeepSeek, Moonshot, etc.).
- **Evaluation & Filtering**: Batch evaluation scripts, field validity filtering, and F1 recalculation tools.
- **Data Conversion**: Legacy CSV/JSON conversion scripts retained for historical data alignment.

## Quick Navigation

- [main.py](main.py): CLI entry point for single-file or batch processing.
- [servers/work_flows/extract_por_super.py](servers/work_flows/extract_por_super.py): Core extraction workflow.
- [servers/utils](servers/utils): Text processing, prompts, merging and other utilities.
- [docs/architecture_overview.md](docs/architecture_overview.md): Architecture and data flow diagram.
- [filter_csv.py](filter_csv.py): Script to filter hallucinated fields and recalculate F1, see [docs/csv_filtering_guide.md](docs/csv_filtering_guide.md).
- [evaluation_results](evaluation_results): Sample evaluation outputs and summary metrics.

## Literature Data Acquisition

This project requires extracting information from literature. We recommend using the following tool to batch download full-text articles from the Elsevier database:

📚 **[dowload_artical_from_doi_or_elsvier](https://github.com/cpb-cbb/dowload_artical_from_doi_or_elsvier)**  
A literature download tool based on Elsevier API, supporting batch retrieval of full-text PDF/JSON via DOI or search criteria.

## Environment Setup

1) Python version: 3.12.11 (see [pyproject.toml](pyproject.toml))
2) Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## LLM Configuration

The project defaults to Zhipu GLM but also supports any OpenAI-compatible models (e.g., Gemini, DeepSeek, Moonshot).

Copy `.env.example` to `.env` and configure the following variables:

```bash
# LLM Service Configuration
LLM_API_KEY=your_api_key_here       # Required: API key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4  # API base URL
LLM_MODEL=openai/glm-4.7            # Optional: Model name
```

**Common Service Configuration Examples:**

```bash
# Zhipu GLM
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=openai/glm-4.7

# Gemini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=openai/gemini-2.5-pro

# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=openai/deepseek-chat
```

## Quick Start

### 1. Single File Extraction

```bash
python - <<'PY'
from servers.work_flows.extract_por_super import run_extraction_workflow

input_path = "path/to/input.json"      # Literature JSON or cleaned text path
output_path = "outputs/extracted.json"

run_extraction_workflow(input_path, output_path)
print("done", output_path)
PY
```

### 2. Batch Directory Processing

[main.py](main.py) includes batch processing examples that can handle directories concurrently:

```bash
python - <<'PY'
from main import process_directory

process_directory(
    input_dir="datas/json_inputs",   # Directory containing .json files
    output_dir="datas/outputs",      # Outputs with _extracted.json suffix
    max_workers=8
)
PY
```

### 3. Result Evaluation

The project provides two evaluation modes for different scenarios:

#### Method A: Rule-Based Evaluation

Fast, deterministic, no LLM cost, suitable for development and debugging.

```python
from envalue.rule_based_evaluator import RuleBasedEvaluator

evaluator = RuleBasedEvaluator(
    ground_truth_csv="datas/ground_truth.csv"  # Ground truth CSV
)

# Evaluate single file
results = evaluator.evaluate_json_file("outputs/extracted.json")

# Batch evaluate directory
results_df = evaluator.evaluate_directory(
    json_dir="outputs",
    output_csv="evaluation_results/rule_based_results.csv"
)
```

**Features:**
- Direct numeric and string exact matching
- Auto-calculates weights (≥4 numbers → weight = number count)
- Outputs TP/FP/FN/TN and Precision/Recall/F1

#### Method B: LLM-Based Evaluation

Uses LLM as an "auditor" to compare extraction results with source text, finding semantic mismatches and omissions. More intelligent but higher cost.

```bash
# Batch LLM evaluation (supports resume)
python batch_envalue.py
```

Or in code:

```python
from envalue.envalue_test import flatten_json, get_agent_audit, generate_evaluation_report_strict

# 1. Flatten extracted data
flat_data = flatten_json(extracted_json)

# 2. LLM audit (compare with source text)
agent_issues = get_agent_audit(source_text, flat_data)

# 3. Generate evaluation report
df_report, metrics = generate_evaluation_report_strict(extracted_json, agent_issues)

print(f"F1 Score: {metrics['F1_Score']}%")
df_report.to_csv("evaluation_report.csv", index=False)
```

**Features:**
- Understands context and semantics, finds subtle errors
- Auto-identifies mismatch (incorrect values) and missing (omissions)
- Requires LLM API configuration (Gemini/DeepSeek, etc.)

#### Post-Processing: Hallucinated Field Filtering

Remove fields that don't conform to the field template and recalculate F1:

```bash
python filter_csv.py evaluation_results/combined_detailed_report.csv \
  -o evaluation_results/combined_detailed_report_filtered.csv
```

See [docs/csv_filtering_guide.md](docs/csv_filtering_guide.md) for more details.

## Data and Output Locations

- Input/Intermediate data: datas/
- Extraction samples and evaluation outputs: evaluation_results/
- Reports and metric summaries: evaluation_reports/

## Adapting to Other Material Domains

This framework can be easily adapted to other material science domains (catalysts, batteries, MOFs, polymers, etc.). Follow these steps:

### Step 1: Define Your Domain Schema

Create a new field template in `servers/utils/field_template.py`:

```python
YOUR_DOMAIN_TEMPLATE = {
    "Synthesis": {
        "Components": ["Precursors", "Solvents", ...],
        "ProcessFlow": ["temperature", "duration", ...]
    },
    "Properties": {
        "YourKey1": ["value", "unit", "conditions"],
        "YourKey2": ["value", "unit"]
    },
    "Performance": {
        "Metric1": ["value", "unit", "test_conditions"],
        ...
    }
}
```

### Step 2: Customize Prompts

Update prompts in `servers/utils/prompts_en.py` to reflect your domain:

```python
PREJUDGE_PROMPT = """
You are analyzing {YOUR_DOMAIN} literature.
Task: Determine if this paper is relevant to {YOUR_MATERIAL_TYPE}...
"""

EXTRACTION_PROMPT = """
Extract the following information for each {SAMPLE_NAME}:
1. Synthesis conditions
2. {YOUR_PROPERTY_1}
3. {YOUR_PROPERTY_2}
...
"""
```

### Step 3: Modify Agents

Adjust agent logic in `servers/agents/` if needed:

- `prejudge_agent.py`: Update relevance criteria
- `process_extra_agent.py`: Adapt synthesis extraction logic
- `micro_feature_agent.py`: Replace with your property extraction agent
- `ele_chem_extra_agent.py`: Replace with your performance extraction agent

### Step 4: Update Workflow

Modify `servers/work_flows/extract_por_super.py`:

```python
def run_extraction_workflow(input_path, output_path):
    # 1. Prejudge relevance
    prejudge_result = prejudge_agent.process(text)
    
    # 2. Extract your domain-specific information
    synthesis_info = synthesis_agent.process(text, samples)
    property_info = property_agent.process(text, samples)
    performance_info = performance_agent.process(text, samples)
    
    # 3. Merge results
    final_result = merge_results(synthesis_info, property_info, performance_info)
    ...
```

### Step 5: Prepare Ground Truth

Create your domain-specific ground truth CSV with columns:
- `File`: Document identifier
- `Key`: Flattened field path (e.g., "Sample1.Properties.YourKey.value")
- `Ground Truth`: Expected value

### Step 6: Test and Iterate

1. Run extraction on a small test set
2. Evaluate using both rule-based and LLM-based methods
3. Analyze errors and refine prompts/schema
4. Iterate until precision and recall meet your requirements

### Example: Adapting to Battery Materials

```python
# 1. Define schema
BATTERY_TEMPLATE = {
    "Synthesis": {...},
    "ElectrochemicalProperties": {
        "SpecificCapacity": ["value", "unit", "current_density"],
        "CycleStability": ["capacity_retention", "cycle_number"],
        "RateCapability": ["current_density", "capacity"]
    }
}

# 2. Update prompts
BATTERY_EXTRACTION_PROMPT = """
Extract battery performance metrics including:
- Specific capacity (mAh/g) at different current densities
- Cycle stability (retention % after N cycles)
- Rate capability data
...
"""

# 3. Test and iterate
```

## Known Limitations

With improved LLM capabilities, hallucination has been greatly reduced in this framework, achieving precision above 98%. However, recall still needs improvement, and the current project only extracts from plain text data. Future work should extend to multimodal extraction.

- **Plain Text Limitation**: Some pore structure parameters only appear in figures or supplementary materials, leading to extraction gaps.
- **Recall Challenge**: Information like energy/power density is sparse in literature, resulting in limited recall. Prioritize experimental data and pore structure parameters.
- **Legacy Scripts**: Located in porous_carbon_info_extra/, ignore if no compatibility needed.

## Contributing

Welcome to submit Issues/PRs to optimize extraction workflows, prompts, and evaluation strategies. Please provide minimal reproducible examples and tests for new Agents and tools.
