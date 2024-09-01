import os
from PIL import ImageFont

# --- Screen Configuration ---
SCREEN_WIDTH = 240
SCREEN_HEIGHT = 320
RESIZABLE_WIDTH = True
RESIZABLE_HEIGHT = True
FULLSCREEN = False

# --- Default Theme ---
DEFAULT_THEME = "plastik"  # black or plastik

# --- Database ---
DATABASE_FILE = os.path.join("data", "pokedex.db")

# --- API ---
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"

# --- Font ---
FONT_NAME = "Pokemon_Classic.ttf"
FONT_PATH = os.path.join("assets", FONT_NAME)
FONT_SIZE = 12
FONT = (FONT_NAME, FONT_SIZE)  # Default font tuple

# --- Fallback Font ---
FALLBACK_FONT = ("Arial", FONT_SIZE)


# --- Error Handling ---
def get_font():
    """Attempts to load the Pokémon font, falls back to default if not found."""
    try:
        return ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except OSError:
        print("WARNING: Pokemon font not found. Using default font.")
        return FALLBACK_FONT
