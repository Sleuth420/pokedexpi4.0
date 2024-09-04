import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import logging
import os


class MenuView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        logging.debug("Initializing MenuView")
        self.master = master
        self.app = app
        self.menu_buttons = []

        # Create a frame for the logo and menu buttons
        self.frame = ttk.Frame(self)
        self.frame.pack()

        self.create_logo()
        self.create_menu_buttons()

        # Set initial focus to the first button
        self.menu_buttons[0].focus()
        self.selected_button_index = 0

    def create_logo(self):
        """Creates and displays the Pokedex logo."""
        logging.debug("Creating logo in MenuView")
        logo_path = os.path.join("assets", "pokedex_logo.png")
        try:
            logo_img = Image.open(logo_path)
            logging.debug(f"Opened logo image: {logo_path}")
            logo_img = logo_img.resize((200, 80), Image.Resampling.LANCZOS)
            logging.debug("Resized logo image to 200x80 pixels")
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logging.debug("Created PhotoImage from logo")

            self.logo_label = tk.Label(self.frame, image=self.logo_photo)
            logging.debug("Created logo label with PhotoImage")
            self.logo_label.pack(pady=(20, 10))
            logging.debug("Displayed logo in a label")

        except FileNotFoundError:
            logging.error(f"Error: Image not found at '{logo_path}'")
            # You can add error handling here, like displaying a message

        except Exception as e:
            logging.exception(f"An unexpected error occurred while creating the logo: {e}")
            # You can add error handling here as well

    def create_menu_buttons(self):
        """Creates the buttons for the menu options."""
        logging.debug("Creating menu buttons in MenuView")
        menu_options = [
            {"text": "Pokédex", "command": self.show_pokedex},
            {"text": "Favourites", "command": self.show_favorites},
            {"text": "Profile", "command": self.show_profile},
            {"text": "Settings", "command": self.show_settings}
        ]

        for option in menu_options:
            button = ttk.Button(
                self,
                text=option["text"],
                command=option["command"]
            )
            button.pack(pady=5, fill=tk.X, padx=20)
            self.menu_buttons.append(button)
            logging.debug(f"Created and packed menu button: {option['text']}")

    def show_pokedex(self):
        """Shows the PokedexView."""
        logging.debug("Showing PokedexView from MenuView")
        self.app.show_view("PokedexView")

    def show_favorites(self):
        """Shows the FavoritesView."""
        logging.debug("Showing FavouritesView from MenuView")
        self.app.show_view("FavouritesView")

    def show_profile(self):
        """Shows the ProfileView."""
        logging.debug("Showing ProfileView from MenuView")
        self.app.show_view("ProfileView")

    def show_settings(self):
        """Shows the SettingsView."""
        logging.debug("Showing SettingsView from MenuView")
        self.app.show_view("SettingsView")

    def handle_up(self, event):
        """Handles the Up arrow key press."""
        logging.debug("Navigating up in MenuView")
        self.selected_button_index = (self.selected_button_index - 1) % len(self.menu_buttons)
        self.menu_buttons[self.selected_button_index].focus()

    def handle_down(self, event):
        """Handles the Down arrow key press."""
        logging.debug("Navigating down in MenuView")
        self.selected_button_index = (self.selected_button_index + 1) % len(self.menu_buttons)
        self.menu_buttons[self.selected_button_index].focus()

    def handle_right(self, event):
        """Handles the Right arrow key press (same as select)."""
        logging.debug("Handling right arrow (select) in MenuView")
        self.handle_select()

    def handle_select(self, event=None):
        """Handles the Enter/Return key press to invoke the selected button."""
        logging.debug("Handling select (Enter/Return) key in MenuView")
        self.menu_buttons[self.selected_button_index].invoke()

    def bind_keys(self):
        """Binds navigation keys to the MenuView."""
        logging.debug("Binding navigation keys in MenuView")
        self.master.bind("<Up>", self.handle_up)
        self.master.bind("<Down>", self.handle_down)
        self.master.bind("<Right>", self.handle_right)
        self.master.bind("<Return>", self.handle_select)
        print("Keys bound in MenuView")  # Debugging print statement

    def unbind_keys(self):
        """Unbinds navigation keys from the MenuView."""
        logging.debug("Unbinding navigation keys in MenuView")
        self.master.unbind("<Up>")
        self.master.unbind("<Down>")
        self.master.unbind("<Right>")
        self.master.unbind("<Return>")
        print("Keys unbound in MenuView")  # Debugging print statement
