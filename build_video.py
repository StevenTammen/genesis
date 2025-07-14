#!/usr/bin/env python3

import os
import sys
from lib.organize import *
from lib.timestamps import *
from lib.process import *

from lib.transcript import *

# Note:
# This script is step 4/6 in the normal processing workflow:
# 1) Run scaffold_recordings.py in the content dir.
# 2) Actually make the recordings (and put in raw/ subdirectory). Update segments.xlsx if necessary (internal timestamp headers).
# 3) Run remove_silence.py in the recording dir. Update segments.xlsx if necessary (internal timestamp times). Update content file if necessary (subject tags, passage tags, video only sections).
# 4) Run build_video.py in the recording dir. Validate it looks right (via VLC), and upload to YouTube. (Copy-paste the title and automatically-built description)
# 5) Wait a day or whatever to let YouTube auto-generate the transcript. Then add the video URL to content page frontmatter, and run write_back_to_content_file.py in the recording dir.
# 6) Run hugo-preprocessor, check over diff, push to website, make video public.

# Note:
# This script assumes silence has already been removed from content recording segments. (See remove_silence.py)
# It also assumes that segments.xlsx already exists, and that:
#   1) segments.xlsx has the correct headers in the correct order, and
#   2) segments.xlsx has internal timestamps defined for any segment-internal timestamps

current_dir_path = os.getcwd()
raw_dir_path = current_dir_path + '/recording/raw'
raw_recording_segment_names = [f for f in os.listdir(raw_dir_path) if f.endswith('.mp4')]
is_single_video_segment_case = len(raw_recording_segment_names) == 1

# -----------------------------------------

# Case: more than one video segment
if(not is_single_video_segment_case):

    clvaa_path = os.path.dirname(sys.argv[0])

    # Build topic transition segments
    generate_topic_transition_slides(current_dir_path, clvaa_path)
    build_topic_transition_segments(current_dir_path)

    # Calculate timestamps based on post-silence-removal content recording segment boundaries
    calculate_timestamps_and_write_to_excel_and_yt_desc(current_dir_path)

    # Combine all the segments into a single video file
    combine_video_files(current_dir_path)

    # Add chapter metadata to the single video file
    add_chapters_to_video_file(current_dir_path)

# -----------------------------------------

# Case: only one video segment
else: # is_single_video_segment_case == True

    content_dir_path = current_dir_path.replace("/mnt/c/Dropbox/recordings/", "/mnt/c/R/")

    # Organize raw first. May refactor this later
    rename_raw_segments_to_be_in_tens(raw_dir_path)

    raw_recording_segment_names = [f for f in os.listdir(raw_dir_path) if f.endswith('.mp4')]

    if(len(raw_recording_segment_names) > 1):
        raise Exception('Simple videos should only have a single segment. Please check the raw subdirectory.')

    files_to_move = []
    for segment_name in raw_recording_segment_names:
        out_file = segment_name.replace(".mp4", "_silence_removed.mp4")
        subprocess.run(shlex.split(f'auto-editor recording/raw/{segment_name} --margin 0.5s --my_ffmpeg -vcodec libx264 --extras "-crf 30" --output recording/raw/{out_file} --no-open'))
        files_to_move.append(out_file)

    for file_to_move in files_to_move:
        src_path = raw_dir_path + '/' + file_to_move
        dest_path = current_dir_path + '/' + 'video.mp4'
        os.rename(src_path, dest_path)

    # Write to YouTube description
    try:
        content_page_path = content_dir_path + '/' + '_index.md'
        full_page_content = read_in_file(content_page_path)
    # Handle discussion pages as well as content pages
    except FileNotFoundError:
        content_page_path = content_dir_path + '/' + 'index.md'
        full_page_content = read_in_file(content_page_path)
    write_youtube_description_to_file(current_dir_path, content_dir_path, full_page_content)
