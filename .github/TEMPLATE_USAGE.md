# Using This Template

Thanks for using the Cloudflare Firewall template! 🎉

## Quick Start After Creating from Template

### 1. Clean Up (Optional)
You may want to remove or modify:
- This file (`.github/TEMPLATE_USAGE.md`) - it's only for template users
- `.github/FUNDING.yml` - replace with your own funding info or delete
- `LICENSE` - update the copyright holder if needed

### 2. Configure for Your Use

Follow the main [README.md](../README.md) to set up for your preferred platform:
- **Local Deployment** - For testing and manual runs
- **GitLab CI/CD** - Automated with built-in state management
- **GitHub Actions** - Automated with Terraform Cloud or external backend

### 3. Set Up Credentials

You'll need:
- ☑️ Cloudflare API Token
- ☑️ Cloudflare Account ID
- ☑️ Backend configuration (for CI/CD deployments)

See the [Getting Cloudflare Credentials](../README.md#getting-cloudflare-credentials) section in the README.

### 4. Customize Blocklists

Edit `helpers/downloader.py` to add/remove blocklist sources based on your needs.

### 5. First Run

Test locally first:
```bash
# Comment out the HTTP backend in main.tf
# Then run:
python helpers/downloader.py --output_dir lists
python helpers/processor.py lists --out output.txt
terraform init
terraform plan -var="cf_api_key=$CF_API_TOKEN" -var="cf_acct_id=$CF_ACCOUNT_ID" -var="TF_ROOT=$(pwd)"
```

### 6. Deploy to CI/CD

Once tested locally, push to your preferred platform and configure CI/CD variables/secrets.

## Need Help?

- 📖 Read the comprehensive [README.md](../README.md)
- 🐛 [Report issues](../../issues/new/choose)
- 💡 [Request features](../../issues/new/choose)

---

**You can delete this file after reading it.** It's only meant to help you get started with the template.

