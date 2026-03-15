'''
These functions mostly relate with the automation that:

- Processes the audio of the recording segments
- Processes the video of the recording segments
- Combines multiple video segments
- Rips just the audio off the video

They are basically meta functions to process the
video segments.
'''

from pathlib import Path
import os
import re
from .general_utility import *
from .timestamps import *
from .organize import *
import subprocess
import shlex

# _compressed
# TODO
def compress_raw_video_with_libx264():
    return

# _both-ears-audio
# TODO
def make_single_ear_audio_both_ears():
    return

# _25fps
# TODO
def convert_from_variable_to_constant_framerate(framerate = 30):
    return

# _silence-removed
# TODO make dynamic (can run both off of raw files like it does at present, but also on things already in processed/ directory, if processed files are already there)
def remove_silence_from_segments(current_dir_path):

    raw_dir_path = current_dir_path + '/recording/raw'
    processed_dir_path = current_dir_path + '/recording/processed'

    # Organize raw first. May refactor this later
    
    # Comment out for now, to manually control generation of raw segments
    # This is because for now, I am moving video clips into the processed/
    # subdirectory manually

    # rename_raw_segments_to_be_in_tens(raw_dir_path)

    segment_names = [f for f in os.listdir(raw_dir_path) if f.endswith('.mp4')]
    files_to_move = []
    for segment_name in segment_names:
        out_file = segment_name.replace(".mp4", "_silence_removed.mp4")
        # print(segment_name)
        # print(out_file)
        subprocess.run(shlex.split(f'auto-editor recording/raw/{segment_name} --margin 0.5s --my_ffmpeg -vcodec libx264 --preset slow --output recording/raw/{out_file} --no-open'))
        files_to_move.append(out_file)
    
    for file_to_move in files_to_move:
        src_path = raw_dir_path + '/' + file_to_move
        dest_path = processed_dir_path + '/' + file_to_move
        # print(src_path)
        # print(dest_path)
        os.rename(src_path, dest_path)

    
# _normalized
# TODO
def audio_normalization_ebu_r_128():
    # loudnorm ffmpeg filter
    return

# _dynamically-normalized
# TODO 
def dynamic_audio_normalization():
    # dynaudnorm ffmpeg filter
    return


# -----------------------------------------------------------------------------------------------------------

# Note: Below, I had initially thought to convert the slides into a PDF, then split the PDFs on pages 
# and turn each page into an image, and then resize those. At some point I could have sworn
# I had this working with decktape (as it was the first path I set off on), but when trying to wire
# everything up here in the Python codebase, the sizing was all off. After poking around the options
# in decktape a bit, I realized that it can export to PNG directly. That seems to work fine, so I
# switched to doing that. The old approach that I initially thought would work (actually did work at some point?)
# is shown below for reference.

# # Turn HTML slides into PDF
# subprocess.run(shlex.split(f'decktape remark topic-transitions-slides.html transitions.pdf'))

# # Turn PDF pages into PNG images
# subprocess.run(shlex.split(f'pdftoppm -png transitions.pdf transition'))

# # Resize images to be exactly 1920x1080
# subprocess.run(shlex.split(f'mogrify -resize 1920x *.png'))

# -----------------------------------------------------------------------------------------------------------

