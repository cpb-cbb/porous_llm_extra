---
name: "Run Porous Carbon Flow"
description: "Run end-to-end porous carbon extraction for supercapacitor literature using the porous-carbon-flow custom agent."
agent: "porous-carbon-flow"
argument-hint: "Paste full_text. Optional: provide sample_list_override and verify_batch=true/false."
---
Run the porous carbon extraction flow on the provided input.

## Inputs
- full_text: the complete paper text (required)
- sample_list_override: optional sample names to force extraction scope
- verify_batch: true or false (default true)

## Required Behavior
1. First perform relevance and sample identification.
2. If relevant, extract synthesis, physicochemical properties, and electrochemical data.
3. Merge output by sample name into one JSON object with blocks:
   - synthesis
   - properties
   - electrochem
4. If verify_batch is true, perform final batch verification once.

## Output
- If document is irrelevant: output step 1.1 irrelevant JSON.
- If relevant: output merged JSON keyed by sample names.
- Output JSON only unless verifier mode explicitly requires T.
