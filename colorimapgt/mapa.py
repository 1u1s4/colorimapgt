import os
import glob
import shutil
import subprocess
import pkg_resources
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.colors as mcolors

class Mapa:
    def __init__(
        self,
        nombre_archivo: str,
        datos: pd.DataFrame=pd.DataFrame({}),
        output_dir: str='output',
        color_base: str='#3F46BF',
        precision: int=2) -> None:
        self.datos = datos
        self.nombre_archivo = nombre_archivo
        self.tracts = gpd.read_file(pkg_resources.resource_filename(__name__, 'regiones/regiones_y_belice.shp'))
        self.output_dir = output_dir
        self.color_base = color_base
        self.precision = precision

        # Crear el directorio si no existe
        os.makedirs(self.output_dir, exist_ok=True)

        # Copiar y renombrar el archivo plantilla.tex al directorio de salida
        shutil.copy(pkg_resources.resource_filename(__name__, 'plantilla.tex'), os.path.join(self.output_dir, f"{self.nombre_archivo}.tex"))

    def hex_a_rgb(self, color_hex: str) -> tuple[int, int, int]:
        # Eliminar el "#"
        color_hex = color_hex.lstrip("#")
        # Convertir a RGB
        return tuple(
            int(color_hex[i:i+2], 16) for i in range(0, 6, 2)
        )

    def generar_escala_colores(self, color_hex: str) -> list[str]:
        color_hex = color_hex.lstrip("#")
        color_base = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in range(0, 6, 2))

        # Crea el mapa de colores personalizado que va desde blanco hasta el color base y desde el color base hasta negro
        color_scale = mcolors.LinearSegmentedColormap.from_list(
            "scale", [(1.0, 1.0, 1.0), color_base, (0.0, 0.0, 0.0)]
        )

        # Genera una lista de valores entre 0 y 1
        scale_values = np.linspace(0, 1, 200) # Ajustado para tener en cuenta el color base adicional

        # Utiliza los valores de la escala para obtener los colores correspondientes de la escala de colores
        colors = [mcolors.rgb2hex(color_scale(val)) for val in scale_values]

        return colors[50:100] # Esto también puede necesitar ser ajustado dependiendo de cómo quieras que se vea la escala de colores

    def agregar_datos(self, datos_nuevos: list) -> None:
        self.datos = pd.DataFrame({
            'region': ['Región I', 'Región II', 'Región III', 'Región IV', 'Región V', 'Región VI', 'Región VII', 'Región VIII'],
            'valor': datos_nuevos
        })

    def hacer_mapa(self) -> None:
        for reg in self.datos['region']:
            # Añadir columna de valor asociado a cada región en el GeoDataFrame de los trazos
            self.tracts.loc[self.tracts['region'] == reg, 'valor'] = self.datos.loc[self.datos['region'] == reg, 'valor'].values[0]
        # Separar entre trazos de regiones de Guatemala y trazos de Belice
        solo_belice = self.tracts[self.tracts["region"] == "Belice"]
        solo_guatemala = self.tracts[self.tracts["region"] != "Belice"]

        # Define el mapa de colores personalizado
        escala_de_color = self.generar_escala_colores(color_hex=self.color_base)
        cmap = colors.LinearSegmentedColormap.from_list("", escala_de_color)

        fig, ax = plt.subplots()  # Crea una figura y ejes con un tamaño específico

        # Para el mapa de las regiones de GT, desactiva la leyenda, establece el color de borde a blanco y el grosor a 1.5
        solo_guatemala.plot(column="valor", cmap=cmap, edgecolor="white", linewidth=0.7, legend=False, ax=ax, aspect=1)
        # Para el mapa de Belice, desactiva la leyenda, establece el color de fondo blanco y los bordes son dashed
        solo_belice.plot(color = ["white"],
                         edgecolor=["black"],
                         linewidth=0.7,
                         linestyle='dashed',
                         legend=False,
                         ax = ax,
                         aspect=1)
        
        ax.axis('off')  # Desactiva los ejes

        # Guarda la figura en el directorio especificado
        plt.savefig(os.path.join(self.output_dir, f"mapa_sin_anotar.pdf"), format='pdf', dpi=100, bbox_inches='tight')

        # Crear el archivo datos.tex en la carpeta output con el formato especificado
        color_1 = "{" + "{},{},{}".format(*self.hex_a_rgb(escala_de_color[0])) + "}"
        color_2 = "{" + "{},{},{}".format(*self.hex_a_rgb(escala_de_color[-1])) + "}"
        with open(os.path.join(self.output_dir, 'datos.tex'), 'w') as file:
            datos = self.datos['valor'].values
            file.write("\\definecolor{color1}{RGB}" + color_1 + "\n")
            file.write("\\definecolor{color2}{RGB}" + color_2 + "\n")
            file.write("\\def \\regionUno{" + "{:.{}f}".format(datos[0], self.precision) + "}\n")
            file.write("\\def \\regionDos{" + "{:.{}f}".format(datos[1], self.precision) + "}\n")
            file.write("\\def \\regionTres{" + "{:.{}f}".format(datos[2], self.precision) + "}\n")
            file.write("\\def \\regionCuatro{" + "{:.{}f}".format(datos[3], self.precision) + "}\n")
            file.write("\\def \\regionCinco{" + "{:.{}f}".format(datos[4], self.precision) + "}\n")
            file.write("\\def \\regionSeis{" + "{:.{}f}".format(datos[5], self.precision) + "}\n")
            file.write("\\def \\regionSiete{" + "{:.{}f}".format(datos[6], self.precision) + "}\n")
            file.write("\\def \\regionOcho{" + "{:.{}f}".format(datos[7], self.precision) + "}\n")

    def compilar(self):
        # Guarda el directorio de trabajo original
        original_dir = os.getcwd()

        # Cambia al directorio de salida
        os.chdir(self.output_dir)

        # Ejecuta el comando para compilar el archivo renombrado
        subprocess.run(['xelatex', '-synctex=1', '-interaction=nonstopmode', f"{self.nombre_archivo}.tex"], capture_output=True, text=True, check=True)

        # Vuelve al directorio de trabajo original
        os.chdir(original_dir)

    def limpiar(self):
        """
        Elimina los archivos auxiliares generados por xelatex, así como el archivo de datos y el archivo .tex
        """
        patrones_para_eliminar = ['*.aux', '*.synctex.gz', '*.log', 'mapa_sin_anotar.pdf', 'datos.tex', f"{self.nombre_archivo}.tex"]

        for patron in patrones_para_eliminar:
            archivos = glob.glob(os.path.join(self.output_dir, patron))
            for archivo in archivos:
                os.remove(archivo)
