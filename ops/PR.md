# Pull Request Workflow

## Pre-PR Checklist

Before opening a pull request, ensure all checks pass:

### 1. Run Local Checks

```bash
# Run linter
ruff check .

# Run type checker
mypy .

# Run tests
pytest

# Run security/dependency scan
pip-audit
```

### 2. Review Changes

## Opening a Pull Request

### 1. Create Branch (if not already)

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Commit Changes

```bash
git add .
git commit -m "Description of changes"
```

### 3. Push Branch

```bash
git push -u origin feature/your-feature-name
```

### 4. Create PR

```bash
gh pr create --title "Your PR Title" --body-file PR.md --base main
```

Or interactively:

```bash
gh pr create
```

---

## PR Description Template

Use this structure for PR descriptions:

```markdown
## Summary
Brief description of what this PR does

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Tests pass locally
- [ ] Lint passes
- [ ] Type check passes
- [ ] Manual testing (if applicable)

## Checklist
- [ ] Code follows SOLID principles
- [ ] Privacy checks passed
- [ ] Documentation updated

## Screenshots (if UI changes)
```

---

## After PR Opened

### 1. Monitor CI

```bash
# View PR checks
gh pr checks

# Watch workflow status
gh run watch
```

### 2. Address CI Failures

If CI fails:

1. Check error logs in GitHub Actions
2. Fix issues locally
3. Push updates
4. Wait for CI to rerun

---

## CI Workflow Reference

The CI pipeline includes:

1. **Lint** - Code style and quality checks
2. **Type Check** - Static type analysis
3. **Tests** - Unit and integration tests
4. **Security Scan** - Dependency vulnerability scanning

All must pass before merging.

---

## Merge Conflicts

```bash
git fetch origin
git rebase origin/main
# Fix conflicts
git push --force-with-lease
```

### Need to Amend PR

```bash
# Make changes
git commit --amend
git push --force-with-lease
```
