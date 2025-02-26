import os
import pandas as pd
import asyncio
import aiohttp
import logging
from datetime import datetime
import sys
 
# Forzar UTF-8 para evitar errores con emojis
sys.stdout.reconfigure(encoding="utf-8")
 
# 📂 Definir Directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
 
# 📌 Crear carpetas si no existen
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
 
# 📌 Configuración de logging
log_filename = os.path.join(LOGS_DIR, datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log")
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
 
# 📌 Parámetros de Procesamiento
BATCH_SIZE = 8000  # Máximo 8,000 registros por archivo
CONCURRENT_REQUESTS = 10  # Limitar concurrencia para no sobrecargar
semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
 
failed_requests = []
 
# 📌 Configuración del cURL
BASE_URL = "https://algoliabycarlos--siman.myvtex.com/_v/catalog/"
COOKIE_HEADER = "janus_sid=7dec2dbc-293c-454c-a1cf-a807299ab175"
 
### 🔥 1️⃣ UNIR ARCHIVOS Y GENERAR SOLO CURLs ###
print("📥 Leyendo archivos de `docs/`...")
 
# Leer todos los archivos XLS en `docs/`
xls_files = [os.path.join(DOCS_DIR, f) for f in os.listdir(DOCS_DIR) if f.endswith(".xls")]
df_list = [pd.read_excel(f) for f in xls_files]
 
# Unir todos los archivos en un solo DataFrame
df = pd.concat(df_list, ignore_index=True)
 
# Eliminar duplicados basado en la columna "_ProductId (Not changeable)" (SKU)
df = df.drop_duplicates(subset=["_ProductId (Not changeable)"])
 
# Generar SOLO la lista de cURLs
df["curl"] = df["_ProductId (Not changeable)"].apply(lambda sku: f"curl --location --request GET '{BASE_URL}{sku}' --header 'Cookie: {COOKIE_HEADER}'")
 
print(f"✅ Procesados {len(df)} SKUs únicos.")
 
# Dividir en archivos de 8,000 registros
num_batches = (len(df) // BATCH_SIZE) + 1
batch_files = []
 
for i in range(num_batches):
    batch_df = df.iloc[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
    if not batch_df.empty:
        file_name = os.path.join(OUTPUT_DIR, f"output_{i+1}.csv")
        batch_df["curl"].to_csv(file_name, index=False, header=False)  # Solo guarda los cURLs en TXT
        batch_files.append(file_name)
        print(f"✅ Archivo guardado: {file_name}")
 
print("\n✅ Todos los archivos han sido generados y están listos para procesar.")
 
### 🔥 2️⃣ PROCESAR ARCHIVOS EN LOTES DE 2 EN 2 ###
 
async def fetch(session, url, line_number, file_path):
    """Ejecuta una petición HTTP basada en la URL."""
    async with semaphore:
        try:
            async with session.get(url, timeout=10) as response:
                status = response.status
                logging.info(f"Línea {line_number}: ✅ PETICIÓN: {url} | CÓDIGO: {status}")
                print(f"[{file_path}] Línea {line_number}: [OK] {url} -> {status}")
                return (line_number, url, status)
        except Exception as e:
            logging.error(f"Línea {line_number}: [ERROR] {url} -> {str(e)}")
            print(f"[{file_path}] Línea {line_number}: [ERROR] {url} -> {e}")
 
            failed_requests.append((line_number, url, str(e)))  # Save failed request
 
            return (line_number, url, "ERROR")
 
async def process_file(file_path):
    """Procesa un archivo TXT de 8,000 registros."""
    print("\n✅ Todos los archivos han sido procesados.")
    with open(file_path, "r", encoding="utf-8") as f:
        curl_commands = f.readlines()
 
    tasks = []
    async with aiohttp.ClientSession() as session:
        for i, curl_command in enumerate(curl_commands, start=1):
            url = curl_command.split(" ")[4].strip("'")  # Extraer URL del cURL
            tasks.append(fetch(session, url, i, file_path.split("\\")[-1]))
 
        results = await asyncio.gather(*tasks)
 
    # Guardar resultados en CSV
    result_file = file_path.replace(".txt", "_resultados.csv")
    pd.DataFrame(results, columns=["Línea", "URL", "Código"]).to_csv(result_file, index=False)
    print(f"✅ Resultados guardados en: {result_file}")
 
async def process_batches():
    """Procesa archivos en lotes de 2 en 2."""
    for i in range(0, len(batch_files), 2):
        batch = batch_files[i:i+2]  # Seleccionar 2 archivos a la vez
        print(f"\n🚀 Procesando archivos: {batch}")
 
        tasks = [process_file(file) for file in batch]
        await asyncio.gather(*tasks)
 
     # Save failed requests after processing all batches
    if failed_requests:
        failed_csv = os.path.join(OUTPUT_DIR, "failed_requests.csv")
        pd.DataFrame(failed_requests, columns=["URL"]).to_csv(failed_csv, index=False)
        print(f"\n⚠️ Fallos guardados en: {failed_csv}")
 
    print("\n✅ Todos los archivos han sido procesados.")
 
# Ejecutar el procesamiento en lotes
asyncio.run(process_batches())
 
print("\n🚀 ¡Proceso completado automáticamente! 🚀")