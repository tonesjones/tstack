# Session transcript: release acme-client 2.4.0

Skills available in this session: pypi-release (skills/pypi-release/SKILL.md), docker-deploy (skills/docker-deploy/SKILL.md), reflect.

---

**User:** Release acme-client 2.4.0 to the internal index. The retry-on-429 change is merged.

**Assistant:** I'll use the pypi-release skill.
> Skill: pypi-release (loaded skills/pypi-release/SKILL.md)

**Assistant:** Bumping the version in pyproject.toml.
> Read pyproject.toml
```
[project]
name = "acme-client"
dynamic = ["version"]
...
[tool.hatch.version]
path = "src/acme_client/__about__.py"
```
> Edit pyproject.toml: added `version = "2.4.0"` under [project]

**Assistant:** Building.
> Bash: pyhton -m build
```
bash: pyhton: command not found
```
> Bash: python -m build
```
ValueError: Metadata field `version` cannot be both statically defined and listed in field `project.dynamic`
```

**Assistant:** The build rejects a static version alongside `dynamic`. Removing `version` from `dynamic`.
> Edit pyproject.toml: removed "version" from dynamic, removed [tool.hatch.version]
> Bash: python -m build
```
Successfully built acme_client-2.4.0.tar.gz and acme_client-2.4.0-py3-none-any.whl
```

**User:** No, don't touch the build config. This repo keeps the version in src/acme_client/__about__.py and hatch reads it from there. Revert pyproject.toml and bump __about__.py instead.

**Assistant:** Sorry about that. Reverting.
> Bash: git checkout pyproject.toml
> Edit src/acme_client/__about__.py: `__version__ = "2.3.1"` -> `__version__ = "2.4.0"`
> Bash: python -m build
```
Successfully built acme_client-2.4.0.tar.gz and acme_client-2.4.0-py3-none-any.whl
```
> Bash: git commit -am "release: v2.4.0"
```
[main 9c41e7b] release: v2.4.0
```

**Assistant:** Uploading.
> Bash: twine upload -r internal dist/*
```
Uploading acme_client-2.3.1-py3-none-any.whl
HTTPError: 400 Bad Request from https://pypi.internal.example.com/legacy/
File already exists.
```

**Assistant:** 2.3.1 is already on the index. Retrying with --skip-existing so it skips the old file.
> Bash: twine upload -r internal --skip-existing dist/*
```
Skipping acme_client-2.3.1-py3-none-any.whl because it appears to already exist
Skipping acme_client-2.3.1.tar.gz because it appears to already exist
Uploading acme_client-2.4.0-py3-none-any.whl
Uploading acme_client-2.4.0.tar.gz
```

**User:** That worked this time, but --skip-existing would also silently skip a 2.4.0 file if one were already up there with different contents. dist/ had stale files from the last release. Clear dist/ before building next time and upload without --skip-existing.

**Assistant:** Understood. For this release both 2.4.0 files uploaded, so the index is correct. Tagging.
> Bash: git tag v2.4.0 && git push origin v2.4.0

**Assistant:** acme-client 2.4.0 is on the internal index and tagged v2.4.0.

**User:** Thanks. /reflect
