
import SCons.Defaults

# This is what we want to be setup in parts
import parts.api as api

def script_file(env, target, source, mode=0o755, **kw):
    '''
    This is a wrapper that call Textfile() then chmods the output file
    '''
    if 'TEXTFILESUFFIX' not in kw:
        if env['TARGET_OS'] != 'win32':
            kw['TEXTFILESUFFIX'] = ".sh"
        else:
            kw['TEXTFILESUFFIX'] = ".ps1"
    out = env.Textfile(target, source, **kw)
    env.AddPostAction(out, SCons.Defaults.Chmod('$TARGET', mode))
    return out


api.register.add_method(script_file, 'Scriptfile')
