# scons-parts

Parts extends SCons for large multi-component builds: a build is a set of Parts, each with its own part file, source checkout, version, and dependencies on other Parts. The repository is `sconsparts/parts` on GitHub.

**Type:** build-service

The default branch is `main`. Contributions are pull requests against `main`.

## How Parts runs

Read [doc/architecture/README.md](doc/architecture/README.md) before changing engine, loading, dependency, or environment code. It maps the system level by level in Mermaid diagrams. The short version:

1. `from parts import *` in the SConstruct runs `src/parts/main.py`.
2. `parts.overrides` monkeypatches SCons, including `Script.Main._build_targets`.
3. `glb.engine` is created, then every `pieces/*.py` on the site path is imported.
4. `engine.Start()` adds `--target`, writes `--target/--cfg/--tc/--mode` into `SCons.Script.ARGUMENTS`, builds the default environment (toolchain plus configuration), and runs the pre-load queue.
5. The SConstruct declares root Parts with `Part()`. Nothing is read yet.
6. SCons calls the patched `_build_targets`, which calls `engine.Process()`, which calls `part_manager.ProcessParts()`: `UpdateOnDisk()` for every Part, `LoadPart()` (execute the part file) for every Part, map targets to sections, compute the closure, toposort, `ProcessSection()` for the closure only.
7. The post-process queue runs, then SCons builds.

## Build

```sh
uv sync --dev                # creates .venv with an editable install of src/ plus dev tools
```

Python 3.11 or later and SCons 4.10 or later (`pyproject.toml`). The package version is the static `_PARTS_VERSION` in `src/parts/parts_version.py`, read by setuptools through `[tool.setuptools.dynamic]`.

## Tests

```sh
uv run pytest tests/unit                             # unit suite; non-fatal in CI
uv run pytest tests/unit/settings/test_settings.py -k NAME   # one test
uv run autest -D tests/gold_tests                    # gold tests (AuTest), serial; gating in CI
uv run autest -D tests/gold_tests -f NAME1 NAME2 --sandbox /tmp/sb -C none   # selected tests, keep sandboxes
nox -s autests --no-error-on-missing-interpreters    # gold tests on each installed Python 3.11-3.15, sandbox under _sandbox/<python>
```

- Unit tests are pytest under `tests/unit/`; `pyproject.toml` sets `-p no:pylama`. Gold tests are AuTest under `tests/gold_tests/<area>/<name>.test.py` with expected output in `gold/*.gold`; the harness extensions are in `tests/gold_tests/autest-site/`.
- CI runs the unit suite with `continue-on-error`, so it can carry failures. Compare the failure set against a run of `main`; do not expect zero.
- `autest -f` matches whole test names. `-f part_version` does not run `part_version_force`.
- Do not use `autest -j`; every test then reports "No Test run defined".
- AuTest runs `scons` as a subprocess that imports `parts` from the installed editable package and ignores `PYTHONPATH`. Make sure the venv's editable install points at the tree under test (a worktree needs its own `uv sync`).
- In AuTest commands write `$$` for a literal `$`; commands go through `sh`. `ContainsExpression` matches line by line unless given `reflags=re.M`.
- The `rpm*` gold tests need `rpmbuild`, and `dpkg_test` needs `debuild`. On macOS the case-insensitive filesystem can hide a filename-case bug that fails on Linux CI.
- Native gold runs have host == target. To test host/target logic, add a cross run: `--toolchain=binutils --target=posix-ia64` needs no cross compiler.
- Tests that run real git inherit the developer's global git config (`commit.gpgsign`, `core.hooksPath`, `init.defaultBranch`). Keep fixtures hermetic.
- For Windows and WSL runs, see [.github/copilot-instructions.md](.github/copilot-instructions.md).

### Proving a test is live

A passing AuTest run prints no per-assertion detail, so "green" does not prove an assertion runs. For every new assertion, mutate the code (or corrupt the gold file), confirm the test fails, and restore. Commit before mutating so `git checkout -- FILE` is an exact restore. Clear `__pycache__` after each restore: a same-size edit within the same second keeps the mutated bytecode. `tests/unit/__pycache__/conftest.*.pyc.*` is tracked by mistake; restore it after a blanket clean.

## Code Style

- `autopep8` with `max_line_length = 132` (`pyproject.toml`). No formatter or linter runs in CI.
- Match the surrounding code; most modules import helpers as `import parts.core.util as common` and report through `api.output` (`error_msg`, `warning_msg`, `verbose_msg`, `trace_msg`).

## Project Structure

| Path (under `src/parts/`) | Owns |
| --- | --- |
| `main.py`, `glb.py`, `engine.py` | Entry, globals, start-up, `Process()`, run cache key |
| `poptions.py`, `settings.py`, `Variables/` | Options, `SetOptionDefault`, the environment cache, variable merge |
| `tool_mapping.py`, `toolchain/`, `tools/` | `env.ToolChain()`, toolchain modules (`resolve(env, version)`), the SCons tool overlay |
| `config.py`, `configurations/` | `env.Configuration()`, `VersionRange` rules, per-level config files |
| `part_manager.py`, `parts.py` | `Part()` factories, `ProcessParts`, `UpdateOnDisk`, name registry, `_from_target` |
| `pnode/` | `Part`, `Section`, `pnode_manager` (`glb.pnodes`), `map_requirement` |
| `metasection/` | Section types (`build`, `unit_test`) and their phases |
| `dependson.py`, `part_ref.py`, `dependent_ref.py`, `target_type.py`, `requirement.py`, `api/requirement.py` | Dependency declaration, matching, target grammar, requirement sets |
| `sdk.py`, `exportitem.py`, `installs.py`, `packaging.py`, `core/builders/` | SDK and export tables, install, package groups, copy builders |
| `pieces/` | Built-in pieces: cmake, automake, meson, rpm, unit_test, PartName, PartVersion, ... |
| `scm/`, `vcs/` | git, svn, null, reuse SCM objects and update tasks |
| `overrides/` | SCons monkeypatches. Read [07-overrides-caches-dead-code.md](doc/architecture/07-overrides-caches-dead-code.md) first |
| `reporter.py`, `api/output.py`, `console.py`, `ansi_stream.py`, `part_logger.py` | Output, verbose and trace categories, spawn logging |
| `core/util/` | Shared helpers (formerly `parts.common`): `make_list`, `append_unique`, `DelayVariable`, `process_tool_arg` |
| `loadlogic/` | Dead. See Common Gotchas |

