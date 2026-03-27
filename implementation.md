# Phase 71 — Few-Shot Activity Classification

**Version:** 1.1 | **Tier:** Standard | **Date:** 2026-03-27

## Goal
Compare zero-shot vs 3-shot prompting for classifying compound activity. Tests whether providing examples improves classification accuracy.

CLI: `python main.py --input data/compounds.csv --n-test 5`

Outputs: fewshot_comparison.json, fewshot_report.txt

## Logic
- Select 3 diverse examples (moderate, potent, highly_potent) as few-shot demonstrations
- Select 5 test compounds (excluding examples) for evaluation
- Zero-shot: class definitions only, no examples
- 3-shot: include labeled examples as user/assistant turn pairs before test query
- Compare accuracy on activity_class

## Key Concepts
- Zero-shot: only thresholds in prompt, no labeled examples
- Few-shot: multi-turn format with 3 (user, assistant) example pairs
- Example selection: deliberately diverse classes (moderate, potent, highly_potent)
- The few-shot format uses Claude's multi-turn conversation to simulate labeled examples

## Verification Checklist
- [x] 3 examples from diverse activity classes
- [x] 5 test compounds evaluated with both approaches
- [x] Few-shot >= zero-shot accuracy
- [x] 10 total API calls

## Results
| Metric | Value |
|--------|-------|
| Zero-shot accuracy | 80% (4/5) |
| Few-shot accuracy | 100% (5/5) |
| Delta | +20% |
| Zero-shot failure | benz_005_CN (pIC50=7.95): predicted highly_potent, true=potent |
| Total tokens | in=2241 out=145 |
| Est. cost | $0.0024 |

Key finding: Few-shot corrected a boundary case error (pIC50=7.95 at the potent/highly_potent edge). The examples calibrated Claude's threshold handling. This is consistent with Phase 70's finding that explicit definitions matter most.

## Risks (resolved)
- Both may achieve 100% when pIC50 thresholds are explicit — zero-shot missed boundary case (pIC50=7.95)
- Example selection bias may favor certain classes — mitigated by selecting diverse classes (moderate/potent/highly_potent)
- 5 test compounds may not capture all edge cases — boundary case at 7.95 was successfully tested
