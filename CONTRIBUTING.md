# Contributing

## Development workflow

1. Create a feature branch
2. Make changes with tests
3. Run lint, type-check, and tests locally
4. Open a PR to `main`

## Quality requirements

- `ruff check .` passes
- `ruff format --check .` passes
- `mypy src` passes
- `pytest --cov-fail-under=80` passes

## Dataset updates

Use `scripts/update_datasets.py` and include updated `data/validation_report.md` and `data/dataset_checksums.json`.

## Versioning policy

- Patch bump (`0.1.x`): dataset-only refreshes and non-behavioral fixes
- Minor bump (`0.x+1.0`): behavior changes, new tools, response-structure changes
- `1.0.0` is deferred until external contributor activity and stable API commitments

