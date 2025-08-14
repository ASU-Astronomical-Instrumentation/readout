# from setuptools import setup, Extension
# from Cython.Build import cythonize
# from Cython.Compiler import Options
#
# Options.annotate = False
#
# source_files = ['kidpy3/_data_collector/data_collector.pyx', 'kidpy3/_data_collector/src/interface_socket.c']
# extensions = [Extension('_data_collector', source_files, include_dirs=["_data_collector/src/"],  )]
#
# setup(
#     name='kidpy3',
#     version='1.0',
#     packages=['_data_collector', '_data_collector.tests'],
#     package_dir={'': 'kidpy3'},
#     url='https://github.com/ASU-Astronomical-Instrumentation/readout',
#     license='',
#     author='carobers',
#     author_email='carobers@asu.edu',
#     description='MKID Readout Library',
#     ext_modules=cythonize(extensions),
#     options={'build_ext': {'inplace': True}},
# )
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