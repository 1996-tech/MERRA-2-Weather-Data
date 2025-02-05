import pandas as pd
import xarray as xr
import numpy as np
import requests
import logging
import yaml
import json
import os
import hashlib
from datetime import datetime
from calendar import monthrange
from opendap_download.multi_processing_download import DownloadManager
import getpass

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('notebook')

# User input of timespan
download_year = 2016

# Washington State precise coordinates
lat_1, lon_1 = 45.543541, -124.848974  # Southwestern coordinate
lat_2, lon_2 = 49.002494, -116.916071  # Northeastern coordinate

def translate_lat_to_geos5_native(latitude):
    """Convert latitude to MERRA-2 grid coordinates"""
    return ((latitude + 90) / 0.5)

def translate_lon_to_geos5_native(longitude):
    """Convert longitude to MERRA-2 grid coordinates"""
    return ((longitude + 180) / 0.625)

def find_closest_coordinate(calc_coord, coord_array):
    """Find closest matching coordinate in the grid"""
    index = np.abs(coord_array-calc_coord).argmin()
    return coord_array[index]

# Create coordinate arrays
lat_coords = np.arange(0, 361, dtype=int)
lon_coords = np.arange(0, 576, dtype=int)

# Calculate grid coordinates
lat_coord_1 = translate_lat_to_geos5_native(lat_1)
lon_coord_1 = translate_lon_to_geos5_native(lon_1)
lat_coord_2 = translate_lat_to_geos5_native(lat_2)
lon_coord_2 = translate_lon_to_geos5_native(lon_2)

# Find closest grid points
lat_co_1_closest = find_closest_coordinate(lat_coord_1, lat_coords)
lon_co_1_closest = find_closest_coordinate(lon_coord_1, lon_coords)
lat_co_2_closest = find_closest_coordinate(lat_coord_2, lat_coords)
lon_co_2_closest = find_closest_coordinate(lon_coord_2, lon_coords)

# Print coordinate information
print('Calculated coordinates for point 1: ' + str((lat_coord_1, lon_coord_1)))
print('Closest coordinates for point 1: ' + str((lat_co_1_closest, lon_co_1_closest)))
print('Calculated coordinates for point 2: ' + str((lat_coord_2, lon_coord_2)))
print('Closest coordinates for point 2: ' + str((lat_co_2_closest, lon_co_2_closest)))

def translate_year_to_file_number(year):
    """Get file number based on year"""
    if year >= 2011:
        return '400'
    elif year >= 2001:
        return '300'
    elif year >= 1992:
        return '200'
    elif year >= 1980:
        return '100'
    else:
        raise Exception('Year out of range')

def generate_url_params(parameter, time_para, lat_para, lon_para):
    """Create parameter string for URL"""
    parameter = map(lambda x: x + time_para, parameter)
    parameter = map(lambda x: x + lat_para, parameter)
    parameter = map(lambda x: x + lon_para, parameter)
    return ','.join(parameter)

def generate_download_links(download_years, base_url, dataset_name, url_params):
    """Generate download URLs for specified years"""
    urls = []
    for y in download_years:
        y_str = str(y)
        file_num = translate_year_to_file_number(y)
        for m in range(1,13):
            m_str = str(m).zfill(2)
            _, nr_of_days = monthrange(y, m)
            for d in range(1,nr_of_days+1):
                d_str = str(d).zfill(2)
                file_name = f'MERRA2_{file_num}.{dataset_name}.{y_str}{m_str}{d_str}.nc4'
                query = f'{base_url}{y_str}/{m_str}/{file_name}.nc4?{params}'
                urls.append(query)
    return urls

# Set up parameters for data download
requested_time = '[0:1:23]'
requested_lat = f'[{lat_co_1_closest}:1:{lat_co_2_closest}]'
requested_lon = f'[{lon_co_1_closest}:1:{lon_co_2_closest}]'

# Base URL for MERRA-2
BASE_URL = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/'

# Generate URLs for temperature data
temp_params = ['T2M']
params = generate_url_params(temp_params, requested_time, requested_lat, requested_lon)
temp_urls = generate_download_links([download_year], BASE_URL, 'tavg1_2d_slv_Nx', params)

# Create download directory
if not os.path.exists('download_temperature'):
    os.makedirs('download_temperature')

# Get NASA credentials
username = input('Username: ')
password = getpass.getpass('Password:')

# Initialize download manager
NUMBER_OF_CONNECTIONS = 5
download_manager = DownloadManager()
download_manager.set_username_and_password(username, password)

# Download temperature data
print(f"\nStarting download for {len(temp_urls)} files...")
download_manager.download_path = 'download_temperature'
download_manager.download_urls = temp_urls
download_manager.start_download(NUMBER_OF_CONNECTIONS)

