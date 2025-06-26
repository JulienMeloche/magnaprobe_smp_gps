
"""
GPS Position Matching Tool for Snow Micro Penetrometer (SMP) and Emlid Receiver Data

This module provides functionality to extract GPS positions from Emlid receiver .pos files 
and match them with corresponding Snow Micro Penetrometer (SMP) measurements using timestamps. 
The tool processes .PNT files from SMP measurements and updates an Excel file with high-precision 
GPS coordinates.

Usage:
    Run this script from the command line:
    
    python smp_gps_matching.py -d /path/to/smp/files -p emlid_positions.pos -e measurements.xlsx -c PPK_correction
    
    or
    
    python smp_gps_matching.py --dir /path/to/smp/files --filepos emlid_positions.pos --excel measurements.xlsx --correction PPP_correction

Required Arguments:
    -d, --dir: Directory containing SMP .PNT files
    -p, --filepos: Path to the Emlid receiver position file (.pos)
    -e, --excel: Path to Excel file containing SMP measurement records
    -c, --correction: Correction file type ('PPK_correction' or 'PPP_correction')

Example:
    python smp_gps_matching.py -d "data/smp_files/" -p "data/emlid_20231215.pos" -e "measurements/smp_records.xlsx" -c "PPK_correction"

Dependencies:
    - pandas
    - dateutil
    - snowmicropyn
    - openpyxl (for Excel file handling)

Author: Julien Meloche eccc
Version: 1.0
"""

import pandas as pd
from dateutil.parser import parse
from snowmicropyn import Profile
import os
import argparse


def row_to_time(date_str, time_str):
    """
    Convert separate date and time strings into a pandas datetime object.
    
    Args:
        date_str (str): Date string in parseable format
        time_str (str): Time string in parseable format
    
    Returns:
        pd.Timestamp: Combined datetime object
    """
    date = parse(date_str)
    time = parse(time_str)
    return pd.to_datetime(date.strftime('%Y-%m-%d') + 'T' + time.strftime('%H:%M:%S'))

# def timestamp_magna(str_datetime, thisUTCtime):
#     """
#     Convert magnaprobe datetime and UTC time into a standardized timestamp.
    
#     The magnaprobe logs time in a compressed format (HHMMSS) that needs to be 
#     combined with the date from the Campbell logger to create a proper timestamp.
    
#     Args:
#         str_datetime (str): Datetime string from Campbell logger (ISO8601 format)
#         thisUTCtime (str): UTC time from GPS in format 'HHMMSS' (e.g., '171119' for 17:11:19)
    
#     Returns:
#         pd.Timestamp: Properly formatted timestamp combining date and UTC time
#     """
#     #modify format of time
#     strtime = thisUTCtime[:2] + ':' + thisUTCtime[2:4] + ':' + thisUTCtime[4:]
#     #extract date for Datetime
#     date = pd.to_datetime(str_datetime, format= 'ISO8601').date()
#     return pd.to_datetime(date.strftime('%Y-%m-%d') + 'T' + strtime)


def get_lat_emlid(timestamp_magna, df_emlid):
    """
    Get the latitude from Emlid data that corresponds to a specific timestamp.
    
    Uses binary search (searchsorted) to find the closest timestamp match.
    
    Args:
        timestamp_magna (pd.Timestamp): Target timestamp from magnaprobe
        df_emlid (pd.DataFrame): Emlid dataframe with 'timestamp' and 'lat' columns
    
    Returns:
        float: Latitude value from Emlid data
    """
    try:
        lat = df_emlid.iloc[df_emlid.timestamp.searchsorted(timestamp_magna),:].lat
    except:
        lat = None
    return lat

def get_lon_emlid(timestamp_magna, df_emlid):
    """
    Get the longitude from Emlid data that corresponds to a specific timestamp.
    
    Uses binary search (searchsorted) to find the closest timestamp match.
    
    Args:
        timestamp_magna (pd.Timestamp): Target timestamp from magnaprobe
        df_emlid (pd.DataFrame): Emlid dataframe with 'timestamp' and 'lon' columns
    
    Returns:
        float: Longitude value from Emlid data
    """
    try:
        lon = df_emlid.iloc[df_emlid.timestamp.searchsorted(timestamp_magna),:].lon
    except:
        lon = None
    return lon

def degree_dms2dec(dd, mn, ss):
    """
    Convert degrees, minutes, seconds (DMS) to decimal degrees.
    
    Args:
        dd (float): Degrees
        mn (float): Minutes
        ss (float): Seconds
    
    Returns:
        float: Decimal degrees
    
    Example:
        >>> degree_dms2dec(45, 30, 15)
        45.50416666666667
    """
    if dd >= 0:
        dec = dd + mn / 60 + ss / 3600
    else:
        dec = -(abs(dd) + mn / 60 + ss / 3600)
    return dec


