from __future__ import absolute_import, division, print_function

import os
import os.path

import parts.api.output as output
import parts.tools.Common
import parts.tools.MSCommon.vsx_sdk
from parts.tools.MSCommon import vssdk

import SCons.Util

ctc_action = SCons.Action.Action('$CTC_COM', '$CTC_COMSTR')
ctc_builder = SCons.Builder.Builder(action=ctc_action,
                                    src_suffix='.ctc',
                                    suffix='.cto',
                                    src_builder=[],
                                    source_scanner=SCons.Tool.SourceFileScanner)
SCons.Tool.SourceFileScanner.add_scanner('.ctc', SCons.Defaults.CScan)


def generate(env):

    vssdk.MergeShellEnv(env)

    env['INCPREFIX'] = '/I'
    env['INCSUFFIX'] = ''
    env['_CTC_INCFLAGS'] = '${_concat(INCPREFIX, CTC_INCLUDES, INCSUFFIX, __env__, RDirs, TARGET, SOURCE)}'
    env['CTC'] = parts.tools.Common.toolvar('ctc', ('ctc',), env=env)
    env['CTC_INCLUDES'] = []
    env['CTC_FLAGS'] = ['-nologo', '-Ccl']
    env['CTC_COM'] = '$CTC $SOURCE $TARGET $CTC_FLAGS $_CTC_INCFLAGS'
    env['BUILDERS']['CTC'] = ctc_builder


def exists(env):
    return vssdk.Exists(env)
