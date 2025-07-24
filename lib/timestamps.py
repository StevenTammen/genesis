'''
These functions mostly relate with the automation that:

- Calculates timestamps based off of segment durations
- Pairs these timestamps with the matching labels

They are basically functions to do the icky math
involved in determining timestamps, so that they do
not have to be figured out manually.
'''

import subprocess
import shlex
from .general_utility import *
from .transcript import *
import re
import pandas as pd

def get_duration_map_based_off_of_processed_recordings(processed_dir_path):

    segment_names = [f for f in os.listdir(processed_dir_path) if f.endswith('.mp4')]

    # https://www.geeksforgeeks.org/python-sort-given-list-of-strings-by-part-the-numeric-part-of-string/
    segment_names.sort(key=lambda segment_name : list(
        map(int, re.findall(r'\d+', segment_name)))[0]) 

    # For each mp4 file in directory, store the file name and full duration
    # (not just like 05:20, but a float value containing the actual seconds value)
    # in an ordered array of tuples. Should be in order of file names ascending
    duration_map = []
    for segment_name in segment_names:
        # Gets duration of video file.
        # See https://stackoverflow.com/questions/31024968/using-ffmpeg-to-obtain-video-durations-in-python
        input_file = processed_dir_path + '/' + segment_name
        result = subprocess.run(shlex.split(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {input_file}'), capture_output=True)
        segment_duration = float(result.stdout.decode('utf-8'))

        # Builds an ordered list of tuples of the form (filename, duration).
        duration_map.append(tuple([segment_name, segment_duration]))

    return duration_map

# Timestamps conceptually represent segment start times (not end times)
def get_segment_start_times(duration_map, topic_transition_duration = 3.0):
   
    # Stores the calculated timestamps as formatted strings. Should be the same length as the array of headers
    timestamps = []
   
    # Keeps track of where in the video you are after each segment has been completed
    cumulative_duration = 0
   
    # The first segment starts at 0:00
    timestamps.append('0:00')

    # We only go through N - 1 segments. Since the first timestamp is always 0:00, this loop
    # is only responsible for N - 1 timestamps, not N timestamps. All the timestamps but the first.
    for recording in duration_map[:-1]:
        # Duration map is a list of tuples of the form (filename, duration).
        # So index [1] is duration
        duration = recording[1]
        last_section_ended_at = cumulative_duration + duration
        string_timestamp = get_string_value_of_time(last_section_ended_at)
        timestamps.append(string_timestamp)
        cumulative_duration += (duration + topic_transition_duration)
       
    return timestamps

# Used in building chapters
def get_segment_end_times_in_milliseconds(duration_map, topic_transition_duration_in_ms = 3000):
    
    # Stores the segment end times as floating point values, representing milliseconds
    # Should be the same length as the array of headers
    segment_end_times_ms = []
   
    # Keeps track of where in the video you are after each segment has been completed
    cumulative_duration_in_ms = 0
   
    # End of the first segment is just the duration; there
    # is no topic transition time involved with the first one
    # Grab the time off the first tuple in the map and multiple by 1000 to get ms
    first_end_time_ms = (duration_map[0])[1] * 1000
    cumulative_duration_in_ms += first_end_time_ms
    segment_end_times_ms.append(cumulative_duration_in_ms)

    # We only go through N - 1 segments. Since we get the first end time above, this loop
    # is only responsible for N - 1 end times, not N end times. All the end times but the first.
    for recording in duration_map[1:]:
        # Duration map is a list of tuples of the form (filename, duration).
        # So index [1] is duration
        duration_in_s = recording[1]
        duration_in_ms = duration_in_s * 1000
        cumulative_duration_in_ms += topic_transition_duration_in_ms + duration_in_ms
        segment_end_times_ms.append(cumulative_duration_in_ms)

    return segment_end_times_ms

def get_youtube_descr_timestamp(header, timestamp):

    # Index [0] is the # markup portion. Index [1] is the text of the header
    split_header = header.split(" ", 1)
    markup_portion = split_header[0]
    header_text = split_header[1]

    # Removes the string '###' from the markup portion
    markup_portion = re.sub('###', '', markup_portion)
    # Adds three spaces for every remaining #, to nest
    nesting = re.sub('#', '   ', markup_portion)

    return (nesting + timestamp + ' - ' + header_text)

def get_labeled_timestamps_for_youtube_descr(headers, start_times):
    # Properly format timestamps combined with headers
    youtube_desc_timestamps = []
    for i in range(len(headers)):
        youtube_desc_timestamps.append(get_youtube_descr_timestamp(headers[i], start_times[i]))

    # Build list with newlines between 
    return ('\n'.join(youtube_desc_timestamps))

def get_markdown_timestamp(video_id, header, timestamp):

    # Index [0] is the # markup portion. Index [1] is the text of the header
    split_header = header.split(" ", 1)
    markup_portion = split_header[0]
    header_text = split_header[1]

    # Removes the string '###' from the markup portion
    markup_portion = re.sub('###', '', markup_portion)
    # Adds emsp for every remaining #, to nest
    nesting = re.sub('#', '&emsp;', markup_portion)

    return build_hugo_timestamp(video_id, timestamp, header_text, nesting)


def get_labeled_timestamps_for_markdown(video_id, headers, start_times):
    # Properly format timestamps combined with headers
    markdown_timestamps = []
    for i in range(len(headers)):
        markdown_timestamps.append(get_markdown_timestamp(video_id, headers[i], start_times[i]))

    # Build list with newlines between 
    return ('\n'.join(markdown_timestamps))


def write_timestamps_to_segments_spreadsheet(spreadsheet_path, files_in_df, start_times):
    '''
    Overwrites 'Full' sheet in segments.xlsx spreadsheet, updating
    the timestamps column to add the timestamps. This function assumes
    the spreadsheet at spreadsheet_path already exists
    '''
    df = read_in_full_df(spreadsheet_path)
    df['File'] = files_in_df
    df['Timestamp'] = start_times

    # Have to use openpyxl here since mode='a' and therefore if_sheet_exists='replace'
    # only work with openpyxl, for whatever reason
    with pd.ExcelWriter(spreadsheet_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name='Full')
    set_spreadsheet_column_widths(spreadsheet_path)

video_shortcode_re_pattern = re.compile(r'^{{% video((?:.|\n)+?)%}}', re.MULTILINE)
timestamps_re_pattern = re.compile(r'^## Timestamps.*\n\n((?:.|\n)+?)\{\{% content %\}\}', re.MULTILINE)
transcript_section_re_pattern = re.compile(r'^{{% transcript %}}((?:.|\n)+?){{% /transcript %}}', re.MULTILINE)
def write_to_content_file(content_page_path, full_page_content, new_video_shortcode, new_timestamps_section, new_transcript):
    full_page_content = video_shortcode_re_pattern.sub(new_video_shortcode, full_page_content, count = 1)
    if(new_timestamps_section != ''):
        full_page_content = timestamps_re_pattern.sub(new_timestamps_section, full_page_content, count = 1)
    full_page_content = transcript_section_re_pattern.sub(new_transcript, full_page_content, count = 1)
    with safe_open_w(content_page_path) as f:
        f.writelines(full_page_content)

summary_re_pattern = re.compile(r'^## Summary.*\n\n((?:.|\n)+?)(?=(?:\n#|\n{{% content %}}))', re.MULTILINE)
def get_summary_from_page_content(full_page_contents):
    summary = summary_re_pattern.search(full_page_contents)
    if(summary == None):
        raise Exception("Must have summary in content file to build YouTube description")
    summary = summary.group(1)
    return summary

def write_youtube_description_to_file(current_dir_path, content_dir_path, full_page_content, labeled_timestamps_for_youtube_descr = ''):
    playlist_url = re.search(r'^playlist: (https://.+)\n', full_page_content, re.MULTILINE)
    if(playlist_url == None):
        raise Exception("Must have playlist URL in frontmatter in content file to build YouTube description")
    playlist_url = playlist_url.group(1)

    url_info = re.search(r'/mnt/c/R/(.+/)content/(.+)', content_dir_path)
    domain = url_info.group(1)
    path = url_info.group(2)
    webpage_url = 'https://www.' + domain + path
    slides_url = 'https://www.' + domain + 'slides/' + path

    summary = get_summary_from_page_content(full_page_content)

    desc_as_string = (f"Link to wider playlist:\n{playlist_url}\n\n"
                     f"Link to webpage content:\n{webpage_url}\n\n"
                     f"View slides:\n{slides_url}\n\n"
                     f"Summary:\n\n{summary}\n")
    
    # Support simple videos that do not have multiple segments, and therefore timestamps.
    # Only include timestamps in description if they exist.
    if(labeled_timestamps_for_youtube_descr != ''):
        desc_as_string = desc_as_string + f"Timestamps:\n\n{labeled_timestamps_for_youtube_descr}\n"

    youtube_description_file_path = current_dir_path + '/' + 'youtube-description.txt'
    with safe_open_w(youtube_description_file_path) as f:
            f.writelines(desc_as_string)
    

def add_start_times_for_segment_internal_timestamps(internal_timestamps, start_times, topic_transition_duration = 3.0):
    all_start_times = []
    i = 0
    len_start_times = len(start_times)
    for internal_timestamp in internal_timestamps:
        if(str(internal_timestamp).lower() == "nan"):
            if(i > len_start_times - 1):
                raise Exception("The number of video segments actually present is not sufficient to cover the non-segment-internal headers in segments.xlsx. Check the processed video segments and segments.xlsx to see where things went wrong.")
            all_start_times.append(start_times[i])
            i = i + 1
        else:
            last_start_time_index = i - 1
            if(last_start_time_index < 0):
                raise Exception("The first header cannot be an internal timestamp")
            last_start_time = start_times[last_start_time_index]
            if(type(internal_timestamp) == str):
                internal_start_time = convert_string_time_to_seconds(last_start_time) + topic_transition_duration + convert_string_time_to_seconds(internal_timestamp)
                all_start_times.append(get_string_value_of_time(internal_start_time))
            else:
                raise Exception("One of the internal timestamps is not properly formatted. Please check segments.xlsx. Prefix them all with apostrophes to force them to be strings.")
    
    if(len(all_start_times) != len(internal_timestamps)):
        raise Exception("There is some issue causing the number of start times to not match the number of headers in segments.xlsx. Check the processed video segments and segments.xlsx to see where things went wrong.")

    return all_start_times

def add_files_to_correct_rows_in_df(internal_timestamps, processed_files):
    files_in_df = []
    i = 0
    len_processed_files = len(processed_files)
    for internal_timestamp in internal_timestamps:
        if(str(internal_timestamp).lower() == "nan"):
            if(i > len_processed_files - 1):
                raise Exception("The number of video segments actually present is not sufficient to cover the non-segment-internal headers in segments.xlsx. Check the processed video segments and segments.xlsx to see where things went wrong.")
            files_in_df.append(processed_files[i])
            i = i + 1
        else:
            files_in_df.append("")
    
    if(len(files_in_df) != len(internal_timestamps)):
        raise Exception("There is some issue causing the number of file rows to not match the number of headers in segments.xlsx. Check the processed video segments and segments.xlsx to see where things went wrong.")

    return files_in_df


def calculate_timestamps_and_write_to_excel_and_yt_desc(current_dir_path):

    processed_dir_path = current_dir_path + '/recording/processed'
    spreadsheet_path = current_dir_path + '/' + 'segments.xlsx'

    duration_map = get_duration_map_based_off_of_processed_recordings(processed_dir_path)
    start_times = get_segment_start_times(duration_map)

    # Deal with internal timestamps, and build list of objects to
    # represent the timestamps for the video. Also get headers
    df = read_in_full_df(spreadsheet_path)  
    internal_timestamps = df['Internal timestamp'].tolist()
    start_times = add_start_times_for_segment_internal_timestamps(internal_timestamps, start_times)
    headers = df['Header'].tolist()

    processed_files = [x[0] for x in duration_map]

    # https://www.geeksforgeeks.org/python-sort-given-list-of-strings-by-part-the-numeric-part-of-string/
    processed_files.sort(key=lambda processed_file : list(
        map(int, re.findall(r'\d+', processed_file)))[0])

    # Write timestamps to segments.xlsx file
    # Overwrites what is there, if anything is already there
    files_in_df = add_files_to_correct_rows_in_df(internal_timestamps, processed_files)
    write_timestamps_to_segments_spreadsheet(spreadsheet_path, files_in_df, start_times)

    # Write youtube description
    # Overwrites what is there, if anything is already there
    content_dir_path = current_dir_path.replace("/mnt/c/Dropbox/recordings/", "/mnt/c/R/")
    # TODO: make above replacement handle if it is dropbox lowercase not just Dropbox uppercase. Causes runtime exception if you cd to lowercase path not uppercase path in shell
    
    # Handle discussion pages as well as content pages
    try:
        content_page_path = content_dir_path + '/' + '_index.md'
        full_page_content = read_in_file(content_page_path)
    except FileNotFoundError:
        content_page_path = content_dir_path + '/' + 'index.md'
        full_page_content = read_in_file(content_page_path)

    labeled_timestamps_for_youtube_descr = get_labeled_timestamps_for_youtube_descr(headers, start_times)
    write_youtube_description_to_file(current_dir_path, content_dir_path, full_page_content, labeled_timestamps_for_youtube_descr)
    
def calculate_timestamps_and_write_to_content_file(current_dir_path, simple_video = False):
    
    content_dir_path = current_dir_path.replace("/mnt/c/Dropbox/recordings/", "/mnt/c/R/")

    # Handle discussion pages as well as content pages
    try:
        content_page_path = content_dir_path + '/' + '_index.md'
        full_page_content = read_in_file(content_page_path)
    except FileNotFoundError:
        content_page_path = content_dir_path + '/' + 'index.md'
        full_page_content = read_in_file(content_page_path)

    video_url = re.search(r'^video: (https://.+)\n', full_page_content, re.MULTILINE)
    if(video_url == None):
        raise Exception("Must have video URL in frontmatter in content file to write timestamps to content file")
    video_url = video_url.group(1)
    video_id = re.search(r'\?v=(.+)', video_url).group(1)

    playlist_url = re.search(r'^playlist: (https://.+)\n', full_page_content, re.MULTILINE)
    if(playlist_url == None):
        raise Exception("Must have playlist URL in frontmatter in content file to add video shortcode to page")
    playlist_url = playlist_url.group(1)

    url_info = re.search(r'/mnt/c/R/(.+/)content/(.+)', content_dir_path)
    domain = url_info.group(1)
    path = url_info.group(2)
    slides_url = 'https://www.' + domain + 'slides/' + path

    new_video_shortcode = (r'{{% video\n' +
        f'videoId="{video_id}"\n\n' +
        f'videoPlaylist="{playlist_url}"\n\n'
        f'slides="{slides_url}"\n'
        r'%}}'
    )

    new_timestamps_section = ''
    # Only do timestamp stuff if the video actually has timestamps
    if(not simple_video):
        processed_dir_path = current_dir_path + '/recording/processed'
        spreadsheet_path = current_dir_path + '/' + 'segments.xlsx'

        duration_map = get_duration_map_based_off_of_processed_recordings(processed_dir_path)
        start_times = get_segment_start_times(duration_map)

        # Deal with internal timestamps, and build list of objects to
        # represent the timestamps for the video. Also get headers
        df = read_in_full_df(spreadsheet_path)  
        internal_timestamps = df['Internal timestamp'].tolist()
        start_times = add_start_times_for_segment_internal_timestamps(internal_timestamps, start_times)
        headers = df['Header'].tolist()

        labeled_timestamps_for_markdown = get_labeled_timestamps_for_markdown(video_id, headers, start_times)
        new_timestamps_section = '## Timestamps {#timestamps}\n\n' + labeled_timestamps_for_markdown + r'\n\n{{% content %}}'

    # For now, combine 3 subsegments together to generate somewhat longer "lines" in the transcript
    new_transcript = r'{{% transcript %}}\n\n## Video/audio transcript {#video-audio-transcript}\n\n' + get_transcript(video_id, 3) + r'\n\n{{% /transcript %}}'

    # Write labeled_timestamps_for_markdown to timestamps section of content file, if applicable
    # Also fill out video shortcode
    # Overwrites what is there (if anything is already there) in both cases
    write_to_content_file(content_page_path, full_page_content, new_video_shortcode, new_timestamps_section, new_transcript)
