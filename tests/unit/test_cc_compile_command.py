"""Regression test: the parts C compile command must actually apply.

tools/cc.py calls SCons.Tool.cc.generate(), which assigns CCCOM/SHCCCOM with a
direct env[] assignment. The parts overrides therefore have to be assigned the
same way -- a SetDefault() is a silent no-op once the base tool has set the
value, which left C compiles running the base SCons command and bypassing the
TEMPFILE response-file wrapping (and $CCARCHFLAGS) that the parts C++ command
(tools/c++.py, which does not call the base generate()) already gets.

These assertions fail against the base/unfixed cc.py (CCCOM == '$CC -o ... ',
no TEMPFILE) and pass once the override is a direct assignment.
"""
import os

import pytest

import parts.settings as parts_settings


PARTS_TOOLS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'parts', 'tools')
)


@pytest.fixture
def env():
    # toolchain=[] -> compiler-less base env, then apply the generic cc/c++ tools
    # from the working tree so we exercise their generate() output directly.
    env = parts_settings.DefaultSettings().Environment(toolchain=[])
    env.Tool('cc', toolpath=[PARTS_TOOLS])
    env.Tool('c++', toolpath=[PARTS_TOOLS])
    return env


@pytest.mark.parametrize('com', ['CCCOM', 'SHCCCOM'])
def test_c_command_uses_parts_tempfile_template(env, com):
    # the parts override (not the base SCons command) must be in effect
    assert 'TEMPFILE' in env[com]
    assert '$CCARCHFLAGS' in env[com]


def test_c_command_matches_cxx_response_file_handling(env):
    # C and C++ should both route through TEMPFILE; the C path used to silently
    # diverge by falling back to the base command.
    assert ('TEMPFILE' in env['CCCOM']) == ('TEMPFILE' in env['CXXCOM'])
    assert ('TEMPFILE' in env['SHCCCOM']) == ('TEMPFILE' in env['SHCXXCOM'])
