#!/usr/bin/env python3

from lib.organize import *
import subprocess
import shlex
import time

current_dir_path = os.getcwd()
raw_dir_path = current_dir_path +'/recording/raw'
# TODO: make above replacement handle if it is dropbox lowercase not just Dropbox uppercase. Causes runtime exception if you cd to lowercase path not uppercase path in shell

segment_names = [f for f in os.listdir(raw_dir_path) if f.endswith('.mp4')]

# https://www.geeksforgeeks.org/python-sort-given-list-of-strings-by-part-the-numeric-part-of-string/
segment_names.sort(key=lambda segment_name : list(
    map(int, re.findall(r'\d+', segment_name)))[0]) 

counter = 10
for segment_name in segment_names:
    new_name = raw_dir_path + '/' + str(counter) + '.mp4'
    os.rename(raw_dir_path + '/' + segment_name, new_name)
    counter += 10

new_segment_names = [f for f in os.listdir(raw_dir_path) if f.endswith('.mp4')]

# https://www.geeksforgeeks.org/python-sort-given-list-of-strings-by-part-the-numeric-part-of-string/
new_segment_names.sort(key=lambda segment_name : list(
    map(int, re.findall(r'\d+', segment_name)))[0]) 

for segment_name in new_segment_names:
    input_file = raw_dir_path + '/' + segment_name
    result = subprocess.run(shlex.split(f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 {input_file}'), capture_output=True)
    return_val = result.stdout.decode('utf-8')
    segment_is_already_1080p = (str(return_val)).strip() == "1920x1080"
    if(not segment_is_already_1080p):
        print("Converting file to 1080p...\n")
        out_file = raw_dir_path + '/' + segment_name.replace('.mp4', '_upscaled.mp4')
        subprocess.run(shlex.split(f'ffmpeg -i {input_file} -vf "scale=-1:1080" -c:v libx264 -crf 30 -preset slow {out_file}'))
