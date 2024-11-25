import os
import shutil
import rasterio
import numpy as np
import pandas as pd
import datetime as dt
import geopandas as gpd
from rasterio.mask import mask
from scipy.interpolate import griddata
from rasterio.transform import from_origin
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from modules.geoglows import Geoglows
from modules.nalbantis import Nalbantis

# Date
DATE = dt.datetime.now().replace(day=1) - pd.DateOffset(months=1)

# Constants for paths
PNG_DIR = "data/index/png"
TIF_DIR = "data/index/tif"
TXT_DIR = "data/index/txt"
DAT_DIR = "data/historical"
COMIDS_PATH = "assets/Esta_Peru.csv"
OUT_PATH = "data/historical/"
OUT_PATH_FORMATED = "data/formated_historical/"
OUTPUT_FILE = f"data/index/txt/{DATE.strftime('%Y_%m')}.csv"

TIF01_FILE = f"data/index/tif/{DATE.strftime('%Y_%m_01')}.tif"
TIF03_FILE = f"data/index/tif/{DATE.strftime('%Y_%m_03')}.tif"
TIF06_FILE = f"data/index/tif/{DATE.strftime('%Y_%m_06')}.tif"
TIF09_FILE = f"data/index/tif/{DATE.strftime('%Y_%m_09')}.tif"
TIF12_FILE = f"data/index/tif/{DATE.strftime('%Y_%m_12')}.tif"

PNG01_FILE = f"data/index/png/{DATE.strftime('%Y_%m_01')}.png"
PNG03_FILE = f"data/index/png/{DATE.strftime('%Y_%m_03')}.png"
PNG06_FILE = f"data/index/png/{DATE.strftime('%Y_%m_06')}.png"
PNG09_FILE = f"data/index/png/{DATE.strftime('%Y_%m_09')}.png"
PNG12_FILE = f"data/index/png/{DATE.strftime('%Y_%m_12')}.png"



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
    glw.save_format_data(data=data, save_type="individual", dir_path=OUT_PATH_FORMATED)


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
                '1': round(sdi.sdi_value_1m.iloc[0], 3),
                '3': round(sdi.sdi_value_3m.iloc[0], 3),
                '6': round(sdi.sdi_value_6m.iloc[0], 3),
                '9': round(sdi.sdi_value_9m.iloc[0], 3),
                '12': round(sdi.sdi_value_12m.iloc[0], 3),
            }
            sdi_outputs.append(sdi_output)

        except:
            pass

    return pd.DataFrame(sdi_outputs)


def color(pixelValue: float) -> str:
    if -10.0 <= pixelValue < -2.75:
        return '#890002'
    elif -2.75 <= pixelValue < -2.5:
        return '#a10001'
    elif -2.5 <= pixelValue < -2.25:
        return '#ca0000'
    elif -2.25 <= pixelValue < -2.0:
        return '#e50201'
    elif -2.0 <= pixelValue < -1.75:
        return '#f41f0a'
    elif -1.75 <= pixelValue < -1.5:
        return '#f1651d'
    elif -1.5 <= pixelValue < -1.25:
        return '#ed9028'
    elif -1.25 <= pixelValue < -1.0:
        return '#e9aa2d'
    elif -1.0 <= pixelValue < -0.75:
        return '#dfbf77'
    elif -0.75 <= pixelValue < -0.25:
        return '#c8c8c8'  # Gris para valores cercanos a -0.25
    elif -0.25 <= pixelValue < 0.25:
        return '#c8c8c8'  # Gris para el rango de -0.25 a 0.25
    elif 0.25 <= pixelValue < 0.5:
        return '#54ba57'
    elif 0.5 <= pixelValue < 0.75:
        return '#009e3c'
    elif 0.75 <= pixelValue < 1.0:
        return '#00a1df'
    elif 1.0 <= pixelValue < 1.25:
        return '#00b0df'
    elif 1.25 <= pixelValue < 1.5:
        return '#00b8e0'
    elif 1.5 <= pixelValue < 1.75:
        return '#009fdf'
    elif 1.75 <= pixelValue < 2.0:
        return '#007cdf'
    elif 2.0 <= pixelValue < 2.25:
        return '#0062df'
    elif 2.25 <= pixelValue < 2.5:
        return '#7100d0'
    elif 2.5 <= pixelValue < 2.75:
        return '#8900b0'
    elif 2.75 <= pixelValue <= 10.0:
        return '#a00090'
    else:
        return "none"



