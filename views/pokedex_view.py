import tkinter as tk
from tkinter import ttk
import logging
import os


class PokedexView(tk.Frame):
    def __init__(self, master, data_manager, app):  # Add app parameter
        super().__init__(master)
        logging.debug("Initializing PokedexView")
        self.master = master
        self.data_manager = data_manager
        self.app = app  # Store the PokedexApp instance
        self.pokemon_list = self.data_manager.get_all_pokemon()
        self.selected_pokemon_index = 0
        self.favorite_pokemon = []  # List to store favorite Pokémon IDs

        # Create UI elements
        self.create_widgets()

        # Bind navigation keys
        self.master.bind("<Up>", self.handle_up)
        self.master.bind("<Down>", self.handle_down)
        self.master.bind("<Left>", self.handle_left)
        self.master.bind("<Right>", self.handle_right)
        self.master.bind("<Return>", self.handle_select)
        self.master.bind("<BackSpace>", self.handle_back)

        # Set initial focus
        self.pokemon_listbox.focus_set()

    def create_widgets(self):
        """Creates the widgets for the PokedexView."""
        logging.debug("Creating widgets in PokedexView")

        # --- Search/Filter Entry ---
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self, textvariable=self.search_var)
        self.search_entry.pack(pady=5)

        # --- Pokemon Listbox ---
        self.pokemon_listbox = tk.Listbox(self, width=30, height=20, font=("Pokemon_Classic", 10))
        self.pokemon_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate the listbox with Pokémon names
        for pokemon in self.pokemon_list:
            self.pokemon_listbox.insert(tk.END, pokemon[1])  # Insert Pokémon name

        # Bind selection event
        self.pokemon_listbox.bind("<<ListboxSelect>>", self.on_pokemon_select)

        # --- On-Screen Keyboard ---
        from .keyboard_view import OnScreenKeyboard  # Import here instead
        self.keyboard = OnScreenKeyboard(self, self.search_var, exit_command=self.exit_keyboard)
        self.keyboard.pack(pady=5)  # Initially hidden

        # Bind focus events to show/hide the keyboard
        self.search_entry.bind("<FocusIn>", self.show_keyboard)
        self.search_entry.bind("<FocusOut>", self.hide_keyboard)

        # Trace the search variable for changes
        self.search_var.trace("w", self.update_search)

    def show_keyboard(self, event):
        """Show the virtual keyboard when the search box is focused."""
        self.keyboard.pack()
        self.keyboard.focus_set()  # Set focus to the keyboard

    def hide_keyboard(self, event):
        """Hide the virtual keyboard when the search box loses focus."""
        self.keyboard.pack_forget()

    def exit_keyboard(self):
        """Exits the keyboard and sets focus back to the search entry."""
        self.search_entry.focus_set()
        self.keyboard.pack_forget()

    def on_pokemon_select(self, event):
        """Handles selection of a Pokémon in the listbox."""
        selection = self.pokemon_listbox.curselection()
        if selection:
            self.selected_pokemon_index = selection[0]

    def toggle_favorite(self):
        """Toggles the favorite status of the selected Pokémon."""
        pokemon_id = self.pokemon_list[self.selected_pokemon_index][0]
        is_favorite = self.data_manager.get_pokemon_by_id(pokemon_id)[13]  # Get current favorite status

        # Toggle the favorite status
        new_favorite_status = not is_favorite
        self.data_manager.update_favorite_status(pokemon_id, new_favorite_status)

        # Update the UI
        if new_favorite_status:
            self.favorite_pokemon.append(pokemon_id)
        else:
            self.favorite_pokemon.remove(pokemon_id)

    def handle_up(self, event):
        """Handles the Up arrow key press."""
        if self.keyboard.winfo_ismapped():
            self.keyboard.handle_up(event)
        else:
            if self.selected_pokemon_index > 0:
                self.selected_pokemon_index -= 1
                self.pokemon_listbox.selection_clear(0, tk.END)
                self.pokemon_listbox.selection_set(self.selected_pokemon_index)
                self.pokemon_listbox.see(self.selected_pokemon_index)
            else:
                self.search_entry.focus_set()  # Set focus to the search box

    def handle_down(self, event):
        """Handles the Down arrow key press."""
        if self.keyboard.winfo_ismapped():
            self.keyboard.handle_down(event)
        else:
            if self.selected_pokemon_index < len(self.pokemon_list) - 1:
                self.selected_pokemon_index += 1
                self.pokemon_listbox.selection_clear(0, tk.END)
                self.pokemon_listbox.selection_set(self.selected_pokemon_index)
                self.pokemon_listbox.see(self.selected_pokemon_index)

    def handle_left(self, event):
        """Handles the Left arrow key press (go back)."""
        if self.keyboard.winfo_ismapped():
            self.keyboard.handle_left(event)
        else:
            self.handle_back()

    def handle_right(self, event):
        """Handles the Right arrow key press (toggle favorite)."""
        if self.keyboard.winfo_ismapped():
            self.keyboard.handle_right(event)
        else:
            self.toggle_favorite()

    def handle_select(self, event=None):
        """Handles the Enter/Return key press to view Pokémon details."""
        if self.keyboard.winfo_ismapped():
            self.keyboard.handle_enter(event)
        else:
            selected_pokemon_id = self.pokemon_list[self.selected_pokemon_index][0]
            self.app.show_view("DetailView", selected_pokemon_id)  # Use self.app to access PokedexApp

    def handle_back(self, event=None):
        """Handles the Backspace key press to go back to the menu."""
        if self.keyboard.winfo_ismapped():
            self.keyboard.handle_backspace(event)
        else:
            self.app.show_view("MenuView")

    def update_search(self, *args):
        """Updates the listbox based on the search text."""
        search_text = self.search_var.get()

        # Input validation: Allow only alphanumeric characters and spaces
        search_text = "".join(c for c in search_text if c.isalnum() or c.isspace())
        self.search_var.set(search_text)  # Update the search_var with the validated text

        # Filter the pokemon_list based on search_text
        filtered_pokemon = [
            pokemon
            for pokemon in self.pokemon_list
            if search_text.lower() in pokemon[1].lower()
            or (pokemon[2] and search_text.lower() in pokemon[2].lower())
            or (pokemon[3] and search_text.lower() in pokemon[3].lower())
        ]

        # Clear the listbox and repopulate with filtered results
        self.pokemon_listbox.delete(0, tk.END)
        for pokemon in filtered_pokemon:
            pokemon_text = f"{pokemon[0]:>3} - {pokemon[1]:<12} {'★' if pokemon[13] else ''}"
            self.pokemon_listbox.insert(tk.END, pokemon_text)