print("\nDownload completed!")
print("Verify the coordinates in the downloaded files before processing.")

# The dimensions map the MERRA2 grid coordinates to lat/lon. The coordinates 
# to request are 0:360 wheare as the other coordinates are 1:361
requested_lat_dim = '[{lat_1}:1:{lat_2}]'.format(
                    lat_1=lat_co_1_closest, lat_2=lat_co_2_closest)
requested_lon_dim = '[{lon_1}:1:{lon_2}]'.format(
                    lon_1=lon_co_1_closest , lon_2=lon_co_2_closest )

lat_lon_dimension_para = 'lat' + requested_lat_dim + ',lon' + requested_lon_dim

# Creating the download url.
dimension_url = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/2014/01/MERRA2_400.tavg1_2d_slv_Nx.20140101.nc4.nc4?'
dimension_url = dimension_url + lat_lon_dimension_para
download_manager.download_path = 'dimension_scale'
download_manager.download_urls = [dimension_url]

# Since the dimension is only one file, we only need one connection. 
%time download_manager.start_download(1)

file_path = os.path.join('dimension_scale', DownloadManager.get_filename(
        dimension_url))

with xr.open_dataset(file_path) as ds_dim:
    df_dim = ds_dim.to_dataframe()

lat_array = ds_dim['lat'].data.tolist()
lon_array = ds_dim['lon'].data.tolist()

# The log output helps evaluating the precision of the received data.
log.info('Requested lat: ' + str((lat_1, lat_2)))
log.info('Received lat: ' + str(lat_array))
log.info('Requested lon: ' + str((lon_1, lon_2)))
log.info('Received lon: ' + str(lon_array))




##Alternative(specific months)

import pandas as pd
import xarray as xr
import numpy as np
import requests
import logging
import yaml
import json
import os
import hashlib
from datetime import datetime
from calendar import monthrange
from opendap_download.multi_processing_download import DownloadManager
import getpass

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('notebook')

# User input of timespan
download_year = 2017

# Washington State precise coordinates
lat_1, lon_1 = 45.543541, -124.848974  # Southwestern coordinate
lat_2, lon_2 = 49.002494, -116.916071  # Northeastern coordinate

def translate_lat_to_geos5_native(latitude):
    """Convert latitude to MERRA-2 grid coordinates"""
    return ((latitude + 90) / 0.5)

def translate_lon_to_geos5_native(longitude):
    """Convert longitude to MERRA-2 grid coordinates"""
    return ((longitude + 180) / 0.625)

def find_closest_coordinate(calc_coord, coord_array):
    """Find closest matching coordinate in the grid"""
    index = np.abs(coord_array-calc_coord).argmin()
    return coord_array[index]

# Create coordinate arrays
lat_coords = np.arange(0, 361, dtype=int)
lon_coords = np.arange(0, 576, dtype=int)

# Calculate grid coordinates
lat_coord_1 = translate_lat_to_geos5_native(lat_1)
lon_coord_1 = translate_lon_to_geos5_native(lon_1)
lat_coord_2 = translate_lat_to_geos5_native(lat_2)
lon_coord_2 = translate_lon_to_geos5_native(lon_2)

# Find closest grid points
lat_co_1_closest = find_closest_coordinate(lat_coord_1, lat_coords)
lon_co_1_closest = find_closest_coordinate(lon_coord_1, lon_coords)
lat_co_2_closest = find_closest_coordinate(lat_coord_2, lat_coords)
lon_co_2_closest = find_closest_coordinate(lon_coord_2, lon_coords)

# Print coordinate information
print('Calculated coordinates for point 1: ' + str((lat_coord_1, lon_coord_1)))
print('Closest coordinates for point 1: ' + str((lat_co_1_closest, lon_co_1_closest)))
print('Calculated coordinates for point 2: ' + str((lat_coord_2, lon_coord_2)))
print('Closest coordinates for point 2: ' + str((lat_co_2_closest, lon_co_2_closest)))

def translate_year_to_file_number(year):
    """Get file number based on year"""
    if year >= 2011:
        return '400'
    elif year >= 2001:
        return '300'
    elif year >= 1992:
        return '200'
    elif year >= 1980:
        return '100'
    else:
        raise Exception('Year out of range')

def generate_url_params(parameter, time_para, lat_para, lon_para):
    """Create parameter string for URL"""
    parameter = map(lambda x: x + time_para, parameter)
    parameter = map(lambda x: x + lat_para, parameter)
    parameter = map(lambda x: x + lon_para, parameter)
    return ','.join(parameter)

