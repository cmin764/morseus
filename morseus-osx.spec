# -*- mode: python -*-

block_cipher = None

repos = "/Users/cmin/Repos/"

a = Analysis(['main.py'],
             pathex=[repos + "morseus"],
             binaries=[],
             datas=[],
             hiddenimports=['scipy._lib.messagestream'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['_tkinter', 'Tkinter', 'enchant', 'twisted'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Morseus',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               Tree(repos + "morseus-clone/"),
               Tree(repos + "libmorse/"),
               Tree(repos + "morseus/deps/dylibs/"),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Morseus')
app = BUNDLE(coll,
             name='Morseus.app',
             icon="artwork/morseus.ico",
             bundle_identifier=None)
