
import parts.api as api

class AppendFile:
        def __init__(self, filename, value):
            self._value = value
            self._filename = filename
        def __call__(self, target, source, env):
            filename = env.subst(self._filename,target=target,source=source)
            with open(filename,"a") as outfile:
                outfile.write(env.subst(self._value,target=target,source=source))


api.register.add_global_parts_object("AppendFile", AppendFile)
api.register.add_global_object("AppendFile", AppendFile)

