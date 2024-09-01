import tkinter as tk
from tkinter import ttk
import logging
import os

class FavouritesView(tk.Frame):
    def __init__(self, master, data_manager, app):  # Add app parameter
        super().__init__(master)
        logging.debug("Initializing FavouritesView")
        self.master = master
        self.data_manager = data_manager
        self.app = app  # Store the PokedexApp instance

        # Create the Treeview for the Favourites List
        self.favourites_tree = ttk.Treeview(
            self,
            columns=("ID", "Name"),
            show="headings",
            style="Custom.Treeview"  # Assuming you have a custom style defined
        )
        self.favourites_tree.heading("ID", text="ID")
        self.favourites_tree.heading("Name", text="Name")
        self.favourites_tree.column("ID", width=40)
        self.favourites_tree.column("Name", width=160)
        self.favourites_tree.pack(fill=tk.BOTH, expand=True)

        # Bind events for navigation and selection
        self.favourites_tree.bind("<<TreeviewSelect>>", self.on_pokemon_select)
        self.favourites_tree.bind("<Up>", self.move_selection_up)
        self.favourites_tree.bind("<Down>", self.move_selection_down)
        self.bind("<Return>", self.show_pokemon_details)
        self.bind("<BackSpace>", self.return_to_menu)

        # Load and display the initial Favourites
        self.load_favourites_data()

    def load_favourites_data(self):
        """Loads favourite Pokémon data into the Treeview."""
        self.favourites_tree.delete(*self.favourites_tree.get_children())
        pokemon_list = self.data_manager.get_all_pokemon()
        for pokemon in pokemon_list:
            if pokemon[13] == 1:  # Check if the Pokémon is a favourite
                self.favourites_tree.insert("", tk.END, values=(pokemon[0], pokemon[1]))

    def on_pokemon_select(self, event):
        """Handles selection of a Pokémon in the Treeview."""
        selection = self.favourites_tree.selection()
        if selection:
            item = self.favourites_tree.item(selection[0])
            pokemon_id = int(item['values'][0])
            # self.show_pokemon_details(pokemon_id)  # Removed, handled by <Return> binding

    def move_selection_up(self, event):
        """Moves the selection up in the Treeview."""
        selection = self.favourites_tree.selection()
        if selection:
            parent = self.favourites_tree.parent(selection[0])
            if parent:
                siblings = self.favourites_tree.get_children(parent)
                index = siblings.index(selection[0])
                if index > 0:
                    self.favourites_tree.selection_set(siblings[index - 1])

    def move_selection_down(self, event):
        """Moves the selection down in the Treeview."""
        selection = self.favourites_tree.selection()
        if selection:
            parent = self.favourites_tree.parent(selection[0])
            if parent:
                siblings = self.favourites_tree.get_children(parent)
                index = siblings.index(selection[0])
                if index < len(siblings) - 1:
                    self.favourites_tree.selection_set(siblings[index + 1])

    def show_pokemon_details(self, event=None):  # Removed pokemon_id parameter
        """Displays detailed information about the selected Pokémon."""
        selection = self.favourites_tree.selection()
        if selection:
            item = self.favourites_tree.item(selection[0])
            pokemon_id = int(item['values'][0])
            self.app.show_view("DetailView", pokemon_id)  # Use self.app to show DetailView

    def return_to_menu(self, event=None):
        """Returns to the main menu."""
        self.app.show_view("MenuView")  # Use self.app to show MenuView