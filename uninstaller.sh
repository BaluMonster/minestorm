#!/bin/bash
# Minestorm uninstaller
# https://github.com/pietroalbini/minestorm

# Detect source directory
# Thanks to http://stackoverflow.com/a/246128/2204144
source="$0"
while [ -h "${source}" ]; do
    dir="$( cd -P "$( dirname "${source}" )" && pwd )"
    source="$(readlink "${source}")"
done
directory="$( cd "$( dirname "${source}" )" && pwd )"
info_file="${directory}/.uninstaller-info"

if [ -f "${info_file}" ]; then
    for file in $( cat "${info_file}" ); do
        rm -rf ${file}
    done
    echo "minestorm uninstalled successifully"
else
    echo "Unable to locate uninstaller details"
fi
