import os

Test.Summary = '''
The emsdk toolchain compiles and links a C program for wasm using emcc/em++,
located via $EMSDK (emsdk's emsdk_env.sh contract).
'''


def _emsdk_available():
    root = os.environ.get('EMSDK')
    return bool(root) and os.path.isfile(os.path.join(root, 'upstream', 'emscripten', 'emcc'))


# Skip unless an emsdk install is reachable via $EMSDK. emcc is not on PATH (it
# is found through $EMSDK), so a plain HasProgram check would not see it.
Test.SkipUnless(
    Condition.Condition(lambda: _emsdk_available(),
                        'emsdk not available (set EMSDK to an emsdk install to run this test)')
)

Setup.Copy.FromDirectory('emsdk_build')

# A clean build proves emcc/em++ were detected via $EMSDK and used for a wasm
# target (the toolchain selection + EnvFinder locator + binutils path).
t = Test.AddBuildRun('all', '--tool-chain=emsdk --target=emscripten-wasm32')
t.ReturnCode = 0
