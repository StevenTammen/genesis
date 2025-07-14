#!/usr/bin/env python3

import os
from lib.timestamps import *

current_dir_path = os.getcwd()
raw_dir_path = current_dir_path + '/recording/raw'
raw_recording_segment_names = [f for f in os.listdir(raw_dir_path) if f.endswith('.mp4')]
is_single_video_segment_case = len(raw_recording_segment_names) == 1

# Case: more than one video segment
if(not is_single_video_segment_case):
    calculate_timestamps_and_write_to_content_file(current_dir_path)

# Case: only one video segment
else: # is_single_video_segment_case == True
    calculate_timestamps_and_write_to_content_file(current_dir_path, True)
