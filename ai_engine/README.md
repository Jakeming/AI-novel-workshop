# AI Engine — project root

## Structure

```
ai-engine/
├── core/
│   └── llm.py           # Deep LLM client (Candidate 1)
├── models/
│   └── schemas.py       # Shared data models
├── tasks/
│   └── prompts.py       # Prompt templates (one per task)
├── validation/
│   ├── comparators.py   # SkeletonComparator, EmotionComparator, EmbeddingComparator (Candidate 2)
│   ├── aggregator.py    # ValidationAggregator — thresholds + verdict (Candidate 2)
│   └── service.py       # ValidationService — public facade (Candidate 2)
├── probe/
│   └── context.py       # ProbeContext + loaders + probes (Candidate 4)
├── requirements.txt
└── README.md
```

## dependency graph

```
llm.py  (no deps)
    ↑
prompts.py  ←  llm.py
    ↑
service.py  ←  comparators.py + aggregator.py  ←  schemas.py

coolant.py  (standalone, rule engine)

WorkflowController.ts  (frontend, standalone)
```
