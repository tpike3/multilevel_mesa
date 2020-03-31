#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re


from setuptools import setup, find_packages
from codecs import open



#get the readme file for the long description below--optional
with open('README.md', 'r') as fh:
    long_description = fh.read()

# see https://github.com/pypa/sampleproject/blob/master/setup.py for explanation of each parameter and links
setup(
    name='multilevel_mesa',
    version='0.0.2',
    description="Provides Extension module to Mesa to allow for Hierarchies and Modules of Agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    packages = ["multilevel_mesa"],
    #for more elaborate projects with directories of files such as tests etc
    install_requires=['networkx', "mesa"]
)