def smp_get_gps_correction(path_smp_dir, path_emlid, output_csv_file, correction_file_type):
    """
    Main function to process and match GPS coordinates between SMP files and Emlid data.
    
    This function:
    1. Loads all .PNT files from the specified directory
    2. Loads Emlid GPS correction data
    3. Reads an Excel file with SMP measurement records
    4. Matches SMP files to Excel records
    5. Assigns high-precision GPS coordinates from Emlid data
    6. Creates an improved Excel file with corrected coordinates
    
    Args:
        path_smp_dir (str): Directory containing SMP .PNT files
        path_emlid (str): Path to Emlid position file
        output_excel_file (str): Path to Excel file with SMP measurement records
        correction_file_type (str): Type of correction file ('PPK_correction' or 'PPP_correction')
    
    Raises:
        FileNotFoundError: If required files or directories don't exist
        ValueError: If data processing fails or file formats are invalid
        
    Output:
        Creates a new Excel file with '_improved.xlsx' suffix containing corrected GPS coordinates
    """
    smp_df = []
    for file in os.listdir(path_smp_dir):
        if (".PNT"in file) or (".pnt" in file):
            p = Profile.load(os.path.join(path_smp_dir,file))
            coord = p.coordinates
            if coord is not None:
                lat, lon = coord
            else:
                lat, lon = None, None
            #add 18 seconds to utc time to match GPS time, recheck if the leap seconds is still 18 seconds (2024)
            smp_df.append({'name' : file, 'timestamp' : pd.Timestamp(p.timestamp).tz_convert(None) + pd.Timedelta(seconds = 18), 'lat' : lat, 'lon' : lon})

    smp_df = pd.DataFrame(smp_df)

    if correction_file_type == 'PPK_correction':
        df_emlid = pd.read_csv(path_emlid, sep =' ', skiprows=9, parse_dates = True, usecols = [0,1,4,6])
        #rename emlid shitty column/format
        col = df_emlid.columns.values
        df_emlid = df_emlid.rename(columns = {col[0] : 'date', col[1] : 'time', col[2] : 'lat', col[3] : 'lon'})
        #convert date and time to timestamp
        df_emlid['timestamp'] = df_emlid.apply(lambda x: row_to_time(x.date, x.time), axis = 1)

    if correction_file_type == 'PPP_correction':
        #get emlid data
        df_emlid = pd.read_csv(path_emlid, skiprows=3, delimiter = "\s+", parse_dates = True)
        df_emlid = df_emlid.loc[:,['YEAR-MM-DD', 'HR:MN:SS.SS','LATDD', 'LATMN', 'LATSS','LONDD', 'LONMN', 'LONSS']]
        df_emlid['lat'] = df_emlid.apply(lambda x : degree_dms2dec(x.LATDD, x.LATMN, x.LATSS), axis = 1)
        df_emlid['lon'] = df_emlid.apply(lambda x : degree_dms2dec(x.LONDD, x.LONMN, x.LONSS), axis = 1)
        #convert date and time to timestamp
        df_emlid['timestamp'] = df_emlid.apply(lambda x: row_to_time(x['YEAR-MM-DD'], x['HR:MN:SS.SS']), axis = 1)

    else:
        print('enter a valid correction file')

    #get file name from excel file to correct
    df_excel = pd.read_excel(output_csv_file)
    list_rows = []
    for index, row in df_excel.iterrows():
        matching_row = smp_df[[str(row.file) in name[-8:] for name in smp_df.name.values]]
        list_rows.append(matching_row)
    df_smp_excel = pd.concat(list_rows,ignore_index=True)

    #check if some files are missing
    if len(df_smp_excel.index.values) != len(df_excel.file.values):
        print('Some files from the excel sheet are missing in the directory, check files!')
        
    #get position from emlid (or high quality GNSS) and match it to SMP timestamp
    df_smp_excel['lat_emlid'] = df_smp_excel.apply(lambda x : get_lat_emlid(x.timestamp, df_emlid), axis = 1)
    df_smp_excel['lon_emlid'] = df_smp_excel.apply(lambda x : get_lon_emlid(x.timestamp, df_emlid), axis = 1)

    if df_smp_excel.lat_emlid.isnull().any() or df_smp_excel.lat_emlid.isnull().any():
            print('Some position could not be matched, check excel file')

    df_update = pd.concat([df_excel, df_smp_excel], axis =1)
    df_update.to_excel(output_csv_file[:-5] + '_improved.xlsx', index = False)
    print(f'the excel file : {output_csv_file} was created with updated position')


if __name__ == "__main__":
    # construct the argument parser and add 1 argument
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', '-d', type=str, help="directory to process of smp file", required = False)
    parser.add_argument('--filepos', '-p', type=str, help="filename of corrected pos", required = False)
    parser.add_argument('--excel', '-e', type=str, help="filename or directory to process", required = False)
    parser.add_argument('--correction', '-c', type=str, help="correction file type", required = True)

    # parse the arguments passed on commandline
    args = parser.parse_args()

    # do some bombproofing (make sure it's a number) - or can use type=float in parser.add_argument
    # run function using passed argument

    print(f'processing the directory {args.dir}')
    try:
        smp_get_gps_correction(args.dir, args.filepos , args.excel , args.correction)

    except:
        raise ValueError(f"Cannot process excel file {args.excel}")
