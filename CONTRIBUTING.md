# Contributing to Cloudflare Firewall

Thank you for considering contributing to this project! 🎉

## Ways to Contribute

### 1. Report Bugs
Found a bug? [Open an issue](../../issues/new?template=bug_report.md) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (local/GitLab/GitHub)
- Relevant logs

### 2. Suggest Features
Have an idea? [Open a feature request](../../issues/new?template=feature_request.md) with:
- Description of the feature
- Use case and benefits
- Proposed implementation (if you have ideas)

### 3. Submit Pull Requests

#### Before You Start
- Check existing issues and PRs to avoid duplicates
- For major changes, open an issue first to discuss

#### Development Process
1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make your changes**
   - Follow the existing code style
   - Test locally before submitting
   - Update documentation if needed

4. **Test your changes**
   ```bash
   # Test the download step
   python helpers/downloader.py --output_dir lists
   
   # Test the processing step
   python helpers/processor.py lists --out output.txt
   
   # Test Terraform (with local backend)
   terraform init
   terraform plan
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new blocklist source"
   # or
   git commit -m "fix: resolve download timeout issue"
   ```
   
   Use conventional commit messages:
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `ci:` - CI/CD changes
   - `refactor:` - Code refactoring

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a PR on GitHub

#### PR Guidelines
- Fill out the PR template completely
- Link related issues
- Ensure CI/CD checks pass
- Respond to review feedback
- Keep PRs focused (one feature/fix per PR)

## Code Style

### Python
- Follow PEP 8
- Use meaningful variable names
- Add docstrings for functions
- Handle errors gracefully

### Terraform
- Use consistent formatting (`terraform fmt`)
- Comment complex logic
- Use variables for configurable values

### Documentation
- Update README.md for user-facing changes
- Keep examples up to date
- Use clear, concise language
- Include code examples where helpful

## Adding New Blocklist Sources

To add a new blocklist source:

1. Edit `helpers/downloader.py`:
   ```python
   files = [
       # ... existing sources ...
       ('https://example.com/blocklist.txt', 'example-blocklist.txt'),
   ]
   ```

2. Test the download:
   ```bash
   python helpers/downloader.py --output_dir lists
   ```

3. Verify the format is compatible:
   ```bash
   python helpers/processor.py lists --out test-output.txt
   ```

4. Update documentation:
   - Add to the "Customizing Blocklists" section
   - Credit the source
   - Note any special considerations

## Testing

### Local Testing Checklist
- [ ] Download step completes successfully
- [ ] Processing removes duplicates correctly
- [ ] Terraform plan shows expected resources
- [ ] Terraform apply works (test with small list first)
- [ ] Cloudflare Zero Trust shows the lists
- [ ] No sensitive data in commits

### CI/CD Testing
- [ ] GitLab CI/CD pipeline passes (if applicable)
- [ ] GitHub Actions workflow passes (if applicable)
- [ ] Artifacts are generated correctly
- [ ] State management works properly

## Project Structure

```
cloudflare-firewall/
├── .github/
│   ├── ISSUE_TEMPLATE/      # Issue templates
│   ├── workflows/           # GitHub Actions
│   ├── pull_request_template.md
│   └── TEMPLATE_USAGE.md
├── helpers/
│   ├── downloader.py        # Downloads blocklists
│   └── processor.py         # Processes and deduplicates
├── lists/                   # Downloaded blocklists (gitignored)
├── main.tf                  # Terraform configuration
├── parse.tf                 # Terraform parsing logic
├── upload.tf                # Terraform Cloudflare resources
├── output.txt               # Processed output (gitignored)
├── README.md                # Main documentation
├── CONTRIBUTING.md          # This file
└── LICENSE                  # MIT License
```

## Questions?

- 💬 Open a [discussion](../../discussions) for general questions
- 📖 Check the [README](README.md) for documentation
- 🐛 Use [issues](../../issues) for bugs and features

## Code of Conduct

Be respectful and constructive:
- ✅ Be welcoming and inclusive
- ✅ Respect differing viewpoints
- ✅ Accept constructive criticism
- ✅ Focus on what's best for the community
- ❌ No harassment or trolling
- ❌ No spam or promotional content

## Recognition

Contributors will be recognized in release notes and repository insights. Thank you for helping improve this project! 🚀

