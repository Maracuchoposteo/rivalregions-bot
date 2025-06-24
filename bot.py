import os
import re
import time
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from telegram.error import TelegramError

# === CONFIGURACIÓN ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
USER_ID = int(os.environ.get("USER_ID"))
CHECK_INTERVAL = 3600  # cada 1 hora

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

# === LISTA DE BLOQUES MONITOREADOS ===
bloques_monitoreados = set()

# === FUNCIONES DEL BOT ===

def get_bloque_data(bloque_id):
    url = f"https://m.rivalregions.com/#blocs/show/{bloque_id}"
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
        logging.error(f"Error al obtener datos del bloque {bloque_id}: {e}")
        return None

def generar_mensaje(info, bloque_id):
    msg = f"📊 *Informe del Bloque {bloque_id}*\n\n"
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
        logging.info("⏳ Verificando bloques...")
        for bloque_id in bloques_monitoreados:
            datos = get_bloque_data(bloque_id)
            if datos:
                mensaje = generar_mensaje(datos, bloque_id)
                enviar_mensaje(mensaje)
        time.sleep(CHECK_INTERVAL)

# === COMANDOS DE TELEGRAM ===

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        await update.message.reply_text("No estás autorizado.")
        return

    if not context.args:
        await update.message.reply_text("❌ Envía el enlace del bloque. Ejemplo:\n/register https://m.rivalregions.com/#blocs/show/1234")
        return

    match = re.search(r'/blocs/show/(\d+)', context.args[0])
    if match:
        bloque_id = int(match.group(1))
        if bloque_id in bloques_monitoreados:
            await update.message.reply_text(f"🔄 El bloque {bloque_id} ya está en monitoreo.")
        else:
            bloques_monitoreados.add(bloque_id)
            await update.message.reply_text(f"✅ Bloque {bloque_id} añadido al monitoreo.")
    else:
        await update.message.reply_text("❌ Enlace inválido.")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        await update.message.reply_text("No estás autorizado.")
        return

    if not context.args:
        await update.message.reply_text("❌ Envía el enlace del bloque. Ejemplo:\n/delete https://m.rivalregions.com/#blocs/show/1234")
        return

    match = re.search(r'/blocs/show/(\d+)', context.args[0])
    if match:
        bloque_id = int(match.group(1))
        if bloque_id in bloques_monitoreados:
            bloques_monitoreados.remove(bloque_id)
            await update.message.reply_text(f"🗑️ Bloque {bloque_id} eliminado del monitoreo.")
        else:
            await update.message.reply_text(f"⚠️ El bloque {bloque_id} no está en monitoreo.")
    else:
        await update.message.reply_text("❌ Enlace inválido.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        await update.message.reply_text("No estás autorizado.")
        return

    if not bloques_monitoreados:
        await update.message.reply_text("📭 No hay bloques actualmente en monitoreo.")
        return

    mensaje = "📋 *Bloques monitoreados:*\n\n"
    for bloque in bloques_monitoreados:
        enlace = f"https://m.rivalregions.com/#blocs/show/{bloque}"
        mensaje += f"🔹 Bloque {bloque} - [Ver Bloque]({enlace})\n"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

# === SERVIDOR HTTP PARA RENDER ===
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo.")

# === INICIAR BOT ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("status", status))

    Thread(target=bot_loop, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: HTTPServer(('0.0.0.0', port), KeepAliveHandler).serve_forever(), daemon=True).start()

    app.run_polling()

if __name__ == "__main__":
    main()