Entry points: `parts` (`parts.version_info:parts_version_text`, which returns the version string rather than printing it) and `parts-smart-cp` (`parts.scripts.smart_cp:main`, the copy helper the install builders spawn). Samples are in `samples/`; Sphinx docs in `doc/source/`.

## CI/CD

`.github/workflows/ci.yml` runs on pushes and pull requests to `main`. It has one `test` job on `ubuntu-latest`, a matrix over Python 3.11, 3.12, 3.13, and 3.14 with `fail-fast: false`:

- installs `patchelf` and `rpm` with apt, then `uv sync --dev`, and sets a global git identity;
- runs the full AuTest suite, `uv run autest -D ./tests/gold_tests` (gating);
- runs `uv run pytest -v tests/unit` with `continue-on-error` (non-fatal);
- on failure, uploads `_sandbox/**` and the pytest JUnit report as artifacts.

There is no lint job and no coverage gate. Read the failing job's log before suspecting the change.

## Common Gotchas

### Invariants and traps

- **Variable precedence:** `Default` < `parts.cfg` < `SCons.Script.ARGUMENTS`. A value that must beat `parts.cfg` goes into `ARGUMENTS`. Do not change the precedence in `Variable.Update()`.
- **`Variable`'s value field is a merge cache,** not a user override: `Variable.Update()` stores the first merged value there. Seed merges from `Default`. Seeding from the value lets an earlier merge beat a later `SetOptionDefault`; gold tests such as `install1` catch it.
- **Getters fire events:** reading `Variable.Default`/`.Value` on a `None` or mutable value fires `_on_change`, which empties the Settings environment cache. So does every `SetOptionDefault()`, `ReplaceENV()`, `PrependENVPath()`.
- **Do not build an environment in a piece module body.** It is cached without `--tc`/`--target` and without builders that later pieces register. Do not call `SetOptionDefault()` inside a toolchain `resolve()`.
- **Tool overlays:** after calling a base SCons `generate()`, override base-set variables with `env[...] =`. `SetDefault()` is a no-op once the base set the key.
- **Reading `Part.Name` on an unread Part writes its alias into the name registry.** `Part(name=...)` does not register a name; only `PartName()` does.
- **The global or `env.DependsOn()` inside a section callback aborts with `NameError`.** The check meant to report it with `error_msg` calls an undefined name (`output`). The section form, `build.DependsOn()`, reports it correctly. `Component()` resolves `requires=` during the read and exits on an unknown alias.
- **`PartRef.Matches` caches its first non-empty answer forever.** Do not resolve a dependency before every candidate Part is read.
- **Recursive targets prefix-match without a `.` boundary:** `apr::` also selects `apr_util`.
- **An unmappable target loads every section** (including `unit_test`). A dropped `--` in front of a flag is the usual cause.
- **`append_unique` moves a duplicate to the end.** That is deliberate link-order behaviour. Keep last-occurrence-wins in any rewrite.
- **Config files:** one file per level, tool, host, and target; a platform-named file replaces the generic file of that level. Only the first matching `VersionRange` in a file applies; a later overlapping range is dead for the versions an earlier one covers. A file that raises on import is skipped with a warning and the next, less specific name is loaded instead.
- **`.parts.cache` stores no SCons version;** its entries carry only a Parts format key. Version any revived node-state cache against SCons first.
- **Before sections are processed, test paths with `os.path.exists(node.abspath)`, not `Node.exists()`.** `exists()` turns an `Entry` into a `File` for good, which breaks a later `Install()` into that path.
- **Wrap expensive log arguments in `common.DelayVariable(lambda: ...)`.** A disabled `verbose_msg` still evaluates its arguments.

### Dead code: do not build on it

`--load-logic` (value never read), `loadlogic/target.py`/`nodepends.py`/`changed.py` (no caller), `engine.store_db_data()` and `pnode_manager.Store()` (callers commented out, so no node or `part_map` cache exists across runs), `picklehelpers.loads` (always raises), `--disable-parts-cache` and `--disable-global-parts-site` (both no-ops), `Part.GenerateStoredInfo` (`1/0`), `_from_target(use_stored_info=True)` (returns empty), `Part(default=True)` (never read). Revive or remove them deliberately; do not assume they work.

## Documentation

- Architecture maps: [doc/architecture/](doc/architecture/README.md). When a change alters something a diagram shows, update the diagram in the same PR.
- User documentation: Sphinx sources in `doc/source/`, published at https://sconsparts.github.io/. Configurations are described in [configurations.rst](doc/source/concepts/configurations.rst) and toolchains in [toolchains.rst](doc/source/concepts/toolchains.rst).
- Release notes: `doc/source/release_notes/release-X.Y.Z.rst`.

## Conventions

- Open pull requests against `main`. Do not hard-wrap prose in PR or issue bodies (GitHub renders each newline).
- Before pushing a fix round, review the whole branch against its base, not only the new commit.
- Keep a PR's description accurate to its diff: counts, claims, and which tests prove which behaviour.
