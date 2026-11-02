#!/usr/bin/env python3
"""
YouTube Subscriptions Migrator (Takeout -> New Account)
Automatiza la suscripción a canales de YouTube a partir del CSV de Google Takeout
utilizando Playwright y un navegador real (Brave / Chrome).
"""

import argparse
import csv
import os
import platform
import random
import select
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DEFAULT_CSV = "subscriptions.csv"
DEFAULT_USER_DATA = "./.browser_data"
DONE_FILE = "subscribed_channels.txt"

def find_browser_executable(preferred="auto"):
    """Localiza el ejecutable de Brave o Chrome según el sistema operativo."""
    os_name = platform.system()
    
    candidates = []
    if preferred in ("auto", "brave"):
        if os_name == "Darwin":
            candidates.extend([
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
            ])
        elif os_name == "Linux":
            candidates.extend([
                "/usr/bin/brave-browser",
                "/usr/bin/brave",
                "/snap/bin/brave",
            ])
        elif os_name == "Windows":
            candidates.extend([
                os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            ])

    if preferred in ("auto", "chrome"):
        if os_name == "Darwin":
            candidates.extend([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            ])
        elif os_name == "Linux":
            candidates.extend([
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ])
        elif os_name == "Windows":
            candidates.extend([
                os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ])

    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None

def load_channels(csv_path):
    if not os.path.exists(csv_path):
        print(f"❌ Error: No se encuentra el archivo CSV en '{csv_path}'.")
        print("   Asegúrate de copiar tu archivo 'subscriptions.csv' en este directorio o indicar la ruta con --csv.")
        return []

    channels = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("Channel Id") or row.get("channel_id") or row.get("Channel ID")
            url = row.get("Channel Url") or row.get("channel_url") or row.get("Channel URL")
            title = row.get("Channel Title") or row.get("channel_title") or row.get("Channel Name")
            if url:
                channels.append({
                    "id": cid.strip() if cid else "",
                    "url": url.strip(),
                    "title": title.strip() if title else ""
                })
    return channels

