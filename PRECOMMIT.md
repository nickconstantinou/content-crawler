# Pre-commit Hook Setup

## Manual Setup Required

Due to sandbox restrictions, you need to set this up manually on the host machine:

```bash
# On your host machine (not in sandbox)
cd ~/workspace/projects/content-crawler

# Copy the hook
cp pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Testing the Hook

```bash
# Test the script directly
./pre-commit.sh
# Or
.git/hooks/pre-commit
```

## What Happens

1. **Before `git commit`** → Runs `pytest test_crawler.py`
2. **If tests pass** → Commit proceeds
3. **If tests fail** → Commit blocked, must fix issues first

## Bypass (Emergency)

If you need to commit without running tests:

```bash
git commit --no-verify -m "Emergency fix"
```

## CI/CD (GitHub Actions)

The `.github/workflows/test.yml` runs automatically on:
- Every push to main/master
- Every pull request

Tests run on GitHub's runners - no local setup needed.

## Quick Test Before Push

Always run locally before pushing:

```bash
cd ~/workspace/projects/content-crawler
python3 -m pytest test_crawler.py -v
```
