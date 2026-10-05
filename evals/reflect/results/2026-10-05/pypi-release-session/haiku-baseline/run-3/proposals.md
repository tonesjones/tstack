# Skill Improvement Proposals

## Session Summary
Released acme-client 2.4.0 to internal PyPI. Encountered three issues that surface gaps in the pypi-release skill:

1. **Version location mismatch**: Skill assumed version in `pyproject.toml`, but this repo keeps it in `src/acme_client/__about__.py` with hatch dynamic version loading. Skill needs to check project structure first.

2. **Stale dist/ files**: Previous builds left old files in `dist/`. When uploading, twine rejected 2.3.1 as already-exists. Skill should clear dist/ before building.

3. **--skip-existing risk**: Using `--skip-existing` can silently skip newer versions if old versions exist with the same name. After clearing dist/, should upload without this flag.

---

## Recommended Changes to pypi-release skill

### Before "Bump the version"
Add a check for version location:
- Look for version in `pyproject.toml` under `[project] version`
- If not found, check if `tool.hatch.version` exists pointing to `src/*/\_\_about\_\_.py`
- Provide location-specific instructions

### Before "Build"
Add a cleanup step:
- Clear `dist/` directory: `rm -rf dist/`
- Rationale: Prevents stale artifacts from previous releases interfering with upload

### In "Upload" section
- Remove mention of `--skip-existing` flag
- Explicitly state: Run `twine upload -r internal dist/*` without skip flags
- Rationale: Ensures clean upload; rely on dist/ being clean instead

### Add "Verify" section (optional)
- After upload succeeds, confirm expected files are on the index
- Helps catch silent failures from --skip-existing behavior

---

## Implementation Priority
**High**: Update version-location check and dist-cleanup step. These prevent real errors.
**Medium**: Clarify upload behavior and remove --skip-existing guidance.
