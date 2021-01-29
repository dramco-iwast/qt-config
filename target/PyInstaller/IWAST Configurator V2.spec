# -*- mode: python -*-

block_cipher = None


a = Analysis(['C:\\Users\\Pierre\\PycharmProjects\\QT_Config_V2\\src\\main\\python\\main.py'],
             pathex=['C:\\Users\\Pierre\\PycharmProjects\\QT_Config_V2\\target\\PyInstaller'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['C:\\Users\\Pierre\\PycharmProjects\\QT_Config_V2\\venv\\lib\\site-packages\\fbs\\freeze\\hooks'],
             runtime_hooks=['C:\\Users\\Pierre\\PycharmProjects\\QT_Config_V2\\target\\PyInstaller\\fbs_pyinstaller_hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='IWAST Configurator V2',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False , icon='C:\\Users\\Pierre\\PycharmProjects\\QT_Config_V2\\src\\main\\icons\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='IWAST Configurator V2')
