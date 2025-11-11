# Git Aliases and Shortcuts

Quick reference for common git operations in the RWC project.

## Setup

### Option 1: Source the alias file (temporary)
```bash
source .git-aliases
```

### Option 2: Add to your ~/.gitconfig (permanent)
```bash
# Quick status
git config --global alias.st 'status -sb'
git config --global alias.l 'log --oneline --graph --decorate -10'

# Branch info
git config --global alias.br 'branch -vv'

# View changes
git config --global alias.d 'diff'
git config --global alias.ds 'diff --staged'
```

## Common Commands

### Status and History
```bash
# Short status
git status -sb

# Recent commits
git log --oneline -10

# Branch view with graph
git log --oneline --graph --decorate --all -20

# Show files changed
git diff --stat
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=rwc --cov-report=term-missing

# Fast fail (stop on first failure)
pytest tests/ -x --tb=short

# Run specific test file
pytest tests/test_security.py -v

# Run specific test
pytest tests/test_security.py::TestPathTraversal::test_blocks_parent_directory -v
```

### Review This Branch
```bash
# Show all changes from master
git diff master..security-fixes-critical

# Show changed files
git diff --name-status master..security-fixes-critical

# Show commits
git log --oneline master..security-fixes-critical

# Show full diff stats
git diff --stat master..security-fixes-critical

# Review a specific commit
git show <commit-hash>
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run flake8 --all-files
```

### Branch Management
```bash
# List all branches
git branch -avv

# Switch to master
git checkout master

# Create new branch
git checkout -b feature-name

# Delete branch (after merging)
git branch -d security-fixes-critical
```

### Merging to Master
```bash
# Review changes first
git diff --stat master..security-fixes-critical

# Merge (no fast-forward for clear history)
git checkout master
git merge security-fixes-critical --no-ff

# Or create PR
git push origin security-fixes-critical
gh pr create --title "Security fixes and improvements" --body-file HIGH-PRIORITY-TASKS-COMPLETE.md
```

## Project-Specific Commands

### Quick Project Status
```bash
# Show everything at once
echo "Branch: $(git branch --show-current)"
echo "Commits: $(git rev-list --count HEAD)"
pytest tests/ -q
pytest tests/ --cov=rwc --cov-report=term | tail -5
```

### Run Production Server
```bash
# Start API server
./run_api_production.sh

# With custom config
RWC_WORKERS=8 FLASK_HOST=0.0.0.0 FLASK_PORT=8000 ./run_api_production.sh
```

### Documentation Quick Access
```bash
# View completion report
cat HIGH-PRIORITY-TASKS-COMPLETE.md

# View full improvements
cat FINAL-IMPROVEMENTS-REPORT.md

# View security fixes
cat SECURITY-FIXES-SUMMARY.md

# View code quality
cat CODE-QUALITY-IMPROVEMENTS.md
```

## Useful Git Options

### Diff with Statistics
```bash
# Show changed files with line counts
git diff --stat

# Show only file names
git diff --name-only

# Show file names with status (A=added, M=modified, D=deleted)
git diff --name-status
```

### Log Formatting
```bash
# Compact log
git log --oneline -10

# With graph
git log --oneline --graph --decorate -10

# With file stats
git log --stat -5

# Search commits
git log --grep="security" --oneline

# By author
git log --author="Claude" --oneline
```

### Stashing
```bash
# Save current work
git stash push -m "WIP: feature description"

# List stashes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{1}
```

## Testing Shortcuts

### Coverage by Module
```bash
pytest tests/ --cov=rwc.core --cov-report=term
pytest tests/ --cov=rwc.utils --cov-report=term
pytest tests/ --cov=rwc.api --cov-report=term
```

### Test Selection
```bash
# Run only security tests
pytest tests/test_security.py -v

# Run only one test class
pytest tests/test_security.py::TestPathTraversal -v

# Run tests matching pattern
pytest tests/ -k "security" -v
pytest tests/ -k "validation" -v
```

### Coverage Reports
```bash
# Terminal report
pytest tests/ --cov=rwc --cov-report=term-missing

# HTML report (opens in browser)
pytest tests/ --cov=rwc --cov-report=html
open htmlcov/index.html  # or xdg-open on Linux

# JSON report
pytest tests/ --cov=rwc --cov-report=json
```

## Common Workflows

### Daily Development
```bash
# Start of day
git checkout security-fixes-critical
git status

# After making changes
git add .
git status
git diff --staged
git commit -m "Description of changes"

# Run tests
pytest tests/ -v

# Run pre-commit checks
pre-commit run --all-files
```

### Before Committing
```bash
# Check what changed
git status
git diff

# Check staged changes
git diff --staged

# Run tests
pytest tests/ -x --tb=short

# Run linting
pre-commit run --all-files

# Commit
git commit -m "Clear description"
```

### Before Merging
```bash
# Review all changes
git diff --stat master..security-fixes-critical
git log --oneline master..security-fixes-critical

# Run full test suite
pytest tests/ -v --cov=rwc

# Check documentation
ls -lh *SUMMARY*.md *REPORT*.md

# Merge
git checkout master
git merge security-fixes-critical --no-ff --no-edit
```

## Troubleshooting

### Undo Last Commit (not pushed)
```bash
git reset --soft HEAD~1  # Keep changes staged
git reset --mixed HEAD~1  # Keep changes unstaged
git reset --hard HEAD~1  # Discard changes (DANGEROUS!)
```

### Discard Local Changes
```bash
# Specific file
git checkout -- filename

# All files
git reset --hard HEAD
```

### View Specific File from Another Branch
```bash
git show master:path/to/file.py
git show security-fixes-critical:rwc/core/__init__.py
```

### Compare Branches
```bash
# Files changed between branches
git diff --name-status master..security-fixes-critical

# Commits in branch but not in master
git log master..security-fixes-critical --oneline

# Commits in master but not in branch
git log security-fixes-critical..master --oneline
```

## GitHub CLI (gh)

### Pull Requests
```bash
# Create PR
gh pr create --title "Title" --body "Description"

# List PRs
gh pr list

# View PR
gh pr view <number>

# Merge PR
gh pr merge <number>
```

### Issues
```bash
# Create issue
gh issue create --title "Bug: description"

# List issues
gh issue list

# View issue
gh issue view <number>
```

---

**Note**: These aliases and commands are optimized for the RWC project but can be adapted for other projects.