def plot_raster(raster_url: str, gdf: gpd.GeoDataFrame, fig_name: str, color: any, aggTime:str) -> None:
    """
    Plots a raster based on a GeoDataFrame without reprojection or resampling.

    Parameters:
     - raster_url (str): Path to the input raster file.
     - gdf (GeoDataFrame): GeoDataFrame containing the geometries for masking.
     - fig_name (str): Output figure file name.
     - color (function): Function that returns a color based on a pixel value.
    """
    # Abre el raster utilizando rasterio
    with rasterio.open(raster_url) as src:
        # Leer los datos del raster
        out_image_masked, out_transform = rasterio.mask.mask(
            src, gdf.geometry, crop=True
        )

    # Convertir a un arreglo de float64
    out_image_masked = out_image_masked.astype(np.float64)

    # Reemplazar valores menores a -10 o mayores a 10 con NaN
    out_image_masked = np.where((out_image_masked < -10) | (out_image_masked > 10), np.nan, out_image_masked)

    # Asegurarse de que no haya valores NaN
    out_image_masked = np.nan_to_num(out_image_masked, nan=np.nan)

    # Encontrar valores mínimos y máximos
    mmin = -3 #np.nanmin(out_image_masked)
    mmax = 3 #np.nanmax(out_image_masked)

    # Si mmin es igual a mmax, evitar crear linspace con un rango inválido
    if mmin == mmax:
        print("Los valores mínimos y máximos son iguales. No se puede crear linspace.")
        return

    # Crear una lista de valores entre 0 y 1
    values = np.linspace(mmin, mmax, 500)  # Limitar a un máximo de 1000 colores

    # Crear una lista de colores utilizando la función color
    colors = [color(value) for value in values]
    cmap_custom = ListedColormap(colors)

    # Crea una figura de Matplotlib y muestra el raster enmascarado
    fig, ax = plt.subplots(figsize=(8, 8))
    plt.margins(0)

    # Mostrar la imagen del raster usando imshow para obtener el mapeador
    img = ax.imshow(out_image_masked[0], cmap=cmap_custom, extent=(
        out_transform[2], 
        out_transform[2] + out_transform[0] * out_image_masked.shape[2],
        out_transform[5] + out_transform[4] * out_image_masked.shape[1], 
        out_transform[5]
    ), vmin=-3, vmax=3)

    gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=1)

    # Establecer límites en los ejes x e y
    plt.xlim(-83.00, -66.50)
    plt.ylim(-19.00, 0.50)

    # Agregar la barra de color
    fig.colorbar(img, ax=ax, label='', pad=0.05, shrink=0.5, extend='both', ticks=[-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3])
    fd = DATE.strftime('%Y-%m')
    plt.title(f"Índice hidrológico de sequía de Nalbantis: {aggTime} mes \nPeriodo: {fd}")
    plt.draw()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Guardar la figura
    plt.savefig(fig_name, bbox_inches='tight', pad_inches=0)


def main():
    """Main function to execute the script."""
    clear_output_directories()

    # Instantiate Geoglows
    glw = Geoglows()

    # Download data and compute the SDI
    print("Downloading")
    download_data(glw)
    print("Downloaded")
    metadata = pd.read_csv(COMIDS_PATH, sep=",")[["Clave", "Longitud", "Latitud", "comid"]]
    metadata.columns = ['Estacion', 'Lon', 'Lat', "comid"]
    sdi_outputs = compute_sdi(metadata)

    # Merge metadata with SDI outputs and save to CSV
    sdi_outputs = pd.merge(metadata, sdi_outputs, on="comid")
    sdi_outputs = sdi_outputs.drop(columns=["comid"])
    sdi_outputs.to_csv(OUTPUT_FILE, sep=",", index=False)

    # Create GeoTIFF
    os.system(f'Rscript generate_tif.R {OUTPUT_FILE} {TIF01_FILE} "X1"')
    os.system(f'Rscript generate_tif.R {OUTPUT_FILE} {TIF03_FILE} "X3"')
    os.system(f'Rscript generate_tif.R {OUTPUT_FILE} {TIF06_FILE} "X6"')
    os.system(f'Rscript generate_tif.R {OUTPUT_FILE} {TIF09_FILE} "X9"')
    os.system(f'Rscript generate_tif.R {OUTPUT_FILE} {TIF12_FILE} "X12"')

    # Generate PNG plots
    ec = gpd.read_file("assets/peru.shp")
    plot_raster(raster_url=TIF01_FILE, gdf=ec, fig_name=PNG01_FILE, color=color, aggTime="01")
    plot_raster(raster_url=TIF03_FILE, gdf=ec, fig_name=PNG03_FILE, color=color, aggTime="03")
    plot_raster( raster_url=TIF06_FILE, gdf=ec, fig_name=PNG06_FILE, color=color, aggTime="06")
    plot_raster(raster_url=TIF09_FILE, gdf=ec, fig_name=PNG09_FILE, color=color, aggTime="09")
    plot_raster(raster_url=TIF12_FILE, gdf=ec, fig_name=PNG12_FILE, color=color, aggTime="12")



if __name__ == "__main__":
    main()
