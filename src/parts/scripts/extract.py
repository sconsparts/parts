# this script allows us to handle upzipping with zipfile or tarfile in the builder
# without locking up the main build logic in SCons because of the GIL.
# if the "extract" tools cannot use uzip/tar it will call this instead.

# These script have general output values that we can query, which allows us an easy mapping for 
# the SCons builder emit functions 

import zipfile
#import tarfile
import argparse
from pathlib import Path
from typing import List

def main():
    
    # create parser 
    parser = argparse.ArgumentParser()

    cmd_parser = parser.add_subparsers(title='Commands',
                                       dest="command", required=True)

    emit = cmd_parser.add_parser("emit", help="Emit outputs")
    build = cmd_parser.add_parser("build", help="build outputs")

    
    emit.add_argument("--sources", "-s", type=Path, nargs='+', required=True, help="Input sources")
    emit.add_argument("--targets", "-t", type=Path, nargs='+', required=True, help="Output targets")

    build.add_argument("--sources", "-s", type=Path, nargs='+', required=True, help="Input sources")
    build.add_argument("--targets", "-t", type=Path, nargs='+', required=True, help="Output targets")

    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()
    print(args)

def emit(target:List[Path], sources=List[Path]):
    
    out = []
    for src in sources:
        out += get_files(src)


def get_zip_files(source:Path) -> List[zipfile.ZipInfo]:

    with zipfile.ZipFile(source) as zfile:
        content = zfile.infolist()
        files = [f for f in content if not f.is_dir()]
        return files
        






def extract(infile:List[Path], outdir:List[Path]):
    pass



if __name__ == '__main__':
    main()
