#!/usr/bin/env python3
'''Fail on new pyflakes "undefined name" findings under src/.

Why this exists: a merge took one branch's import block and the other branch's
call site, 60 lines apart in the same file, and produced
`parts.common.make_list(...)` in a module that only imported
`parts.core.util as common`. Git saw no textual conflict. The name error fired at
import time, which broke tool loading, which failed 95 of 127 gold tests with
"Failed to load Unknown ToolChain or Tool: ar" -- a message pointing nowhere
near the actual line. pyflakes finds that class of break in about two seconds.

The tree already carries known findings of this kind, so this compares against a
committed baseline and only fails on findings that are not in it. Findings that
have been fixed are reported but do not fail, so fixing a bug never breaks CI;
refresh the baseline with --update when convenient.

    python tests/lint/undefined_names.py              # check (used by CI)
    python tests/lint/undefined_names.py --update      # rewrite the baseline

Scope is src/ only. tests/ is full of names injected into SConscript-style files
at runtime, which pyflakes cannot see and would report as false positives.
'''
import argparse
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[2]
BASELINE = HERE.with_name('undefined_names_baseline.txt')
TARGET = 'src'

# pyflakes line format: path:line:col: undefined name 'x'
FINDING = re.compile(r"^(?P<path>.+?):\d+:\d+: (?P<msg>undefined name '.*')$")


def collect():
    '''Return the set of "path: undefined name 'x'" findings, without line numbers.

    Line numbers are dropped so that editing unrelated parts of a file does not
    churn the baseline. The tradeoff is that a second occurrence of a name
    already baselined in the same file is not flagged; a name that is new to a
    file, or any finding in a new file, still is.
    '''
    proc = subprocess.run(
        [sys.executable, '-m', 'pyflakes', TARGET],
        cwd=ROOT, capture_output=True, text=True,
    )
    # pyflakes exits 1 when it reports something, so a non-zero exit with no
    # findings on stdout means the tool itself did not run
    if proc.returncode not in (0, 1) or (proc.returncode == 1 and not proc.stdout.strip()):
        sys.stderr.write(
            'pyflakes did not run (exit {0}). Is it installed? `uv sync --group dev`\n{1}'.format(
                proc.returncode, proc.stderr))
        raise SystemExit(2)

    found = set()
    for line in proc.stdout.splitlines():
        match = FINDING.match(line.strip())
        if match:
            path = match.group('path').replace('\\', '/')
            found.add('{0}: {1}'.format(path, match.group('msg')))
    return found


def read_baseline():
    if not BASELINE.exists():
        return set()
    return {
        line.strip() for line in BASELINE.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true',
                        help='rewrite the baseline from the current tree')
    args = parser.parse_args()

    found = collect()

    if args.update:
        BASELINE.write_text(
            '# pyflakes "undefined name" findings known to exist in src/.\n'
            '# Regenerate with: python tests/lint/undefined_names.py --update\n'
            '# Each entry is a latent NameError: the line raises if it is ever reached.\n'
            + ''.join(f'{line}\n' for line in sorted(found)))
        print(f'wrote {len(found)} findings to {BASELINE.relative_to(ROOT)}')
        return 0

    baseline = read_baseline()
    new = sorted(found - baseline)
    fixed = sorted(baseline - found)

    if fixed:
        print(f'{len(fixed)} baselined finding(s) no longer present -- '
              f'refresh with `python {HERE.relative_to(ROOT)} --update`:')
        for line in fixed:
            print(f'  {line}')

    if new:
        print(f'\n{len(new)} NEW undefined name(s) under {TARGET}/:', file=sys.stderr)
        for line in new:
            print(f'  {line}', file=sys.stderr)
        print('\nEach of these raises NameError if the line is reached. If a merge '
              'or refactor renamed a module, the import and the call site have gone '
              'out of sync.', file=sys.stderr)
        return 1

    print(f'no new undefined names under {TARGET}/ '
          f'({len(baseline)} known finding(s) baselined)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
