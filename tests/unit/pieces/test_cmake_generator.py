'''
CMAKE_GENERATOR is a registered variable, and the configure step is tracked by
a file the chosen generator writes.

The CMake() configure step passes -G only when the variable is non-empty, and
an unregistered variable also substitutes to '', so the command line alone
cannot show whether it is registered. Registration is what gives it
a default and a help entry.
'''
import pytest

import parts.pieces.cmake as cmake_piece  # registers the CMAKE_* variables
import parts.settings as parts_settings


def test_cmake_generator_is_registered_empty():
    env = parts_settings.DefaultSettings().Environment()
    assert 'CMAKE_GENERATOR' in env
    assert env['CMAKE_GENERATOR'] == ''


@pytest.mark.parametrize('generator,output', [
    ('', 'Makefile'),
    ('Unix Makefiles', 'Makefile'),
    ('MinGW Makefiles', 'Makefile'),
    ('Ninja', 'build.ninja'),
    ('Ninja Multi-Config', 'build.ninja'),
    ('Xcode', 'CMakeCache.txt'),
    ('Visual Studio 17 2022', 'CMakeCache.txt'),
])
def test_configure_is_tracked_by_a_file_the_generator_writes(generator, output):
    # a target the generator never writes makes every build configure again
    assert cmake_piece.configure_output(generator) == output
