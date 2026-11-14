# Dev error analysis

## q03: retrieval ranking and context coverage

- Two chunks needed to cover the reviewed evidence occur at hybrid
  ranks 6 and 13, on PDF page 69.
- Increasing retrieval depth to 20 retrieves both chunks.
- With the current pack_context implementation, tested budgets of
  2500, 3500, 4500 and 6000 characters do not retain both chunks.
- A tested budget of 8000 characters retains both chunks.
- This checks inclusion of the two inspected chunk IDs.
  It does not establish answer correctness or semantic grounding.
- Increasing context budget alone may increase model input cost
  and include more irrelevant text.

## Planned dev experiments

Baseline:
- Hybrid RRF, candidate_k=20, rrf_k=60.
- Retrieval top_k=3; context budget=2500 characters.

Improvement 1:
- Rerank 20 hybrid candidates and retain the top 3.
- Keep the same context budget.
- Hypothesis: reranking improves evidence ranking.

Improvement 2:
- Keep Improvement 1 retrieval settings.
- Add adjacent source chunks during context packing when space permits.
- Keep the same context budget.
- Hypothesis: neighboring text improves evidence completeness.

## Evaluation controls

- Apply each configuration to the complete dev split.
- Never use gold evidence or target chunk IDs in retrieval or packing.
- Report retrieval metrics separately from final-context evidence coverage.
- Log all context additions and enforce the character budget.
- Do not run test until configuration selection is complete.