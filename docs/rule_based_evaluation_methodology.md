# Rule-Based Evaluation Methodology

## Overview

We developed a **deterministic rule-matching evaluation system** to quantitatively assess the accuracy of information extraction results without relying on large language models.

## Core Mechanisms

### 1. JSON Flattening

Nested JSON data structures are flattened into key-value pairs to enable field-by-field comparison.

**Example:**

```json
{
  "Synthesis": {
    "Temperature": "800°C"
  }
}
```

→ `Synthesis.Temperature: 800°C`

### 2. Multi-Type Matching Rules

The system applies different comparison strategies based on data types:

#### Pure Numerical Values

- Exact numerical matching (e.g., `1000` vs `1000`)
- Floating-point comparison with numerical equality check

#### Mixed Content (Numbers + Text)

- Extracts all numerical values for comparison
- Example: `1000 m²/g` → `[1000]`
- Matches if all numerical components are identical

#### Pure Text

- Skipped from evaluation (marked as **SKIP**)
- Does not contribute to performance metrics

### 3. Weighted Scoring Mechanism

To prioritize fields with higher information density:

- **Default weight**: 1
- **Multi-value fields**: Weight = number count (if ≥ 4 numbers)
- **Example**: `"Surface area: 1000 m²/g, Pore size: 2.5 nm, Pore volume: 0.8 cm³/g, Yield: 85%"` → Weight = 4

This approach ensures that parameter-rich fields have proportionally greater impact on evaluation metrics.

### 4. Four-Category Classification

Each field is classified into one of four categories:

| Category                      | Description                       | Example Scenario                           |
| ----------------------------- | --------------------------------- | ------------------------------------------ |
| **TP** (True Positive)  | Correctly extracted               | Extracted:`1000`, Ground Truth: `1000` |
| **FP** (False Positive) | Incorrectly extracted or spurious | Extracted:`500`, Ground Truth: `1000`  |
| **FN** (False Negative) | Missing extraction                | Ground Truth exists but not extracted      |
| **SKIP**                | Pure text field                   | Non-numerical string comparisons           |

## Evaluation Metrics

All metrics are calculated based on **weighted counts**:

$$
\text{Precision} = \frac{\sum \text{TP}_{\text{weighted}}}{\sum \text{TP}_{\text{weighted}} + \sum \text{FP}_{\text{weighted}}}
$$

$$
\text{Recall} = \frac{\sum \text{TP}_{\text{weighted}}}{\sum \text{TP}_{\text{weighted}} + \sum \text{FN}_{\text{weighted}}}
$$

$$
\text{F1-Score} = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}
$$

Where:

- TP `<sub>`weighted `</sub>` = True Positives × Weight
- FP `<sub>`weighted `</sub>` = False Positives × Weight
- FN `<sub>`weighted `</sub>` = False Negatives × Weight

## Domain-Specific Analysis

The system provides granular statistics across three domains:

1. **Synthesis** - Precursor materials, synthesis conditions, temperatures, etc.
2. **Physicochemical Properties** - Surface area, pore size, pore volume, etc.
3. **Electrochemical Performance** - Capacitance, cycling stability, rate capability, etc.

Each domain is evaluated independently to identify domain-specific extraction strengths and weaknesses.

## Key Advantages

✅ **Reproducibility**: Fully deterministic with no randomness
✅ **Cost-Effective**: No LLM API calls required
✅ **Transparency**: Clear reasoning for each evaluation decision
✅ **Fine-Grained**: Domain-level performance breakdown
✅ **Traceable**: Every mismatch includes specific reasons

## Use Case

This methodology is particularly suitable for **structured extraction tasks where numerical parameters dominate**, such as:

- Scientific literature mining
- Materials property databases
- Experimental data extraction
- Quantitative performance benchmarking

The rule-based approach enables rapid identification of extraction errors and systematic quality control without subjective judgment.

## Implementation Details

### Algorithm Workflow

```
1. Load ground truth dataset (CSV)
2. For each JSON file:
   a. Flatten nested structure
   b. Match keys against ground truth
   c. Apply type-specific comparison rules
   d. Calculate weights
   e. Assign TP/FP/FN/SKIP status
3. Aggregate weighted statistics
4. Compute Precision, Recall, F1-Score
5. Generate domain-specific reports
```

### Comparison Logic

```python
if exact_match(extracted, ground_truth):
    return TP
elif is_pure_number(extracted) and is_pure_number(ground_truth):
    return TP if float(extracted) == float(ground_truth) else FP
elif has_numbers(extracted) or has_numbers(ground_truth):
    return TP if extract_numbers(extracted) == extract_numbers(ground_truth) else FP
else:
    return SKIP  # Pure text
```

## Example Output

```
strong
```
