import glob
import os
import tqdm
import requests
import zipfile
import tarfile

PROJDIR = os.path.normpath(os.path.join(os.environ['PWD'], '..'))
print(f"PROJDIR: {PROJDIR}")
BUILDPATH = f"{PROJDIR}/build/dependencies"
print(f"BUILDPATH: {BUILDPATH}")
INSTALL_DIR = f"{PROJDIR}/build/dependencies/out"
print(f"INSTALL_DIR: {INSTALL_DIR}")


def grab_hdf5(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("Failed to get latest release")
    data = r.json()
    a = data['assets']
    asset_dict = a[-2]
    filename:str = asset_dict['name']
    download_url = asset_dict['browser_download_url']
    latest_version = data['tag_name']
    print(f"Latest Version: {latest_version}")
    dl_path = f"{BUILDPATH}/{filename}"

    # Do we already have a build folder
    if os.path.exists(f"{BUILDPATH}/hdf5_{latest_version}"):
        print(f"Skipping download and extract of hdf5 as it appears to have already been downloaded")
        return

    # We dont have a build folder, do we already have the tar.gz file?
    elif os.path.exists(f"{BUILDPATH}/hdf5.tar.gz"):
        with tarfile.open(dl_path, 'r') as tar:
            tar.extractall(f"{BUILDPATH}", filter="data")
        return

    # In the case of neither, download it, and extract it
    else:
        print(f"Downloading from {download_url}")
        r2 = requests.get(download_url, allow_redirects=True)
        if not r2.status_code == 200:
            raise Exception("Failed to download file")
        with open(dl_path, "wb") as f:
            f.write(r2.content)
        with tarfile.open(dl_path, 'r') as tar:
            tar.extractall(f"{BUILDPATH}", filter="data")
        # os.remove(dl_path)


def grab_extract_gzip2(url, override=""):
    filename = url.split("/")[-1]
    dl_path = f"{BUILDPATH}/{filename}"

    if not override == "" and os.path.exists(f"{BUILDPATH}/{override}"):
        extracted_dir = f"{BUILDPATH}/{override}"
        print(f"{override} already downloaded and extracted to \n\t{os.path.abspath(extracted_dir)}")
        return os.path.abspath(extracted_dir)
    print(f"Checking for {dl_path.strip('.tar.gz')}")
    if not os.path.exists(f"{dl_path}"):
        print(f"Downloading from {url}")
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception("Failed to download gzip file")
        with open(dl_path, "wb") as f:
            f.write(r.content)
        with tarfile.open(dl_path, "r:gz") as tar:
            tar.extractall(f"{BUILDPATH}", filter="data")
        # os.remove(dl_path)
    else:
        print(f"{filename} already downloaded and extracted to \n\t{os.path.abspath(dl_path.strip(".tar.gz"))}")
    if not override == "":
        return f"{BUILDPATH}/{override}"
    return os.path.abspath(dl_path.strip(".tar.gz"))

def build_lib(path):
    if os.path.exists(f"{path}/build"):
        print(f"Skipping build of {path} as it already has a build folder")
        return
    build_dir = f"{path}/build"
    os.makedirs(build_dir, exist_ok=True)
    os.chdir(build_dir)
    os.system(f"cmake -G 'Unix Makefiles' -DCMAKE_INSTALL_PREFIX:PATH={INSTALL_DIR} ../")
    os.system("make install -j")


def build_hdf5():
    # if os.path.exists(f"{INSTALL_DIR}/lib/libhdf5.so"):
    #     print(f"Skipping build of hdf5 as it appears to have already been built")
    #     return
    hdf_dir = os.path.abspath(glob.glob(f"{BUILDPATH}/hdf5-*")[0])
    build_dir = f"{hdf_dir}/build_lib"
    os.makedirs(build_dir, exist_ok=True)
    os.chdir(f"{hdf_dir}")
    os.chdir(f"{build_dir}")
    os.system(f'../configure --prefix={INSTALL_DIR}'
              f' --enable-build-mode=production')
    os.system("make install -j")



if __name__ == "__main__":
    os.makedirs("../build/dependencies/", exist_ok=True)
    os.chdir(PROJDIR)
    grab_hdf5("https://api.github.com/repos/hdfgroup/hdf5/releases/latest")
    build_hdf5()
    os.makedirs(f"{PROJDIR}/kidpy3/lib", exist_ok=True)
    os.makedirs(f"{PROJDIR}/kidpy3/lib/include", exist_ok=True)
    os.system(f"cp {INSTALL_DIR}/lib/*.so {PROJDIR}/kidpy3/lib")
    os.system(f"cp {INSTALL_DIR}/lib/*.so* {PROJDIR}/kidpy3/lib")
    os.system(f"cp {INSTALL_DIR}/include/*.h {PROJDIR}/kidpy3/lib/include")