# How to Push Code Updates to GitHub

## Quick Commands

```bash
# 1. Check what files have changed
git status

# 2. Add all changes (or specific files)
git add .

# 3. Commit with a message
git commit -m "Your commit message here"

# 4. Push to GitHub
git push origin main
```

---

## Step-by-Step Guide

### Step 1: Check Your Changes

See what files have been modified:
```bash
git status
```

This shows:
- **Modified files** (files you've changed)
- **Untracked files** (new files not yet in git)
- **Staged files** (files ready to commit)

### Step 2: Review Your Changes (Optional)

See what changed in a specific file:
```bash
git diff <filename>
```

Or see all changes:
```bash
git diff
```

### Step 3: Stage Your Changes

**Option A: Add all changes**
```bash
git add .
```

**Option B: Add specific files**
```bash
git add path/to/file1.py path/to/file2.py
```

**Option C: Add all changes in a directory**
```bash
git add core/
```

### Step 4: Commit Your Changes

Create a commit with a descriptive message:
```bash
git commit -m "Add PandasAI LLM insights to all functions"
```

**Good commit messages:**
- ✅ "Add LLM insights to prediction and SQL query functions"
- ✅ "Fix LLM insights display issue"
- ✅ "Update documentation for PandasAI integration"
- ❌ "fix" (too vague)
- ❌ "updates" (not descriptive)

### Step 5: Push to GitHub

Push your commits to the remote repository:
```bash
git push origin main
```

If this is your first push or branch name is different:
```bash
git push -u origin main
```

---

## Common Scenarios

### Scenario 1: First Time Pushing

If you haven't set up the remote yet:
```bash
# Add remote (if not already added)
git remote add origin https://github.com/JeffFutureProof/capstone_project_slackbotjeffc.git

# Push
git push -u origin main
```

### Scenario 2: Authentication Issues

If GitHub asks for credentials:

**Option A: Use Personal Access Token (PAT)**
1. Create a PAT at: https://github.com/settings/tokens
2. Use it as password when prompted
3. Or embed in URL: `git push https://YOUR_TOKEN@github.com/JeffFutureProof/capstone_project_slackbotjeffc.git main`

**Option B: Configure Git Credential Helper**
```bash
git config --global credential.helper store
# Then enter credentials once, they'll be saved
```

### Scenario 3: Remote Has Changes You Don't Have

If you get "Updates were rejected":
```bash
# First, pull remote changes
git pull origin main

# Resolve any conflicts if needed
# Then push again
git push origin main
```

### Scenario 4: Undo Last Commit (Before Pushing)

If you committed but haven't pushed yet:
```bash
# Undo commit but keep changes
git reset --soft HEAD~1

# Or undo commit and discard changes (careful!)
git reset --hard HEAD~1
```

---

## Best Practices

### 1. Commit Frequently
- Commit small, logical changes
- Don't wait until everything is done

### 2. Write Good Commit Messages
- Use present tense: "Add feature" not "Added feature"
- Be specific: "Fix LLM insights not showing" not "fix bug"
- First line should be < 50 characters
- Add details in body if needed

### 3. Review Before Pushing
```bash
# See what you're about to push
git log origin/main..HEAD

# See file changes
git diff origin/main..HEAD
```

### 4. Don't Commit Sensitive Data
- Never commit `.env` files
- Never commit API keys or passwords
- Check `.gitignore` is set up correctly

---

## Complete Workflow Example

```bash
# 1. Check status
git status

# 2. See what changed
git diff

# 3. Stage changes
git add .

# 4. Commit
git commit -m "Add LLM insights to all query functions

- Enhanced prediction function with LLM analysis
- Added insights to SQL query results
- Improved error handling for LLM calls"

# 5. Push
git push origin main
```

---

## Troubleshooting

### "fatal: not a git repository"
You're not in a git repository. Make sure you're in the project directory.

### "error: failed to push some refs"
Remote has changes you don't have. Run `git pull` first.

### "Authentication failed"
- Check your GitHub credentials
- Use a Personal Access Token instead of password
- Verify you have push access to the repository

### "Your branch is ahead of 'origin/main'"
This is normal - it means you have local commits not yet pushed. Just run `git push`.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `git status` | See what files changed |
| `git add .` | Stage all changes |
| `git commit -m "msg"` | Commit with message |
| `git push origin main` | Push to GitHub |
| `git pull origin main` | Get latest from GitHub |
| `git log` | See commit history |
| `git diff` | See what changed |

---

## Your Repository

- **Remote URL**: `https://github.com/JeffFutureProof/capstone_project_slackbotjeffc.git`
- **Default Branch**: `main`

Happy coding! 🚀

