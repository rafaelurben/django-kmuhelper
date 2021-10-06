from rich import print

from kmuhelper import settings

def log(string, *args):
    print("[deep_pink4][KMUHelper startup.py][/] -", string, *args)

# Set up database settings

log("Started... DEBUG is", settings.DEBUG)

try:
    log("Setting up settings...")
    settings.setup_settings()
    log("Set up settings!")
except Exception as error:
    log("Error while setting up settings:", type(error), error)

log("Ended.")
