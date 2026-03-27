# Phase 71 — Few-Shot Activity Classification

**Version:** 1.0 | **Tier:** Standard | **Date:** 2026-03-27

## Goal
Compare zero-shot vs 3-shot prompting for classifying compound activity (inactive/weak/moderate/potent/highly_potent). Tests whether providing examples improves classification accuracy on the remaining compounds.

CLI: `python main.py --input data/compounds.csv --n-test 5`

Outputs: fewshot_comparison.json, fewshot_report.txt

## Logic
- Select 3 diverse example compounds (different classes) as few-shot examples
- Select 5 test compounds (not in examples) for evaluation
- Zero-shot: ask Claude to classify with just the class definitions
- 3-shot: same request but include 3 labeled examples before the test compound
- Compare accuracy on activity_class between the two approaches

## Key Concepts
- Zero-shot: only class definitions in prompt, no examples
- Few-shot: include labeled examples (compound + pIC50 → class) before the test query
- Example selection: pick diverse classes (one moderate, one potent, one highly_potent)
- Accuracy: exact match on activity_class field
- Tests whether examples help when definitions are already clear

## Verification Checklist
- [ ] 3 examples selected from diverse activity classes
- [ ] 5 test compounds evaluated with both approaches
- [ ] Accuracy comparison reported
- [ ] 10 total API calls (2 per test compound × 5)

## Risks
- Both may achieve 100% if classification thresholds are given (our data has explicit pIC50)
- The real value of few-shot shows when thresholds are ambiguous or unlabeled
