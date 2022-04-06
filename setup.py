"""setup script"""
from setuptools import setup

setup(
    name="python-project-tools",
    version="0.1.0",
    author="Stefan Hoelzl",
    license="MIT",
    packages=["tools"],
    entry_points={
        "console_scripts": [
            "release=tools.release:main",
            "requirements=tools.requirements:main",
        ],
    },
    install_requires=[
        "fire>=0.4.0",
        "requests>=2.26.0",
        "semver>=2.13.0",
        "toml>=0.10.2",
    ],
    zip_safe=False,
)
