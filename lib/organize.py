'''
These functions mostly relate with the automation that:

- Controls which video segments are present in the directories
- Controls what they are called

They are basically meta functions to organize all the files
and the get them ready for processing and concatenation.
'''

import os
import subprocess
import shlex
import pandas as pd
import shutil
from .general_utility import *
from .write_to_files import *
import re

class Recording:
    def __init__(self, recording_dir_path):
        self.recording_dir_path = recording_dir_path
        self.recording_dir = Path(self.recording_dir_path)

        self.spreadsheet_path = recording_dir_path + '/' + 'segments.xlsx'
        self.spreadsheet = Path(self.spreadsheet_path)

        self.recording_subdir_path = recording_dir_path + '/recording'
        self.recording_subdir = Path(self.recording_subdir_path)
        
        self.raw_subdir_path = recording_dir_path + '/recording/raw'
        self.raw_subdir = Path(self.raw_subdir_path)
        
        self.processed_subdir_path = recording_dir_path + '/recording/processed'
        self.processed_subdir = Path(self.processed_subdir_path)

        self.topic_transitions_subdir_path = recording_dir_path + '/recording/topic-transitions'
        self.topic_transitions_subdir = Path(self.topic_transitions_subdir_path)

def add_to_things_that_need_scaffolding(recording_dir_path, dirs_to_make, dirs_without_spreadsheets):

    scaffolding_type = ''
    content_headers = get_content_headers(recording_dir_path)
    if(content_headers == None):
        scaffolding_type = 'No content ever = no video no slides'
    # # TODO
    # elif(???):
    #     scaffolding_type = 'No content at the moment = simple video no slides'
    elif(len(content_headers) == 0):
        scaffolding_type = 'No content subheaders = simple video yes slides'
    else:
        scaffolding_type = 'Content subheaders = normal video yes slides'

    need_to_scaffold_recording_dir = False
    need_to_scaffold_spreadsheet = False
    need_to_scaffold_recording_subdir = False
    need_to_scaffold_raw_subdir = False
    need_to_scaffold_processed_subdir = False
    need_to_scaffold_topic_transitions_subdir = False

    if(scaffolding_type == 'No content ever = no video no slides'):
        # Everything stays False = scaffold nothing
        pass
    elif(scaffolding_type == 'No content at the moment = simple video no slides'):
        need_to_scaffold_recording_dir = True
        need_to_scaffold_recording_subdir = True
        need_to_scaffold_raw_subdir = True
    elif(scaffolding_type == 'No content subheaders = simple video yes slides'):
        need_to_scaffold_recording_dir = True
        need_to_scaffold_recording_subdir = True
        need_to_scaffold_raw_subdir = True
    else: # scaffolding_type == 'Content subheaders = normal video yes slides'
        need_to_scaffold_recording_dir = True
        need_to_scaffold_spreadsheet = True
        need_to_scaffold_recording_subdir = True
        need_to_scaffold_raw_subdir = True
        need_to_scaffold_processed_subdir = True
        need_to_scaffold_topic_transitions_subdir = True

    added_something = False
    r = Recording(recording_dir_path)
    # Order is importing when adding to the list of dirs to make
    if(need_to_scaffold_recording_dir and (not r.recording_dir.exists())):
        print(f'Will make {r.recording_dir_path}')
        dirs_to_make.append(r.recording_dir_path)
        added_something = True
    if(need_to_scaffold_spreadsheet and (not r.spreadsheet.exists())):
        print(f'Will make {r.spreadsheet_path}')
        dirs_without_spreadsheets.append(r.recording_dir_path)
        added_something = True
    if(need_to_scaffold_recording_subdir and (not r.recording_subdir.exists())):
        print(f'Will make {r.recording_subdir_path}')
        dirs_to_make.append(r.recording_subdir_path)
        added_something = True
    if(need_to_scaffold_raw_subdir and (not r.raw_subdir.exists())):
        print(f'Will make {r.raw_subdir_path}')
        dirs_to_make.append(r.raw_subdir_path)
        added_something = True
    if(need_to_scaffold_processed_subdir and (not r.processed_subdir.exists())):
        print(f'Will make {r.processed_subdir_path}')
        dirs_to_make.append(r.processed_subdir_path)
        added_something = True
    if(need_to_scaffold_topic_transitions_subdir and (not r.topic_transitions_subdir.exists())):
        print(f'Will make {r.topic_transitions_subdir_path}')
        dirs_to_make.append(r.topic_transitions_subdir_path)
        added_something = True
    # Add extra newline if added something, to keep content
    # folders separate from each other in output
    if(added_something):
        print()

