# -*- mode: python -*-

block_cipher = None

root = "/home/cmin/Repos/"

a = Analysis(['main.py'],
             pathex=[root + "morseus"],
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
               Tree(root + "morseus-min/"),
               Tree(root + "libmorse/"),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Morseus')
