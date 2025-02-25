import pandas as pd
import os

# Definir la ruta de la carpeta "docs" dentro del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directorio del script actual
CARPETA_DOCS = os.path.join(BASE_DIR, "docs")  # Ruta de la carpeta "docs"

# Lista para almacenar los DataFrames
archivos_unidos = []

# Buscar archivos .xls en la carpeta "docs"
for archivo in os.listdir(CARPETA_DOCS):
    if archivo.endswith(".xls"):
        ruta_archivo = os.path.join(CARPETA_DOCS, archivo)
        print(f"Procesando: {ruta_archivo}")  # Mensaje para ver qué archivos se están uniendo
        
        # Leer el archivo .xls
        df = pd.read_excel(ruta_archivo, engine="xlrd")
        
        # Agregar una columna con el nombre del archivo para identificar el origen de los datos
        df["Archivo_Origen"] = archivo
        
        archivos_unidos.append(df)

# Concatenar todos los DataFrames en uno solo
df_final = pd.concat(archivos_unidos, ignore_index=True)

# Guardar el archivo combinado en la carpeta "output"
ARCHIVO_SALIDA = os.path.join(BASE_DIR, "output", "Archivos_Unidos.xlsx")
df_final.to_excel(ARCHIVO_SALIDA, index=False, engine="openpyxl")

print(f"[✔] Archivos combinados exitosamente en: {ARCHIVO_SALIDA}")
