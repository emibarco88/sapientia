# Bundle 2A Integration Notes

## FastAPI router

The application must include:

```python
from sapientia.intelligence_experience.api import (
    router as intelligence_experience_router,
)

app.include_router(intelligence_experience_router)
```

The installer attempts this automatically in `src/sapientia/main.py`.

## Existing database dependency

The generated API checks these locations:

1. `sapientia.database.get_db`
2. `sapientia.db.get_db`

When Sapientia defines the session dependency elsewhere, replace only that
import block. Do not create a second SQLAlchemy engine or session factory.

## Existing EKR compatibility

`EKRSourceAdapter` resolves compatible assessment, intelligence and business
object tables through PostgreSQL `information_schema`. This avoids coupling
the Phase 2 experience to one historical migration version.

No department-specific behaviour is included.

## AI enrichment

Deterministic mode works independently of OpenAI. Enriched mode accepts a
client implementing:

```python
def enrich_narrative(
    self,
    deterministic_narrative: dict,
    tone: str,
) -> dict:
    ...
```

AI may improve wording and explanation, but deterministic evidence remains
authoritative.
