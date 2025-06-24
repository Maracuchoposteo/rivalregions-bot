from rival_regions_wrapper.middleware import LocalAuthentication
from rival_regions_wrapper.wrapper import ResourceState, War
import time, os, logging
from telegram import Bot
from telegram.error import TelegramError
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# Configuración de Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
BLOQUE_ID = 2148
CHECK_INTERVAL = 3600

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)

# Autenticación en Rival Regions
auth = LocalAuthentication()
auth.set_credentials(os.getenv("RR_EMAIL"), os.getenv("RR_PASSWORD"), "email")

def get_data():
    info = {"fronteras": [], "revoluciones": [], "habitantes": []}
    estados = auth.get(f'blocs/info/{BLOQUE_ID}')  # o el endpoint correcto para tu bloque

    for state in estados['states']:
        # Obtener población
        pop = ResourceState(auth, state).info('citizens')['amount']
        info["habitantes"].append(f"👥 {state}: {pop} habitantes")

        # Obtener conflictos
        wars = War(auth, state).list_active()
        if wars:
            info["revoluciones"].append(f"⚔️ {state}: {len(wars)} conflicto(s) activo(s)")

        # Fronteras (si está soportado por la API)
        border = auth.get(f'country/{state}/borders')
        status = "✅ abierta" if border['open'] else "🚧 cerrada"
        info["fronteras"].append(f"🌐 {state}: frontera {status}")

    return info

# … (mismo servidor HTTP y bucle)

