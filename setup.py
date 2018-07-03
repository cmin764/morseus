#! /usr/bin/env python


import os
import re
import site
import sys
from distutils import sysconfig

from setuptools import find_packages, setup


SKIP_REQUIREMENT = (
    "git+",
)


def is_venv():
    real, base = map(lambda arg: hasattr(sys, arg),
                     ["real_prefix", "base_prefix"])
    return real or base and base != sys.prefix


def get_site():
    func = getattr(site, "getsitepackages", None)
    if func:
        return func()[0]
    return sysconfig.get_python_lib()


def read(fpath):
    check = os.path.isfile
    path = os.path.join(os.path.dirname(__file__), fpath)
    if not check(path):
        path = fpath
        if not check(path):
            return None
    with open(path) as stream:
        return stream.read()


def skip_requirement(line):
    for skip in SKIP_REQUIREMENT:
        if skip in line:
            return True
    return False


def get_requirements(path="requirements.txt"):
    data = read(path)
    lines = []
    if not data:
        return lines
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or skip_requirement(line):
            continue
        if line.startswith("-r"):
            new_path = line[2:].strip()
            lines.extend(get_requirements(path=new_path))
            continue
        lines.append(line)
    return lines


def get_data_files(source, files, use_source=False):
    destination = (source if use_source else
                   os.path.join(get_site(), source))
    paths = [os.path.join(source, name) for name in files]
    return destination, paths


UNIX = bool(re.search(r"linux|darwin", sys.platform))
VENV = is_venv()
PIP = "--single-version-externally-managed" in sys.argv
LOCAL = PIP and any(map(lambda arg: arg.startswith("--home"), sys.argv))
USE_SOURCE = not UNIX or LOCAL or (VENV and not PIP)


setup(
    name="morseus",
    version="0.5.2",
    description="Morse signals translator.",
    long_description=read("README.md") or "",
    url="https://github.com/cmin764/morseus",
    license="MIT",
    author="Cosmin Poieana",
    author_email="cmin764@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=get_requirements(),
    test_suite="tests",
)