# Assumes recording/topic-transitions/topic-transition-slides.html already exists, having been already created by
# generate_topic_transition_slides()
def build_topic_transition_segments(current_dir_path):
    topic_transitions_dir_path = current_dir_path + '/recording/topic-transitions/'
    
    # First, build the list of names for the topic transition video segments
    spreadsheet_path = current_dir_path + '/' + 'segments.xlsx'
    # Get the booleans representing which video segments are topic transitions,
    # in a list
    topic_transitions = get_is_new_topic_list(spreadsheet_path)
    topic_transition_segment_names = []
    count = 0
    for is_new_topic in topic_transitions:
        if(is_new_topic):
            topic_transition_segment_names.append(f'{count}-{count + 10}_no-audio.mp4')
        count += 10

    # I decided to just temporarily change the cwd when running these commands. Seemed the easiest path.
    # https://stackoverflow.com/a/70682130
    os.chdir(topic_transitions_dir_path)

    # Turn HTML slides into 1920x1080 images
    subprocess.run(shlex.split(f'decktape --screenshots --screenshots-directory . --screenshots-size 1920x1080  --screenshots-format png remark topic-transitions-slides.html transitions.pdf'))

    images = [f for f in os.listdir(topic_transitions_dir_path) if f.endswith('.png')]

    # Remove the 1920x1080 part of the decktape slide image file names to make sorting them easier.
    # This is sort of jank, but easier overall IMO than making the \d+ re.findall re do something more complex
    def rename_image(image):
        new_name = image.replace('_1920x1080', '')
        os.rename(image, new_name)
        return new_name
    images = [rename_image(image) for image in images]
    
    # https://www.geeksforgeeks.org/python-sort-given-list-of-strings-by-part-the-numeric-part-of-string/
    images.sort(key=lambda image : list(
        map(int, re.findall(r'\d+', image)))[0])
    
    # Validate that we have the number of topic transitions that we expect, and throw an exception
    # if not
    if(len(topic_transition_segment_names) != len(images)):
        raise Exception("The number of topic transitions suggested by the content headers " +
                        "on the page do not match the number specified in segments.xlsx.")

    # Turn each image into a 3 second video (at 25 fps to match the framerate of other recorded content. Zoom records at 25 fps).
    # https://stackoverflow.com/a/73073276
    for i in range(len(images)):
        subprocess.run(shlex.split(f'ffmpeg -framerate 25 -i {images[i]} -t 3 -c:v libx265 -x265-params lossless=1 -pix_fmt yuv420p -vf "scale=1920:1080,loop=-1:1" -movflags faststart {topic_transition_segment_names[i]}'))

    # Add dummy audio tracks for each of these segments so they can be multiplexed together with all the recorded segments. See:
    # https://superuser.com/questions/1624249/use-ffmpeg-concat-demuxer-with-multiple-files-with-without-audio-tracks
    # https://superuser.com/questions/1044988/merging-several-videos-with-audio-channel-and-without-audio/1044997#1044997
    no_audio_transition_segments = [f for f in os.listdir(topic_transitions_dir_path) if f.endswith('.mp4')]
    for no_audio_transition_segment in no_audio_transition_segments:
        subprocess.run(shlex.split(f'ffmpeg -i {no_audio_transition_segment} -f lavfi -i anullsrc -c:v copy -map 0:v -map 0:a? -map 1:a -shortest {no_audio_transition_segment.replace("_no-audio", "")}'))
    
    # Remove temp files from this whole process
    def remove_file(file):
        print(f'Removing {file}...')
        os.remove(file)
    remove_file('transitions.pdf')
    [remove_file(image) for image in images]
    [remove_file(no_audio_transition_segment) for no_audio_transition_segment in no_audio_transition_segments]

    os.chdir(current_dir_path)


transition_segment_pattern = re.compile("[0-9]+-[0-9]+.mp4")
def is_transition_segment(segment_name):
    return transition_segment_pattern.match(segment_name)


def clear_chapters_on_video_file():
    subprocess.run(shlex.split(f'ffmpeg -i video.mp4 -c copy -map_chapters -1 output.mp4'))
    os.remove('video.mp4')
    os.rename('output.mp4', 'video.mp4')

def get_header_text_from_full_header(full_header):
    # Index [0] is the # markup portion. Index [1] is the text of the header
    split_header = full_header.split(" ", 1)
    header_text = split_header[1]
    return header_text


