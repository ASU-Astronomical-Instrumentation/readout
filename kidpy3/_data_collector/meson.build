project('_data_collector', 'c',
        version : '1.0.0',
        default_options : ['warning_level=3', 'c_std=gnu11'])

cc = meson.get_compiler('c')
lib_args = ['-DBUILDING_MESON_LIBRARY', '-D__BUILD_FOR_LIB__']

# Check the operating system
os_name = host_machine.system()

if os_name == 'linux'
    # Linux: Assume standard system installation (finds it via pkg-config or cmake)
    # Make sure you have the 'libhdf5-dev' (Debian/Ubuntu) or 'hdf5-devel' (Fedora/RHEL) package installed!
    hdf5_inc = include_directories('/HDF_Group/HDF5/2.1.1/include')
    hdf5_lib = cc.find_library('hdf5', dirs:'/HDF_Group/HDF5/2.1.1/lib')
    hdf5_dep = dependency('hdf5', language: 'c', static: false)
elif os_name == 'windows'
    # Explicitly block Windows builds as requested
    error('Windows is explicitly not supported for this project.')

else
    error('Unsupported operating system: ' + os_name)
endif

incdir = include_directories('src')
# Build the shared library using the unified hdf5_dep variable
mylib = shared_library('_data_collector', 'src/_data_collector.c',
               install : false,
               c_args : lib_args,
               dependencies: [hdf5_dep],
               include_directories: incdir
)
executable('test_runner','src/test_runner.c', link_with: mylib, include_directories:[hdf5_inc, incdir],
c_args : ['-pg', '-O0'])
