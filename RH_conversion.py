import pandas as pd
import numpy as np

def saturation_vapor_pressure(T):
    """Calculate saturation vapor pressure (hPa) using Bolton's formula
    T: temperature in Kelvin
    """
    Tc = T - 273.15  # Convert to Celsius
    return 6.112 * np.exp((17.67 * Tc) / (Tc + 243.5))

def specific_to_relative_humidity(q, T, P):
    """
    Convert specific humidity to relative humidity
    
    Parameters:
    q: specific humidity (kg/kg)
    T: temperature (Kelvin)
    P: pressure (atm)
    
    Returns:
    RH: relative humidity (%)
    """
    # Calculate saturation vapor pressure in hPa
    es = saturation_vapor_pressure(T)
    
    # Convert es from hPa to atm (1 atm = 1013.25 hPa)
    es_atm = es / 1013.25
    
    # Calculate relative humidity
    RH = (q * P) / (0.622 * es_atm) * 100
    
    # Clip values to valid range [0-100]
    return np.clip(RH, 0, 100)

# Read the CSV files
specific_humidity = pd.read_csv('washington_humidity_daily.csv')
temperature = pd.read_csv('washington_temperature_daily.csv')
pressure = pd.read_csv('washington_pressure_daily.csv')

# Convert pressure to atm
pressure_cols = [col for col in pressure.columns if col not in ['latitude', 'longitude']]
pressure[pressure_cols] = pressure[pressure_cols] / 1013.25

# Create a list to store DataFrames for each date
relative_humidity_dfs = []

# Start with lat/lon
relative_humidity_dfs.append(specific_humidity[['latitude', 'longitude']])

# Process each date column
for date in specific_humidity.columns:
    if date in ['latitude', 'longitude']:
        continue
        
    # Skip if we don't have all required data for this date
    if date not in temperature.columns or date not in pressure.columns:
        continue
        
    # Convert to relative humidity
    rh = specific_to_relative_humidity(
        specific_humidity[date],
        temperature[date],
        pressure[date]
    )
    
    # Create a DataFrame for this date's data
    date_df = pd.DataFrame({date: rh})
    relative_humidity_dfs.append(date_df)

# Combine all DataFrames efficiently
result = pd.concat(relative_humidity_dfs, axis=1)

# Save the result
result.to_csv('washington_relative_humidity_daily.csv', index=False)

print("Conversion completed and saved to washington_relative_humidity_daily.csv")
