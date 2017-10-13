import sys
import os
import tarfile

TEST_TARBALL_NAME = 'test2'


def generateShell(name):
    with open('%s.sh' % name, 'w') as f:
        f.write('''#!/bin/sh

echo "I'm done!" >markerfile
exit 0

''')
        with open('/dev/urandom', 'r') as rnd:
            f.write(rnd.read(150 * 1024 * 1024))

    os.chmod('%s.sh' % name, 0o755)


def packFile(name):
    tar = tarfile.open(name='%s.tar.gz' % name, mode='w:gz')
    try:
        tar.add('%s.sh' % name)
    finally:
        tar.close()
    os.unlink('%s.sh' % name)


def generateTarball(name):
    generateShell(name)
    packFile(name)

if __name__ == '__main__':
    generateTarball(sys.argv[1])
