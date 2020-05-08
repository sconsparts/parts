from setuptools import setup, find_packages
import sys

sys.path.append("./src/parts")
import parts_version

setup(name="scons-parts",
      description="Extension module to SCons build system",
      author="Jason Kenny",
      author_email="dragon512@live.com",
      url="https://bitbucket.org/sconsparts/parts",
      license="MIT",
      version=parts_version._PARTS_VERSION,
      package_dir={'': 'src'},
      packages=find_packages('src'),
      entry_points={
          'console_scripts': ['parts=parts.version_info:parts_version_text'],
      },

      install_requires=[
          "future",
          "scons"
      ],

      package_data={
          # If any package contains *.txt or *.rst files, include them:
          '': ['*.txt'],

      },
             # see classifiers
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
         classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Topic :: Terminals',
            ],
      )
