'''
These functions are just general utility functions.
Reading in files, that sort of thing.
'''

import os
from pathlib import Path
import pandas as pd
import openpyxl
from .config import config
import math

def read_in_file(file_path):
    with open(file_path, "r", encoding="utf8") as f:
      return f.read()

def read_in_full_df(spreadsheet_path):
    spreadsheet_file = Path(spreadsheet_path)
    if(not spreadsheet_file.exists()):
        raise Exception("Segments.xlsx file does not exist. Are you running this script in the right directory?")
    df = pd.read_excel(spreadsheet_path, "Full", index_col=0)
    return df

def get_headers_list(spreadsheet_path):
  df = read_in_full_df(spreadsheet_path)
  headers_list = df['Header'].tolist()
  return headers_list

def get_is_new_topic_list(spreadsheet_path):
  df = read_in_full_df(spreadsheet_path)
  headers_list = df['Is new topic?'].tolist()
  return headers_list

def get_internal_timestamps_list(spreadsheet_path):
  df = read_in_full_df(spreadsheet_path)
  internal_timestamps_list = df['Internal timestamp'].tolist()
  return internal_timestamps_list

def get_non_internal_headers_list(spreadsheet_path):
    df = read_in_full_df(spreadsheet_path)
    headers_list = df['Header'].tolist()
    internal_timestamps_list = df['Internal timestamp'].tolist()
    non_internal_headers_list = []
    for i in range(len(headers_list)):
        if(str(internal_timestamps_list[i]).lower() == "nan"):
            non_internal_headers_list.append(headers_list[i])
    return non_internal_headers_list

# https://stackoverflow.com/a/40347279
def fast_scandir(dirname):
    # Ignores recording subdirectories, since we only care about the possibility of discussion pages
    # when recursing. (Don't name any discussion page 'recording'. Just don't)
    subfolders= [f.path for f in os.scandir(dirname) if (f.is_dir() and f.name != 'recording')]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders

def set_spreadsheet_column_widths(spreadsheet_path):
    wb = openpyxl.load_workbook(spreadsheet_path)
    full_sheet = wb['Full']
    initial_sheet = wb['Initial']
    for spreadsheet_column in  config.spreadsheet_columns:
        #  First, for 'Full' sheet
        full_sheet.column_dimensions[spreadsheet_column.col].width = spreadsheet_column.width
        # Then, for 'Initial' sheet
        initial_sheet.column_dimensions[spreadsheet_column.col].width = spreadsheet_column.width
    wb.save(spreadsheet_path)

def safe_open_w(path):
  '''
  Open "path" for writing, creating any parent directories as needed.

  https://stackoverflow.com/a/23794010
  '''
  os.makedirs(os.path.dirname(path), exist_ok=True)
  return open(path, 'w', encoding="utf8")

# https://stackoverflow.com/questions/18399609/iterate-over-list-taking-three-items-at-a-time
def chunks(input_list, num_things_in_each_chunk):
    for i in range(0, len(input_list), num_things_in_each_chunk):
        yield input_list[i:i+num_things_in_each_chunk]

def get_string_value_of_time(numerical_time):
   
    # This function assumes the var numerical_time is in seconds (rather than milliseconds or whatever).
    # Otherwise, before anything else, run whatever you have to in order to convert numerical_time to seconds.
    # Be that numerical_time = numerical_time * 1000 or whatever else.
   
    # There are 60 seconds in an hour, and 60 minutes in an hour. That's where 3600.00 comes from
    # We use a decimal version of this number to ensure all math is done with floats
    hours = math.floor(numerical_time/3600.0)
   
    # https://www.geeksforgeeks.org/what-is-a-modulo-operator-in-python/
    minutes = math.floor((numerical_time % 3600.0)/60.0)
   
    seconds = math.floor(numerical_time % 60)
   
    if(hours > 0):
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"
    

def convert_string_time_to_seconds(string_time):

    time_segments = string_time.split(":")

    # If there is a value for hours
    if(len(time_segments) == 3):
        hours = int(time_segments[0])
        minutes = int(time_segments[1])
        seconds = int(time_segments[2])
        # Convert to just seconds
        return  hours * 3600 + minutes * 60 + seconds
    
    # If there is no value for hours = just minutes and seconds
    else: # len(time_segments) == 2
        minutes = int(time_segments[0])
        seconds = int(time_segments[1])
        # Convert to just seconds
        return  minutes * 60 + seconds
    
def convert_string_time_to_ms(string_time):
    return (convert_string_time_to_seconds(string_time) * 1000)

    
# Builds timestamp shortcode for Hugo
# We put two spaces at the end to make each timestamp end up on its own line
def build_hugo_timestamp(video_id, timestamp, text, nesting = ''):
    return (nesting + 
            r'{{% timestamp videoId="' +
            video_id +
            '" time="' +
            str(convert_string_time_to_seconds(timestamp)) +
            '" display="' +
            timestamp +
            r'" %}} - ' +
            text +
            '  ')
