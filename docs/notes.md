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

## Compatibility Check

* ensure pytest pass in the latest version

```bash
uv sync --resolution highest
uv run pytest -v
```

* add `--resolution lowest-direct` equivalent in `pyproject.toml` temporarily

```
[tool.uv]
resolution = "lowest-direct"
```

* update (downgrade) dependencies in pyproject.toml and try pytest
* repeat this downgrade as far as pytest pass

```bash
uv lock && uv sync && uv run pytest -v

# check actual versions
uv pip list
uv tree
uv tree --invert --package package_name

arr=(line-bot-sdk mdformat mdformat-gfm mistletoe)
for pkg in "${arr[@]}";
do; uv tree --invert --package  $pkg; done
```

* after find lower limit, remove `resolution = "lowest-direct"` and reset to the latest

```bash
uv sync --resolution highest
uv run pytest -v
```

## Upgrade Packages

```bash
uv pip list --outdated

uv sync --upgrade --dry-run
uv sync --upgrade
```
