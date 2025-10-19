# Cloudflare DNS Blocklist Manager

This project automatically downloads, processes, and deploys DNS blocklists to Cloudflare Zero Trust using GitLab CI/CD and Terraform.

## Overview

The pipeline performs three main tasks:

1. **Download** - Fetches blocklists from various sources
2. **Process** - Removes duplicates and validates domains/IPs
3. **Deploy** - Uploads the processed lists to Cloudflare Zero Trust as DNS blocking rules

## Prerequisites

- GitLab account with CI/CD enabled
- Cloudflare account with Zero Trust enabled
- Cloudflare API token with appropriate permissions

## Setup Instructions

### 1. Configure Scheduled Pipeline (Optional)

To automatically update your blocklists on a regular schedule:

1. Go to your GitLab project
2. Navigate to **CI/CD → Schedules**
3. Click **New schedule**
4. Configure the schedule:
   - **Description**: "Daily blocklist update" (or your preferred name)
   - **Interval Pattern**: Use cron syntax, examples:
     - `0 2 * * *` - Daily at 2:00 AM
     - `0 */6 * * *` - Every 6 hours
     - `0 0 * * 0` - Weekly on Sunday at midnight
     - `0 3 * * 1,4` - Monday and Thursday at 3:00 AM
   - **Target Branch**: `main` (or `master`)
   - **Activated**: Check the box
5. Click **Save pipeline schedule**

The pipeline will now run automatically according to your schedule, keeping your blocklists up-to-date.

### 2. GitLab CI/CD Variables

Configure the following environment variables in your GitLab project:

**Settings → CI/CD → Variables**

| Variable Name | Description | Required | Protected | Masked |
|--------------|-------------|----------|-----------|---------|
| `CF_API_TOKEN` | Cloudflare API token with Zero Trust permissions | Yes | Yes | Yes |
| `CF_ACCOUNT_ID` | Your Cloudflare account ID | Yes | Yes | No |

#### Getting Your Cloudflare API Token

1. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to **My Profile → API Tokens**
3. Click **Create Token**
4. Use the **Edit Cloudflare Zero Trust** template or create a custom token with:
   - Account: Zero Trust: Edit
   - Account: Access: Apps and Policies: Edit
5. Copy the token and add it to GitLab CI/CD variables as `CF_API_TOKEN`

#### Getting Your Cloudflare Account ID

1. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select your account
3. The Account ID is displayed on the right side of the Overview page
4. Copy it and add it to GitLab CI/CD variables as `CF_ACCOUNT_ID`

### 2. Terraform Backend Configuration

The pipeline uses GitLab's managed Terraform state. No additional configuration is needed as the state is automatically stored in GitLab.

## Pipeline Stages

### Stage 1: Download
- Downloads blocklists from configured sources
- Currently configured sources:
  - Hagezi Multi Pro
  - Mullvad Ad Blocking
  - Mullvad Privacy
- Files are saved to the `lists/` directory
- Artifacts expire after 24 hours

### Stage 2: Process
- Merges all downloaded lists
- Removes duplicates
- Validates domains and IP addresses
- Filters out comments and empty lines
- Creates a single `output.txt` file
- Artifacts expire after 24 hours

### Stage 3: Deploy
- Initializes Terraform with GitLab backend
- Validates Terraform configuration
- **Destroys existing DNS architecture** (ensures clean state)
- Creates new execution plan
- Applies changes to Cloudflare Zero Trust automatically
- Only runs on `main` or `master` branch

**Note:** The pipeline destroys and recreates all DNS blocklists on every run to ensure consistency and prevent drift.

## Customizing Blocklists

To add or remove blocklist sources, edit [`helpers/downloader.py`](helpers/downloader.py):

```python
files = [
    ('https://url-to-blocklist.txt', 'output_filename.txt'),
    # Add more sources here
]
```

## Manual Execution

You can run the scripts manually:

```bash
# Download blocklists
python helpers/downloader.py --output_dir lists

# Process and deduplicate
python helpers/processor.py lists --out output.txt

# Deploy with Terraform
terraform init
terraform plan -var="cf_api_key=YOUR_TOKEN" -var="cf_acct_id=YOUR_ACCOUNT_ID" -var="TF_ROOT=$(pwd)"
terraform apply
```

## Terraform Resources

The deployment creates:

- **Cloudflare Teams Lists** - Domain lists chunked into groups of 1000 domains each
- **Cloudflare Teams Rule** - DNS blocking rule that references all created lists

## Pipeline Triggers

The pipeline runs automatically on:

- **Scheduled runs** (if configured) - all stages including deployment
- **Pushes** to `main` or `master` branch - all stages including deployment
- **Merge requests** - download and process stages only (no deployment)

## Monitoring

After deployment, you can monitor blocked requests in the Cloudflare Zero Trust dashboard:

1. Go to **Analytics → Gateway**
2. View blocked DNS queries
3. Adjust policies as needed

## Troubleshooting

### Terraform state is locked

If you cancel a pipeline during the deploy stage, Terraform's state lock may not be released. You'll see an error like:
```
Error acquiring the state lock
```

**Solution 1: GitLab UI (Recommended)**
1. Go to **Infrastructure → Terraform States**
2. Find the `production` state
3. Click **Unlock**

**Solution 2: Use the unlock job**
1. Go to **CI/CD → Pipelines**
2. Click on the latest pipeline
3. Manually trigger the `unlock_terraform_state` job in the unlock stage
4. Retry the deployment

### Pipeline fails at download stage
- Check internet connectivity
- Verify blocklist URLs are accessible
- Check for rate limiting from source providers

### Pipeline fails at process stage
- Ensure `lists/` directory contains valid text files
- Check for file encoding issues

### Pipeline fails at deploy stage
- Verify `CF_API_TOKEN` has correct permissions
- Verify `CF_ACCOUNT_ID` is correct
- Check Terraform logs for specific errors
- Ensure Zero Trust is enabled on your Cloudflare account

### Too many domains error
Cloudflare has limits on the number of domains per list. The script automatically chunks lists into groups of 1000 domains. If you still encounter issues, you may need to reduce the number of blocklists or implement additional filtering.

## License

This project is provided as-is for personal use.