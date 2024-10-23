import numpy as np
import rasterio
import matplotlib.pyplot as plt
import matplotlib.colors as clr
from mpl_toolkits.basemap import Basemap
import subprocess
import sys

def plot_raster(name_tif, output_path, title, date, period):
    # Leer el archivo raster
    with rasterio.open(name_tif) as rrqpe_dat:
        rrqpe_tmp = rrqpe_dat.read(1)
        rrqpe_tmp = np.ma.array(
            rrqpe_tmp, mask=(rrqpe_tmp < -20.0), 
            fill_value=-3.39999995e+38
        )

        # Obtener límites geográficos
        lat_ini, lat_fin = rrqpe_dat.bounds.bottom, rrqpe_dat.bounds.top
        lon_ini, lon_fin = rrqpe_dat.bounds.left, rrqpe_dat.bounds.right
        
        # Crear grilla
        py1, px1 = rrqpe_dat.index(lon_ini, lat_ini)
        py2, px2 = rrqpe_dat.index(lon_fin, lat_fin)
        nx, ny = px2 - px1, py1 - py2
        grid_lon = np.linspace(lon_ini, lon_fin, nx)
        grid_lat = np.linspace(lat_ini, lat_fin, ny)
        xintrp, yintrp = np.meshgrid(grid_lon, grid_lat)

        rrqpe = rrqpe_tmp[py2:py1, px1:px2]

    # Configuración del gráfico
    fig, ax = plt.subplots(figsize=(10.4, 8.6))
    cmap_rrqpe = clr.LinearSegmentedColormap.from_list(
        'custom_cmap', [
            '#890002', '#C50000', '#F50302', '#F08125', '#E8AF2E',
            '#D3D3D3', '#D3D3D3', '#00A904', '#00A0FF', '#8000E1', 
            '#A101C7', '#E50FED'], N=36
    )

    m = Basemap(projection='merc', llcrnrlat=lat_ini, 
                urcrnrlat=lat_fin, llcrnrlon=lon_ini, 
                urcrnrlon=lon_fin, lat_ts=7, resolution='i')
    m.drawcoastlines(linewidth=1.0)
    m.drawstates(linewidth=1.2)
    m.drawcountries(linewidth=1.2)
    m.drawparallels(np.arange(-5, 2, 2), labels=[True, False, False, False])
    m.drawmeridians(np.arange(-81, -74, 2), labels=[False, False, False, True])
    m.bluemarble(alpha=0.7, scale=2.0)

    xx, yy = m(xintrp, yintrp)
    grafica = m.pcolormesh(
        xx, yy, rrqpe, vmin=-3.0, vmax=3.0, cmap=cmap_rrqpe,
        shading='gouraud'
    )
    
    # Configuración de la barra de color
    fig.colorbar(grafica, label='', pad=0.05, shrink=0.5, 
                 extend='both', ticks=np.arange(-3.0, 4.0, 0.5))
    plt.title(f"\nÍndice estandarizado de precipitación a: {title} {date}\n"
              f" Periodo: {period}")

    # Guardar figura
    fig.savefig("auxiliard.png", format='png', dpi=120)
    plt.close()

    # Procesar imagen
    #subprocess.call(["/usr/local/bin/convert", "auxiliard.png", "-trim",
    #                 "auxiliard2.png"])
    #subprocess.call(["cp", "auxiliard2.png", output_path])

if __name__ == "__main__":
    # Leer argumentos de línea de comandos
    name_tif = "data/index/tif/2024_10_01.tif"
    output_path = "data/index/png/2024_10_01.png"
    title = "01"
    date = "mes"
    period = "Septiembre 2024"

    plot_raster(name_tif, output_path, title, date, period)
