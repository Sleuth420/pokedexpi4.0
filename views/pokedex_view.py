import tkinter as tk
from tkinter import ttk
import logging
import platform
import os


class PokedexView(tk.Frame):
    def __init__(self, master, data_manager, app):
        super().__init__(master)
        logging.debug("Initializing PokedexView")
        self.master = master
        self.data_manager = data_manager
        self.app = app

        self.pokemon_list = []
        self.filtered_pokemon = []
        self.selected_index = 0
        self.favorite_toggling = False
        self.current_offset = 0
        self.batch_size = 50
        self.search_active = False
        self.loading_more = False
        self.search_term = tk.StringVar()

        self.create_widgets()
        self.load_pokemon_batch()
        self.update_selection()

        # Bind search bar to filtering (debounced for performance)
        self.search_term.trace("w", lambda *args: self.master.after(200, self.filter_pokemon_list))

        # Set initial focus to the Listbox
        self.pokemon_listbox.focus_set()

    def create_widgets(self):
        logging.debug("Creating widgets in PokedexView")

        # Search bar with clear button
        search_frame = ttk.Frame(self)
        search_frame.pack()

        self.search_bar = ttk.Entry(search_frame, textvariable=self.search_term)
        self.search_bar.pack(side=tk.LEFT)
        self.search_bar.bind("<Return>", self.on_search_enter)

        self.clear_button = ttk.Button(search_frame, text="Clear", command=self.clear_search)
        self.clear_button.pack(side=tk.LEFT)

        self.pokemon_listbox = tk.Listbox(self, width=20, activestyle='none')
        self.pokemon_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        # Result count label
        self.result_count_label = ttk.Label(self, text="")
        self.result_count_label.pack()

        # Bind events
        self.pokemon_listbox.bind('<<ListboxSelect>>', self.on_pokemon_select)
        self.pokemon_listbox.bind("<Down>", self.on_listbox_scroll)

    def load_pokemon_batch(self):
        """Loads a batch of Pokémon and appends to the list."""
        if not self.loading_more:
            self.loading_more = True
            self.master.unbind("<Down>")  # Temporarily disable Down arrow

            # Load more Pokémon asynchronously
            self.after(100, self._load_pokemon_batch_async)

    def _load_pokemon_batch_async(self):
        """Loads a batch of Pokémon asynchronously."""
        try:
            new_pokemon = self.data_manager.get_all_pokemon(
                limit=self.batch_size, offset=self.current_offset
            )
            self.pokemon_list.extend(new_pokemon)
            if self.search_active:
                self.filter_pokemon_list()
            else:
                self.populate_listbox()
            self.current_offset += self.batch_size
        except Exception as e:
            logging.error(f"Error loading Pokemon batch: {e}")
            # Display an error message to the user (implementation needed)
        finally:
            self.master.after(
                0, lambda: self.master.bind("<Down>", self.handle_down)
            )  # Re-enable Down arrow
            self.loading_more = False

    def populate_listbox(self, pokemon_list=None):
        """Populates the listbox with the given pokemon_list or the full list if None."""
        logging.debug("Populating listbox in PokedexView")
        self.pokemon_listbox.delete(0, tk.END)

        if pokemon_list is None:
            pokemon_list = self.pokemon_list

        for pokemon in pokemon_list:
            pokemon_text = f"{pokemon[0]:>3} - {pokemon[1]:<12} {'★' if pokemon[13] else ''}"
            self.pokemon_listbox.insert(tk.END, pokemon_text)

        self.update_result_count()

    def filter_pokemon_list(self):
        """Filters the Pokemon list based on the search term and updates the Listbox."""
        search_term = self.search_term.get().lower()
        self.filtered_pokemon = []
        if search_term:
            self.search_active = True
            for pokemon in self.pokemon_list:
                # Check if the search term matches either the name or type
                if (
                        search_term in pokemon[1].lower()
                        or (pokemon[2] and search_term in pokemon[2].lower())
                        or (pokemon[3] and search_term in pokemon[3].lower())
                ):
                    self.filtered_pokemon.append(pokemon)
        else:
            self.search_active = False

        self.populate_listbox(
            self.filtered_pokemon if self.search_active else None
        )

    def clear_search(self):
        """Clears the search bar and resets the Pokemon list."""
        self.search_term.set("")
        self.search_active = False
        self.populate_listbox()

    def on_search_enter(self, event=None):
        """Handles the Enter key press on the search bar."""
        self.show_keyboard()  # Implement this method for your custom keyboard

    def show_keyboard(self):
        """Placeholder for your custom on-screen keyboard logic.

        This method should:
        - Create and display your custom keyboard UI.
        - Handle input from the keyboard.
        - Update the search bar text (`self.search_term`) accordingly.
        """
        # TODO: Implement your custom keyboard logic here
        pass

    def on_listbox_scroll(self, *args):
        """Checks if scrolled near the bottom and loads more Pokémon if needed."""
        if (
                self.pokemon_listbox.yview()[1] > 0.9
                and not self.search_active
                and not self.loading_more
        ):
            self.load_pokemon_batch()

    def handle_up(self, event):
        """Handles the Up arrow key press."""
        logging.debug("Navigating up in PokedexView")
        if self.pokemon_listbox.size() > 0:
            if self.pokemon_listbox.curselection():
                current_selection = self.pokemon_listbox.curselection()[0]
                if current_selection == 0:
                    self.search_bar.focus_set()
                    self.pokemon_listbox.selection_clear(0, tk.END)  # Clear listbox selection
                else:
                    self.selected_index = max(
                        0, (self.selected_index - 1) % self.pokemon_listbox.size()
                    )
                    self.update_selection()
            else:
                # No selection, so move focus to the search bar
                self.search_bar.focus_set()
                self.pokemon_listbox.selection_clear(0, tk.END)  # Clear listbox selection

    def handle_down(self, event):
        """Handles the Down arrow key press."""
        logging.debug("Navigating down in PokedexView")
        if self.pokemon_listbox.curselection():  # Only move down if listbox has focus
            self.selected_index = (self.selected_index + 1) % self.pokemon_listbox.size()
            self.update_selection()
            # Check if we need to load more Pokémon
            self.on_listbox_scroll()
        elif self.search_bar.focus_get() or self.clear_button.focus_get():
            # If focus is on search bar or clear button, move focus to the listbox
            self.pokemon_listbox.focus_set()
            self.selected_index = 0  # Select the first item
            self.update_selection()

    def handle_left(self, event):
        """Handles the Left arrow key press. Navigates from clear button to search bar."""
        logging.debug("Handling left arrow in PokedexView")
        if self.clear_button.focus_get():
            self.search_bar.focus_set()

    def handle_right(self, event):
        """Handles the Right arrow key press."""
        logging.debug("Handling right arrow in PokedexView")
        if self.pokemon_listbox.curselection():
            # Toggle favorite if the listbox has focus
            self.toggle_favorite()
        elif self.search_bar.focus_get():
            # Move to the clear button if the search bar has focus
            self.clear_button.focus_set()

    def handle_select(self, event=None):
        """Handles the Enter/Return key press (or 'A' button) to show Pokemon details."""
        logging.debug("Handling selection in PokedexView")
        if self.pokemon_listbox.curselection():
            self.selected_index = self.pokemon_listbox.curselection()[0]
            selected_pokemon_id = self.get_selected_pokemon_id()
            self.master.app.show_view("DetailView", selected_pokemon_id)

    def handle_back(self, event=None):
        """Handles the Backspace key press (or 'B' button) to go back to the menu."""
        logging.debug("Going back to MenuView from PokedexView")
        self.app.show_view("MenuView")

    def update_selection(self):
        """Updates the visual selection in the listbox."""
        logging.debug(f"Updating selection in PokedexView to index: {self.selected_index}")
        self.pokemon_listbox.selection_clear(0, tk.END)
        if 0 <= self.selected_index < self.pokemon_listbox.size():
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
        if self.pokemon_listbox.curselection():
            selected_index = self.pokemon_listbox.curselection()[0]
            pokemon_id = self.get_selected_pokemon_id()

            is_favorite = not self.get_selected_pokemon()[13]
            self.data_manager.update_favorite_status(pokemon_id, is_favorite)

            # Reload Pokemon list from the database
            if self.search_active:
                self.filter_pokemon_list()  # Reload filtered list
            else:
                self.pokemon_list = self.data_manager.get_all_pokemon()  # Reload full list
                self.populate_listbox()

            # Restore the selection
            self.selected_index = selected_index
            self.update_selection()

    def get_selected_pokemon(self):
        """Gets the currently selected Pokemon data."""
        if self.search_active:
            return self.filtered_pokemon[self.selected_index]
        else:
            return self.pokemon_list[self.selected_index]

    def get_selected_pokemon_id(self):
        """Gets the ID of the currently selected Pokemon."""
        return self.get_selected_pokemon()[0]

    def update_result_count(self):
        """Updates the label with the number of search results."""
        if self.search_active:
            count = len(self.filtered_pokemon)
            self.result_count_label.config(
                text=f"Found {count} Pokémon"
            )
        else:
            self.result_count_label.config(text="")

    def bind_keys(self):
        """Binds navigation keys to the PokedexView."""
        logging.debug("Binding navigation keys in PokedexView")
        self.master.bind("<Up>", self.handle_up)
        self.master.bind("<Down>", self.handle_down)
        self.master.bind("<Left>", self.handle_left)
        self.master.bind("<Right>", self.handle_right)
        self.master.bind("<Return>", self.handle_select)
        self.master.bind("<a>", self.handle_select)  # Bind 'A' button to select
        self.master.bind("<BackSpace>", self.handle_back)
        self.master.bind("<b>", self.handle_back)  # Bind 'B' button to back
        print("Keys bound in PokedexView")  # Debugging print statement

    def unbind_keys(self):
        """Unbinds navigation keys from the PokedexView."""
        logging.debug("Unbinding navigation keys in PokedexView")
        self.master.unbind("<Up>")
        self.master.unbind("<Down>")
        self.master.unbind("<Left>")
        self.master.unbind("<Right>")
        self.master.unbind("<Return>")
        self.master.unbind("<a>")
        self.master.unbind("<BackSpace>")
        self.master.unbind("<b>")
        print("Keys unbound in PokedexView")  # Debugging print statement
