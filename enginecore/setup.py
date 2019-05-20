"""Simulation engine for Anvil! & similar High-Availability systems"""
from setuptools import setup, find_packages

setup(
    name="SimEngine",
    version="3.7",
    packages=find_packages(),
    scripts=["simengine-cli"],
    install_requires=[
        "redis>=2.10.6",
        "circuits",
        "neo4j-driver",
        "pysnmp",
        "libvirt-python",
        "websocket-client",
    ],
    author="Seneca OSTEP & Alteeve",
    author_email="olga.belavina@senecacollege.ca",
    description="Simulation platform for High-Availability systems",
    license="GPL",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
    url="https://simengine.readthedocs.io/en/latest/",
    project_urls={
        "Bug Tracker": "https://github.com/Seneca-CDOT/simengine/issues",
        "Documentation": "https://simengine.readthedocs.io/en/latest/",
        "Source Code": "https://github.com/Seneca-CDOT/simengine",
    },
)
