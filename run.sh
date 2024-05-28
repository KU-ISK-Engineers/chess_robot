#!/bin/bash

root_dir="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

echo "Changing directory to project root"
cd $(echo $root_dir)

echo "Running program"
python run.py
