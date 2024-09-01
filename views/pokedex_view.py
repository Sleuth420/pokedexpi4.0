import tkinter as tk
from tkinter import ttk
import config
from PIL import Image, ImageTk
import io
import requests
import logging


class PokedexView(tk.Frame):
    def __init__(self, master, data_manager, app):
        super().__init__(master)
        logging.debug("Initializing PokedexView")
        self.master = master
        self.data_manager = data_manager
        self.app = app

        self.pokemon_list = self.data_manager.get_all_pokemon()
        self.selected_index = 0
        self.favorite_toggling = False

        self.create_widgets()
        self.populate_listbox()
        self.update_selection()

        # Bind navigation keys
        self.master.bind("<Up>", self.handle_up)
        self.master.bind("<Down>", self.handle_down)
        self.master.bind("<Right>", self.handle_right)
        self.master.bind("<Return>", self.handle_select)
        self.master.bind("<BackSpace>", self.handle_back)

    def create_widgets(self):
        logging.debug("Creating widgets in PokedexView")

        self.pokemon_listbox = tk.Listbox(
            self,
            width=20,
            activestyle='none'
        )
        self.pokemon_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        # Bind events
        self.pokemon_listbox.bind('<<ListboxSelect>>', self.on_pokemon_select)
        self.bind("<f>", self.toggle_favorite)  # Bind "F" key for favorite toggle

    def populate_listbox(self):
        """Populates the listbox, adding a visual indicator for favorite Pokémon."""
        logging.debug("Populating listbox in PokedexView")
        self.pokemon_listbox.delete(0, tk.END)  # Clear the listbox
        for pokemon in self.pokemon_list:
            pokemon_text = f"{pokemon[0]:>3} - {pokemon[1]:<12} {'★' if pokemon[13] else ''}"
            self.pokemon_listbox.insert(tk.END, pokemon_text)

    def handle_up(self, event):
        """Handles the Up arrow key press."""
        logging.debug("Navigating up in PokedexView")
        if self.pokemon_listbox.size() > 0:
            if self.favorite_toggling:
                self.favorite_toggling = False
            else:
                self.selected_index = (self.selected_index - 1) % self.pokemon_listbox.size()
            self.update_selection()

    def handle_down(self, event):
        """Handles the Down arrow key press."""
        logging.debug("Navigating down in PokedexView")
        if self.pokemon_listbox.size() > 0:
            if self.favorite_toggling:
                self.favorite_toggling = False
            else:
                self.selected_index = (self.selected_index + 1) % self.pokemon_listbox.size()
            self.update_selection()

    def handle_left(self, event):
        """Handles the Left arrow key press (no action)."""
        pass  # No horizontal movement in the listbox

    def handle_right(self, event):
        """Handles the Right arrow key press to toggle favorites."""
        logging.debug("Handling right arrow (favorite toggle) in PokedexView")
        self.toggle_favorite()

    def handle_select(self, event=None):
        """Handles the Enter/Return key press to show Pokemon details."""
        logging.debug("Handling selection in PokedexView")
        if self.pokemon_listbox.curselection():
            self.selected_index = self.pokemon_listbox.curselection()[0]
            selected_pokemon_id = self.pokemon_list[self.selected_index][0]
            self.master.app.show_view("DetailView", selected_pokemon_id)

    def handle_back(self, event=None):
        """Handles the Backspace key press to go back to the menu."""
        logging.debug("Going back to MenuView from PokedexView")
        self.app.show_view("MenuView")  # Corrected: using self.app

    def update_selection(self):
        """Updates the visual selection in the listbox."""
        logging.debug(f"Updating selection in PokedexView to index: {self.selected_index}")
        self.pokemon_listbox.selection_clear(0, tk.END)
        self.pokemon_listbox.selection_set(self.selected_index)
        self.pokemon_listbox.see(self.selected_index)

    def on_pokemon_select(self, event):
        """Handles the <<ListboxSelect>> event."""
        logging.debug("Handling listbox selection event in PokedexView")
        if self.pokemon_listbox.curselection():
            self.selected_index = self.pokemon_listbox.curselection()[0]

    def toggle_favorite(self, event=None):
        """Toggles the favorite status of the selected Pokemon."""
        logging.debug("Toggling favorite status in PokedexView")
        self.favorite_toggling = True
        if self.pokemon_listbox.curselection():
            selected_index = self.pokemon_listbox.curselection()[0]
            selected_pokemon = self.pokemon_list[selected_index]
            pokemon_id = selected_pokemon[0]

            # Toggle favorite status in the database
            is_favorite = not selected_pokemon[13]
            self.data_manager.update_favorite_status(pokemon_id, is_favorite)

            # Update the Pokemon list and refresh the listbox
            self.pokemon_list = self.data_manager.get_all_pokemon()
            self.populate_listbox()  # Refresh the listbox to show updated favorites

            # Reselect the Pokemon and update the display
            self.selected_index = selected_index
            self.update_selection()
