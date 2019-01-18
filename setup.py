#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re


from setuptools import setup, find_packages
from codecs import open


#get version from init file
version = ''
with open('ml_mesa/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

#get the readme file for the long description below--optional
with open('README.md', 'rb', encoding='utf-8') as f:
    readme = f.read()

# see https://github.com/pypa/sampleproject/blob/master/setup.py for explanation of each parameter and links
setup(
    name='ml_mesa',
    version=version,
    description="Provides Extension module to Mesa to allow for Heirarhcies and Modules of Agents",
    long_description=readme,
    url='https://github.com/tpike3/ml_mesa',
    author='Tom Pike',
    author_email='tpike3@gmu.edu',
    classifiers=[
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Life',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: English',
    ],
    keywords='agent based modeling model ABM simulation multi-agent coaltion game theory',
    packages = ["ml_mesa"],
    #for more elaborate projects with directories of files such as tests etc
    install_requires=['networkx', "mesa"]
)