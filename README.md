# Cloudflare Firewall (DNS Blocklist Manager)

Automatically download, process, and deploy DNS blocklists to Cloudflare Zero Trust using your preferred CI/CD platform (or run locally).

> **🎯 This is a GitHub Template!** Click the **"Use this template"** button above to create your own instance of this project. See [Template Usage Guide](.github/TEMPLATE_USAGE.md) for post-creation setup steps.

## 🎯 Quick Start

Choose your deployment method:

| Method | Setup Time | Best For | State Management |
|--------|------------|----------|------------------|
| **[Local](#local-deployment)** | 5 min | Testing, one-time runs | Local files |
| **[GitLab CI/CD](#gitlab-cicd-deployment)** | 10 min | GitLab users, automated updates | Built-in HTTP backend |
| **[GitHub Actions](#github-actions-deployment)** | 15 min | GitHub users, automated updates | Terraform Cloud (free) |

## Overview

This tool performs three main tasks:

1. **Download** - Fetches blocklists from various sources (Hagezi, Mullvad, etc.)
2. **Process** - Removes duplicates and validates domains/IPs
3. **Deploy** - Uploads processed lists to Cloudflare Zero Trust as DNS blocking rules

**Features:**
- ✅ Automatic deduplication and validation
- ✅ Chunks large lists (1000 domains per Cloudflare list)
- ✅ Configurable entry limits based on account type
- ✅ Scheduled automatic updates (CI/CD)
- ✅ Clean state on each deployment (destroy & recreate)
- ✅ Support for multiple blocklist sources

## Prerequisites

**Required for all deployment methods:**
- Cloudflare account with Zero Trust enabled
- Cloudflare API token with appropriate permissions (see [Getting Credentials](#getting-cloudflare-credentials))
- Python 3.11+ (for local deployment)
- Terraform 1.6.0+ (for local deployment)

## Getting Cloudflare Credentials

### API Token

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to **My Profile → API Tokens**
3. Click **Create Token**
4. Use the **Edit Cloudflare Zero Trust** template or create custom with:
   - Account: Zero Trust: Edit
   - Account: Access: Apps and Policies: Edit
5. Copy the token (save it securely)

### Account ID

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select your account
3. The Account ID is displayed on the right side of the Overview page
4. Copy the Account ID

---

## Local Deployment

Perfect for testing, one-time runs, or manual control.

### Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd cloudflare-firewall

# 2. Install Python dependencies (if needed)
pip install -r requirements.txt  # Create if your scripts need external packages

# 3. Set environment variables
export CF_API_TOKEN="your_cloudflare_api_token"
export CF_ACCOUNT_ID="your_cloudflare_account_id"
```

### Configure Backend for Local Use

By default, `main.tf` is configured with an HTTP backend for CI/CD pipelines. **For local development, you must comment out the HTTP backend** to use local state files:

**Edit `main.tf` and comment out the HTTP backend:**
```terraform
terraform {
  # Comment this out for local development:
  # backend "http" {}
  
  required_providers {
    ...
  }
}
```

> **Important:** The HTTP backend is uncommented by default (for CI/CD). You must manually comment it out before running `terraform init` locally.

### Configure Settings (Optional)

Edit `settings.env` to customize blocklist sources and processing limits:

```bash
# settings.env
FREE_ACCOUNT=false    # true = 1000 entries/list, false = 5000 entries/list
MAX_LISTS=300         # Maximum number of lists to create
BLOCKLISTS=https://codeberg.org/hagezi/mirror2/raw/branch/main/dns-blocklists/wildcard/pro-onlydomains.txt,https://raw.githubusercontent.com/mullvad/dns-blocklists/main/output/doh/doh_adblock.txt,https://raw.githubusercontent.com/mullvad/dns-blocklists/main/output/doh/doh_privacy.txt
```

**What these settings do:**
- `FREE_ACCOUNT`: Controls entries per list (1000 for free, 5000 for enterprise)
- `MAX_LISTS`: Maximum number of Cloudflare lists to create
- `BLOCKLISTS`: Comma-delimited URLs of blocklists to download

**Capacity calculation:**
- Free account: `1000 entries/list × 300 lists = 300,000 max entries`
- Enterprise account: `5000 entries/list × 300 lists = 1,500,000 max entries`

Excess entries are automatically truncated during processing.

### Run Pipeline

```bash
# Step 1: Download blocklists
python helpers/downloader.py --output_dir lists

# Step 2: Process and deduplicate
python helpers/processor.py lists --out output.txt

# Step 3: Deploy with Terraform
terraform init
terraform plan \
  -var="cf_api_key=$CF_API_TOKEN" \
  -var="cf_acct_id=$CF_ACCOUNT_ID" \
  -var="TF_ROOT=$(pwd)"
terraform apply -auto-approve

# Check results
echo "Deployed $(wc -l < output.txt) domains to Cloudflare"
```

### Scheduling Local Runs

Use cron for automatic updates:

```bash
# Edit crontab
crontab -e

# Add entry (runs daily at 2 AM)
0 2 * * * cd /path/to/cloudflare-firewall && ./run.sh >> /var/log/blocklist-update.log 2>&1
```

Create `run.sh`:
```bash
#!/bin/bash
export CF_API_TOKEN="your_token"
export CF_ACCOUNT_ID="your_account_id"

python helpers/downloader.py --output_dir lists
python helpers/processor.py lists --out output.txt
terraform apply -auto-approve \
  -var="cf_api_key=$CF_API_TOKEN" \
  -var="cf_acct_id=$CF_ACCOUNT_ID" \
  -var="TF_ROOT=$(pwd)"
```

---

## GitLab CI/CD Deployment

Automated pipeline with built-in state management using GitLab's HTTP backend.

### Setup

#### 1. Push Code to GitLab

```bash
git remote add gitlab https://gitlab.com/username/cloudflare-firewall.git
git push gitlab main
```

#### 2. Configure CI/CD Variables

Go to **Settings → CI/CD → Variables** and add:

| Variable | Value | Protected | Masked |
|----------|-------|-----------|--------|
| `CF_API_TOKEN` | Your Cloudflare API token | ✅ Yes | ✅ Yes |
| `CF_ACCOUNT_ID` | Your Cloudflare account ID | ✅ Yes | ❌ No |

#### 3. Configure Schedule (Optional)

To run automatically:

1. Go to **CI/CD → Schedules**
2. Click **New schedule**
3. Configure:
   - **Description**: "Daily blocklist update"
   - **Interval Pattern**: Cron expression (see examples below)
   - **Target Branch**: `main`
   - **Activated**: ✅ Check
4. Save

**Cron Examples:**
- `0 2 * * *` - Daily at 2:00 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 3 * * 1,4` - Monday and Thursday at 3:00 AM UTC

### Pipeline Configuration

The pipeline is defined in `.gitlab-ci.yml`:

**Stages:**
1. **download** - Fetches blocklists (Python 3.11-slim container)
2. **process** - Deduplicates and validates (Python 3.11-slim container)
3. **deploy** - Applies to Cloudflare (Terraform 1.6.0 container)

**Triggers:**
- Scheduled runs (if configured)
- Push to `main` or `master` branch
- Merge requests (download + process only, no deploy)

**State Management:**
- Uses GitLab's built-in HTTP Terraform backend
- State stored at: `/projects/{PROJECT_ID}/terraform/state/production`
- Automatic authentication via `CI_JOB_TOKEN`
- No additional backend configuration needed

**Timeouts:**
- All jobs: 12 hours (configurable in `.gitlab-ci.yml`)

### Monitoring

View pipeline status:
- **CI/CD → Pipelines** - See all pipeline runs
- **CI/CD → Jobs** - View individual job logs

After deployment, monitor blocked requests:
- **Cloudflare Dashboard → Analytics → Gateway**

---

## GitHub Actions Deployment

Automated workflow with flexible backend options for GitHub repositories.

> **💡 Recommended Backend:** Use [Terraform Cloud's free tier](https://app.terraform.io/) for state management. Unlike GitLab, GitHub Actions doesn't have a built-in Terraform backend, but Terraform Cloud provides a purpose-built, free solution that's easy to set up.

### Setup

#### 1. Push Code to GitHub

```bash
git remote add github https://github.com/username/cloudflare-firewall.git
git push github main
```

#### 2. Configure Secrets

Go to **Settings → Secrets and variables → Actions → Secrets**

**Required:**
- `CF_API_TOKEN` - Your Cloudflare API token
- `CF_ACCOUNT_ID` - Your Cloudflare account ID
- `TF_CLOUD_TOKEN` - Terraform Cloud API token (recommended)
  - OR `TF_BACKEND_PASSWORD` - If using GitLab/other HTTP backend

#### 3. Configure Variables

Go to **Settings → Secrets and variables → Actions → Variables**

**For Terraform Cloud (recommended):**
- `TF_CLOUD_ORGANIZATION` - Your Terraform Cloud organization name
- `TF_WORKSPACE` - Your workspace name

**For GitLab HTTP backend:**
- `TF_BACKEND_ADDRESS` - Backend URL (e.g., `https://gitlab.com/api/v4/projects/{ID}/terraform/state/production`)
- `TF_BACKEND_LOCK_ADDRESS` - Lock endpoint URL
- `TF_BACKEND_UNLOCK_ADDRESS` - Unlock endpoint URL
- `TF_BACKEND_USERNAME` - Backend username

### Workflow Configuration

**Triggers:**
- Push to `main` or `master` branch (full pipeline)
- Pull requests (download + process only, no deploy)
- Schedule: Daily at midnight UTC (configurable)
- Manual trigger via Actions tab

**Jobs:**
1. **download_lists** - Downloads blocklists (Python 3.11)
2. **process_lists** - Processes and deduplicates (Python 3.11)
3. **deploy_to_cloudflare** - Deploys via Terraform (1.6.0)

**State Management:**
- Remote backend required (Terraform Cloud recommended, or GitLab HTTP/S3/etc.)
- State persists across runs
- Supports state locking
- Team-friendly
- Requires backend configuration (see Backend Options below)

### Backend Options

> **Important Note:** Unlike GitLab CI/CD, GitHub Actions does NOT have a built-in Terraform state backend. GitLab provides a native HTTP backend API (`/projects/{id}/terraform/state/`) with automatic authentication. GitHub requires you to use an external backend provider.

#### Option 1: Terraform Cloud (Free Tier) ✅ Recommended for GitHub
Use Terraform Cloud's free tier for reliable, purpose-built state management.

**Setup Steps:**
1. Create a free account at [app.terraform.io](https://app.terraform.io/)
2. Create an organization (e.g., "my-org")
3. Create a workspace (e.g., "cloudflare-firewall")
4. Generate an API token: User Settings → Tokens → Create an API token
5. Configure workspace settings:
   - Execution Mode: **Remote** or **Local** (Local recommended for this use case)
   - Terraform Version: 1.6.0 or later

**GitHub Repository Configuration:**
- **Variables:**
  - `TF_CLOUD_ORGANIZATION`: Your Terraform Cloud organization name
  - `TF_WORKSPACE`: Your workspace name (e.g., "cloudflare-firewall")
- **Secrets:**
  - `TF_CLOUD_TOKEN`: Your Terraform Cloud API token

**Workflow Configuration:**
Edit `.github/workflows/deploy.yml`, replace the Terraform Init step:
```yaml
- name: Terraform Init
  run: terraform init
  env:
    TF_CLOUD_ORGANIZATION: ${{ vars.TF_CLOUD_ORGANIZATION }}
    TF_WORKSPACE: ${{ vars.TF_WORKSPACE }}
    TF_TOKEN_app_terraform_io: ${{ secrets.TF_CLOUD_TOKEN }}
```

**Benefits of Terraform Cloud:**
- ✅ Purpose-built for Terraform state management
- ✅ Free tier includes state management, locking, and versioning
- ✅ Web UI for viewing state and run history
- ✅ Team collaboration features
- ✅ No need for additional cloud accounts
- ✅ Automatic state backup and versioning
- ✅ Native integration with GitHub Actions

#### Option 2: Use GitLab's HTTP Backend from GitHub Actions
You can use GitLab's HTTP backend even when running GitHub Actions. This requires the current `deploy.yml` configuration:

**GitHub Repository Configuration:**
- **Variables:**
  - `TF_BACKEND_ADDRESS`: `https://gitlab.com/api/v4/projects/{PROJECT_ID}/terraform/state/production`
  - `TF_BACKEND_LOCK_ADDRESS`: `https://gitlab.com/api/v4/projects/{PROJECT_ID}/terraform/state/production/lock`
  - `TF_BACKEND_UNLOCK_ADDRESS`: `https://gitlab.com/api/v4/projects/{PROJECT_ID}/terraform/state/production/lock`
  - `TF_BACKEND_USERNAME`: Your GitLab username or `gitlab-ci-token`
- **Secrets:**
  - `TF_BACKEND_PASSWORD`: GitLab Personal Access Token with `api` scope

**How to get GitLab credentials:**
1. Create a project on GitLab (can be private, empty repo)
2. Get the Project ID from the GitLab project page
3. Create a Personal Access Token: GitLab → Preferences → Access Tokens → Add new token
   - Name: `github-actions-terraform`
   - Scopes: ✅ `api`
   - Expiration: Set as needed
4. Use the token as `TF_BACKEND_PASSWORD` in GitHub

**Benefits:**
- ✅ Free (GitLab Free tier includes Terraform state)
- ✅ State locking included
- ✅ GitLab's robust HTTP backend
- ✅ Works from any CI/CD platform
- ✅ No workflow file changes needed (already configured)

#### Option 3: AWS S3 Backend
Edit `.github/workflows/deploy.yml`, replace Terraform Init step:
```yaml
- name: Terraform Init
  run: |
    terraform init \
      -backend-config="bucket=${{ vars.TF_STATE_BUCKET }}" \
      -backend-config="key=cloudflare-dns/terraform.tfstate" \
      -backend-config="region=${{ vars.AWS_REGION }}"
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### Monitoring

View workflow runs:
- Go to **Actions** tab in GitHub repository
- Click on workflow name to see runs
- Click on specific run to see detailed logs

Use GitHub CLI:
```bash
# List recent runs
gh run list

# Watch latest run in real-time
gh run watch

# View logs
gh run view --log

# Manually trigger workflow
gh workflow run deploy.yml
```

---

## Platform Comparison

### Features

| Feature | Local | GitLab CI/CD | GitHub Actions |
|---------|-------|--------------|----------------|
| **Setup Complexity** | Low | Medium | Medium-High |
| **Automation** | Manual/Cron | ✅ Built-in | ✅ Built-in |
| **Terraform State Backend** | Local files | ✅ Built-in HTTP API | ❌ None (external required) |
| **State Management** | Local files | Native GitLab backend | Terraform Cloud/GitLab/S3 |
| **State Locking** | ❌ No | ✅ Yes | ✅ Yes (with backend) |
| **Team Collaboration** | ❌ No | ✅ Yes | ✅ Yes (with backend) |
| **Scheduled Runs** | Cron | ✅ Built-in scheduler | ✅ Built-in scheduler |
| **Logs/Artifacts** | Local files | 24-hour retention | 1-day retention (configurable) |
| **Cost** | Free (your compute) | Free tier available | Free (TF Cloud free tier) |
| **Internet Required** | ✅ Yes | ✅ Yes | ✅ Yes |

### When to Use Each

**Use Local when:**
- ✅ Testing the setup
- ✅ One-time deployment
- ✅ You have a dedicated machine for automation
- ✅ Learning how the tool works
- ✅ No need for team collaboration

**Use GitLab CI/CD when:**
- ✅ Your code is already on GitLab
- ✅ You want automated updates
- ✅ You need team collaboration
- ✅ You want built-in state management
- ✅ You prefer GitLab's interface

**Use GitHub Actions when:**
- ✅ Your code is already on GitHub
- ✅ You want automated updates
- ✅ You need team collaboration
- ✅ You can use Terraform Cloud (recommended) or other external backend
- ✅ You prefer GitHub's interface
- ⚠️ Note: Requires external backend for production (Terraform Cloud free tier recommended)

### Variable/Secret Mapping

| Purpose | Local | GitLab CI/CD | GitHub Actions |
|---------|-------|--------------|----------------|
| Cloudflare API Token | `$CF_API_TOKEN` | `$CF_API_TOKEN` (CI/CD var) | `${{ secrets.CF_API_TOKEN }}` |
| Cloudflare Account ID | `$CF_ACCOUNT_ID` | `$CF_ACCOUNT_ID` (CI/CD var) | `${{ secrets.CF_ACCOUNT_ID }}` |
| Project Directory | `$(pwd)` | `$CI_PROJECT_DIR` | `${{ github.workspace }}` |
| Backend Token | N/A | `$CI_JOB_TOKEN` (auto) | `${{ secrets.TF_BACKEND_PASSWORD }}` |

---

## Configuration

### Settings Configuration (`settings.env`)

The `settings.env` file controls blocklist sources and processing limits:

| Parameter | Description | Values |
|-----------|-------------|--------|
| `FREE_ACCOUNT` | Account type | `true` (1000 entries/list) or `false` (5000 entries/list) |
| `MAX_LISTS` | Maximum number of lists | Numeric value (e.g., `300`) |
| `BLOCKLISTS` | Blocklist URLs to download | Comma-delimited URLs |

**Example configuration:**

```bash
# Account settings
FREE_ACCOUNT=false
MAX_LISTS=300

# Blocklist sources (comma-delimited URLs)
BLOCKLISTS=https://codeberg.org/hagezi/mirror2/raw/branch/main/dns-blocklists/wildcard/pro-onlydomains.txt,https://raw.githubusercontent.com/mullvad/dns-blocklists/main/output/doh/doh_adblock.txt,https://raw.githubusercontent.com/mullvad/dns-blocklists/main/output/doh/doh_privacy.txt
```

**Capacity calculation:**
- Free account: `1000 entries/list × 300 lists = 300,000 max entries`
- Enterprise account: `5000 entries/list × 300 lists = 1,500,000 max entries`

**Blocklist URLs:**
- Add or remove blocklist URLs by editing the comma-delimited `BLOCKLISTS` parameter
- URLs must be publicly accessible
- Filenames are automatically generated based on the domain and URL hash
- If `BLOCKLISTS` is empty, the downloader falls back to default lists

The processor automatically truncates entries beyond the calculated limit. You'll see the entry count in the output:
```
Processing completed! Entries processed: 245832/1500000
```

### Customizing Blocklists

**Recommended method:** Edit the `BLOCKLISTS` parameter in `settings.env`:

```bash
# Add or remove URLs (comma-delimited, no spaces between URLs)
BLOCKLISTS=https://url1.com/list.txt,https://url2.com/list.txt,https://url3.com/list.txt
```

**Alternative method:** Directly edit `helpers/downloader.py` if you need custom filename control. The downloader will use fallback lists if `BLOCKLISTS` is not defined in `settings.env`.

**Popular blocklist sources:**
- Hagezi: https://github.com/hagezi/dns-blocklists
  - Example: `https://codeberg.org/hagezi/mirror2/raw/branch/main/dns-blocklists/wildcard/pro-onlydomains.txt`
- OISD: https://oisd.nl/
  - Example: `https://big.oisd.nl/domainswild`
- StevenBlack: https://github.com/StevenBlack/hosts
  - Example: `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`
- Mullvad: https://mullvad.net/
  - Ad blocking: `https://raw.githubusercontent.com/mullvad/dns-blocklists/main/output/doh/doh_adblock.txt`
  - Privacy: `https://raw.githubusercontent.com/mullvad/dns-blocklists/main/output/doh/doh_privacy.txt`

---

## Troubleshooting

### Common Issues (All Platforms)

#### Issue: Download fails
**Causes:**
- Blocklist source is down or slow
- Rate limiting from source
- Network connectivity

**Solutions:**
```bash
# Test download manually
curl -I https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/domains/multi-pro.txt

# Check network connectivity
ping 8.8.8.8

# Increase timeout in downloader.py if needed
```

#### Issue: Processing fails
**Causes:**
- Downloaded files are corrupted
- Insufficient disk space
- Invalid domain formats

**Solutions:**
```bash
# Check downloaded files
ls -lh lists/
head lists/*.txt

# Check disk space
df -h

# Manually test processor
python helpers/processor.py lists --out test-output.txt
```

#### Issue: Terraform deployment fails
**Causes:**
- Invalid Cloudflare credentials
- API rate limiting
- Too many domains (Cloudflare limits)
- Zero Trust not enabled

**Solutions:**
```bash
# Verify credentials
export CF_API_TOKEN="your_token"
export CF_ACCOUNT_ID="your_account"

# Test Terraform independently
terraform init
terraform validate
terraform plan -var="cf_api_key=$CF_API_TOKEN" -var="cf_acct_id=$CF_ACCOUNT_ID" -var="TF_ROOT=$(pwd)"

# Check Terraform logs
terraform apply -var="cf_api_key=$CF_API_TOKEN" -var="cf_acct_id=$CF_ACCOUNT_ID" -var="TF_ROOT=$(pwd)" 2>&1 | tee terraform.log
```

**Verify Zero Trust is enabled:**
1. Go to Cloudflare Dashboard
2. Navigate to Zero Trust section
3. Ensure Gateway is configured

#### Issue: Too many domains error
**Cause:** Cloudflare has limits per list (typically 1000)

**Solution:** The processor automatically chunks lists, but if you still hit limits:
```python
# Edit the chunking size in your Terraform configuration
# Reduce from 1000 to 500 or adjust processing logic
```

### Platform-Specific Issues

#### Local Deployment

**Issue: Python/Terraform not found**
```bash
# Install Python 3.11
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
# Windows: Download from python.org

# Install Terraform
# macOS: brew install terraform
# Ubuntu: wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
# Windows: Download from terraform.io
```

**Issue: Permission denied**
```bash
chmod +x run.sh
```

#### GitLab CI/CD

**Issue: Pipeline doesn't trigger**
- Verify `.gitlab-ci.yml` is in repository root
- Check CI/CD is enabled: **Settings → CI/CD → General pipelines**
- Verify runner is available: **Settings → CI/CD → Runners**

**Issue: CI/CD variables not found**
- Go to **Settings → CI/CD → Variables**
- Verify variable names match exactly (case-sensitive)
- Ensure variables are not marked as "Environment scope" specific

**Issue: State locking errors**
```yaml
# Locking is disabled in the workflow with -lock=false
# This is intentional for single-user environments
# If you need locking, remove -lock=false flags from .gitlab-ci.yml
```

#### GitHub Actions

**Issue: Workflow doesn't appear in Actions tab**
```bash
# Ensure workflow file is in correct location
ls .github/workflows/

# Ensure YAML is valid
yamllint .github/workflows/*.yml

# Push to trigger
git push origin main
```

**Issue: Secrets not accessible**
- Verify secrets are set in **Settings → Secrets and variables → Actions**
- Secret names are case-sensitive
- Secrets don't show values (by design)
- Use `secrets.SECRET_NAME` not `vars.SECRET_NAME`

**Issue: Artifacts not found**
- Previous job must complete successfully
- Artifact names must match between upload/download
- Check retention period (default 1 day)

**Issue: Backend configuration fails**
```bash
# Verify all backend variables are set
curl -I $TF_BACKEND_ADDRESS

# Check variables are configured correctly in GitHub
gh variable list
gh secret list
```

---

## Advanced Configuration

### Adjusting Timeouts

**Local:** No timeout (runs until complete)

**GitLab CI/CD:** Edit `.gitlab-ci.yml`
```yaml
default:
  timeout: 12h  # Change to your preferred timeout
```

**GitHub Actions:** Edit workflow file
```yaml
jobs:
  download_lists:
    timeout-minutes: 720  # Change to your preferred timeout (in minutes)
```

### Artifact Retention

**GitLab CI/CD:** Edit `.gitlab-ci.yml`
```yaml
artifacts:
  expire_in: 24 hours  # Change to: 1 hour, 7 days, 1 week, etc.
```

**GitHub Actions:** Edit workflow file
```yaml
- uses: actions/upload-artifact@v4
  with:
    retention-days: 1  # Change to your preferred days
```

### Custom Schedule

**Local (cron):**
```bash
# Edit crontab
crontab -e

# Examples:
# 0 */6 * * *     # Every 6 hours
# 0 2,14 * * *    # 2 AM and 2 PM daily
# 0 0 * * 0       # Weekly on Sunday
# */30 * * * *    # Every 30 minutes
```

**GitLab CI/CD:**
- Use the web UI scheduler (as described in setup)
- Or add schedule-specific rules in `.gitlab-ci.yml`

**GitHub Actions:** Edit workflow file
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
    - cron: '0 12 * * *' # Daily at noon (multiple schedules supported)
```

Use [crontab.guru](https://crontab.guru/) to generate cron expressions.

---

## Security Best Practices

1. **Never commit credentials to repository**
   ```bash
   # Add to .gitignore
   echo "*.env" >> .gitignore
   echo "terraform.tfstate*" >> .gitignore
   echo "*.tfvars" >> .gitignore
   ```

2. **Use secrets management**
   - Local: Use environment variables or secrets managers
   - GitLab: Use CI/CD Variables with "Masked" enabled
   - GitHub: Use Repository Secrets

3. **Limit API token permissions**
   - Create token with minimum required permissions
   - Use different tokens for dev/prod if possible
   - Rotate tokens regularly

4. **Enable branch protection**
   - Require reviews for main branch
   - Prevent force pushes
   - Require status checks to pass

5. **Review logs carefully**
   - Ensure credentials don't leak in logs
   - Monitor Cloudflare API usage
   - Set up alerting for failures

6. **Regular updates**
   - Keep Python dependencies updated
   - Update Terraform to latest stable version
   - Update CI/CD runner images

---

## Backend Configuration

The project uses different backend configurations depending on the deployment method:

### CI/CD (GitLab/GitHub Actions) - Default
- **Backend:** HTTP backend (configured via command line)
- **Configuration:** `backend "http" {}` is uncommented in `main.tf`
- **Use when:** Running in automated pipelines
- **State:** Stored remotely (GitLab HTTP backend or Terraform Cloud)

### Local Development
- **Backend:** Local state files (`terraform.tfstate`)
- **Configuration:** Comment out `backend "http" {}` in `main.tf`
- **Use when:** Running manually on your machine
- **State:** Stored in working directory

**To switch from CI/CD to Local:**
1. Edit `main.tf`
2. Comment out the line: `# backend "http" {}`
3. Run `terraform init` to reinitialize with local backend

**To switch from Local to CI/CD:**
1. Edit `main.tf`
2. Uncomment the line: `backend "http" {}`
3. Commit and push to trigger CI/CD pipeline

> **Tip:** You can maintain separate branches for local vs CI/CD if you frequently switch between them, or use `.gitignore` to exclude local state files.

---

## Terraform Resources

The deployment creates:

| Resource Type | Purpose | Naming |
|---------------|---------|--------|
| `cloudflare_teams_list` | Domain lists | `master_domain_list_{0,1,2...}` |
| `cloudflare_teams_rule` | DNS blocking rule | `DNS Block Protection` |

**Resource Management:**
- Destroys all resources on each run
- Creates fresh lists from processed output
- Ensures no drift from manual changes
- State locking disabled by default (single-user)

---

## Monitoring & Logs

### View Blocked Requests

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **Zero Trust → Analytics → Gateway**
3. Filter by:
   - **Action**: Block
   - **Time Range**: Last 24 hours (or custom)
4. Export data if needed

### Pipeline Logs

**Local:**
```bash
# Redirect to file
./run.sh > blocklist-update.log 2>&1

# View logs
tail -f blocklist-update.log
```

**GitLab CI/CD:**
- Go to **CI/CD → Pipelines**
- Click on pipeline run
- Click on job to view logs
- Download job logs if needed

**GitHub Actions:**
```bash
# Using GitHub CLI
gh run list
gh run view --log
gh run watch  # Real-time

# Or use web interface
# Actions → Click run → Click job → View logs
```

---

## Migrating Between Platforms

### GitLab → GitHub

1. Push code to GitHub
2. Configure GitHub secrets (same values as GitLab variables)
3. Configure backend (Terraform Cloud recommended, or continue using GitLab HTTP backend)
4. Optionally migrate Terraform state:
   ```bash
   terraform init -migrate-state
   ```

### GitHub → GitLab

1. Push code to GitLab
2. Configure GitLab CI/CD variables (same values as GitHub secrets)
3. Pipeline auto-uses GitLab HTTP backend
4. Optionally migrate Terraform state

### Local → CI/CD

1. Push code to your platform
2. Configure secrets/variables from your local environment variables
3. Test with manual trigger first
4. Enable scheduling after successful test

### CI/CD → Local

1. Clone repository
2. Set environment variables
3. Run pipeline steps manually
4. State will be local (not shared with CI/CD)

---

## FAQ

**Q: Why doesn't GitHub Actions have built-in Terraform state storage like GitLab?**  
A: GitLab includes a native HTTP backend API for Terraform state as part of its platform (`/api/v4/projects/{id}/terraform/state/`). GitHub Actions does not provide an equivalent service. For GitHub Actions, we recommend:
- **Terraform Cloud** (recommended - free tier, purpose-built for Terraform)
- GitLab's HTTP backend from GitHub Actions (free, works cross-platform)
- Cloud storage (AWS S3, Azure Blob, Google Cloud Storage)

**Q: How often should I update blocklists?**  
A: Daily updates are typical. Adjust based on your needs and blocklist source update frequency.

**Q: Can I run multiple instances simultaneously?**  
A: Not recommended without state locking. Use remote backend with locking enabled for concurrent runs.

**Q: Will this affect my existing Cloudflare DNS settings?**  
A: No, this only manages Zero Trust Gateway blocklists, not your DNS records.

**Q: What happens if a pipeline fails?**  
A: No changes are applied to Cloudflare. Fix the issue and re-run. Previous deployment remains active.

**Q: Can I use custom blocklists?**
A: Yes! Edit the `BLOCKLISTS` parameter in `settings.env` with comma-delimited URLs, or directly edit `helpers/downloader.py` for more control.

**Q: How do I temporarily disable blocking?**  
A: In Cloudflare Dashboard, go to **Zero Trust → Gateway → Firewall Policies** and disable the rule.

**Q: Can I whitelist specific domains?**  
A: Yes, create a whitelist rule in Cloudflare Gateway that runs before the block rule.

**Q: How much does this cost?**  
A: Depends on your plan:
- **Cloudflare Zero Trust:** Free tier available (check limits)
- **GitLab/GitHub:** Free tier available for CI/CD
- **Local:** Only your compute/network costs

**Q: Is state locking required?**  
A: Not for single-user setups. The provided configs disable locking for simplicity. Enable it for team environments.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Quick contribution ideas:**
- Additional blocklist sources
- Improved processing logic
- Better error handling
- Support for more CI/CD platforms
- Documentation improvements

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes and test
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Feel free to use this template for your own deployments or fork it for customization.

---

## Support

- **Issues:** Open an issue on your Git platform
- **Cloudflare Docs:** https://developers.cloudflare.com/cloudflare-one/
- **Terraform Docs:** https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs
- **GitLab CI/CD:** https://docs.gitlab.com/ee/ci/
- **GitHub Actions:** https://docs.github.com/actions

---

**Project Structure:**
```
cloudflare-firewall/
├── .github/workflows/       # GitHub Actions workflows
│   └── deploy.yml          # GitHub Actions workflow (requires remote backend)
├── .gitlab-ci.yml          # GitLab CI/CD pipeline
├── helpers/
│   ├── downloader.py       # Downloads blocklists
│   └── processor.py        # Processes and deduplicates
├── lists/                  # Downloaded blocklists (generated)
├── main.tf                 # Terraform main configuration
├── parse.tf                # Terraform parsing logic
├── upload.tf               # Terraform upload configuration
├── settings.env            # Entry limits configuration
├── output.txt              # Processed output (generated)
└── README.md               # This file
```
