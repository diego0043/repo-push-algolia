import os
import csv

# Definir rutas en base a la estructura del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directorio del script actual
TXT_FILE_PATH = os.path.join(BASE_DIR,   "data", "skus.txt")  # Ruta del archivo TXT
OUTPUT_DIR = os.path.join(BASE_DIR, "output")  # Carpeta de salida
CSV_FILE_PATH = os.path.join(OUTPUT_DIR, "output.csv")  # Ruta del archivo CSV

# Crear carpeta 'output' si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# URL base para construir las peticiones
BASE_URL = "https://algoliabycarlos--siman.myvtex.com/_v/catalog/"

# Cookie necesaria para la autenticación (ajusta según necesidad)
COOKIE_HEADER = "janus_sid=7dec2dbc-293c-454c-a1cf-a807299ab175"

# Leer los SKUs desde el archivo TXT
with open(TXT_FILE_PATH, "r", encoding="utf-8") as file:
    skus = [line.strip() for line in file.readlines() if line.strip()]

# Crear el archivo CSV con la estructura esperada
with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
        
    # Generar cada línea de cURL y escribir en el CSV
    for sku in skus:
        curl_command = f"curl --location --request GET '{BASE_URL}{sku}' --header 'Cookie: {COOKIE_HEADER}'"
        writer.writerow([curl_command])

print(f"✅ Archivo CSV generado correctamente en: {CSV_FILE_PATH}")
