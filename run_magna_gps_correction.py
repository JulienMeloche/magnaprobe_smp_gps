
"""
GPS Position Matching Tool for Magnaprobe and Emlid Receiver Data

This module provides functionality to extract GPS positions from Emlid receiver .pos files 
and match them with corresponding magnaprobe measurements using UTC timestamps. The tool 
supports both PPK (Post-Processed Kinematic) and PPP (Precise Point Positioning) correction 
file formats.

Usage:
    Run this script from the command line using run_gps_matching.py:
    
    python run_gps_matching.py -m magnaprobe_data.dat -p emlid_positions.pos -n output_corrected.csv -c PPK_correction
    
    or
    
    python run_gps_matching.py --filemagna magnaprobe_data.dat --filepos emlid_positions.pos --newfile output_corrected.csv --correction PPP_correction

Required Arguments:
    -m, --filemagna: Path to the magnaprobe CSV data file
    -p, --filepos: Path to the Emlid receiver position file (.pos)
    -n, --newfile: Output filename for the GPS-corrected magnaprobe data
    -c, --correction: Correction file type ('PPK_correction' or 'PPP_correction')

Example:
    python run_gps_matching.py -m "data/magnaprobe_20231215.csv" -p "data/emlid_20231215.pos" -n "output/corrected_magnaprobe.csv" -c "PPK_correction"

Dependencies:
    - pandas
    - dateutil

Author: Julien Meloche eccc
Version: 1.0

Examples:
  python run_gps_matching.py -m data.csv -p positions.pos -n output.csv -c PPK_correction
  python run_gps_matching.py --filemagna magnaprobe.csv --filepos emlid.pos --newfile corrected.csv --correction PPP_correction

"""

import pandas as pd
from dateutil.parser import parse
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

def timestamp_magna(str_datetime, thisUTCtime):
    """
    Convert magnaprobe datetime and UTC time into a standardized timestamp.
    
    The magnaprobe logs time in a compressed format (HHMMSS) that needs to be 
    combined with the date from the Campbell logger to create a proper timestamp.
    
    Args:
        str_datetime (str): Datetime string from Campbell logger (ISO8601 format)
        thisUTCtime (str): UTC time from GPS in format 'HHMMSS' (e.g., '171119' for 17:11:19)
    
    Returns:
        pd.Timestamp: Properly formatted timestamp combining date and UTC time
    """
    #modify format of time
    strtime = thisUTCtime[:2] + ':' + thisUTCtime[2:4] + ':' + thisUTCtime[4:]
    #extract date for Datetime
    date = pd.to_datetime(str_datetime, format= 'ISO8601').date()
    #add 18 seconds to utc time to match GPS time, recheck if the leap seconds is still 18 seconds (2024)
    return pd.to_datetime(date.strftime('%Y-%m-%d') + 'T' + strtime) + pd.Timedelta(seconds = 18)


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
    return df_emlid.iloc[df_emlid.timestamp.searchsorted(timestamp_magna),:].lat

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
    return df_emlid.iloc[df_emlid.timestamp.searchsorted(timestamp_magna),:].lon

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

