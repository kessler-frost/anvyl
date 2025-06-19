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

# Runtime dependencies (core dependencies needed for the package to work)
RUNTIME_REQUIREMENTS = [
    "grpcio>=1.59.0",
    "grpcio-tools>=1.59.0",
    "docker>=6.1.0",
    "sqlmodel>=0.0.14",
    "fastapi>=0.104.0",
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    "httpx>=0.25.2",
    "pyinfra>=3.3.1",
    "pydantic>=2.5.0",
    "psutil>=5.9.0",
    "uvicorn>=0.24.0",
    "python-dotenv>=1.0.0",
    "requests>=2.31.0",
]

# Development dependencies (only needed for development, testing, etc.)
DEVELOPMENT_REQUIREMENTS = [
    "black>=23.11.0",
    "isort>=5.12.0",
    "mypy>=1.7.1",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-grpc>=0.8.0",
    "pytest-docker>=2.0.1",
]

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
    
    # Runtime dependencies
    install_requires=RUNTIME_REQUIREMENTS,
    
    # Optional dependencies
    extras_require={
        "dev": DEVELOPMENT_REQUIREMENTS,
        "all": RUNTIME_REQUIREMENTS + DEVELOPMENT_REQUIREMENTS,
    },
    
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