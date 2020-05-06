

import os
import re

from parts.tools.Common.Finders import MsiFinder

if __name__ == '__main__':
    def selfTest():
        print(MsiFinder('.*Python.*', 'PythonExe')())
        print(MsiFinder('.*Intel Compiler.*', 'IclExe')())
        print(MsiFinder(r'^Java\W.*Development', 'ss160450', subDir='bin')())
        print(MsiFinder(r'^Java\W.*Development', 'ss170250', subDir='bin')())
    selfTest()

# vim: set et ts=4 sw=4 ft=python :