def scaffold_directories(dirs_to_make):
    for dir_to_make in dirs_to_make:
        os.makedirs(dir_to_make)

def scaffold_spreadsheets(dirs_without_spreadsheets):
    for dir_without_spreadsheet in dirs_without_spreadsheets:
        write_content_headers_to_segments_spreadsheet(dir_without_spreadsheet)

# TODO: documentation
def scaffold_recording_dirs(content_dir_path):
    dirs_to_make = []
    dirs_without_spreadsheets = []

    # Recordings/ dir version of parent folder
    parent_recordings_dir_path = re.sub(r'.+/([^/]+)/content/', r'/mnt/c/Dropbox/recordings/\1/content/', content_dir_path)
    parent_recordings_dir = Path(parent_recordings_dir_path)
    
    # fast_scandir is recursive, so works for discussion pages too
    # (that is, all levels of subfolders, not only first level)
    content_dir_paths = fast_scandir(content_dir_path)

    # But those paths are for the normal project directory, not for
    # the recording directory. We want the recording directory versions
    content_dir_paths = list(map(lambda x: re.sub(r'.+/([^/]+)/content/', r'/mnt/c/Dropbox/recordings/\1/content/', x), content_dir_paths))

    # Special case: if no subdirectories, means content_dir_path
    # specifies the path of a single page study, so we need to
    # scaffold stuff in parent_recordings_dir directly, rather than
    # in subfolders
    if(len(content_dir_paths) == 0):
        add_to_things_that_need_scaffolding(parent_recordings_dir_path, dirs_to_make, dirs_without_spreadsheets)
    
    # Otherwise
    else:
        if(not parent_recordings_dir.exists()):
            print(f'Will make {parent_recordings_dir_path}\n')
            dirs_to_make.append(parent_recordings_dir_path)
        for content_dir_path in content_dir_paths:
            add_to_things_that_need_scaffolding(content_dir_path, dirs_to_make, dirs_without_spreadsheets)

    # If nothing to scaffold, short circuit
    if(len(dirs_to_make) == 0 and len(dirs_without_spreadsheets) == 0):
        print("Nothing to scaffold. Exiting...")
        return
    
    # Otherwise
    while(True):
        answer = input("Check over what will be scaffolded. Proceed (y/n)?\n> ")
        if answer.lower() in ["y","yes"]:
            scaffold_directories(dirs_to_make)
            scaffold_spreadsheets(dirs_without_spreadsheets)
            return
        elif answer.lower() in ["n","no"]:
            return 
        else:
            print("Please respond with 'y'/'yes' or 'n'/'no'\n")

# TODO
def automatically_organize_gopro_recordings():
    '''
    Automatically concatenates the videos that span across multiple 
    recording chunks (which is most of them, in practice).

    Then calls rename_raw_segments_to_be_in_tens()
    '''
    return

def rename_raw_segments_to_be_in_tens(raw_dir_path):
    '''
    Preserves order, but renames everything to multiples of 10.
    So like 10.mp4, 20.mp4, and so on.

    Many recording programs will spit out videos that are in the right
    order (that is, in terms of how things were recorded), but with 
    kind of gross file names full of dates and times. And the format
    is not consistent across programs either.

    Standardizing the names like this (and using multiples of 10) makes it
    easy to add new segments wherever you want them in the order. You can
    then call this function again to re-baseline the order (make everything
    only multiples of 10 again). Although be sure that the processed/ and
    topic-transitions/ files are then also updated in the same way.

    At present, this function presupposes that the recordinsg are
    .mp4 files.
    '''
    segment_names = [f for f in os.listdir(raw_dir_path) if f.endswith('.mp4')]
    
    # https://www.geeksforgeeks.org/python-sort-given-list-of-strings-by-part-the-numeric-part-of-string/
    segment_names.sort(key=lambda segment_name : list(
        map(int, re.findall(r'\d+', segment_name)))[0]) 

    counter = 10
    for segment_name in segment_names:
        new_name = raw_dir_path + '/' + str(counter) + '.mp4'
        os.rename(raw_dir_path + '/' + segment_name, new_name)
        counter += 10

