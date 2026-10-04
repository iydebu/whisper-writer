# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for WhisperWriter (onedir, windowed).
Run from the project root:  pyinstaller build/WhisperWriter.spec --distpath dist --workpath build/temp
build/build.bat does this plus the installer.

What goes where:
  dist/WhisperWriter-<ver>/WhisperWriter/WhisperWriter.exe   the app
  .../_internal/        Python, libraries, src code, assets
  .../_internal/cuda/   cuBLAS for GPU mode (preloaded by run.py)
Models are NOT bundled here -- the installer copies them to {app}/models as components.
"""
import os
import site
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

PROJECT_ROOT = os.getcwd()
SRC = os.path.join(PROJECT_ROOT, 'src')

# cuBLAS 12 is the only CUDA runtime piece ctranslate2 needs that it does not ship
# (it bundles cuDNN itself). Take it from torch's wheel; torch itself is NOT bundled.
_site = next(p for p in site.getsitepackages() if p.endswith('site-packages'))
CUDA_DLLS = [os.path.join(_site, 'torch', 'lib', n) for n in ('cublas64_12.dll', 'cublasLt64_12.dll')]
for _p in CUDA_DLLS:
    if not os.path.exists(_p):
        raise SystemExit(f'Missing {_p} -- install torch (CUDA 12 build) in the build venv.')

datas = [
    (os.path.join(PROJECT_ROOT, 'assets'), 'assets'),
    (os.path.join(PROJECT_ROOT, 'logo.ico'), '.'),
    (os.path.join(PROJECT_ROOT, 'VERSION'), '.'),     # shown in the tray About box
    (os.path.join(SRC, 'config_schema.yaml'), '.'),
    (os.path.join(SRC, 'default_config.yaml'), '.'),
]
datas += collect_data_files('faster_whisper')      # silero VAD onnx model
datas += collect_data_files('ctranslate2')

binaries = [(p, 'cuda') for p in CUDA_DLLS]
binaries += collect_dynamic_libs('ctranslate2')      # ctranslate2.dll, cudnn64_9.dll, libiomp5md.dll
binaries += collect_dynamic_libs('vosk')

hiddenimports = [
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'sentencepiece',
    'webrtcvad',
    'onnxruntime',
    'selftest',
]
hiddenimports += collect_submodules('faster_whisper')
hiddenimports += collect_submodules('ui')

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'run.py')],
    pathex=[PROJECT_ROOT, SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[os.path.join(PROJECT_ROOT, 'build', 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    # torch/transformers are only needed to CONVERT models (models/setup_models.py),
    # never at runtime. Keeping them out saves ~4 GB.
    excludes=[
        'torch', 'torchvision', 'torchaudio', 'torchgen', 'transformers',
        'tensorflow', 'jax', 'sympy', 'scipy', 'pandas',
        'tkinter', 'matplotlib', 'notebook', 'IPython', 'pytest',
    ],
    noarchive=False,
)

# Ship ONE copy of the MSVC runtime: the system's current one, at the _internal root.
# (PyQt5's wheel carries an old copy; mixing versions crashes onnxruntime.) App-local
# deployment of these DLLs is allowed by the VC++ redist license.
VC_DLLS = {'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'concrt140.dll'}
_sys32 = os.path.join(os.environ['SystemRoot'], 'System32')
a.binaries = [b for b in a.binaries if os.path.basename(b[0]).lower() not in VC_DLLS]
a.binaries += [(n, os.path.join(_sys32, n), 'BINARY') for n in sorted(VC_DLLS)]
# Dependency scan re-adds cublasLt as torch/lib/cublasLt64_12.dll (451 MB duplicate). The copy
# in cuda/ is preloaded by run.py before cublas64_12, which satisfies that dependency.
a.binaries = [b for b in a.binaries if not b[0].replace('\\', '/').startswith('torch/')]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WhisperWriter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,              # tray app; output goes to %APPDATA%\WhisperWriter\whisperwriter.log
    disable_windowed_traceback=False,
    icon=os.path.join(PROJECT_ROOT, 'logo.ico'),
    version=os.path.join(PROJECT_ROOT, 'build', 'version_info.txt'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='WhisperWriter',
)
