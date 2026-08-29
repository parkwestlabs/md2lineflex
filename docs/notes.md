# Development Notes

## PyPI Account Registration

* register
    - create an account at https://pypi.org/account/register/
    - setup 2FA
* Account settings ➔ Publishing ➔ Add a pending publisher
    - PyPI Project Name: md2lineflex
    - Owner / Organization: parkwestlabs
    - Repository name: md2lineflex
    - Workflow name: publish.yml
    - Environment name: (blank)
* Test: https://test.pypi.org/
* Prod: https://pypi.org/

## Project Initial Setup

```bash
uv init --lib --python 3.10 .
# Initialized project `md2lineflex` at md2lineflex

# for the first commit
git commit -m "feat: initial release"

uv build
# will create dist/

# command to publish with PyPI API Token manually
# GitHub Actions will publish after setup PyPI Trusted Publisher
uv publish --token <your_PyPI_API_token>
```

## Dev Workflow

### CD Triggers

* tag automatically (recommended)
    - publish a new release on GitHub UI
    - this will tag behind the scene
* tag manually
    - `git tag vX.Y.Z`
    - `git push origin main --tags`

### GitHub Actions

* Settings ➔ Rulesets ➔ New ruleset ➔ Add branch ruleset
    - Ruleset Name: `Main Branch Protection`
    - Enforcement status: Active
    - Target branches: Include default branch
    - Require a pull request before merging (Required approvals: 1)
    - Require status checks to pass
    - Add checks: `test`
    - push Create button
    - note: Branches ➔ Branch protection rules is legacy
* using PyPI Trusted Publisher (OIDC federation)
    - https://docs.astral.sh/uv/guides/integration/github/

1. CI `ci.yml` (create PR or merge PR to main)
    - check: run `ruff` (lint/format) and `pytest`
2. CD `publish.yml` (push tags or create Release on GitHub)
    - build: `uv build`
    - publish: `uv publish` (without API Token)

## Supported Python Version

```bash
curl -s https://pypi.org/pypi/line-bot-sdk/json | jq -r '.info.requires_python'
# >=3.10.0
```

## License

MIT License

```bash
# command to generate
curl -s https://raw.githubusercontent.com/licenses/license-templates/master/templates/mit.txt | \
sed "s/{{ year }}/$(date +%Y)/g; s/{{ organization }}/$(git config user.name)/g" > LICENSE
```
