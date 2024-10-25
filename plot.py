import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import rasterio
import rasterio.mask
import geopandas as gpd

def color(pixelValue: float) -> str:
    if -10.0 <= pixelValue <= -2.50:
        return '#890002'
    elif -2.50 < pixelValue <= -2.00:
        return '#aa0001'
    elif -2.00 < pixelValue <= -1.75:
        return '#ca0000'
    elif -1.75 < pixelValue <= -1.50:
        return '#e50201'
    elif -1.50 < pixelValue <= -1.25:
        return '#f41f0a'
    elif -1.25 < pixelValue <= -1.00:
        return '#f1651d'
    elif -1.00 < pixelValue <= -0.75:
        return '#ed9028'
    elif -0.75 < pixelValue <= -0.50:
        return '#e9aa2d'
    elif -0.50 < pixelValue <= -0.25:
        return '#dfbf77'
    elif -0.25 < pixelValue <= 0.00:
        return '#97C798'
    elif 0.00 < pixelValue <= 0.25:
        return '#54BA57'
    elif 0.25 < pixelValue <= 0.50:
        return '#12AD16'
    elif 0.50 < pixelValue <= 0.75:
        return '#009E3C'
    elif 0.75 < pixelValue <= 5:
        return '#00A1DF'
    else:
        return "none"

def plot_raster(raster_url: str, gdf: gpd.GeoDataFrame, fig_name: str, color: any) -> None:
    """
    Plots a raster based on a GeoDataFrame without reprojection or resampling.

    Parameters:
    raster_url (str): Path to the input raster file.
    gdf (GeoDataFrame): GeoDataFrame containing the geometries for masking.
    fig_name (str): Output figure file name.
    color (function): Function that returns a color based on a pixel value.
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
    mmin = np.nanmin(out_image_masked)
    mmax = np.nanmax(out_image_masked)

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
    img = ax.imshow(out_image_masked[0], cmap=cmap_custom, extent=(out_transform[2], out_transform[2] + out_transform[0] * out_image_masked.shape[2],
            out_transform[5] + out_transform[4] * out_image_masked.shape[1], out_transform[5]))

    gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=1)

    # Establecer límites en los ejes x e y
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)

    # Agregar la barra de color
    fig.colorbar(img, ax=ax, label='', pad=0.05, shrink=0.5, extend='both', ticks=[-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5])
    plt.title("Índice hidrológico de sequía de Nalbantis: 01 mes \nPeriodo: Sep 2024")
    plt.draw()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Guardar la figura
    plt.savefig(fig_name, bbox_inches='tight', pad_inches=0)

# Cargar el shapefile
path = "assets/ecuador.shp"
ec = gpd.read_file(path)

# Llamar a la función de plot
plot_raster(
    raster_url="data/index/tif/2024_10_01.tif",
    gdf=ec,
    fig_name="out.png",
    color=color)
