from cx_Freeze import setup, Executable

executables = [Executable('main.py')]
name = 'tgnotion'
version = '0.2'

build_exe_options = {
    'build_exe': '../build/' + name + '_' + version + '_amd64',
    'packages': [
        'sqlalchemy',
    ],
    'excludes': [
        'tkinter',
        'pytest',
        'Ipython',
    ],
}

setup(name='tgnotion',
      version='0.2',
      packages=[],
      options={"build_exe": build_exe_options},
      executables=executables)