def add_ms_end_times_for_segment_internal_timestamps(duration_map, internal_timestamps, end_times_ms, topic_transition_duration_in_ms = 3000):

    # Get starting times
    start_times = get_segment_start_times(duration_map)

    # Iterate through internal timestamps, as elsewhere in the codebase.
    # (Compare add_start_times_for_segment_internal_timestamps() and
    # add_files_to_correct_rows_in_df()).
    # This one is a bit more complicated though
    all_end_times_ms = []
    i = 0
    len_end_times = len(start_times)
    len_internal_timestamps = len(internal_timestamps)
    for j in range(len_internal_timestamps):
        is_last = j == (len_internal_timestamps - 1)
        is_blank = str(internal_timestamps[j]).lower() == "nan"
        if(is_last):
            # Normal headers that are last are still normal
            if(is_blank):
                if(i > len_end_times - 1):
                    raise Exception("The number of video segments actually present is not sufficient to cover the non-segment-internal headers in segments.xlsx. Check the processed video segments and segments.xlsx to see where things went wrong.")
                end_time_ms = end_times_ms[i]
            # Internal headers that are last still have the end time of their segment
            else:
                end_time_ms = end_time_of_current_segment_with_internal

        else: # Header cases that are not the last header
            next_internal_timestamp_is_blank = str(internal_timestamps[j+1]).lower() == "nan"

            # Case: Is a header for a segment that does not contain any internal timestamps
            if(is_blank and next_internal_timestamp_is_blank):
                if(i > len_end_times - 1):
                    raise Exception("The number of video segments actually present is not sufficient to cover the non-segment-internal headers in segments.xlsx. Check the processed video segments and segments.xlsx to see where things went wrong.")
                end_time_ms = end_times_ms[i]
                i = i + 1

            # Case: End time of very first chunk of a segment containing internal timestamps = segment start
            # up to the start time time of the first internal timestamp
            elif(is_blank and (not next_internal_timestamp_is_blank)):
                if(i > len_end_times - 1):
                    raise Exception("The number of video segments actually present is not sufficient to cover the non-segment-internal headers in segments.xlsx. Check the processed video segments and segments.xlsx to see where things went wrong.")
                start_time_of_current_segment_with_internal = convert_string_time_to_ms(start_times[i])
                end_time_of_current_segment_with_internal = end_times_ms[i]
                end_time_ms = start_time_of_current_segment_with_internal + topic_transition_duration_in_ms + convert_string_time_to_ms(internal_timestamps[j+1])
            
            # Case: End time of a middle chunk of a segment containing internal timestamps = from one
            # internal timestamp up to the start time of another internal timestamp
            elif((not is_blank) and (not next_internal_timestamp_is_blank)):
                end_time_ms = start_time_of_current_segment_with_internal + topic_transition_duration_in_ms + convert_string_time_to_ms(internal_timestamps[j+1])

            # Case: Last chunk of a segment containing internal timestamps = from last internal
            # timestamp up to the end time of the overall segment
            elif((not is_blank) and next_internal_timestamp_is_blank):
                end_time_ms = end_time_of_current_segment_with_internal
                i = i + 1

        all_end_times_ms.append(end_time_ms)

    end_times_as_strings = []
    for end_time_ms in all_end_times_ms:
        end_times_as_strings.append(get_string_value_of_time(end_time_ms/1000.0))
    print(end_times_as_strings)

    return all_end_times_ms

