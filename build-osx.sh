#! /usr/bin/env bash

pyinstaller -y --clean --windowed --icon "artwork/morseus.ico" morseus-osx.spec

pushd dist
hdiutil create ./Morseus.dmg -srcfolder Morseus.app -ov
popd
