import sys
import os
sys.path.append('./parts')
import parts_version


def get_packages(path):
    ret = []
    for d in os.listdir(path):
        np = os.path.join(path, d)
        if os.path.isdir(np) and d != '.svn':
            tmp = np.replace('/', '.')[2:]
            tmp = tmp.replace('\\', '.')
            ret.append(tmp)
            tmp = get_packages(np)
            if tmp != []:
                ret.extend(tmp)
    return ret


def get_data_files(root, path, installpath):
    ret = []
    files = []
    if os.path.exists(path) == False:
        return ret
    pth = os.path.join(root, installpath)
    for d in os.listdir(path):
        np = os.path.join(path, d)
        if os.path.isdir(np) and d.endswith('.svn') == False:
            tmp = get_data_files(root, np, os.path.join(installpath, d))
            if tmp != []:
                ret.extend(tmp)
        elif os.path.isfile(np) and d.endswith('.py'):
            files.append(np)
    if files != []:
        ret.append((pth, files))
    return ret


def get_package_data(path, root):
    ret = []
    files = []

    # might not exist...
    if os.path.exists(path) == False:
        return ret

    for d in os.listdir(path):
        np = os.path.join(path, d)
        pkg_file = os.path.join(root, d)
        if os.path.isdir(np) and d.endswith('.svn') == False:
            tmp = get_package_data(np, pkg_file)
            if tmp != []:
                ret.extend(tmp)
        elif os.path.isfile(np) and d.endswith('.py'):
            tmp = pkg_file.replace('\\', '/')
            files.append(tmp)

    ret += files
    return ret

pk_data = get_package_data('parts-site', '')
# if the packaging of this parts distro has not "special" data to install
# we don't want to add the parts.parts-site directory package
# doing this mean the package_data will be ignored
if pk_data:
    pk_package = ['parts.parts-site']
else:
    pk_package = []

from distutils.core import setup
# try:
#    import py2exe
# except:
#    print "py2exe not found"

setup(name="parts",
      description="Extension module to SCons build system",
      author="Jason Kenny",
      author_email="jason.l.kenny@intel.com",
      version=parts_version._PARTS_VERSION,
      packages=['parts'] + get_packages('./parts') + pk_package,
      entry_points={
          'console_scripts': ['parts=parts.version_info:parts_version_text'],
      },
      package_dir={'parts.parts-site': 'parts-site'},
      package_data={
          'parts.parts-site': pk_data,
      },
      data_files=[("", ["license.txt"])],
      url="https://bitbucket.org/dragon512/parts",
      license="MIT"
      )
