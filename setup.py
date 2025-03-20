from setuptools import setup, find_packages

setup(
    name="autocoder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "httpx>=0.20.0",
        "pyyaml>=6.0",
        "colorama>=0.4.4",
        "tqdm>=4.62.0",
        "gitpython>=3.1.0",
        "pytest>=7.0.0",
        "markdown>=3.3.0",
        "mypy>=0.910",
    ],
    entry_points={
        "console_scripts": [
            "autocoder=autocoder.cli:main",
        ],
    },
    python_requires=">=3.9",
    author="Autocoder Team",
    description="An AI-powered automatic code generation tool using Qwen 2.5 Coder model",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/autocoder/autocoder",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
) 