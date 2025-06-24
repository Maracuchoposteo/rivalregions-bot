import requests
import time
import logging
import os
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# === CONFIGURACIÓN ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
USER_ID = int(os.environ.get("USER_ID"))
BLOQUE_ID = 2148
CHECK_INTERVAL = 3600  # 1 hora

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

# === FUNCIONES DEL BOT ===
def get_bloque_data():
    url = f"https://rivalregions.com/#blocs/show/{BLOQUE_ID}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')

        info = {"fronteras": [], "revoluciones": [], "habitantes": []}
        estados = soup.select(".list-group-item")

        for estado in estados:
            nombre = estado.select_one("b").text.strip()
            texto = estado.get_text(separator=" ").lower()

            if "border open" in texto:
                frontera = f"🌐 {nombre}: Frontera ABIERTA"
            elif "border closed" in texto:
                frontera = f"🚧 {nombre}: Frontera CERRADA"
            else:
                frontera = f"❓ {nombre}: Estado desconocido"
            info["fronteras"].append(frontera)

            if "revolution" in texto or "front" in texto:
                info["revoluciones"].append(f"⚔️ {nombre} tiene actividad militar")

            if "people:" in texto:
                try:
                    cantidad = texto.split("people:")[1].strip().split()[0]
                    info["habitantes"].append(f"👥 {nombre}: {cantidad} habitantes")
                except:
                    pass

        return info

    except Exception as e:
        logging.error(f"Error al obtener datos del bloque: {e}")
        return None

def generar_mensaje(info):
    msg = "📊 *Informe del Bloque*\n\n"
    msg += "🛂 *Fronteras:*\n" + "\n".join(info["fronteras"]) + "\n\n"
    msg += "🔥 *Frentes/Revoluciones:*\n"
    msg += "\n".join(info["revoluciones"]) if info["revoluciones"] else "Sin actividad militar\n\n"
    msg += "\n👥 *Población:*\n" + "\n".join(info["habitantes"])
    return msg

def enviar_mensaje(texto):
    try:
        bot.send_message(chat_id=USER_ID, text=texto, parse_mode="Markdown")
    except TelegramError as e:
        logging.error(f"Error al enviar mensaje: {e}")

def bot_loop():
    while True:
        logging.info("⏳ Verificando bloque...")
        datos = get_bloque_data()
        if datos:
            mensaje = generar_mensaje(datos)
            enviar_mensaje(mensaje)
        time.sleep(CHECK_INTERVAL)

# === SERVIDOR HTTP PARA MANTENER EL SERVICIO ACTIVO ===
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot en ejecucion")

# === INICIAR BOT Y SERVIDOR ===
if __name__ == "__main__":
    Thread(target=bot_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), KeepAliveHandler).serve_forever()
