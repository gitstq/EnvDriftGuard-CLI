#!/usr/bin/env python
"""Setup script for EnvGuard-CLI."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="envguard",
    version="1.0.0",
    author="EnvGuard Contributors",
    description="Lightweight terminal environment configuration drift detection engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/envguard/envguard-cli",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    entry_points={
        "console_scripts": [
            "envguard=envguard.cli:main",
        ],
    },
)
