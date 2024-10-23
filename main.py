import os
import shutil
import rasterio
import numpy as np
import pandas as pd
import datetime as dt
import geopandas as gpd
from scipy.interpolate import griddata
from rasterio.transform import from_origin

from modules.geoglows import Geoglows
from modules.nalbantis import Nalbantis


# Constants for paths
PNG_DIR = "data/index/png"
TIF_DIR = "data/index/tif"
TXT_DIR = "data/index/txt"
DAT_DIR = "data/historical"
COMIDS_PATH = "assets/ecuador.csv"
OUT_PATH = "data/historical/"
OUTPUT_FILE = f"data/index/txt/{dt.datetime.now().strftime('%Y_%m')}.csv"
BASE_TIF_PATH = "assets/base.tif"
BASE_TWF_PATH = "assets/base.tfw"


def clear_output_directories():
    """Delete and recreate output directories."""
    for dir_path in [PNG_DIR, TIF_DIR, TXT_DIR, DAT_DIR]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path)


def download_data(glw):
    """Download data and return verified COMIDs."""
    dataset = glw.get_bucket()
    comids = glw.verify_comids(ds=dataset, csv=COMIDS_PATH)
    data = glw.get_data(ds=dataset, comids=comids)
    glw.save_data(data=data, save_type="individual", dir_path=OUT_PATH)


def compute_sdi(metadata):
    """Compute the Streamflow Drought Index for each COMID."""
    sdi_outputs = []

    for comid in metadata.comid:
        print(comid)
        try:
            file_path = f"{OUT_PATH}{comid}.csv"
            data = pd.read_csv(file_path, sep=",", index_col=0)
            data.index = pd.to_datetime(data.index)

            # Prepare the DataFrame
            data.columns = ["value"]
            data = pd.DataFrame({
                'year': data.index.year,
                'month': data.index.month,
                'day': data.index.day,
                'value': data['value']
            })

            # Compute the Nalbantis index
            nlb = Nalbantis()
            sdi = nlb.compute_overall(data)
            sdi = sdi.tail(1)

            sdi_output = {
                'comid': comid,
                'sdi_1': round(sdi.sdi_value_1m.iloc[0], 3),
                'sdi_3': round(sdi.sdi_value_3m.iloc[0], 3),
                'sdi_6': round(sdi.sdi_value_6m.iloc[0], 3),
                'sdi_9': round(sdi.sdi_value_9m.iloc[0], 3),
                'sdi_12': round(sdi.sdi_value_12m.iloc[0], 3),
            }
            sdi_outputs.append(sdi_output)

        except FileNotFoundError:
            print(f"File not found for COMID {comid}, skipping...")
            sdi_outputs.append({
                'comid': comid,
                'sdi_1': 0, 'sdi_3': 0, 'sdi_6': 0,
                'sdi_9': 0, 'sdi_12': 0
            })
        except Exception as e:
            print(f"An error occurred for COMID {comid}: {e}")
            sdi_outputs.append({
                'comid': comid,
                'sdi_1': 0, 'sdi_3': 0, 'sdi_6': 0,
                'sdi_9': 0, 'sdi_12': 0
            })

    return pd.DataFrame(sdi_outputs)



def to_raster(df, interpolation_field, output_raster_path):
    """
    Interpolates values from a DataFrame field into a raster with the same 
    extent, resolution, and CRS as a given base raster.

    Parameters:
    df (pandas.DataFrame): DataFrame with 'Longitude', 'Latitude', and the 
                           field to interpolate.
    interpolation_field (str): Column name of the field to interpolate.
    output_raster_path (str): Path where the interpolated raster will be saved.
    """
    
    # Define the domain of interest [LonMin, LonMax, LatMin, LatMax]
    domain = [-81, -75, -5, 1.25]
    lon_min, lon_max, lat_min, lat_max = domain
    
    # Filter rows with valid 'Latitud', 'Longitud', and the interpolation field
    df_filtered = df.dropna(subset=['Latitud', 'Longitud', interpolation_field])
    
    # Create a GeoDataFrame with point geometries from the coordinates
    gdf = gpd.GeoDataFrame(df_filtered, 
                           geometry=gpd.points_from_xy(df_filtered['Longitud'], 
                                                       df_filtered['Latitud']))

    # Create a grid for interpolation
    resolution = 0.05  # Cambia la resolución según sea necesario
    lon_grid = np.arange(lon_min, lon_max, resolution)
    lat_grid = np.arange(lat_min, lat_max, resolution)
    grid_lon, grid_lat = np.meshgrid(lon_grid, lat_grid)
    
    # Interpolate the values on the grid
    points = np.column_stack((df_filtered['Longitud'], df_filtered['Latitud']))
    values = df_filtered[interpolation_field].values
    interpolated_values = griddata(points, values, (grid_lon, grid_lat), method='linear')
    
    # Manejo de NaNs
    interpolated_values = np.nan_to_num(interpolated_values, nan=0)
    
    # Create a raster with the interpolated values
    transform = from_origin(lon_min, lat_max, resolution, resolution)
    
    with rasterio.open(
        output_raster_path,
        'w',
        driver='GTiff',
        height=grid_lon.shape[0],
        width=grid_lon.shape[1],
        count=1,
        dtype=interpolated_values.dtype,
        crs='EPSG:4326',  # Define CRS (change as needed)
        transform=transform
    ) as dst:
        dst.write(interpolated_values, 1)



def main():
    """Main function to execute the script."""
    clear_output_directories()

    # Instantiate Geoglows
    glw = Geoglows()

    # Download data and compute the SDI
    download_data(glw)
    metadata = pd.read_csv(COMIDS_PATH, sep=",").drop(
        columns=["order", "latitude", "longitude"]
    )
    sdi_outputs = compute_sdi(metadata)

    # Merge metadata with SDI outputs and save to CSV
    sdi_outputs = pd.merge(metadata, sdi_outputs, on="comid")
    sdi_outputs.to_csv(OUTPUT_FILE, sep=",", index=False)

    # Date for files
    date = dt.datetime.now().strftime('%Y_%m')
    
    # Create the raster
    to_raster(sdi_outputs, "sdi_1", f"data/index/tif/{date}_01.tif")
    to_raster(sdi_outputs, "sdi_3", f"data/index/tif/{date}_03.tif")
    to_raster(sdi_outputs, "sdi_6", f"data/index/tif/{date}_06.tif")
    to_raster(sdi_outputs, "sdi_9", f"data/index/tif/{date}_09.tif")
    to_raster(sdi_outputs, "sdi_12", f"data/index/tif/{date}_12.tif")


if __name__ == "__main__":
    main()
