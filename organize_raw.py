#!/usr/bin/env python3

from lib.organize import *

current_dir_path = os.getcwd()
raw_dir_path = current_dir_path +'/recording/raw'
# TODO: make above replacement handle if it is dropbox lowercase not just Dropbox uppercase. Causes runtime exception if you cd to lowercase path not uppercase path in shell

rename_raw_segments_to_be_in_tens(raw_dir_path)
