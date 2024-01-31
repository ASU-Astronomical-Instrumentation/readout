================
Getting Started
================


Requirements
------------

1. `Python 3.8.18 <https://www.python.org/downloads/release/python-3818/>`_
2. Ubuntu 18.04.6 LTS or later

    .. WARNING::
       Ubuntu 18.04.6 is End of Life. Upgrading to Ubuntu 22.04 LTS is **strongly** recommended.
       The current version of the library is tested on Ubuntu 22.04 LTS.

3. python packages (pip requirements) are listed in the `python-pip3.8.18.txt` file

4. redis server

System Setup
------------

For users with Ubuntu 18.04.6 LTS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. NOTE::
   The following instructions assume that you are running a brand new installation of 
   Ubuntu 18.04.6 LTS. If you are running an older version of Ubuntu, 
   you may need to install additional packages or use different commands to install 
   the required packages. There shall not be any support for previous versions of Ubuntu.
   Since python3.8.18 is not offered by the default repositories of Ubuntu 18.04.6 LTS,
   we will have to build it from the source.


1. Update the system and grab the packages we need::

      sudo apt update && sudo apt upgrade -y

      sudo apt-get install build-essential pkg-config git -y

      sudo apt-get install build-essential gdb lcov pkg-config \
         libbz2-dev libffi-dev libgdbm-dev libgdbm-compat-dev liblzma-dev \
         libncurses5-dev libreadline6-dev libsqlite3-dev libssl-dev \
         lzma lzma-dev tk-dev uuid-dev zlib1g-dev -y

2. Grab the python source and compile it::
      
      cd ~/Downloads

      wget https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz

      tar -zxvf Python-3.8.18.tgz

      cd Python-3.8.18

      ./configure --enable-optimizations --enable-shared

      make -j

      sudo make altinstall

3. Close the current shell and launch a fresh one. Check the python version::

      python3.8 --version

4. Create a virtual environment to work from. In the event you have to run different python codes
   with different versions of python, you can create a virtual environment for each version of python
   you have installed. You can (and should) also do this on a per-project basis. This will allow you to run different versions of python on the same machine
   without any conflicts. While somewhat inconvenient, it will save you countless hours in the long run::

      python3.8 -m venv ~/venv3.8
   
   Activate the environment with ``source ~/venv3.8/bin/activate``

   .. TIP::
      You can add the command ``source ~/venv3.8/bin/activate`` to your ``.bashrc`` file
      to automatically activate the environment when you open a new shell.

      The virtual environment can be placed anywhere and be named almost anything.

      ``echo "source ~/venv3.8/bin/activate" >> ~/.bashrc``
      

For users with Ubuntu 20.04 LTS or later
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Install python3.8::

      sudo apt update && sudo apt upgrade -y

      sudo apt-get install python3.8 python3.8-venv python3-dev -y

2. Create a virtual environment to work from and activate it as mentioned above::

      python3.8 -m venv ~/venv3.8

      source ~/venv3.8/bin/activate

Setup the Redis Server
----------------------
1. Install the redis server::

      sudo apt update && sudo apt upgrade -y

      sudo apt-get install redis-server -y



Setup the Library 
-----------------

1. Clone the library and install the required packages::

      git clone https://github.com/ASU-Astronomical-Instrumentation/readout.git
      cd readout
      pip3 install -r python-pip3.8.18.txt


2. TBD

