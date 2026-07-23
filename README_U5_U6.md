# Sapientia U5/U6 implementation package

This overlay extends the supplied Sapientia codebase with:

- **U5 Enterprise Reasoning**: deterministic graph traversal, impact paths, critical dependencies and ranked root-cause candidates.
- **U6 Enterprise Intelligence**: evidence-backed findings, recommendations, executive summaries and persisted enterprise answers.

## Architectural decisions

U5 uses `ekr_reasoning`. U6 persists intelligence outputs in `ekr_ai`, preserving the previously agreed schema consolidation and avoiding a second generic intelligence schema alongside the existing `ekr_intelligence` implementation.

The LLM is deliberately not used to discover facts. The deterministic engines create the facts, confidence, missing-evidence state and citations. An LLM can later verbalise the persisted answer without changing its evidence.

## Install

From this package:

```bash
./scripts/install_u5_u6.sh /path/to/Sapientia
```

Then apply migrations using your normal PostgreSQL workflow:

```bash
psql "${DATABASE_URL/postgresql+psycopg2:/postgresql:}" -v ON_ERROR_STOP=1 -f database/100_ekr_reasoning.sql
psql "${DATABASE_URL/postgresql+psycopg2:/postgresql:}" -v ON_ERROR_STOP=1 -f database/100_verify_ekr_reasoning.sql
psql "${DATABASE_URL/postgresql+psycopg2:/postgresql:}" -v ON_ERROR_STOP=1 -f database/101_ekr_enterprise_intelligence.sql
psql "${DATABASE_URL/postgresql+psycopg2:/postgresql:}" -v ON_ERROR_STOP=1 -f database/101_verify_ekr_enterprise_intelligence.sql
```

Apply `integration/main_py_changes.md` to register the three new commands.

## Commands

```bash
PYTHONPATH=src python3 -m sapientia.main reasoning \
  --project-id 1 \
  --origin-object-id 10 \
  --direction BOTH \
  --max-depth 6 \
  --business-domain FINANCE

PYTHONPATH=src python3 -m sapientia.main enterprise-intelligence-v2 \
  --project-id 1 \
  --business-domain FINANCE

PYTHONPATH=src python3 -m sapientia.main enterprise-ask \
  --project-id 1 \
  --business-domain FINANCE \
  --question "What would be impacted if Purchase Orders stopped loading?"
```

## Execution order

1. Run U1–U4 so a published understanding snapshot, active enterprise objects and operational relationships exist.
2. Run U5 reasoning for the enterprise objects you want to analyse.
3. Run U6 generation to produce findings and recommendations.
4. Ask evidence-backed enterprise questions.

## Important boundary

This package has been statically compiled and its pure graph/intelligence unit tests are included. It has not been executed against your PostgreSQL database, so apply it first in your development environment.
