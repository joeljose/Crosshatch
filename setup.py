"""Setup configuration for the crosshatch package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="crosshatch",
    version="2.0.0",
    author="Joel Jose",
    author_email="joeljose.k1@gmail.com",
    description="Modern implementation of crosshatch artistic effects using SAM2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joeljose/Crosshatch",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Artistic Software",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
        "torch>=2.5.1",
        "torchvision>=0.20.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "notebooks": [
            "jupyter>=1.0.0",
            "matplotlib>=3.7.0",
            "ipython>=8.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "crosshatch=crosshatch.__main__:main",
        ],
    },
)
