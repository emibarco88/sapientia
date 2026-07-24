# Enterprise Intelligence Platform V1 — Bundle 3

Adds assessment version history, automatic comparison, object changes, confidence evolution, APIs and a history page.

Database: localhost:5432 / sapientia / user postgres

Install:
```bash
chmod +x install.sh verify.sh rollback.sh
./install.sh /Users/emilianobarco/Desktop/Projects/Sapientia
```

After installation restart API/UI, generate Enterprise Intelligence again, then open:
`/workspace/FINANCE/intelligence/history`

At least two assessment versions are required for comparison.
