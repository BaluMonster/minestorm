#!/usr/bin/python3
# minestorm installer
# Copyright (C) 2014 Pietro Albini

# Bootstrap setuptools
import ez_setup
ez_setup.use_setuptools()
del ez_setup

import setuptools
setuptools.setup(
    name='minestorm',
    version='1.0.0-alpha1',
    description='Advanced Minecraft servers wrapper',

    author='Pietro Albini',
    author_email='pietro@pietroalbini.io',
    url='http://pietroalbini.io',

    license='GNU-GPL v3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operative System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
    ],

    packages=[
        'minestorm',
        'minestorm.common',
        'minestorm.console',
        'minestorm.console.ui',
        'minestorm.server',
        'minestorm.test',
        'minestorm.test.common',
    ],
    package_dir={
        'minestorm': 'minestorm',
    },
    zip_safe=False,

    entry_points = {
        'console_scripts': [
            'minestorm = minestorm.cli:main',
        ],
    },

    include_package_data=True,
    package_data={
        'minestorm': ['_samples/*'],
    },

    install_requires=[
        # Nothing yet
    ],
)
