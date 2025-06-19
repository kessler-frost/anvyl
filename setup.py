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

setup(
    name="anvyl",
    version="0.1.0",
    description="Anvyl Infrastructure Orchestrator - Self-hosted infrastructure management for Apple Silicon",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Anvyl Team",
    author_email="team@anvyl.dev",
    url="https://github.com/kessler-frost/anvyl",
    
    # Package discovery - include both packages and standalone modules
    packages=find_packages(include=["anvyl_sdk", "anvyl_sdk.*", "database", "database.*", "generated", "generated.*"]),
    py_modules=["anvyl_cli", "anvyl_grpc_server"],
    
    # Include additional files
    package_data={
        "generated": ["*.py"],
        "protos": ["*.proto"],
        "anvyl_sdk": ["*.py"],
        "database": ["*.py"],
    },
    
    # Include data files
    include_package_data=True,
    
    # Python version requirement
    python_requires=">=3.12",
    
    # Entry points for CLI
    entry_points={
        "console_scripts": [
            "anvyl=anvyl_cli:app",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: Software Development :: Build Tools",
    ],
    
    # Keywords
    keywords="infrastructure orchestration containers docker grpc cli apple-silicon macos",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/kessler-frost/anvyl/issues",
        "Source": "https://github.com/kessler-frost/anvyl",
        "Documentation": "https://github.com/kessler-frost/anvyl#readme",
        "Changelog": "https://github.com/kessler-frost/anvyl/releases",
    },
    
    # Zip safe
    zip_safe=False,
)