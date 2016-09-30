#!/bin/bash

# This script runs your HW1 code with a memory cap of 1MB, to help
# detect whether you are streaming properly.

# Extract the processing code from between BEGIN/END student code 
jupyter nbconvert hw1.ipynb --to python --stdout |
  sed -n '/BEGIN STUDENT CODE/,/END STUDENT CODE/p' > hw1_sol.py

# Concatenate the code to run the processing on the large dataset
cat << EOF >> hw1_sol.py
import os
DATA_DIR = os.environ['MASTERDIR'] + '/sp16/hw1/'

import zipfile

def process_logs_large():
    """
    Runs the process_logs function on the full dataset.  The code below 
    performs a streaming unzip of the compressed dataset which is (158MB). 
    This saves the 1.6GB of disk space needed to unzip this file onto disk.
    """
    with zipfile.ZipFile(DATA_DIR + "web_log_large.zip") as z:
        fname = z.filelist[0].filename
        f = z.open(fname)
        process_logs(f)
        f.close()
process_logs_large()
EOF

# Limit the virtual memory to 1000000 bytes = 1 MB
ulimit -v 1000000

echo "Running process_logs_large()"

ipython hw1_sol.py

echo "Memory Test Done."
