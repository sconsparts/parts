# this script allows us to handle upzipping with zipfile or tarfile in the builder
# without locking up the main build logic in SCons because of the GIL.
# if the "extract" tools cannot use uzip/tar it will call this instead.

# These script have general output values that we can query, which allows us an easy mapping for 
# the SCons builder emit functions 

import json
import tarfile
import zipfile
#import tarfile
import argparse
from pathlib import Path
from typing import List, Union
import sys

def main():
    
    # create parser 
    parser = argparse.ArgumentParser()
        
    parser.add_argument("--out-directory","--out-dir", "-o", type=Path, required=True, help="Output directory to extract files")
    parser.add_argument("--json-data", type=Path, required=True, help="JSON file with information on what to process")

    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()
    extract(args.json_data, args.out_directory)


#def get_zip_files(source:Path) -> List[zipfile.ZipInfo]:

#    with zipfile.ZipFile(source) as zfile:
#        content = zfile.infolist()
#        files = [f for f in content if not f.is_dir()]
#        return files
        

def extract(json_file_name:Path, target:Path):
    
    # read in data from json file
    if not json_file_name.exists():
        print(f"Error! {json_file_name} does not exist")
    with open(json_file_name) as json_file:
        json_data = json.load(json_file)

    # pull data
    compress_files = json_data['files']
    source = Path(json_data['source'])

    # verify the source exists
    if not source.exists():
        print(f"Error! {source} does not exist")
        sys.exit(2)

    # extract the files
    if source.suffix.endswith(".zip"):
        print(f"Extracting files from {source}")
        py36_fix = str(source) # python 36 has a bug with Path in Zip/Tar file code
        with zipfile.ZipFile(py36_fix) as zfile:
            for cfile in compress_files:
                tmp = zfile.extract(cfile,path=target)
                print(f"Created: {tmp}")
    elif source.suffix.endswith(".gz"):
        print(f"Extracting files from {source}")
        py36_fix = str(source) # python 36 has a bug with Path in Zip/Tar file code
        with tarfile.open(py36_fix) as tfile:
            for cfile in compress_files:
                # tarefile does tell you the finial path of what was extracted
                print(f"{cfile} path={target}")
                tfile.extract(cfile,path=target)
                #print(f"Created: {cfile}")
    else:
        print("Error: Unknown file type!")
        sys.exit(2)
            
if __name__ == '__main__':
    main()
