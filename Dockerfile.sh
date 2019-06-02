#!/bin/bash


# Update 
apt update --fix-missing
apt upgrade -y


# Install miscellaneous usefull tools
apt install -y  minicom \
                socat \
                wget \
                net-tools


# Install pyhon3 
apt install -y  python3 \
                python3-pip


# Install required python packages
pip3 install pyserial


# Install CommSimulator
cp CommSimulator.py /usr/bin/CommSimulator
