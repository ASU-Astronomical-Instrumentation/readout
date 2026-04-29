from __future__ import annotations
from Cython.Build import cythonize
from Cython.Compiler import Options
from setuptools import Distribution
from setuptools import Extension
from setuptools.command.build_ext import build_ext

def build() -> None:
    source_files = ['kidpy3/_data_collector/data_collector.pyx', 'kidpy3/_data_collector/src/_data_collector.c']
    extensions = [Extension('_data_collector',
                            source_files,
                            include_dirs=["_data_collector/src/", "/HDF_Group/HDF5/2.1.1/include"],
                            library_dirs=["kidpy3/lib", "/HDF_Group/HDF5/2.1.1/lib"],
                            libraries=["hdf5_hl", "hdf5", "m"],
                            extra_compile_args=["-O3"],
                            runtime_library_dirs=["/HDF_Group/HDF5/2.1.1/lib"],
                            )]
    ext_modules = cythonize(extensions, annotate=True, verbose=True )
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