def magnaprobe_get_gps_correction(path_magna, path_emlid, output_csv_name, correction_file_type):
    """
    Main function to process and match GPS coordinates between magnaprobe and Emlid data.
    
    This function reads both magnaprobe and Emlid position data, matches them by timestamp,
    and outputs a corrected CSV file with high-precision GPS coordinates.
    
    Args:
        path_magna (str): Path to the magnaprobe CSV data file
        path_emlid (str): Path to the Emlid position file
        output_csv_name (str): Output filename for the corrected data
        correction_file_type (str): Type of correction file ('PPK_correction' or 'PPP_correction')
    
    Raises:
        ValueError: If correction file type is invalid or data processing fails
        
    Note:
        - PPK files have a different format than PPP files
        - The function filters data to the time range where both instruments were recording
        - Coordinates are converted from degrees/minutes format to decimal degrees
    """
    df_magna = pd.read_csv(path_magna, skiprows=1).dropna()

    if correction_file_type == 'PPK_correction':
        df_emlid = pd.read_csv(path_emlid, sep =' ', skiprows=9, parse_dates = True, usecols = [0,1,4,6])
        #rename emlid shitty column/format
        col = df_emlid.columns.values
        df_emlid = df_emlid.rename(columns = {col[0] : 'date', col[1] : 'time', col[2] : 'lat', col[3] : 'lon'})
        #convert date and time to timestamp
        df_emlid['timestamp'] = df_emlid.apply(lambda x: row_to_time(x.date, x.time), axis = 1)

    elif correction_file_type == 'PPP_correction':
        df_emlid = pd.read_csv(path_emlid, skiprows=3, delimiter = "\\s+", parse_dates = True)
        df_emlid = df_emlid.loc[:,['YEAR-MM-DD', 'HR:MN:SS.SS','LATDD', 'LATMN', 'LATSS','LONDD', 'LONMN', 'LONSS']]
        df_emlid['lat'] = df_emlid.apply(lambda x : degree_dms2dec(x.LATDD, x.LATMN, x.LATSS), axis = 1)
        df_emlid['lon'] = df_emlid.apply(lambda x : degree_dms2dec(x.LONDD, x.LONMN, x.LONSS), axis = 1)
        #convert date and time to timestamp
        df_emlid['timestamp'] = df_emlid.apply(lambda x: row_to_time(x['YEAR-MM-DD'], x['HR:MN:SS.SS']), axis = 1)

    else:
        print('enter a valid correction file')

    #get begin and end of emlid data
    begin = df_emlid.timestamp.iloc[0]
    end = df_emlid.timestamp.iloc[-1]

    df_magna['timestamp_utc'] = df_magna.apply(lambda x:timestamp_magna(x.TIMESTAMP, x.ThisUTCtime), axis =1)
    #filter begin and end of emlid data
    try:
        df_magna_trim = df_magna[(df_magna.timestamp_utc > begin) & (df_magna.timestamp_utc < end)].copy()
    except:
        print('begin and end time of emlid do not match magnaprobe time')

    #convert lat lon from magna in decimal
    df_magna_trim['lat_magna'] = df_magna_trim['latitude_a'].astype('float') + df_magna_trim['latitude_b'].astype('float')/60
    df_magna_trim['lon_magna'] = df_magna_trim['Longitude_a'].astype('float') + df_magna_trim['Longitude_b'].astype('float')/60


    #extract emlid lat/lon
    try:
        df_magna_trim['lat_emlid'] = df_magna_trim.apply(lambda x : get_lat_emlid(x.timestamp_utc, df_emlid), axis = 1)
        df_magna_trim['lon_emlid'] = df_magna_trim.apply(lambda x : get_lon_emlid(x.timestamp_utc, df_emlid), axis = 1)
        
        #clean magnaprobe file from uncessary columns
        df_magna_clean = df_magna_trim.drop(['RECORD', 'BattVolts', 'latitude_a', 'latitude_b', 'Longitude_a', 'Longitude_b',
                                            'fix_quality', 'nmbr_satellites', 'LatitudeDDDDD', 'LongitudeDDDDD', 'HDOP', 'altitudeB', 
                                            'DepthVolts', 'month', 'dayofmonth', 'hourofday', 'minutes', 'seconds', 'microseconds'], axis = 1)
        
        print(f'output csv file named : {output_csv_name}')
        df_magna_clean.to_csv(output_csv_name, index = False)

    except ValueError as error:
        print(f'failed to retrieve lat/lon /n')
        print(f'Error found : {error}')


if __name__ == "__main__":
    # construct the argument parser and add 1 argument
    parser = argparse.ArgumentParser()
    parser.add_argument('--filemagna', '-m', type=str, help="filename of magnaprobe", required = True)
    parser.add_argument('--filepos', '-p', type=str, help="filename of corrected pos", required = True)
    parser.add_argument('--newfile', '-n', type=str, help="new filename of corrected magna", required = True)
    parser.add_argument('--correction', '-c', type=str, help="correction file type", required = True)

    # parse the arguments passed on commandline
    args = parser.parse_args()


    print(f'processing the file {args.filemagna}')
    try:
        output_csv_name = args.filepos
        magnaprobe_get_gps_correction(args.filemagna, args.filepos, args.newfile, args.correction)

    except:
        raise ValueError(f"Cannot process excel file {args.filemagna}")
