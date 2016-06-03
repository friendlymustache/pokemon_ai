sudo apt-get update
sudo apt-get install -y make
sudo apt-get install -y gcc
sudo apt-get install -y g++
sudo apt-get install -y git
sudo apt-get install -y python-pip
sudo apt-get install -y python-setuptools
sudo apt-get install -y python-dev
sudo apt-get install -y libblas-dev
sudo apt-get install -y liblapack-dev
sudo apt-get install -y gfortran
sudo pip install numpy
sudo pip install matplotlib

git clone --recursive https://github.com/dmlc/xgboost
cd xgboost; make -j4
cd python-package; sudo python setup.py install