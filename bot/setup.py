from cx_Freeze import setup, Executable
# [ ] delete this file
executables = [Executable('main.py')]
name = 'tgnotion'
version = input('please write version number: ')

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

setup(name=name,
      version=version,
      packages=[],
      options={"build_exe": build_exe_options},
      executables=executables)
