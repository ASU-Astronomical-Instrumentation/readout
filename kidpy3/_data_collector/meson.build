project('_data_collector', 'c',
        version : '1.0.0',
        default_options : ['warning_level=3', 'c_std=gnu11'])

cc = meson.get_compiler('c')
# Check the operating system

# Linux: Assume standard system installation (finds it via pkg-config or cmake)
# Make sure you have the 'libhdf5-dev' (Debian/Ubuntu) or 'hdf5-devel' (Fedora/RHEL) package installed!
hdf5_inc = include_directories('/HDF_Group/HDF5/2.1.1/include')
hdf5_lib = cc.find_library('hdf5', dirs:'/HDF_Group/HDF5/2.1.1/lib')
hdf5_dep = dependency('hdf5', language: 'c', static: false)

incdir = include_directories('src')
#myargs = ['-pg', '-O0', '-g', '-finstrument-functions']
myargs = ['-O3']
# Build the shared library using the unified hdf5_dep variable
#mylib = shared_library('_data_collector', 'src/_data_collector.c',
#   install : false,
#   dependencies: [hdf5_dep],
#   include_directories: incdir
#)

myprog = executable('test_runner',['src/test_runner.c',  'src/_data_collector.c'],
            include_directories: [incdir],
            c_args: myargs, link_args: myargs,
            dependencies: [hdf5_dep]
)
