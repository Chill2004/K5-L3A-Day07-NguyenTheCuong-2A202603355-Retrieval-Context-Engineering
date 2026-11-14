# Configuration selection before test

Selected configuration: top5.
Comparison baseline: baseline.

Shared settings:
- Gemini model: gemini-3.5-flash-lite.
- Retriever: hybrid RRF.
- candidate_k: 20.
- rrf_k: 60.
- Context budget: 2500 characters.
- Maximum searches: 2.

Changed factor:
- baseline top_k: 3.
- selected top_k: 5.

Dev observations:
- baseline: 13 answered / 15 answerable questions.
- top5: 14 answered / 15 answerable questions.
- single_search: 13 answered / 15 answerable questions.
- All configurations returned abstention for both unanswerable questions.
- top5 used explicit model abstention for both unanswerable questions.
- top5 q03 omitted the required 5.0 score threshold.
- top5 q12 was rejected for missing inline citation.
- Answered status is not equivalent to a fully correct answer.

Selection rationale:
Top5 offers a modest observed improvement in answer completeness and
explicit abstention behavior. Its remaining errors are retained.

Limitations:
- Selection uses dev inspection by Codex (AI); no independent human grading is claimed.
- Model generation variability may contribute to differences.
- API and database failures are retained separately.
- No configuration will be tuned using test outcomes.
