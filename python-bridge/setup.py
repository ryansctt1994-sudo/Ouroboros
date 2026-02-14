"""
EDEN ECS Setup
==============

Installation script for the EDEN Entity-Component-System package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="eden-ecs",
    version="1.0.0",
    author="AIOSPANDORA Development Team",
    author_email="dev@aiospandora.io",
    description="Entity-Component-System architecture for cosmic consciousness",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AIOSPANDORA/Ouroboros",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Pure Python stdlib - no external dependencies
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "eden-demo=eden_ecs.demo:run_demo",
        ],
    },
)
