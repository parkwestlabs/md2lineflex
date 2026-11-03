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
    - Environment name: pypi
    - must match the GitHub Environment name `pypi` (see GitHub Actions below)
    - never leave it as `(Any)`: it accepts any workflow or environment
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

# one-time manual publish for the initial check only (do not use for regular releases)
# GitHub Actions publishes via Trusted Publisher after this setup; do not store API tokens in the repo
uv publish --token <your_PyPI_API_token>
```

## Dev Workflow

### CD Triggers

* tag automatically (recommended)
    - publish a new release on GitHub UI
    - this will tag behind the scene
* tag manually
    - `git tag vX.Y.Z` on the merged commit of main
    - `git push origin vX.Y.Z` (push only the tag; `--tags` would also push other local tags)

### GitHub Actions

* Settings ➔ Rulesets ➔ New ruleset ➔ Add branch ruleset
    - Ruleset Name: `Main Branch Protection`
    - Enforcement status: Active
    - Target branches: Include default branch
    - Require a pull request before merging (Required approvals: 0, since this is a solo project; the PR itself is still required)
    - Require status checks to pass
    - Add checks: `ci-passed`
        - `ci.yml` has a `ci-passed` gate job that depends on the matrix `test` jobs
        - matrix jobs report as `test (3.10)`, `test (3.11)`, ... so a required check named `test` never reports and blocks merging
    - push Create button
    - note: Branches ➔ Branch protection rules is legacy
    - bypass list: Repository role `Admin` (lets the owner push or merge when CI is unavailable; this bypass also covers deletion and force-push rules in the same ruleset)

* Settings ➔ Rulesets ➔ New ruleset ➔ Add tag ruleset
    - Ruleset Name: `Release Tag Protection`
    - Enforcement status: Active
    - Target tags: All tags (`v*` also works if other tag names are used)
    - Restrict creations, updates, and deletions
    - bypass list: Repository role `Admin`

* Settings ➔ Environments ➔ New environment ➔ `pypi`
    - Required reviewers: add the owner (approval is required before publish runs; self-review is allowed for a solo project)
    - Deployment branches and tags: Selected branches and tags
        - Add rule: Ref type `Tag`, name pattern `v*`
        - do not choose "Protected branches only": it does not cover tags, so tag deployments would be rejected
* verify with `gh api repos/OWNER/REPO/environments/pypi` (check `protection_rules` and `deployment_branch_policy`)
* using PyPI Trusted Publisher (OIDC federation)
    - https://docs.astral.sh/uv/guides/integration/github/

1. CI `ci.yml` (create PR or merge PR to main)
    - check: run `ruff` (lint/format) and `pytest`
2. CD `publish.yml` (push tags or create Release on GitHub)
    - build: `uv build`
    - publish: `uv publish` (without API Token)
    - the publish job waits for approval in the `pypi` environment (Actions run page ➔ Review deployments)

### Release Procedure

1. Merge the release PR into `main` after `ci-passed` is green.
2. Create a GitHub Release (Releases ➔ Draft a new release) with tag `vX.Y.Z` and target `main`, then Publish release.
3. Approve the `pypi` deployment on the Actions run.
4. Confirm the new version on https://pypi.org/project/md2lineflex/.

Tag and version must match: `publish.yml` fails when `pyproject.toml` `version` differs from the tag.

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
