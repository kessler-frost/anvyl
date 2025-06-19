#!/usr/bin/env python3
"""
Setup script for Anvyl CLI
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# Read requirements from requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="anvyl",
    version="0.1.0",
    description="Anvyl Infrastructure Orchestrator CLI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Anvyl Team",
    author_email="team@anvyl.dev",
    url="https://github.com/kessler-frost/anvyl",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "anvyl=anvyl_cli:app",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="infrastructure orchestration containers docker cli",
    project_urls={
        "Bug Reports": "https://github.com/kessler-frost/anvyl/issues",
        "Source": "https://github.com/kessler-frost/anvyl",
        "Documentation": "https://github.com/kessler-frost/anvyl#readme",
    },
)