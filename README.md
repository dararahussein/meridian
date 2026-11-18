# meridian

`meridian` is an end-to-end platform for executing stateful multi-agent DAG workflows, hybrid lexical/dense retrieval (RAG), runtime safety guardrails, deterministic & LLM-judged evaluations, and full-span trace observability.

## Architecture

```text
+-------------------------------------------------------------------------+
|                    Interfaces: CLI  |  FastAPI Gateway  |  Web Studio   |
+-------------------------------------+-----------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------+
|                         Orchestrator (DAG Runtime)                      |
|     Parallel Fan-Out/Fan-In  |  State Checkpoints  |  Deterministic     |
|     Conditional Routing      |  Human Approval     |  Trace Replay      |
+-----------+------------------+---------------------+--------------------+
            |                  |                     |
            v                  v                     v
   +----------------+  +---------------+   +----------------------+
   |  Core Router   |  |  Hybrid RAG   |   |  Tool & Memory Bus   |
   | - Multi-model  |  | - AST/Doc     |   | - Schema compiler    |
   |   fallbacks    |  |   chunkers    |   | - Episodic/semantic  |
   | - Structured   |  | - BM25 + Vec  |   |   compaction         |
   |   JSON repair  |  | - RRF fusion  |   | - Guardrail filters  |
   +--------+-------+  +-------+-------+   +----------+-----------+
            |                  |                      |
            +------------------+----------------------+
                               |
                               v
+-------------------------------------------------------------------------+
|                Observability & Evaluation Harness                       |
|   Hierarchical Span Tree  |  Token/Cost Ledger  |  Regression Suites    |
+-------------------------------------------------------------------------+
```

## Subsystems

| Module | Path | Responsibility |
| :--- | :--- | :--- |
| **Core** | `src/meridian/core/` | Unified model gateway, adaptive retries, circuit breakers, structured output validation, semantic caching, and token/cost accounting |
| **Orchestrator** | `src/meridian/orchestrator/` | Directed acyclic workflow scheduler, dynamic branching, persistent checkpoints, and step-level replay |
| **Hybrid RAG** | `src/meridian/rag/` | Recursive/AST chunking, inverted BM25 index, dense vector search, Reciprocal Rank Fusion (RRF), and cross-encoder reranking |
| **Tools** | `src/meridian/tools/` | Typed Python-to-JSON-Schema compiler, timeout/quota isolation, and HTTP/SQL/filesystem connectors |
| **Memory** | `src/meridian/memory/` | Rolling context compaction, episodic trajectory storage, and entity-relationship knowledge graph extraction |
| **Guardrails** | `src/meridian/guardrails/` | Prompt-injection heuristics, regex/NER PII redaction, and output contract enforcement |
| **Evals** | `src/meridian/evals/` | Golden dataset runner, exact/fuzzy/rubric scorers, pairwise comparisons, and latency/cost regression gates |
| **Observability** | `src/meridian/observability/` | Span tracing, prompt/completion diffing, and latency waterfall export |
| **API & Web** | `src/meridian/api/`, `web/` | Streaming SSE/WebSocket backend and React/TypeScript DAG trace inspector |
| **CLI** | `src/meridian/cli/` | Local workflow execution, dataset evaluation, and trace inspection commands |

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run backend test suite
make test

# Start API gateway
make api
```
