#!/bin/bash

cd bot
python setup.py build
cd ../build
tar -zcf tgnotion_0.2_amd64.tar.gz *