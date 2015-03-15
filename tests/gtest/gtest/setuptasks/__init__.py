# we don't really want to export the files in this area by themselfs
# we need them all loaded at once, so we fill the __all__ value
# so a simple from setuptasks * will just work
import os

from copy_items import *
from svn import *