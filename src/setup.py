#!/usr/bin/env python
from setuptools import setup, find_packages

print find_packages()

setup(
    name = "pyfool",
    version = "0.0.1",
    packages = find_packages(),

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['pyCLI'],


    # metadata for upload to PyPI
    author = "Bernhard Bockelbrink",
    author_email = "me@example.com",
    description = "Various Tools",
    keywords = "duplicate directories",
    url = "http://github.com/bboc/tools",

    entry_points = {
        'console_scripts': [
            'dupdirs = dupdirs.__main__:main',
        ],
    }

)
