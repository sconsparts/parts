Shared agent instructions for this repo live in AGENTS.md - read it first.

# Copilot Instructions

## Cross-Platform Testing (UV First)

This guide defines a repeatable workflow for running the project test suite on Windows and Linux (via WSL) from a Windows host.

## Goal

Run the same test intent on both platforms and make failures comparable:
1. Windows: run the gold test suite directly.
2. Linux (WSL): run the same suite inside one explicitly selected distro.
3. Keep environments and sandboxes separate per platform.

## Baseline Requirements

1. Windows Python must be 3.11+.
2. WSL distro Python must be 3.11+.
3. uv must be installed in each target environment.
4. Linux build tools must be present for compile-heavy tests.

## Pick WSL Distro Explicitly

Never rely on default distro selection for CI-like comparisons.

```powershell
wsl -l -v
wsl -d <DistroName> -e bash -lc "python3 --version"
```

## Windows Clean Run (UV)

Run from repository root.

```powershell
uv --version

if (Test-Path .venv-uv-win) { Remove-Item -Recurse -Force .venv-uv-win }
if (Test-Path _sandbox/win_uv314) { Remove-Item -Recurse -Force _sandbox/win_uv314 }

uv venv .venv-uv-win --python 3.14
uv pip install --python .venv-uv-win\Scripts\python.exe -e . autest scons

$env:Path = "$PWD\.venv-uv-win\Scripts;" + $env:Path
autest -D tests/gold_tests --sandbox _sandbox/win_uv314 *> win_uv_autest.log
```

## Linux Clean Run In WSL (UV)

Run from Windows terminal and target one distro (example: Ubuntu-26.04).

```powershell
wsl -d Ubuntu-26.04 -e bash -lc '
set -e

# Install uv once if missing
if ! command -v uv >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Linux toolchain required by many tests
sudo apt-get update
sudo apt-get install -y build-essential

# Use Linux-native filesystem, not /mnt/c
rm -rf ~/parts_wsltest_uv
cp -a /mnt/c/Users/jkenny/code/parts ~/parts_wsltest_uv
cd ~/parts_wsltest_uv

rm -rf .venv-uv _sandbox/linux_uv314
~/.local/bin/uv venv .venv-uv --python 3.14
~/.local/bin/uv pip install --python .venv-uv/bin/python -e . autest scons

.venv-uv/bin/autest -D tests/gold_tests --sandbox _sandbox/linux_uv314 | tee wsl_uv_autest_u2604.log
'
```

## Compare Results

For each platform capture:
1. Total
2. Passed
3. Failed
4. Skipped
5. Top failure names and first failure reason

Recommended log artifacts:
1. win_uv_autest.log
2. wsl_uv_autest_<distro>.log

## Validated Baseline (2026-09-11)

The following results were observed from clean uv-based runs:
1. Windows (Python 3.14): Total 125, Passed 101, Failed 0, Skipped 24.
2. Ubuntu-26.04 WSL (Python 3.14): Total 125, Passed 104, Failed 0, Skipped 21.

Expected Linux skips in this baseline include:
1. rpm tests when rpmbuild is not installed.
2. dpkg tests when debuild is not installed.
3. Windows-only tests (wdk, wix, wix_wrapper, rc_long_cmd).
4. checkout1 when svnadmin is not installed.
5. run_utest-loadlogic and utesttest-issue-29 due to test configuration.

## Common Issues and Fixes

1. Python too old in WSL.
Symptom: package install or runtime incompatibility.
Fix: use a distro/interpreter with Python 3.11+.

2. /mnt/c permission errors during install/build.
Symptom: Operation not permitted under src/scons_parts.egg-info.
Fix: copy repo to Linux home and run from there.

3. Missing Linux compiler toolchain.
Symptom: scons reports no GXX for target posix-x86_64.
Fix: sudo apt-get install -y build-essential.

4. Missing packaging tools.
Symptom: dpkg/rpm-related tests skipped.
Fix: install needed distro tools if those tests are in scope.

5. Git setup failures in WSL tests.
Symptom: checkout-git setup commit fails.
Fix: set git identity in distro:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## Recommended Conventions

1. Use Windows sandbox prefix _sandbox/win<pyver>.
2. Use WSL sandbox prefix _sandbox/linux<pyver>.
3. Always pass -d <DistroName> in WSL commands.
4. Record Python and uv versions at test start.
5. Compare only supported interpreter runs (3.11+).
