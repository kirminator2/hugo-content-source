#!/bin/bash
set -e

TOKEN="$GH_PAT"
SOURCE_DIR="$HOME/hugo-content-source"
PAGES_DIR="$HOME/gptnews.github.io"

cd "$SOURCE_DIR"
git pull --rebase origin master 2>/dev/null || true

"$HOME/bin/hugo" --minify --cleanDestinationDir --destination "$PAGES_DIR"

cd "$PAGES_DIR"

git add -A

if git diff --cached --quiet; then
    echo "No changes to deploy"
    exit 0
fi

git commit -m "Auto-deploy: $(date '+%Y-%m-%d %H:%M')"
git push --force origin master

echo "Deployed successfully"
