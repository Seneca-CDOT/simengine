"""Simulation engine for Anvil! & similar High-Availability systems"""
from setuptools import setup
import enginecore

setup(
    name="SimEngine",
    version="1.0",
    packages=['enginecore'],
    scripts=['simengine-cli'],

    author="Seneca OSTEP & Alteeve",
    author_email="olga.belavina@senecacollege.ca",
    description="Simulation platform for High-Availability systems",
    license="GPL",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux"
    ],
    url="https://simengine.readthedocs.io/en/latest/",
    project_urls={
        "Bug Tracker": "https://github.com/Seneca-CDOT/simengine/issues",
        "Documentation": "https://simengine.readthedocs.io/en/latest/",
        "Source Code": "https://github.com/Seneca-CDOT/simengine",
    }

)