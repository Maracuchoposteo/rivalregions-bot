import requests
import time
import logging
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError

# === CONFIGURACIÓN ===
BOT_TOKEN = "os.environ.get(7960061018:AAFbA3DQOCVV5naImpj0mX8LVq1koLQ4rHI)"
USER_ID = int(os.environ.get(5239354695))  # sin comillas si es número
BLOQUE_ID = 2148  # ID del bloque a monitorear
CHECK_INTERVAL = 3600  # 1 hora

# === INICIAR LOGGING ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)

# === FUNCIONES ===

def get_bloque_data():
    url = f"https://m.rivalregions.com/#blocs/show/{BLOQUE_ID}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')

        info = {"fronteras": [], "revoluciones": [], "habitantes": []}
        estados = soup.select(".list-group-item")

        for estado in estados:
            nombre = estado.select_one("b").text.strip()
            texto = estado.get_text(separator=" ").lower()

            # Fronteras
            if "border open" in texto:
                frontera = f"🌐 {nombre}: Frontera ABIERTA"
            elif "border closed" in texto:
                frontera = f"🚧 {nombre}: Frontera CERRADA"
            else:
                frontera = f"❓ {nombre}: Estado desconocido"
            info["fronteras"].append(frontera)

            # Revoluciones / Frentes
            if "revolution" in texto or "front" in texto:
                info["revoluciones"].append(f"⚔️ {nombre} tiene actividad militar")

            # Habitantes
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

# === BUCLE PRINCIPAL ===

if __name__ == "__main__":
    while True:
        logging.info("⏳ Verificando bloque...")
        datos = get_bloque_data()
        if datos:
            mensaje = generar_mensaje(datos)
            enviar_mensaje(mensaje)
        time.sleep(CHECK_INTERVAL)
          
