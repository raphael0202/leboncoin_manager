#!/usr/bin/python3
# coding: utf-8
 
from setuptools import setup, find_packages
 
import leboncoin_manager
 
setup(
    name='leboncoin_manager',
    version=leboncoin_manager.__version__,
    packages=find_packages(),
    author="Raphaël B.",
    author_email="raphael0202@yahoo.fr",
    description="Easily manage your ads on leboncoin.fr",
    long_description=open('README.rst').read(),
    install_requires= ["selenium"],
    include_package_data=True,
    url='https://github.com/raphael0202/leboncoin_manager',
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only"
    ],
    entry_points={
        'console_scripts': [
            'leboncoin_manager = leboncoin_manager.leboncoin_manager',
        ],
    },
)
