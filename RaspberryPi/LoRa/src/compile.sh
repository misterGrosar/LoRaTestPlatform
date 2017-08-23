#!/bin/sh
# launcher.sh
# This is helper script for compiling LoRa C libraries and program

# compile LoRa libs
make clean
make

# create shared objects libs for use in python
#gcc -shared -o libsum.so -fPIC sum.c