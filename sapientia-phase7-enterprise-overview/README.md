# Sapientia Phase 7 — Enterprise Overview

This patch introduces the first Phase 7 UI iteration:

- Replaces the technical dashboard with a business-oriented Enterprise Overview.
- Uses one active enterprise for the MVP (the first domain returned by `/domains`).
- Removes the right-hand technical context panel from the dashboard.
- Simplifies the sidebar to Enterprise, Knowledge, Insights, Enterprise Agent and Data Sources.
- Adds the Enterprise Journey and business-friendly status language.
- Preserves the existing backend API contracts and routes.

## Apply

From the extracted patch folder:

```bash
./apply_phase7.sh /absolute/path/to/Sapientia
```

Or copy these files manually:

- `ui/app/dashboard/page.tsx`
- `ui/app/globals.css`
- `ui/app/layout.tsx`
- `ui/components/layout/Sidebar.tsx`

## Install and validate

```bash
cd /absolute/path/to/Sapientia/ui
rm -rf .next
npm install
npm run build
npm run dev
```

Start the API in another terminal from the repository root:

```bash
source .venv/bin/activate
PYTHONPATH=src uvicorn api.main:app --reload
```

Then open `http://localhost:3000`, log in and verify the Enterprise Overview.
