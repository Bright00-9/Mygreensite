# dashboard/utils.py

# Average kgCO2e per kWh for AWS regions
CARBON_INTENSITY_MAP = {
    'us-east-1': 0.379,  # USA (Virginia)
    'eu-central-1': 0.311, # Germany
    'af-south-1': 0.900,   # South Africa
    'eu-west-1': 0.278,    # Ireland
    # Add more as needed based on your usage
}

def calculate_carbon(instance_type, hours, region):
    # Simplified estimation:
    # 1. Assume an average power consumption of 0.1 kWh per vCPU-hour
    # 2. Multiply by the region's carbon intensity
    power_factor = 0.1 
    intensity = CARBON_INTENSITY_MAP.get(region, 0.4) # Default to 0.4 if unknown
    
    return hours * power_factor * intensity


# dashboard/utils.py

# Average PUE for AWS regions (approximate)
PUE_MAP = {
    'us-east-1': 1.15,
    'af-south-1': 1.24,
    'eu-central-1': 1.35,
}

# Grid Intensity in kgCO2e/kWh (Location-based)
GRID_INTENSITY = {
    'us-east-1': 0.35,
    'af-south-1': 0.85, # Higher due to coal reliance in local grid
    'eu-central-1': 0.25,
}

def calculate_carbon_impact(instance_type, vcpus, hours, region):
    # 1. Assume avg power draw per vCPU (t-series instances ~0.05kW)
    avg_power_kw = vcpus * 0.05 
    
    # 2. Get PUE and Grid Intensity for the region
    pue = PUE_MAP.get(region, 1.2)
    intensity = GRID_INTENSITY.get(region, 0.4)
    
    # 3. Calculate CO2e
    return hours * avg_power_kw * pue * intensity