def generate_download_links(download_years, base_url, dataset_name, url_params):
    """Generate download URLs for specified years"""
    urls = []
    for y in download_years:
        y_str = str(y)
        file_num = translate_year_to_file_number(y)
        # Modified to only loop through months 1-4 (January to April)
        for m in range(1, 5):  # Changed from range(1,13)
            m_str = str(m).zfill(2)
            _, nr_of_days = monthrange(y, m)
            for d in range(1, nr_of_days+1):
                d_str = str(d).zfill(2)
                file_name = f'MERRA2_{file_num}.{dataset_name}.{y_str}{m_str}{d_str}.nc4'
                query = f'{base_url}{y_str}/{m_str}/{file_name}.nc4?{params}'
                urls.append(query)
    return urls

# Set up parameters for data download
requested_time = '[0:1:23]'
requested_lat = f'[{lat_co_1_closest}:1:{lat_co_2_closest}]'
requested_lon = f'[{lon_co_1_closest}:1:{lon_co_2_closest}]'

# Base URL for MERRA-2
BASE_URL = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/'

# Generate URLs for temperature data
temp_params = ['T2M']
params = generate_url_params(temp_params, requested_time, requested_lat, requested_lon)
temp_urls = generate_download_links([download_year], BASE_URL, 'tavg1_2d_slv_Nx', params)

# Create download directory
if not os.path.exists('download_temperature2'):
    os.makedirs('download_temperature2')

# Get NASA credentials
username = input('Username: ')
password = getpass.getpass('Password:')

# Initialize download manager
NUMBER_OF_CONNECTIONS = 5
download_manager = DownloadManager()
download_manager.set_username_and_password(username, password)

# Download temperature data
print(f"\nStarting download for {len(temp_urls)} files...")
download_manager.download_path = 'download_temperature2'
download_manager.download_urls = temp_urls
download_manager.start_download(NUMBER_OF_CONNECTIONS)

print("\nDownload completed!")
print("Verify the coordinates in the downloaded files before processing.")

# The dimensions map the MERRA2 grid coordinates to lat/lon.
requested_lat_dim = '[{lat_1}:1:{lat_2}]'.format(
                    lat_1=lat_co_1_closest, lat_2=lat_co_2_closest)
requested_lon_dim = '[{lon_1}:1:{lon_2}]'.format(
                    lon_1=lon_co_1_closest, lon_2=lon_co_2_closest)

lat_lon_dimension_para = 'lat' + requested_lat_dim + ',lon' + requested_lon_dim

# Creating the download url for dimension verification
dimension_url = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/2014/01/MERRA2_400.tavg1_2d_slv_Nx.20140101.nc4.nc4?'
dimension_url = dimension_url + lat_lon_dimension_para
download_manager.download_path = 'dimension_scale'
download_manager.download_urls = [dimension_url]

# Download dimension file
download_manager.start_download(1)

file_path = os.path.join('dimension_scale', DownloadManager.get_filename(
        dimension_url))

with xr.open_dataset(file_path) as ds_dim:
    df_dim = ds_dim.to_dataframe()

lat_array = ds_dim['lat'].data.tolist()
lon_array = ds_dim['lon'].data.tolist()

# Log coordinate information
log.info('Requested lat: ' + str((lat_1, lat_2)))
log.info('Received lat: ' + str(lat_array))
log.info('Requested lon: ' + str((lon_1, lon_2)))
log.info('Received lon: ' + str(lon_array))


## Rainfall data download

import pandas as pd
import xarray as xr
import numpy as np
import requests
import logging
import yaml
import json
import os
import hashlib
from datetime import datetime
from calendar import monthrange
from opendap_download.multi_processing_download import DownloadManager
import getpass

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('notebook')

# User input of timespan
download_year = 2016

# Washington State precise coordinates
lat_1, lon_1 = 45.543541, -124.848974  # Southwestern coordinate
lat_2, lon_2 = 49.002494, -116.916071  # Northeastern coordinate

def translate_lat_to_geos5_native(latitude):
    """Convert latitude to MERRA-2 grid coordinates"""
    return ((latitude + 90) / 0.5)

def translate_lon_to_geos5_native(longitude):
    """Convert longitude to MERRA-2 grid coordinates"""
    return ((longitude + 180) / 0.625)

def find_closest_coordinate(calc_coord, coord_array):
    """Find closest matching coordinate in the grid"""
    index = np.abs(coord_array-calc_coord).argmin()
    return coord_array[index]

# Create coordinate arrays
lat_coords = np.arange(0, 361, dtype=int)
lon_coords = np.arange(0, 576, dtype=int)

# Calculate grid coordinates
lat_coord_1 = translate_lat_to_geos5_native(lat_1)
lon_coord_1 = translate_lon_to_geos5_native(lon_1)
lat_coord_2 = translate_lat_to_geos5_native(lat_2)
lon_coord_2 = translate_lon_to_geos5_native(lon_2)

