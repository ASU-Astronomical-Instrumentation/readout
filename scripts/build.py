from __future__ import annotations
from Cython.Build import cythonize
from setuptools import Distribution
from setuptools import Extension
from setuptools.command.build_ext import build_ext

def build() -> None:
    source_files = ['kidpy3/_data_collector/data_collector.pyx', 'kidpy3/_data_collector/src/interface_socket.c']
    extensions = [Extension('_data_collector', source_files, include_dirs=["_data_collector/src/"])]
    ext_modules = cythonize(extensions)
    distribution = Distribution({
        "name": "kidpy3",
        "packages": ["kidpy3"],
        "ext_modules": ext_modules,

    })
    cmd = build_ext(distribution)
    cmd.build_lib = "./kidpy3/"
    cmd.ensure_finalized()
    cmd.run()


if __name__ == "__main__":
    build()