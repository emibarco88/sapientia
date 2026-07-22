#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -d "$PROJECT_ROOT/ui" ]]; then
  echo "Error: $PROJECT_ROOT/ui was not found."
  echo "Run this script from the Sapientia repository root or pass the repository path."
  exit 1
fi

mkdir -p "$PROJECT_ROOT/ui/app/dashboard"
mkdir -p "$PROJECT_ROOT/ui/components/layout"

cp "$PATCH_DIR/ui/app/dashboard/page.tsx" "$PROJECT_ROOT/ui/app/dashboard/page.tsx"
cp "$PATCH_DIR/ui/app/globals.css" "$PROJECT_ROOT/ui/app/globals.css"
cp "$PATCH_DIR/ui/app/layout.tsx" "$PROJECT_ROOT/ui/app/layout.tsx"
cp "$PATCH_DIR/ui/components/layout/Sidebar.tsx" "$PROJECT_ROOT/ui/components/layout/Sidebar.tsx"

echo "Phase 7 Enterprise Overview files applied successfully."
echo ""
echo "Next:"
echo "  cd \"$PROJECT_ROOT/ui\""
echo "  rm -rf .next"
echo "  npm install"
echo "  npm run build"
echo "  npm run dev"
