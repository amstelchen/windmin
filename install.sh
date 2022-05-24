#!/bin/bash

if [[ -z $1 || -z $2 ]]; then
    echo "parameters missing."
    exit
fi
echo $1
LNG=$2

sudo cp ~/.local/bin/$1 /usr/bin/$1
sudo cp -v $1.png /usr/share/pixmaps/$1.png
sudo cp -v $1.desktop.$LNG /usr/share/applications/$1.desktop
cp -v $1.desktop.$LNG ~/Desktop/$1.desktop

xgettext -d $1 -o $1/locales/$1.pot $1/*.py
#L="nl"; LC="LC_MESSAGES"; mkdir -p $L/$LC ; msginit -l $L -o $L/$LC/gameinfo.po && msgfmt -o $L/$LC/gameinfo.mo $L/$LC/gameinfo.po
poedit 2>/dev/null
sudo cp -v $1/locales/de/LC_MESSAGES/*.mo /usr/share/locale/de/LC_MESSAGES/

poetry build
pip install dist/windmin-0.1.0-py3-none-any.whl --force-reinstall
exec $1

#python setup.py sdist
#python -m build --wheel --no-isolation
#updpkgsums
#makepkg -fci