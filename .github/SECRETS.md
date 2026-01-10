# GitHub Repository Secrets Configuration

This document lists all secrets required for CI/CD workflows to function properly.

---

## 🔑 Required Secrets

### Build & Testing

| Secret Name | Required For | Description | Example Value |
|-------------|--------------|-------------|---------------|
| `DATABASE_URL` | Build test | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `NEXTAUTH_SECRET` | Build test | NextAuth.js secret key | Generate with `openssl rand -base64 32` |

**Note:** Build tests will use dummy values if these are not configured. Real secrets only needed for actual deployments.

---

### Deployment (Vercel)

| Secret Name | Required For | Description | Where to Find |
|-------------|--------------|-------------|---------------|
| `VERCEL_TOKEN` | Preview & Production deploys | Vercel API token | [Vercel Dashboard](https://vercel.com/account/tokens) → Settings → Tokens |
| `VERCEL_ORG_ID` | Preview & Production deploys | Vercel team/org ID | Project Settings → General → Project ID section |
| `VERCEL_PROJECT_ID` | Preview & Production deploys | Vercel project ID | Project Settings → General → Project ID |

**Note:** Deployment steps are skipped if Vercel secrets are not configured.

---

## 📋 How to Add Secrets

### Via GitHub Web UI

1. Go to your repository on GitHub
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add the secret name and value
6. Click **Add secret**

### Via GitHub CLI

```bash
# Database URL
gh secret set DATABASE_URL -b "postgresql://user:pass@host:5432/dendra"

# NextAuth Secret (generate a random 32-char string)
gh secret set NEXTAUTH_SECRET -b "$(openssl rand -base64 32)"

# Vercel Token (from Vercel dashboard)
gh secret set VERCEL_TOKEN -b "your-vercel-token-here"

# Vercel Org ID (from Vercel project settings)
gh secret set VERCEL_ORG_ID -b "your-org-id-here"

# Vercel Project ID (from Vercel project settings)
gh secret set VERCEL_PROJECT_ID -b "your-project-id-here"
```

---

## 🔍 Verifying Secrets

### Check if secrets are configured

```bash
# List all secrets (won't show values, just names)
gh secret list

# Expected output:
# DATABASE_URL         Updated 2025-11-08
# NEXTAUTH_SECRET      Updated 2025-11-08
# VERCEL_TOKEN         Updated 2025-11-08
# VERCEL_ORG_ID        Updated 2025-11-08
# VERCEL_PROJECT_ID    Updated 2025-11-08
```

### Test a workflow with secrets

```bash
# Trigger the CI workflow manually
gh workflow run ci.yml

# Check the workflow run
gh run list --workflow=ci.yml

# View details of the latest run
gh run view
```

---

## 🚨 Secret Security Best Practices

### ✅ DO

- Generate secrets using cryptographically secure methods
- Rotate secrets regularly (every 90 days)
- Use different secrets for staging and production
- Limit secret access to necessary workflows only
- Delete secrets that are no longer needed

### ❌ DON'T

- Never commit secrets to the repository
- Don't share secrets via email or chat
- Don't log secret values in workflow output
- Don't use weak or predictable secrets
- Don't reuse secrets across different services

---

## 🔄 Current Workflow Behavior

### Without Secrets Configured

| Workflow Step | Behavior |
|---------------|----------|
| Code Quality | ✅ Runs normally |
| Build Test | ✅ Uses dummy values |
| Security Scan | ✅ Runs normally |
| Unit Tests | ✅ Runs normally |
| Preview Deploy | ⏭️  **Skipped** (gracefully) |
| Production Deploy | ⏭️  **Skipped** (gracefully) |

**Result:** CI/CD passes even without deployment secrets.

### With Secrets Configured

| Workflow Step | Behavior |
|---------------|----------|
| Code Quality | ✅ Runs normally |
| Build Test | ✅ Uses real secrets |
| Security Scan | ✅ Runs normally |
| Unit Tests | ✅ Runs normally |
| Preview Deploy | 🚀 **Deploys** to Vercel preview |
| Production Deploy | 🚀 **Deploys** to Vercel production |

**Result:** Full CI/CD with automatic deployments.

---

## 📊 Priority Levels

### Critical (Required for Production)

1. ✅ `DATABASE_URL` - Must be set before production deploy
2. ✅ `NEXTAUTH_SECRET` - Must be set before production deploy
3. ✅ `VERCEL_TOKEN` - Required for automatic deployments

### Important (Required for Full CI/CD)

4. ✅ `VERCEL_ORG_ID` - Required for Vercel deployments
5. ✅ `VERCEL_PROJECT_ID` - Required for Vercel deployments

---

## 🛠️ Troubleshooting

### "Context access might be invalid" Warnings

**Issue:** GitHub Actions linter shows warnings for undefined secrets.

**Solution:** These are just warnings, not errors. Workflows are designed to handle missing secrets gracefully.

```yaml
# Workflows use fallback values:
DATABASE_URL: ${{ secrets.DATABASE_URL || 'postgresql://dummy...' }}

# Or skip steps if secrets are missing:
if: secrets.VERCEL_TOKEN != ''
```

### Deployment Steps Skipped

**Issue:** Preview or production deployments don't run.

**Causes:**
1. Secrets not configured (check with `gh secret list`)
2. Not on correct branch (production only on `main`)
3. Not correct event type (preview only on PRs)

**Solution:** Configure missing secrets or check workflow conditions.

### Build Fails with "DATABASE_URL is required"

**Issue:** Next.js build requires `DATABASE_URL` at build time.

**Solution:** Ensure secret is set, or workflow will use dummy value (sufficient for build test).

---

## 📚 Related Documentation

- [GitHub Actions Secrets Docs](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vercel CLI Docs](https://vercel.com/docs/cli)
- [NextAuth.js Configuration](https://next-auth.js.org/configuration/options)

---

## 📝 Checklist: First-Time Setup

- [ ] Generate `NEXTAUTH_SECRET` with `openssl rand -base64 32`
- [ ] Add `DATABASE_URL` from Supabase/PostgreSQL provider
- [ ] Get `VERCEL_TOKEN` from Vercel dashboard
- [ ] Get `VERCEL_ORG_ID` from Vercel project settings
- [ ] Get `VERCEL_PROJECT_ID` from Vercel project settings
- [ ] Add all secrets via GitHub UI or CLI
- [ ] Verify secrets with `gh secret list`
- [ ] Test workflow with `gh workflow run ci.yml`
- [ ] Check workflow run with `gh run view`

---

**Last Updated:** 2025-11-08  
**Maintainer:** Development Team  
**Status:** Production-Ready