# TODO
def rename_processed_segments_to_be_in_tens():
    # Will only really use if after adding new segment = have to re-call rename_raw_segments_to_be_in_tens()
    # Want order to match between raw and processed. Hence why this would then need to be called
    return

# TODO: documentation
def generate_topic_transition_slides(recording_dir_path, clvaa_path):

    # Copy slides template into topic_transitions_dir
    topic_transitions_slides_template_path = clvaa_path + '/' + 'templates' + '/' + 'topic-transitions-slides-template.html'
    topic_transitions_dir_path = recording_dir_path + '/recording/topic-transitions'
    if not os.path.exists(topic_transitions_dir_path):
        os.makedirs(topic_transitions_dir_path)
    topic_transitions_slides_path = topic_transitions_dir_path + '/' + 'topic-transitions-slides.html'
    # This overwrites whatever file is currently there, if it already exists. That's fine
    shutil.copyfile(topic_transitions_slides_template_path, topic_transitions_slides_path)

    # Add headers to slides template to complete topic_transitions_slides
    template = read_in_file(topic_transitions_slides_path)
    spreadsheet_path = recording_dir_path + '/' + 'segments.xlsx'
    headers = get_non_internal_headers_list(spreadsheet_path)

    # Filter the list down only to headers that are topic transitions
    topic_transitions = get_is_new_topic_list(spreadsheet_path)
    headers = [header for header, is_new_topic in zip(headers, topic_transitions) if is_new_topic]

    headers_split_into_slides = '\n\n---\n\n'.join(headers)
    to_write = re.sub('markdown-content', headers_split_into_slides, template)
    with safe_open_w(topic_transitions_slides_path) as f:
        f.writelines(to_write)


# TODO:
# I will make this function later to actually autogenerate the transition segments eventually. Maybe?
# Right now I manually record the segments, and then use ffmpeg to standardize them to 2.0 seconds
def generate_topic_transition_segments(topic_transitions_dir_path, duration = 2.0):
    # Eventually:
    # Pulls from list of segments on the 'Full' tab of the segments spreadsheet
    # Only pulls non-dud segments
    # Can change duration based upon input float
    pass

# TODO: documentation
def standardize_transition_segment_lengths(topic_transitions_dir_path, duration = 3.0):
    transition_segment_names = [f for f in os.listdir(topic_transitions_dir_path) if f.endswith('.mp4')]
    for segment_name in transition_segment_names:
        file_name_parts = os.path.splitext(segment_name)
        base_name = file_name_parts[0]
        extension = file_name_parts[1]

        # Standardize length to {duration} using ffmpeg.
        # Starts just after first second of video, and goes for {duration} time
        # On running command in shell: https://stackoverflow.com/a/72741384
        input_file = topic_transitions_dir_path + '/' + segment_name
        output_file = topic_transitions_dir_path + '/' + base_name + '-shortened' + extension
        subprocess.run(shlex.split(f'ffmpeg -i {input_file} -ss 00:01 -t {duration} {output_file}'))

        # Overwrite initial file. Cannot overwrite directly within ffmpeg command. See this StackOverflow:
        # https://stackoverflow.com/questions/28877049/issue-with-overwriting-file-while-using-ffmpeg-for-converting
        os.remove(input_file)
        os.rename(output_file, input_file)

# TODO
def remove_dud_segments():
    # Deletes the dud video files
    # Removes the dud rows from the 'Full' tab of the segments spreadsheet
    return