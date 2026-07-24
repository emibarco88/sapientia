#!/bin/bash
set -euo pipefail

DEFAULT_ROOT="/Users/emilianobarco/Desktop/Projects/Sapientia"
PROJECT_ROOT="${1:-$DEFAULT_ROOT}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD="$SCRIPT_DIR/payload"
UI_ROOT="$PROJECT_ROOT/ui"

if [ ! -d "$UI_ROOT" ]; then
  echo "Sapientia UI was not found at: $UI_ROOT"
  echo "Usage: ./install.sh /path/to/Sapientia"
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_ROOT="$PROJECT_ROOT/.sapientia_backups/vnext_business_ui_$STAMP"
mkdir -p "$BACKUP_ROOT"

FILES=(
  "ui/app/layout.tsx"
  "ui/app/dashboard/page.tsx"
  "ui/app/domains/[domain]/page.tsx"
  "ui/app/workspace/[domain]/page.tsx"
  "ui/app/workspace/[domain]/explorer/page.tsx"
  "ui/app/workspaces/page.tsx"
  "ui/app/ux-v2.css"
  "ui/app/vnext.css"
  "ui/components/layout/AppShell.tsx"
  "ui/components/layout/Header.tsx"
  "ui/components/layout/Sidebar.tsx"
  "ui/components/enterprise/EnterpriseContext.tsx"
  "ui/components/vnext/AskBar.tsx"
  "ui/components/vnext/DomainStatus.tsx"
)

for relative in "${FILES[@]}"; do
  source_file="$PROJECT_ROOT/$relative"
  if [ -f "$source_file" ]; then
    mkdir -p "$BACKUP_ROOT/$(dirname "$relative")"
    cp "$source_file" "$BACKUP_ROOT/$relative"
  fi
done

cp -R "$PAYLOAD/ui/." "$UI_ROOT/"

cat > "$BACKUP_ROOT/restore.sh" <<RESTORE
#!/bin/bash
set -euo pipefail
PROJECT_ROOT="$PROJECT_ROOT"
BACKUP_ROOT="$BACKUP_ROOT"
cp -R "\$BACKUP_ROOT/ui/." "\$PROJECT_ROOT/ui/"
echo "Sapientia UI restored from \$BACKUP_ROOT"
RESTORE
chmod +x "$BACKUP_ROOT/restore.sh"

echo ""
echo "Sapientia vNext Business UI installed."
echo "Backup: $BACKUP_ROOT"
echo "Restore: $BACKUP_ROOT/restore.sh"
echo ""
echo "Next steps:"
echo "  cd \"$UI_ROOT\""
echo "  npm run dev"
echo ""
