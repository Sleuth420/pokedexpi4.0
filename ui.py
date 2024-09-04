import tkinter as tk
from views import menu_view, pokedex_view, detail_view, favourites_view
from data_manager import PokemonDataManager
import logging


class PokedexApp:
    def __init__(self, master):
        self.master = master
        logging.debug("Initializing PokedexApp")

        # Initialize the data manager
        self.data_manager = PokemonDataManager()

        # Store view instances
        self.views = {}
        self.current_view = None

        # Display the initial view
        self.show_view("MenuView")

    def show_view(self, view_name, *args):
        """Switches between different views in the application."""
        logging.debug(f"Switching to view: {view_name}")

        # Hide the current view if it exists
        if self.current_view:
            self.current_view.pack_forget()
            self.current_view.unbind_keys()  # Unbind keys from the current view

        # Create the view instance if it doesn't exist
        if view_name not in self.views:
            if view_name == "MenuView":
                self.views["MenuView"] = menu_view.MenuView(self.master, self)
            elif view_name == "PokedexView":
                self.views["PokedexView"] = pokedex_view.PokedexView(self.master, self.data_manager, self)
            elif view_name == "DetailView":
                self.views["DetailView"] = detail_view.DetailView(self.master, self.data_manager, *args, self)
            elif view_name == "FavouritesView":
                self.views["FavouritesView"] = favourites_view.FavouritesView(self.master, self.data_manager, self)
            else:
                logging.error(f"Error: View '{view_name}' not found.")
                return

        # Display the selected view and bind its keys
        self.current_view = self.views[view_name]
        self.current_view.pack(fill=tk.BOTH, expand=True)
        self.current_view.bind_keys()  # Bind keys for the new view