# https://ikyle.me/blog/2020/add-mp4-chapters-ffmpeg
def add_chapters_to_video_file(recording_dir_path):

    # Remove local metadata file
    metadata_path = recording_dir_path + '/' + 'metadata.txt'
    metadata_file = Path(metadata_path)
    if(metadata_file.exists()):
        os.remove(metadata_path)

    # Save current metadata to temporary file
    subprocess.run(shlex.split(f'ffmpeg -i video.mp4 -f ffmetadata metadata.txt'))
    
    metadata_as_str = read_in_file(metadata_path)

    # If any chapters already exist in metadata file, remove them.
    # Every run of this method makes the chapters anew.
    if '[CHAPTER]' in metadata_as_str: # Metatdata already has chapters
        index_where_chapters_begin = metadata_as_str.index('[CHAPTER]')
        metadata_as_str = metadata_as_str[:index_where_chapters_begin]
        print(metadata_as_str)

    # Add chapters to the temp file, appending them after current metadata
    spreadsheet_path = recording_dir_path + '/' + 'segments.xlsx'
    headers = get_headers_list(spreadsheet_path)
    processed_dir_path = recording_dir_path + '/recording/processed'
    duration_map = get_duration_map_based_off_of_processed_recordings(processed_dir_path)
    end_times_ms = get_segment_end_times_in_milliseconds(duration_map)

    internal_timestamps = get_internal_timestamps_list(spreadsheet_path)

    # Handle internal timestamps
    end_times_ms = add_ms_end_times_for_segment_internal_timestamps(duration_map, internal_timestamps, end_times_ms)

    metadata_as_str += '\n\n'

    # Do the first one by providing 0 as the start time
    metadata_as_str += '[CHAPTER]\n'
    metadata_as_str += 'TIMEBASE=1/1000\n'
    metadata_as_str += 'START=' + '0' + '\n'
    metadata_as_str += 'END=' + str(end_times_ms[0]) + '\n'
    metadata_as_str += 'title=' + get_header_text_from_full_header(headers[0]) + '\n\n'

    # Do the rest in a loop
    for i in range(1, len(end_times_ms)):
        metadata_as_str += '[CHAPTER]\n'
        metadata_as_str += 'TIMEBASE=1/1000\n'
        metadata_as_str += 'START=' + str(end_times_ms[i-1] + 1) + '\n'
        metadata_as_str += 'END=' + str(end_times_ms[i]) + '\n'
        metadata_as_str += 'title=' + get_header_text_from_full_header(headers[i]) + '\n\n'

    # Write the metadata, apply it to the video file
    # Note: you MUST include the -map_chapters flag, otherwise overwriting the metadata 
    # file will not change the chapters upon recalculation. I had a frustrating time debugging this 
    # particular thing. See https://stackoverflow.com/questions/59279937/unable-to-overwrite-ffmpeg-metadata
    with safe_open_w(metadata_path) as f:
        f.writelines(metadata_as_str)
    subprocess.run(shlex.split(f'ffmpeg -i video.mp4 -i metadata.txt -map_metadata 1 -map_chapters 1 -codec copy output.mp4'))
    
    # Overwrite the old video with the new video with metadata
    old_video_path = metadata_path = recording_dir_path + '/' + 'video.mp4'
    new_video_path = metadata_path = recording_dir_path + '/' + 'output.mp4'
    os.remove(old_video_path)
    os.rename(new_video_path, old_video_path)



# TODO - automatically build audio stream for segments that were created with static images, so that they
# will work with the concat demuxer. Once generating those segments rather than recording them
def combine_video_files(recording_dir_path):

    # Get main video segments from the folder ./recording/processed
    main_segments_dir = recording_dir_path + '/recording/processed'
    main_segments = [f for f in os.listdir(main_segments_dir) if f.endswith('.mp4')]
    
    # https://www.geeksforgeeks.org/python-sort-given-list-of-strings-by-part-the-numeric-part-of-string/
    # main_segments.sort(key=lambda main_segment : list(
    #     map(int, re.findall(r'\d+', main_segment)))[0]) 

    # Get the topic transition segments from the folder ./recording/topic-transitions/
    transition_segments_dir = recording_dir_path + '/recording/topic-transitions'
    transition_segments = [f for f in os.listdir(transition_segments_dir) if f.endswith('.mp4')]

    combined_segment_list = main_segments + transition_segments

    # https://www.geeksforgeeks.org/python-sort-given-list-of-strings-by-part-the-numeric-part-of-string/
    combined_segment_list.sort(key=lambda transition_segment : list(
        map(int, re.findall(r'\d+', transition_segment)))[0]) 

    # Add the proper directory paths before each file name, based upon the segment type
    for i in range(len(combined_segment_list)):
        if(is_transition_segment(combined_segment_list[i])):
            combined_segment_list[i] = 'recording/topic-transitions/' + combined_segment_list[i]
        else:
            combined_segment_list[i] = 'recording/processed/' + combined_segment_list[i]

    # Build arguments for ffmpeg command
    input_files = ''
    stream_mappings = ''
    num_inputs = len(combined_segment_list)
    for i in range(num_inputs):
        input_files += f'-i {combined_segment_list[i]} '
        stream_mappings += f'[{i}:v][{i}:a]'
    
    # Run the concatenation command with the concat video filter.
    # This does re-render (rather than copy, as with -c copy)
    subprocess.run(shlex.split(f'ffmpeg {input_files} -filter_complex "{stream_mappings}concat=n={num_inputs}:v=1:a=1[outv][outa]" -map "[outv]" -map "[outa]" video.mp4'))

# TODO
def rip_audio_off_video():
    return
