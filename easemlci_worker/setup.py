# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages  # type: ignore
from easemlci import __version__

with open("README.md", "r") as fh:
    README = fh.read()

# The main source of truth for install requirements of this project is the requirements.txt file.
with open("requirements.txt", "r") as f:
    REQUIREMENTS = f.readlines()

setup(
    name='easemlci',
    version=__version__+".dev.4",
    description='Libraries and scripts to customize buildbot for ease.ml ci&cd',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Leonel Aguilar',
    author_email='leonel.aguilar.m@gmail.com',
    url='https://github.com/DS3Lab/easeml',
    license='MIT',
    install_requires=REQUIREMENTS,
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
)



