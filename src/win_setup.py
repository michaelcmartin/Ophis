from distutils.core import setup
import py2exe, sys

sys.argv.append('py2exe')

setup(options = {'py2exe': {'bundle_files': 1}},
      packages = ['Ophis'],
      zipfile = None,
      console = [{'script': "scripts/ophis"}])
