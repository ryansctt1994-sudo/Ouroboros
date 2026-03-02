#!/usr/bin/env python3
"""
Ouroboros/EDEN Setup Configuration
===================================

Author: AIOSPANDORA Development Team
License: MIT
"""

from setuptools import setup, find_packages

setup(
    name="ouroboros-eden",
    version="1.0.0",
    description="EDEN AIOS - Cosmic Consciousness Operating System",
    author="AIOSPANDORA Development Team",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "networkx>=2.6.0",
        "matplotlib>=3.4.0",
    ],
    extras_require={
        "eden": [
            # eden_ecs is now included in-tree — no external dependency needed
        ],
        "ml": [
            # ML requirements if needed
        ],
        "dev": [
            "pytest>=7.0.0",
        ],
    },
    python_requires=">=3.8",
)
