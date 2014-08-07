#!/bin/bash
# Minestorm installer
# https://github.com/pietroalbini/minestorm

INSTALLATION_PATH=/opt/minestorm
SYMLINK=/usr/local/bin/minestorm

uninstaller_info="${INSTALLATION_PATH}/.uninstaller-info"

if [ -e "${INSTALLATION_PATH}" ] ; then
    mv "${INSTALLATION_PATH}" /tmp/old_minestorm
    echo "The directory ${INSTALLATION_PATH} already exists!"
    echo " Moved old content to /tmp/old_minestorm"
fi

git clone https://github.com/pietroalbini/minestorm.git "${INSTALLATION_PATH}" >/dev/null 2>&1

if [ $? = 1 ] ; then
    echo "Error during installation of minestorm"
    echo " Failed to clone source code! Check your internet connection"
    exit 1
fi

cd ${INSTALLATION_PATH}
tag=`git describe --abbrev=0 --tags 2>/dev/null` # Get latest tag
if [ $? = 0 ] ; then
    git checkout ${tag} >/dev/null 2>&1
else
    git checkout master >/dev/null 2>&1
fi

cp "${INSTALLATION_PATH}/minestorm.json.dist" "${INSTALLATION_PATH}/minestorm.json" >/dev/null

if [ -e "${SYMLINK}" ] ; then
    echo "A thing already exists on ${SYMLINK}"
    echo " Symlink not created"
else
    ln -s "${INSTALLATION_PATH}/cli" "${SYMLINK}" >/dev/null
    chmod +x "${SYMLINK}"
fi

touch "${uninstaller_info}"
echo "${INSTALLATION_PATH}" >> "${uninstaller_info}"
echo "${SYMLINK}" >> "${uninstaller_info}"

echo "minestorm ${tag} successifully installed"
