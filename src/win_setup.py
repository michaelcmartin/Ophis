import py2exe

py2exe.freeze(options={'bundle_files': 1, 'packages': ['Ophis']},
              console=[{'script': "scripts/ophis"}],
              zipfile='modules.zip')
