import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob

def create_pressure_matrix(lat_array, lon_array, download_dir='download_pressure2', year=2017):
    """
    Creates a surface pressure matrix from MERRA-2 data with lat/lon pairs in rows and timestamps in columns.
    
    Args:
        lat_array (list): List of latitude values from dimension file
        lon_array (list): List of longitude values from dimension file
        download_dir (str): Directory containing downloaded pressure NC4 files
        year (int): The year of the data being processed
        
    Returns:
        pd.DataFrame: Matrix with MultiIndex (lat, lon) and timestamp columns
    """
    # Get list of all downloaded files
    nc_files = sorted(glob.glob(os.path.join(download_dir, f'MERRA2_*.nc4')))
    if not nc_files:
        raise ValueError(f"No MERRA2 .nc4 files found in {download_dir}")
    
    # Initialize empty list to store data
    pressure_data_list = []
    
    # Process each file
    for nc_file in nc_files:
        try:
            # Explicitly specify netcdf4 engine
            with xr.open_dataset(nc_file, engine='netcdf4') as ds:
                # Extract the date from filename
                date_str = os.path.basename(nc_file).split('.')[-2]  # Format: YYYYMMDD
                
                # Get timestamps for this file (24 hours)
                base_date = pd.to_datetime(f"{date_str}", format="%Y%m%d")
                timestamps = [base_date + pd.Timedelta(hours=h) for h in range(24)]
                
                # Extract surface pressure data
                ps_data = ds['PS'].values      # surface pressure [Pa]
                
                # For each timestamp in the file (24 hours)
                for t_idx, timestamp in enumerate(timestamps):
                    # Get pressure slice for this timestamp
                    ps_slice = ps_data[t_idx]
                    
                    # Create a DataFrame for this timestamp using the provided lat/lon arrays
                    for lat_idx, lat in enumerate(lat_array):
                        for lon_idx, lon in enumerate(lon_array):
                            # Get pressure value and convert from Pa to hPa
                            ps = float(ps_slice[lat_idx, lon_idx]) / 100.0  # Convert Pa to hPa
                            
                            pressure_data_list.append({
                                'latitude': float(lat),
                                'longitude': float(lon),
                                'surface_pressure': float(ps),
                                'timestamp': timestamp
                            })
        except Exception as e:
            print(f"Error processing file {nc_file}: {str(e)}")
            continue
    
    if not pressure_data_list:
        raise ValueError("No data was successfully processed from the files")
    
    # Create DataFrame from all collected data
    df_combined = pd.DataFrame(pressure_data_list)
    
    # Create the matrix using pivot
    matrix = df_combined.pivot_table(
        index=['latitude', 'longitude'],
        columns='timestamp',
        values='surface_pressure'
    )
    
    # Sort the index for better organization
    matrix.sort_index(level=['latitude', 'longitude'], ascending=[False, True], inplace=True)
    
    return matrix

def calculate_pressure_averages(matrix):
    """
    Calculate daily, monthly, and annual averages from the pressure matrix.
    
    Args:
        matrix (pd.DataFrame): The pressure matrix with timestamps as columns
        
    Returns:
        tuple: (daily_averages, monthly_averages, annual_average) DataFrames
    """
    # Convert column names to datetime if they aren't already
    if not isinstance(matrix.columns, pd.DatetimeIndex):
        matrix.columns = pd.to_datetime(matrix.columns)
    
    # Calculate daily averages
    daily_averages = matrix.T.groupby(lambda x: x.date()).mean().T
    
    # Calculate monthly averages
    monthly_averages = matrix.T.groupby(lambda x: x.strftime('%Y-%m')).mean().T
    
    # Calculate annual average
    annual_average = pd.DataFrame(matrix.mean(axis=1), columns=['2017'])
    
    return daily_averages, monthly_averages, annual_average

def save_pressure_averages(daily_avg, monthly_avg, annual_avg, output_prefix='washington_pressure'):
    """
    Saves the pressure averages to CSV files and prints summary statistics
    
    Args:
        daily_avg (pd.DataFrame): Daily pressure averages
        monthly_avg (pd.DataFrame): Monthly pressure averages
        annual_avg (pd.DataFrame): Annual pressure average
        output_prefix (str): Prefix for output filenames
    """
    # Save to CSV
    daily_avg.to_csv(f'{output_prefix}_daily2017.csv', float_format='%.2f')
    monthly_avg.to_csv(f'{output_prefix}_monthly2017.csv', float_format='%.2f')
    annual_avg.to_csv(f'{output_prefix}_annual2017.csv', float_format='%.2f')
    
    # Print summary information
    print("\nSummary Statistics:")
    print("\nDaily Averages:")
    print(f"Date range: {daily_avg.columns.min()} to {daily_avg.columns.max()}")
    print(f"Surface pressure range: {daily_avg.min().min():.2f} to {daily_avg.max().max():.2f} hPa")
    
    print("\nMonthly Averages:")
    print(f"Month range: {monthly_avg.columns.min()} to {monthly_avg.columns.max()}")
    print(f"Surface pressure range: {monthly_avg.min().min():.2f} to {monthly_avg.max().max():.2f} hPa")
    
    print("\nAnnual Average:")
    print(f"Year: 2016")
    print(f"Surface pressure range: {annual_avg.min().min():.2f} to {annual_avg.max().max():.2f} hPa")
    
    # Print coordinate ranges
    lat_range = daily_avg.index.get_level_values('latitude').unique()
    lon_range = daily_avg.index.get_level_values('longitude').unique()
    print(f"\nGeographic Coverage:")
    print(f"Latitude range: {lat_range.min():.3f}°N to {lat_range.max():.3f}°N")
    print(f"Longitude range: {lon_range.min():.3f}°E to {lon_range.max():.3f}°E")
    
    print(f"\nFiles saved with prefix: {output_prefix}")

# Example usage:
if __name__ == "__main__":
    # Create the matrix using the lat_array and lon_array from the dimension file
    pressure_matrix = create_pressure_matrix(lat_array, lon_array, year=2017)
    
    # Calculate averages
    daily_avgs, monthly_avgs, annual_avg = calculate_pressure_averages(pressure_matrix)
    
    # Save and display information
    save_pressure_averages(daily_avgs, monthly_avgs, annual_avg)
