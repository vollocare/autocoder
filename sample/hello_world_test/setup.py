from setuptools import setup, find_packages

setup(
    name="hello_world_cli",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "hello_world=hello_world.cli:main",
        ],
    },
    install_requires=[
        "pytest>=7.0.0"
    ],
    python_requires=">=3.9",
)