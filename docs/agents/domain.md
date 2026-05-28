# Domain docs

This repository uses a multi-context layout for different functional domains.

## Layout

```
/
├── CONTEXT-MAP.md              ← maps each context to its CONTEXT.md location
├── docs/adr/                   ← system-wide architecture decisions
├── CLAUDE.md                   ← agent skills configuration
│
├── contexts/
│   └── 拆文工坊/                 ← first context: novel deconstruction workshop
│       ├── CONTEXT.md           ← domain glossary for this context
│       └── docs/adr/            ← context-specific decisions
│
├── .agents/                     ← agent skill definitions
├── 拆文.md                      ← context-specific document
├── 拆文工坊产品与架构设计方案.md    ← context-specific document
└── ...
```

## Contexts

| Context | Path | Description |
|---------|------|-------------|
| 拆文工坊 | `contexts/拆文工坊/` | Novel deconstruction & analysis workshop |

*More contexts will be added as the project grows.*

## Consumer rules

- Skills read `CONTEXT.md` to learn domain language before exploring or suggesting changes
- ADRs in `docs/adr/` record decisions the skills should not re-litigate
- When adding a new context: create `contexts/<name>/CONTEXT.md` and add an entry to `CONTEXT-MAP.md`
