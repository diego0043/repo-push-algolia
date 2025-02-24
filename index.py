import os
import csv
import aiohttp
import asyncio
import logging
from datetime import datetime
import re
import sys

# Asegurar que la salida en Windows use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Definir rutas en base a la estructura del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directorio del script actual
CSV_FILE_PATH = os.path.join(BASE_DIR, "output", "output.csv")  # Ruta del CSV generado
LOGS_DIR = os.path.join(BASE_DIR, "logs")  # Carpeta para logs
RESULTS_CSV_PATH = os.path.join(LOGS_DIR, "resultados.csv")  # Archivo para guardar respuestas

# Crear carpeta 'logs' si no existe
os.makedirs(LOGS_DIR, exist_ok=True)

# Nombre del archivo de log con fecha y hora
log_filename = os.path.join(LOGS_DIR, datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log")

# Configuración de logging con UTF-8
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"  # 🔥 Evita errores de codificación en Windows/Linux
)

# Control de concurrencia para evitar bloqueos
CONCURRENT_REQUESTS = 10  # Reducido para evitar bloqueos
semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

def extract_url_and_header(curl_command):
    """Extrae la URL y el header 'Cookie' de un comando curl."""
    url_match = re.search(r"https?://[^\s']+", curl_command)
    header_match = re.search(r"Cookie:\s?([^\s']+)", curl_command)

    url = url_match.group(0) if url_match else None
    cookie = header_match.group(1) if header_match else None

    if not url or not cookie:
        return None, None  # Indicar que hay un error

    return url, {"Cookie": cookie}

async def fetch(session, curl_command, line_number):
    """Ejecuta una petición HTTP basada en el comando cURL del CSV."""
    async with semaphore:  # Limita la concurrencia
        try:
            url, headers = extract_url_and_header(curl_command)

            if not url or not headers:
                logging.error(f"Línea {line_number}: Error ❌ Comando inválido -> {curl_command}")
                print(f"Línea {line_number}: [ERROR] Comando inválido -> {curl_command}")
                return None

            async with session.get(url, headers=headers, timeout=15) as response:
                status = response.status
                result = (url, status)

                logging.info(f"Línea {line_number}: ✅ PETICIÓN: {url} | CÓDIGO: {status}")
                print(f"Línea {line_number}: [OK] {url} -> {status}")

                return result

        except Exception as e:
            logging.error(f"Línea {line_number}: Error ❌ {curl_command} -> {str(e)}")
            print(f"Línea {line_number}: [ERROR] {curl_command} -> {e}")
            return None

async def process_requests():
    """Maneja las solicitudes concurrentes leyendo desde el CSV y guarda los resultados."""
    tasks = []
    results = []
    total_lines = 0

    async with aiohttp.ClientSession() as session:
        with open(CSV_FILE_PATH, newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Saltar el encabezado

            for line_number, row in enumerate(reader, start=1):
                total_lines += 1
                if not row or len(row) == 0:  # Evitar filas vacías
                    continue

                curl_command = row[0].strip()  # Eliminar espacios en blanco extra
                if curl_command:  # Validar que no sea una línea vacía
                    task = fetch(session, curl_command, line_number)
                    tasks.append(task)

                if len(tasks) >= CONCURRENT_REQUESTS:
                    results.extend(await asyncio.gather(*tasks))
                    tasks = []

        if tasks:
            results.extend(await asyncio.gather(*tasks))

    # Guardar los resultados en un CSV
    with open(RESULTS_CSV_PATH, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["URL", "Código de Respuesta"])  # Encabezados
        writer.writerows(filter(None, results))  # Guardar solo respuestas válidas

    print(f"\n✅ Procesadas {total_lines} líneas del CSV")
    print(f"✅ Resultados guardados en: {RESULTS_CSV_PATH}")
    print(f"📝 Logs guardados en: {log_filename}")

# Ejecutar el script
asyncio.run(process_requests())
