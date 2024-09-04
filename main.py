import logging
from ui import PokedexApp
import tkinter as tk
import config
from ttkthemes import ThemedTk

# Configure logging
logging.basicConfig(filename='pokedex.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

if __name__ == "__main__":
    try:
        # Start the Pokedex application
        logging.debug("Starting PokedexApp")

        # Create the themed main window
        root = ThemedTk(theme=config.DEFAULT_THEME)
        root.title("Pokedex")
        root.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        root.resizable(config.RESIZABLE_WIDTH, config.RESIZABLE_HEIGHT)

        # Create the Pokedex App instance
        app = PokedexApp(root)
        root.app = app  # Store PokedexApp as an attribute of root

        # Start the Tkinter event loop
        root.mainloop()

    except Exception as e:
        logging.error(f"An error occurred during application startup: {e}")
