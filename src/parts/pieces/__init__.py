# pylint: disable=missing-docstring, unused-import


import glob
import os.path
import parts.glb as glb


def loadAllPieces():
    import parts.load_module as load_module
    # The pieces directories to load
    piecesDirs = load_module.get_site_directories('pieces')
    # scan each directory and load all the pieces file
    for directory in piecesDirs:
        if os.path.exists(directory):
            pyObjects = glob.glob(os.path.join(directory, '*.py'))
            for pyFile in pyObjects:
                name = os.path.splitext(os.path.basename(pyFile))[0]
                if name != '__init__':
                    load_module.load_module([directory], name, 'pieces')


if not glb.pieces_loaded:
    #print("loading pieces")
    loadAllPieces()
    glb.pieces_loaded = True
