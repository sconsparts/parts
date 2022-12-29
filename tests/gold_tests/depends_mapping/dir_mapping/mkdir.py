
import argparse
import os
from pathlib import Path

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--outdir", type=Path, help="Path to make")
    parser.add_argument("--name", help="name to use for file generated")

    args = parser.parse_args()
    name = args.name
    outdir:Path = args.outdir

    # make out put directory
    print(f"making directory {outdir}")
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"making directory {outdir}/include")
    out_include = outdir / "include"
    out_include.mkdir(parents=True, exist_ok=True)

    out_file = out_include / f"{name}.h"
    out_file.write_text(f'''
    #include <stdio.h>
    // {name}
    ''')


if __name__ == '__main__':
    main()


    


