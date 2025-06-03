# GPS Position Matching Tools for Snow Measurement Instruments

## 🏔️ Overview

This repository contains two specialized tools designed to improve GPS accuracy for snow depth and snow property measurements:

### 📍 Magnaprobe GPS Correction Tool
Matches GPS coordinates between Magnaprobe measurements with high-precision GPS coordinates

### 🔬 SMP GPS Correction Tool  
 Matches GPS coordinate and Snow Micro Penetrometer measurements with high-precision GPS coordinates

Both tools support Emlid Post-Processed Kinematic (PPK) and NRCan Precise Point Positioning (PPP) correction formats.


### Installation

#### 1. Clone the repository:
```bash
git clone https://github.com/JulienMeloche/magnaprobe_smp_gps.git
cd magnaprobe_smp_gps
```

install packages for smp:
```bash
pip install pandas dateutil snowmicropyn openpyxl argparse
```
or only magnaprobe (no snowmicropyn)
```bash
pip install pandas dateutil openpyxl argparse
```
### Basic Usage

#### Magnaprobe GPS Correction
```bash
python magnaprobe_gps_matching.py -m magnaprobe_data.csv -p emlid_positions.pos -n corrected_output.csv -c PPK_correction
```

#### SMP GPS Correction
```bash
python smp_gps_matching.py -d /path/to/smp/files -p emlid_positions.pos -e measurements.xlsx -c PPK_correction
```

## 📋 Magnaprobe GPS Correction Tool

Corrects GPS coordinates for Magnaprobe snow depth measurements using high-precision Emlid receiver data.

### Command Line Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--filemagna` | `-m` | Path to magnaprobe (.dat) data file | ✅ |
| `--filepos` | `-p` | Path to Emlid receiver position file | ✅ |
| `--newfile` | `-n` | Output filename for corrected data | ✅ |
| `--correction` | `-c` | Correction type (`PPK_correction` or `PPP_correction`) | ✅ |

### Examples

#### Basic PPK correction:
```bash
python run_magna_gps_matching.py -m "data/magnaprobe_20231215.dat" -p "data/emlid_20231215.pos" -n "output/corrected_magnaprobe.csv" -c "PPK_correction"
```

#### PPP correction with full paths:
```bash
python runmagna_gps_matching.py --filemagna "/home/user/field_data/magnaprobe.dat" --filepos "/home/user/gps_data/emlid.pos" --newfile "/home/user/analysis/corrected.csv" --correction "PPP_correction"
```

### Input File Requirements

> **📋 Magnaprobe .dat File Requirements:**
> - Must contain columns: `TIMESTAMP`, `ThisUTCtime`, `latitude_a`, `latitude_b`, `Longitude_a`, `Longitude_b`
> - UTC time format: `HHMMSS` (e.g., `171119` for 17:11:19)
> - Skip first row (header)
> 
> **📡 Emlid Position File (.pos):**
> - PPK format: Space-separated, skip 9 header lines
> - PPP format: Whitespace-separated, skip 3 header lines, includes DMS coordinates

## 🔬 SMP GPS Correction Tool

Matches Snow Micro Penetrometer measurements with high-precision GPS coordinates and updates Excel measurement records.

### Command Line Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--dir` | `-d` | Directory containing SMP .PNT files | ✅ |
| `--filepos` | `-p` | Path to Emlid receiver position file | ✅ |
| `--excel` | `-e` | Path to Excel file with measurement records | ✅ |
| `--correction` | `-c` | Correction type (`PPK_correction` or `PPP_correction`) | ✅ |

### Examples

#### Process SMP files with PPK correction:
```bash
python run_smp_gps_matching.py -d "field_data/smp_measurements/" -p "gps_data/emlid_correction.pos" -e "analysis/smp_records.xlsx" -c "PPK_correction"
```

#### Windows example:
```cmd
python run_smp_gps_matching.py -d "C:\Data\SMP_Files" -p "C:\GPS\emlid.pos" -e "C:\Analysis\measurements.xlsx" -c "PPP_correction"
```

### Input File Requirements

> **📁 SMP Directory:**
> - Contains `.PNT` or `.pnt` files from Snow Micro Penetrometer
> - Files must be readable by `snowmicropyn` library
> 
> **📊 Excel Measurement File:**
> - Must contain a `file` column with SMP filenames
> - Will be updated with GPS coordinates and saved as `*_improved.xlsx`

## 📁 File Format Examples

### Sample Magnaprobe CSV Structure
```csv
TIMESTAMP,RECORD,BattVolts,ThisUTCtime,latitude_a,latitude_b,Longitude_a,Longitude_b,fix_quality,nmbr_satellites,LatitudeDDDDD,LongitudeDDDDD,HDOP,altitudeB,DepthVolts,month,dayofmonth,hourofday,minutes,seconds,microseconds
2023-12-15T10:30:00,1,12.5,103000,45,30.5,-108,45.2,1,8,45.508,-108.753,1.2,1200,2.5,12,15,10,30,0,0
```

### Sample PPK Position File
```
2023-12-15 10:30:00.000  45.508333  -108.753333  1200.0  1  8
2023-12-15 10:30:01.000  45.508334  -108.753334  1200.1  1  8
```

### Sample Excel SMP Records
| file | depth | force | location |
|------|-------|--------|----------|
| S23_001.pnt | 45.2 | 12.3 | Site A |
| S23_002.pnt | 52.1 | 15.7 | Site B |

## 🔧 Advanced Configuration

### Coordinate System Notes
- **Output coordinates**: Always in decimal degrees (WGS84)
- **Timestamp matching**: Uses nearest neighbor of timestamp for GPS coordinate assignment

## 🐛 Troubleshooting

### Common Issues

#### ⚠️ "Time ranges do not overlap"
- Check that measurement times fall within Emlid GPS recording period
- Verify timezone settings (all times should be UTC)

#### ⚠️ "No .PNT files found"
- Ensure SMP files have `.PNT` or `.pnt` extensions
- Check directory path is correct

#### ⚠️ "Cannot match files to Excel records"
- Verify filename column in Excel matches actual SMP filenames
- Check for case sensitivity issues


## 📊 Output Files

### Magnaprobe Tool Output
Creates a CSV file with original measurements plus:
- `lat_emlid`: High-precision latitude from Emlid receiver
- `lon_emlid`: High-precision longitude from Emlid receiver  
- `timestamp_utc`: Standardized UTC timestamp

### SMP Tool Output
Creates an Excel file with suffix `_improved.xlsx` containing:
- Original measurement data
- `lat_emlid`: Matched GPS latitude
- `lon_emlid`: Matched GPS longitude
- `timestamp`: SMP measurement timestamp
