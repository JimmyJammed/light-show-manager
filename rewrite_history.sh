#!/bin/bash
# Rewrite git history to a single "Initial commit"
# This script will:
# 1. Create a backup branch
# 2. Create a new orphan branch
# 3. Add all current files
# 4. Create a single commit
# 5. Replace the main branch

set -e

REPO_NAME="light-show-manager"
BACKUP_BRANCH="backup-before-rewrite-$(date +%Y%m%d-%H%M%S)"
CURRENT_BRANCH=$(git branch --show-current)

echo "🔄 Rewriting git history for $REPO_NAME"
echo ""
echo "⚠️  WARNING: This will rewrite ALL git history!"
echo "   Current branch: $CURRENT_BRANCH"
echo "   Backup branch will be created: $BACKUP_BRANCH"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# Create backup branch
echo ""
echo "📦 Creating backup branch: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH"
echo "✅ Backup created"

# Create new orphan branch (no history)
echo ""
echo "🌱 Creating new orphan branch..."
git checkout --orphan new-main

# Add all files
echo ""
echo "📝 Adding all files..."
git add -A

# Create initial commit
echo ""
echo "💾 Creating initial commit..."
git commit -m "Initial commit"

# Delete old main branch
echo ""
echo "🗑️  Deleting old $CURRENT_BRANCH branch..."
git branch -D "$CURRENT_BRANCH"

# Rename current branch to main
echo ""
echo "🏷️  Renaming branch to $CURRENT_BRANCH..."
git branch -m "$CURRENT_BRANCH"

echo ""
echo "✅ History rewrite complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Review the changes: git log"
echo "   2. If everything looks good, force push to remote:"
echo "      git push -f origin $CURRENT_BRANCH"
echo ""
echo "⚠️  Note: Your backup branch '$BACKUP_BRANCH' is still available locally"
echo "   To restore: git checkout $BACKUP_BRANCH"

