import os
from setuptools import setup, find_packages
from importlib.machinery import SourceFileLoader


module_name = "solverecaptchas"

module = SourceFileLoader(
    module_name, os.path.join(module_name, "__init__.py")
).load_module()

setup(
    name=module_name.replace("_", "-"),
    version=module.__version__,
    author=module.__author__,
    author_email=module.authors_email,
    license=module.__license__,
    description=module.package_info,
    url="https://github.com/embium/solverecaptchas",
    long_description=open("README.rst").read(),
    platforms="all",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities"
    ],
    python_requires=">=3.7",
    package_data={'data': ['*.*']},
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        "playwright",
        "playwright-stealth",
        "pydub",
        "vosk",
        "requests",
        "aiohttp",
        "aiofiles",
        "numpy",
        "pillow",
        "opencv-python"
    ]
)