def load_completed_ids():
    if not os.path.exists(DONE_FILE):
        return set()
    with open(DONE_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def mark_completed(channel_id):
    if not channel_id:
        return
    with open(DONE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{channel_id}\n")

def is_logged_in(page):
    try:
        if "youtube.com" not in page.url:
            return False
        
        # Presencia del botón o imagen del avatar en la barra superior
        avatar = page.locator("#avatar-btn, button#avatar-btn, ytd-topbar-menu-button-renderer img#avatar")
        if avatar.count() > 0 and avatar.first.is_visible():
            return True
            
        # Comprobar si el botón de inicio de sesión no existe pero sí el masthead
        signin = page.locator("a[href*='ServiceLogin'], a[aria-label*='Sign in'], a[aria-label*='Acceder']")
        masthead = page.locator("ytd-masthead")
        if masthead.count() > 0 and masthead.first.is_visible() and signin.count() == 0:
            return True
    except Exception:
        pass
    return False

def check_stdin():
    if not sys.stdin.isatty():
        return False
    try:
        r, _, _ = select.select([sys.stdin], [], [], 0)
        if r:
            sys.stdin.readline()
            return True
    except Exception:
        pass
    return False

def wait_for_login(page, max_seconds=300):
    print("\n" + "="*65)
    print("👉 Abre la ventana del navegador e INICIA SESIÓN en tu cuenta de YouTube.")
    print("   El script detectará automáticamente el inicio de sesión.")
    print("   (También puedes pulsar [ENTER] en esta terminal cuando estés dentro)")
    print("="*65 + "\n")
    
    start_time = time.time()
    last_print = 0
    while time.time() - start_time < max_seconds:
        if check_stdin():
            print("\n✅ Confirmación manual recibida.")
            return True

        if is_logged_in(page):
            print("\n✅ ¡Sesión detectada automáticamente!")
            return True

        time.sleep(1.5)
        elapsed = int(time.time() - start_time)
        if elapsed - last_print >= 15:
            last_print = elapsed
            remaining = int(max_seconds - elapsed)
            print(f"⏳ Esperando login... ({remaining}s restantes)")
            
    print("⚠️ Tiempo límite de espera agotado.")
    return False

def subscribe_to_channel(page, channel):
    url = channel["url"]
    title = channel["title"] or url
    print(f"\n📺 Canal: {title}")
    print(f"   URL: {url}")
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"  ❌ Error cargando la página: {e}")
        return False

    page.wait_for_timeout(2500)
    
    # 1. Comprobar si ya está suscrito
    already_subscribed_selectors = [
        "button[aria-label*='Subscribed']",
        "button[aria-label*='Suscrito']",
        "button[aria-label*='Cancelar suscripción']",
        "button[aria-label*='Unsubscribe']",
        "yt-button-shape:has-text('Subscribed')",
        "yt-button-shape:has-text('Suscrito')",
        "ytd-subscribe-button-renderer[subscribed]",
    ]
    
    for sel in already_subscribed_selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                print(f"  ℹ️ Ya estás suscrito a este canal.")
                return True
        except Exception:
            pass

    # 2. Buscar botón de suscripción
    subscribe_selectors = [
        "ytd-subscribe-button-renderer button:has-text('Suscribirse')",
        "ytd-subscribe-button-renderer button:has-text('Subscribe')",
        "button[aria-label*='Suscribirse a']",
        "button[aria-label*='Subscribe to']",
        "button[aria-label*='Suscribirme']",
        "yt-button-shape button:has-text('Suscribirse')",
        "yt-button-shape button:has-text('Subscribe')",
        "ytd-subscribe-button-renderer button",
    ]

    btn = None
    for sel in subscribe_selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                btn = loc.first
                break
        except Exception:
            pass

    if not btn:
        print(f"  ⚠️ No se encontró el botón de suscripción (revisar URL o estado del canal).")
        return False

    try:
        btn.click()
        page.wait_for_timeout(2000)
        print(f"  🎉 ¡Suscripción realizada!")
        return True
    except Exception as e:
        print(f"  ❌ Error al pulsar el botón: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Migrador de suscripciones de YouTube mediante CSV de Google Takeout y Playwright."
    )
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV, help="Ruta al archivo CSV de suscripciones (defecto: subscriptions.csv).")
    parser.add_argument("--limit", type=int, default=1, help="Número de canales a procesar en esta ejecución (defecto: 1 para modo prueba).")
    parser.add_argument("--all", action="store_true", help="Procesar TODOS los canales pendientes.")
    parser.add_argument("--delay-min", type=float, default=3.0, help="Espera mínima entre suscripciones en segundos (defecto: 3.0).")
    parser.add_argument("--delay-max", type=float, default=6.0, help="Espera máxima entre suscripciones en segundos (defecto: 6.0).")
    parser.add_argument("--browser", choices=["auto", "brave", "chrome", "chromium"], default="auto", help="Navegador preferido (defecto: auto).")
    parser.add_argument("--user-data-dir", type=str, default=DEFAULT_USER_DATA, help="Directorio de perfil del navegador (defecto: ./.browser_data).")
    args = parser.parse_args()

    channels = load_channels(args.csv)
    if not channels:
        return

    completed_ids = load_completed_ids()
    remaining_channels = [c for c in channels if c["id"] not in completed_ids]

    print(f"📊 Estado actual:")
    print(f"   - Total canales en CSV: {len(channels)}")
    print(f"   - Canales ya procesados: {len(completed_ids)}")
    print(f"   - Canales pendientes: {len(remaining_channels)}")

    if not remaining_channels:
        print("✨ ¡Todos los canales ya han sido procesados previamente!")
        return

    channels_to_process = remaining_channels if args.all else remaining_channels[:args.limit]
    mode_text = f"TODOS los canales restantes ({len(channels_to_process)})" if args.all else f"MODO PRUEBA (1 canal: {channels_to_process[0]['title']})"
    print(f"🎯 Modo de ejecución: {mode_text}\n")

    executable_path = None
    if args.browser != "chromium":
        executable_path = find_browser_executable(args.browser)

    if executable_path:
        print(f"🌐 Navegador detectado: {executable_path}")
    else:
        print("🌐 Navegador: Chromium gestionado por Playwright.")

    user_data_path = Path(args.user_data_dir).resolve()
    user_data_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        launch_args = {
            "user_data_dir": str(user_data_path),
            "headless": False,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
            "no_viewport": True,
        }
        if executable_path:
            launch_args["executable_path"] = executable_path

        context = p.chromium.launch_persistent_context(**launch_args)
        page = context.pages[0] if context.pages else context.new_page()

        print("Navegando a YouTube...")
        page.goto("https://www.youtube.com", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Aceptar cookies si aparece banner
        try:
            consent_btn = page.locator("button:has-text('Aceptar todo'), button:has-text('Accept all'), button:has-text('Rechazar todo'), button:has-text('Reject all')")
            if consent_btn.count() > 0 and consent_btn.first.is_visible():
                consent_btn.first.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

        # Comprobar o esperar inicio de sesión
        if not is_logged_in(page):
            if not wait_for_login(page, max_seconds=300):
                print("❌ No se inició sesión. Cerrando navegador...")
                context.close()
                return
        else:
            print("✅ Sesión ya activa en este perfil de navegador.")

        print("\n🚀 Comenzando proceso de suscripción...")
        for idx, channel in enumerate(channels_to_process, 1):
            print(f"\n[{idx}/{len(channels_to_process)}]", end=" ")
            success = subscribe_to_channel(page, channel)
            if success:
                mark_completed(channel["id"])
            
            # Pausa aleatoria entre canales si quedan más por procesar
            if idx < len(channels_to_process):
                delay = random.uniform(args.delay_min, args.delay_max)
                print(f"⏳ Pausa de seguridad de {delay:.1f}s...")
                time.sleep(delay)

        print("\n" + "="*65)
        if not args.all and len(remaining_channels) > len(channels_to_process):
            print(f"🏁 Prueba completada ({len(channels_to_process)} canal procesado).")
            print("Si la prueba ha funcionado, ejecuta el resto con:")
            print("  python subscribe.py --all")
        else:
            print("🎉 ¡Todos los canales seleccionados han sido procesados!")
        print("="*65)

        page.wait_for_timeout(3000)
        context.close()

if __name__ == "__main__":
    main()
