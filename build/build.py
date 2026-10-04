r"""
Builds dist/WhisperWriter (PyInstaller) and dist/installer/WhisperWriter_Setup_<ver>.exe (Inno Setup).
Run with the project venv:   venv\Scripts\python build\build.py [--no-installer] [--no-extras]
The version comes from the VERSION file at the project root -- change it there only.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
VERSION = open('VERSION', encoding='utf-8').read().strip()
parts = [int(x) for x in VERSION.split('.')] + [0] * 4
v4 = tuple(parts[:4])


def step(msg):
    print(f'\n=== {msg}', flush=True)


step(f'WhisperWriter {VERSION}: writing build/version_info.txt')
with open(os.path.join('build', 'version_info.txt'), 'w', encoding='utf-8') as f:
    f.write(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={v4}, prodvers={v4}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'iydebu'),
      StringStruct('FileDescription', 'WhisperWriter - offline speech to text'),
      StringStruct('FileVersion', '{VERSION}'),
      StringStruct('InternalName', 'WhisperWriter'),
      StringStruct('OriginalFilename', 'WhisperWriter.exe'),
      StringStruct('ProductName', 'WhisperWriter'),
      StringStruct('ProductVersion', '{VERSION}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""")

step('MSVC runtime')
# PyQt5's wheel ships an old MSVC runtime (14.26) in PyQt5/Qt5/bin. If Qt loads it first,
# onnxruntime (faster-whisper's VAD) fails with 'DLL initialization routine failed'.
# PyInstaller's analysis step imports PyQt5 before onnxruntime and dies on exactly that.
# Fix for the build only (the venv is left untouched): a sitecustomize that preloads the
# system's current runtime, so Qt reuses it. The spec then ships that same runtime.
# Needs the Microsoft VC++ 2015-2022 x64 redistributable on the build PC.
VC_DLLS = ('vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'concrt140.dll')
sys32 = os.path.join(os.environ['SystemRoot'], 'System32')
missing = [n for n in VC_DLLS if not os.path.exists(os.path.join(sys32, n))]
if missing:
    sys.exit(f'{missing} not in System32 -- install the Microsoft Visual C++ 2015-2022 x64 redistributable.')
preload_dir = os.path.join(ROOT, 'build', 'temp', 'preload')
os.makedirs(preload_dir, exist_ok=True)
with open(os.path.join(preload_dir, 'sitecustomize.py'), 'w', encoding='utf-8') as f:
    f.write('import ctypes, os\n'
            f'for _n in {VC_DLLS!r}:\n'
            '    ctypes.WinDLL(os.path.join(os.environ["SystemRoot"], "System32", _n))\n')
env = dict(os.environ, PYTHONPATH=preload_dir + os.pathsep + os.environ.get('PYTHONPATH', ''))
print('OK system runtime will be preloaded during analysis')

step('PyInstaller')
# One folder per version: an old build that Explorer/antivirus still holds open can't block the next one.
APP_DIST = os.path.join('dist', f'WhisperWriter-{VERSION}')
shutil.rmtree(APP_DIST, ignore_errors=True)
subprocess.run([sys.executable, '-m', 'PyInstaller', os.path.join('build', 'WhisperWriter.spec'),
                '--distpath', APP_DIST, '--workpath', os.path.join('build', 'temp'),
                '--noconfirm', '--log-level', 'WARN'], check=True, env=env)
exe = os.path.join(APP_DIST, 'WhisperWriter', 'WhisperWriter.exe')
if not os.path.exists(exe):
    sys.exit(f'Build failed: {exe} missing')
size = sum(os.path.getsize(os.path.join(d, n)) for d, _, fs in os.walk(os.path.dirname(exe)) for n in fs)
print(f'OK {exe}  ({size / 2**20:.0f} MB app folder)')

if '--no-installer' in sys.argv:
    sys.exit(0)

step('Inno Setup')
candidates = [
    os.path.expandvars(r'%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe'),
    os.path.expandvars(r'%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe'),
    os.path.expandvars(r'%ProgramFiles%\Inno Setup 6\ISCC.exe'),
]
iscc = next((c for c in candidates if os.path.exists(c)), None)
if not iscc:
    sys.exit('Inno Setup 6 not found. Install it from https://jrsoftware.org/isdl.php and re-run.')
# /Q = quiet (errors still print). Main setup, then the optional extra-models add-on
# (skip with --no-extras; the models rarely change).
subprocess.run([iscc, '/Q', f'/DMyAppVersion={VERSION}', f'/DAppDist={os.path.abspath(os.path.dirname(exe))}',
                os.path.join('build', 'WhisperWriter.iss')], check=True)
outputs = [f'WhisperWriter_Setup_{VERSION}.exe']
if '--no-extras' not in sys.argv:
    subprocess.run([iscc, '/Q', f'/DMyAppVersion={VERSION}', os.path.join('build', 'WhisperWriter_ExtraModels.iss')], check=True)
    outputs.append(f'WhisperWriter_ExtraModels_Setup_{VERSION}.exe')
for name in outputs:
    path = os.path.join('dist', 'installer', name)
    print(f'OK {path}  ({os.path.getsize(path) / 2**30:.2f} GB)')
