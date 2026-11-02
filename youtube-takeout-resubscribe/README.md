# YouTube Takeout Resubscribe 📺

Script en Python con **Playwright** para migrar automáticamente tus suscripciones de YouTube a una nueva cuenta a partir del archivo CSV generado por **Google Takeout**.

A diferencia de soluciones que usan la API oficial de YouTube (la cual tiene cuotas diarias muy estrictas que solo permiten suscribirte a unos pocos canales al día), este script automatiza la interacción en un navegador real (**Brave**, **Chrome** o **Chromium**), permitiéndote iniciar sesión manualmente y suscribirte con pausas seguras anti-bloqueo.

---

## 🚀 Características

- **Inicio de sesión interactivo y seguro**: Levanta una ventana de navegador real para que hagas login manualmente en tu cuenta nueva de Google/YouTube.
- **Detección automática de sesión**: El script detecta por sí solo cuando terminas el login.
- **Persistencia de sesión**: Guarda el perfil en un directorio local (`.browser_data/`). No necesitas volver a loguearte en ejecuciones posteriores.
- **Modo prueba por defecto**: Procesa primero 1 solo canal para verificar que todo funciona antes de lanzar la lista completa.
- **Reanudable (Idempotente)**: Guarda los canales completados en `subscribed_channels.txt`. Si se interrumpe, continuará donde lo dejó.
- **Pausas humanas**: Intervalos aleatorios configurables entre suscripciones para evitar bloqueos por spam o rate limits de YouTube.
- **Multiplataforma**: Compatible con macOS, Linux y Windows.

---

## 📋 Requisitos Previos

- **Python 3.8 o superior**.
- Navegador **Brave Browser** o **Google Chrome** instalado en tu sistema (recomendado para evitar las restricciones de Google sobre navegadores automatizados).

---

## 📦 Paso 1: Exportar tus suscripciones con Google Takeout

1. Accede a [Google Takeout](https://takeout.google.com/) con tu **cuenta antigua** (la que tiene las suscripciones).
2. Haz clic en **"Desmarcar todo"**.
3. Baja hasta la categoría **"YouTube y YouTube Music"** y márcala.
4. Pulsa sobre el botón **"Se han incluido todos los datos de YouTube"**:
   - Pulsa **"Desmarcar todo"**.
   - Marca únicamente la opción **"suscripciones"** (`subscriptions`).
   - Pulsa **"Aceptar"**.
5. Haz clic en **"Siguiente paso"**, selecciona entrega por correo o descarga directa y pulsa **"Crear exportación"**.
6. Descarga y descomprime el archivo `.zip`.
7. En la carpeta `Takeout/YouTube and YouTube Music/subscriptions/` encontrarás el archivo **`subscriptions.csv`**.
8. Copia `subscriptions.csv` dentro de la carpeta de este script.

---

## 🛠️ Paso 2: Instalación del entorno

Abre una terminal en la carpeta de este proyecto y sigue estos pasos:

### 1. Crear y activar el entorno virtual (`.venv`):

**En macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**En Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

*(Opcional si no tienes Brave ni Chrome instalados y quieres usar el Chromium interno de Playwright):*
```bash
playwright install chromium
```

---

## 💻 Paso 3: Ejecución

### 1. Prueba inicial (1 canal)

Por seguridad, la ejecución por defecto procesa **solo 1 canal**:

```bash
python subscribe.py
```

**Flujo de ejecución:**
1. Se abrirá una ventana de navegador.
2. Si es la primera vez, verás la página de YouTube. Haz clic en **"Acceder"** e inicia sesión con tu **nueva cuenta**.
3. En cuanto inicies sesión, el script detectará el avatar/perfil y te avisará por la terminal.
4. Navegará al primer canal del CSV y pulsará el botón de suscripción.
5. Verás en la terminal el mensaje de confirmación y el navegador se cerrará guardando tu sesión.

### 2. Suscribirse a todos los canales restantes

Una vez verificada la prueba, lanza el script con el flag `--all`:

```bash
python subscribe.py --all
```

El script omitirá los canales a los que ya te hayas suscrito previamente y continuará con el resto, aplicando una pausa de 3 a 6 segundos entre cada uno.

---

## ⚙️ Opciones avanzadas de línea de comandos

Puedes personalizar la ejecución con los siguientes argumentos:

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `--all` | `False` | Procesa **todos** los canales pendientes del CSV. |
| `--limit N` | `1` | Procesa como máximo `N` canales pendientes. |
| `--csv RUTA` | `subscriptions.csv` | Ruta alternativa al archivo CSV de suscripciones. |
| `--delay-min SEGS` | `3.0` | Segundos mínimos de espera entre suscripciones. |
| `--delay-max SEGS` | `6.0` | Segundos máximos de espera entre suscripciones. |
| `--browser TIPO` | `auto` | Navegador a usar: `auto`, `brave`, `chrome` o `chromium`. |
| `--user-data-dir RUTA` | `./.browser_data` | Directorio donde se guardan cookies y sesión. |

### Ejemplos:

Procesar 10 canales con pausas más largas:
```bash
python subscribe.py --limit 10 --delay-min 5.0 --delay-max 10.0
```

Indicar una ruta personalizada para el CSV:
```bash
python subscribe.py --all --csv /ruta/a/mi_takeout/subscriptions.csv
```

---

## 📁 Archivos generados localmente

- `.browser_data/`: Perfil de navegador persistente con tu sesión iniciada de Google/YouTube.
- `subscribed_channels.txt`: Lista con los IDs de los canales a los que ya se ha suscrito con éxito. Si quieres empezar de cero, simplemente borra este archivo.

---

## ❓ Preguntas Frecuentes y Solución de Problemas

#### Google bloquea el inicio de sesión diciendo "Navegador no seguro"
Esto ocurre cuando se utiliza un Chromium automatizado estándar. Este script utiliza por defecto **Brave** o **Chrome** con el flag `--disable-blink-features=AutomationControlled` para que Google lo identifique como una sesión normal de usuario. Asegúrate de tener instalado Brave o Google Chrome.

#### ¿Qué pasa si se corta la conexión o cierro la ventana a mitad del proceso?
No pasa nada. El script registra cada canal completado en `subscribed_channels.txt`. La próxima vez que ejecutes `python subscribe.py --all`, continuará automáticamente por el siguiente canal pendiente.

#### ¿Puedo aumentar la velocidad quitando las pausas?
No es recomendable. YouTube detecta patrones de suscripciones demasiado rápidas e inhabilita temporalmente el botón de suscripción en tu cuenta. El rango de 3 a 6 segundos por defecto es seguro y fiable.
