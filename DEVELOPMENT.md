# Development Guide

This document provides instructions for setting up the local development environment, running tests, and releasing new versions of `md2lineflex`.

---

## Local Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/parkwestlabs/md2lineflex.git
    cd md2lineflex
    ```
1. **Install dependencies**:
    ```bash
    uv sync
    ```
1. **Run linter and tests**:
    ```bash
    # Run linter and formatter
    uv run ruff check .
    uv run ruff format .

    # Run tests
    uv run pytest -v

    # Update snapshots if needed
    uv run pytest -v --snapshot-update
    ```

### Visual Testing with Flex Message Simulator

The snapshot JSON files generated in `tests/__snapshots__/` contain the raw LINE Flex Message container JSON (`contents`).

You can copy the contents of any `.json` file in `tests/__snapshots__/` and paste it directly into the [LINE Flex Message Simulator](https://developers.line.biz/flex-simulator/) to visually verify how the rendered Markdown looks on an actual LINE client UI.

---

## Release Process

### 1. Versioning Strategy

We follow [Semantic Versioning (SemVer)](https://semver.org/):

* `X.Y.Z`
    - `Z` (Patch): Bug fixes and documentation updates.
    - `Y` (Minor): Backward-compatible new features.
    - `X` (Major): Breaking changes.

### 2. Commit & Pull Request Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages and PR titles:

* `feat`: New feature / enhancement
* `fix`: Bug fix
* `docs`: Documentation updates
* `chore`: Maintenance, dependencies, or CI updates

### 3. Step-by-Step Release Workflow

1. Update the version in `pyproject.toml`:
    ```toml
    [project]
    version = "X.Y.Z"
    ```
2. Commit and push your changes to `main` via Pull Request:
    ```bash
    git commit -m "feat: Bump version to X.Y.Z"
    git push origin main
    ```
3. Publish a new release on GitHub:
    * Go to GitHub UI -> **Releases** -> **Draft a new release**.
    * Create a new tag: `vX.Y.Z` (Target: `main`).
    * Click **Generate release notes**.
    * Click **Publish release**.

(Pushing the tag `vX.Y.Z` will automatically trigger the `.github/workflows/publish.yml` pipeline to build, run smoke tests, sign, and publish the package to PyPI via OIDC Trusted Publisher).

---

For initial PyPI setup notes, see [docs/notes.md](docs/notes.md).
