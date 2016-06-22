#!/bin/bash

cd `dirname "$0"`

./stop_real
echo "sleep 1 second ..."
sleep 1
./start