# Find closest grid points
lat_co_1_closest = find_closest_coordinate(lat_coord_1, lat_coords)
lon_co_1_closest = find_closest_coordinate(lon_coord_1, lon_coords)
lat_co_2_closest = find_closest_coordinate(lat_coord_2, lat_coords)
lon_co_2_closest = find_closest_coordinate(lon_coord_2, lon_coords)

# Print coordinate information
print('Calculated coordinates for point 1: ' + str((lat_coord_1, lon_coord_1)))
print('Closest coordinates for point 1: ' + str((lat_co_1_closest, lon_co_1_closest)))
print('Calculated coordinates for point 2: ' + str((lat_coord_2, lon_coord_2)))
print('Closest coordinates for point 2: ' + str((lat_co_2_closest, lon_co_2_closest)))

def translate_year_to_file_number(year):
    """Get file number based on year"""
    if year >= 2011:
        return '400'
    elif year >= 2001:
        return '300'
    elif year >= 1992:
        return '200'
    elif year >= 1980:
        return '100'
    else:
        raise Exception('Year out of range')

def generate_url_params(parameter, time_para, lat_para, lon_para):
    """Create parameter string for URL"""
    parameter = map(lambda x: x + time_para, parameter)
    parameter = map(lambda x: x + lat_para, parameter)
    parameter = map(lambda x: x + lon_para, parameter)
    return ','.join(parameter)

def generate_download_links(download_years, base_url, dataset_name, url_params):
    """Generate download URLs for specified years"""
    urls = []
    for y in download_years:
        y_str = str(y)
        file_num = translate_year_to_file_number(y)
        for m in range(1,13):
            m_str = str(m).zfill(2)
            _, nr_of_days = monthrange(y, m)
            for d in range(1,nr_of_days+1):
                d_str = str(d).zfill(2)
                file_name = f'MERRA2_{file_num}.{dataset_name}.{y_str}{m_str}{d_str}.nc4'
                query = f'{base_url}{y_str}/{m_str}/{file_name}.nc4?{params}'
                urls.append(query)
    return urls

# Set up parameters for data download
requested_time = '[0:1:23]'
requested_lat = f'[{lat_co_1_closest}:1:{lat_co_2_closest}]'
requested_lon = f'[{lon_co_1_closest}:1:{lon_co_2_closest}]'

# Base URL for MERRA-2 (changed to the correct collection for TQV)
BASE_URL = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/M2I1NXASM.5.12.4/'

# Generate URLs for rainfall data (TQV)
rainfall_params = ['QV2M']
params = generate_url_params(rainfall_params, requested_time, requested_lat, requested_lon)
rainfall_urls = generate_download_links([download_year], BASE_URL, 'inst1_2d_asm_Nx', params)

# Create download directory
if not os.path.exists('download_rh'):
    os.makedirs('download_rh')

# Get NASA credentials
username = input('Username: ')
password = getpass.getpass('Password:')

# Initialize download manager
NUMBER_OF_CONNECTIONS = 5
download_manager = DownloadManager()
download_manager.set_username_and_password(username, password)

# Download rainfall data
print(f"\nStarting download for {len(rainfall_urls)} files...")
download_manager.download_path = 'download_rh'
download_manager.download_urls = rainfall_urls
download_manager.start_download(NUMBER_OF_CONNECTIONS)

print("\nDownload completed!")
print("Verify the coordinates in the downloaded files before processing.")

# The dimensions map the MERRA2 grid coordinates to lat/lon
requested_lat_dim = '[{lat_1}:1:{lat_2}]'.format(
                    lat_1=lat_co_1_closest, lat_2=lat_co_2_closest)
requested_lon_dim = '[{lon_1}:1:{lon_2}]'.format(
                    lon_1=lon_co_1_closest , lon_2=lon_co_2_closest )

lat_lon_dimension_para = 'lat' + requested_lat_dim + ',lon' + requested_lon_dim

# Creating the download url for dimensions
dimension_url = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/M2I1NXASM.5.12.4/2014/01/MERRA2_400.inst1_2d_asm_Nx.20140101.nc4.nc4?'
dimension_url = dimension_url + lat_lon_dimension_para
download_manager.download_path = 'dimension_scale'
download_manager.download_urls = [dimension_url]

# Download dimension data
download_manager.start_download(1)

file_path = os.path.join('dimension_scale', DownloadManager.get_filename(
        dimension_url))

with xr.open_dataset(file_path) as ds_dim:
    df_dim = ds_dim.to_dataframe()

lat_array = ds_dim['lat'].data.tolist()
lon_array = ds_dim['lon'].data.tolist()

# Log output for coordinate verification
log.info('Requested lat: ' + str((lat_1, lat_2)))
log.info('Received lat: ' + str(lat_array))
log.info('Requested lon: ' + str((lon_1, lon_2)))
log.info('Received lon: ' + str(lon_array))
