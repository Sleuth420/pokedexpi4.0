import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import requests
import logging


class DetailView(tk.Frame):
    def __init__(self, master, data_manager, pokemon_id, app):  # Add app parameter
        super().__init__(master)
        logging.debug(f"Initializing DetailView for Pokemon ID: {pokemon_id}")

        self.master = master
        self.data_manager = data_manager
        self.pokemon_id = pokemon_id
        self.app = app  # Store the PokedexApp instance

        # Fetch Pokemon data
        self.pokemon_data = self.data_manager.get_pokemon_by_id(self.pokemon_id)
        self.is_favorite = self.pokemon_data[13]

        # Create UI elements
        self.create_widgets()

        # Load and display the sprite
        self.load_and_display_sprite()

        # Bind navigation keys
        self.master.bind("<Up>", self.handle_up)
        self.master.bind("<Down>", self.handle_down)
        self.master.bind("<Right>", self.handle_right)
        self.master.bind("<BackSpace>", self.handle_back)

        self.current_detail_index = 0  # Start at the top of the details

    def create_widgets(self):
        """Creates the widgets for the DetailView."""
        logging.debug("Creating widgets in DetailView")

        # --- Main Frame for Scrolling ---
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Canvas for Scrollable Content ---
        self.detail_canvas = tk.Canvas(main_frame)
        self.detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Scrollbar ---
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.detail_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_canvas.configure(yscrollcommand=self.scrollbar.set)

        # --- Content Frame ---
        self.content_frame = ttk.Frame(self.detail_canvas)
        self.detail_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # --- Title ---
        title_label = ttk.Label(self.content_frame, text=f"{self.pokemon_data[1].capitalize()} - #{self.pokemon_id} {'★' if self.is_favorite else ''}", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        # --- Sprite ---
        self.sprite_label = tk.Label(self.content_frame, bg="gray")
        self.sprite_label.pack()

        # --- Stats ---
        self.stats_labels = []  # Store labels for navigation
        stats_frame = ttk.Frame(self.content_frame)
        stats_frame.pack(pady=5)

        stats = ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"]
        for i in range(6):
            stat_label = ttk.Label(stats_frame, text=f"{stats[i]}: {self.pokemon_data[i + 4]}")
            stat_label.grid(row=i, column=0, sticky="w")
            self.stats_labels.append(stat_label)  # Add labels to the list

        # --- Description ---
        self.description_label = ttk.Label(self.content_frame, text=f"Description:\n{self.pokemon_data[12]}", wraplength=200)
        self.description_label.pack(pady=10)
        self.stats_labels.append(self.description_label)  # Add description label for navigation

        # Configure the Canvas to update the scroll region
        self.content_frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event):
        """Update the scroll region when the content frame is resized."""
        self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))

    def load_and_display_sprite(self):
        """Loads and displays the Pokemon sprite."""
        logging.debug("Loading and displaying sprite in DetailView")
        try:
            sprite_url = self.pokemon_data[10]  # Assuming sprite URL is at index 10
            if sprite_url:
                response = requests.get(sprite_url)
                response.raise_for_status()
                sprite_image = Image.open(io.BytesIO(response.content))
                self.sprite_photo = ImageTk.PhotoImage(sprite_image.resize((100, 100), Image.Resampling.LANCZOS))
                self.sprite_label.config(image=self.sprite_photo, bg="white")
            else:
                self.sprite_label.config(text="No Sprite", bg="gray")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error loading sprite: {e}")
            self.sprite_label.config(text="Error", bg="gray")

    def handle_up(self, event):
        """Handles the Up arrow key press for detail navigation."""
        logging.debug("Navigating up in DetailView")
        if self.current_detail_index > 0:
            self.current_detail_index = (self.current_detail_index - 1) % len(self.stats_labels)
            self.stats_labels[self.current_detail_index].focus()
            self.detail_canvas.yview_scroll(-1, "units")  # Scroll up one unit

    def handle_down(self, event):
        """Handles the Down arrow key press for detail navigation."""
        logging.debug("Navigating down in DetailView")
        if self.current_detail_index < len(self.stats_labels) - 1:
            self.current_detail_index = (self.current_detail_index + 1) % len(self.stats_labels)
            self.stats_labels[self.current_detail_index].focus()
            self.detail_canvas.yview_scroll(1, "units")  # Scroll down one unit

    def handle_right(self, event):
        """Handles the Right arrow key press for toggling favorites."""
        logging.debug("Handling right arrow (favorite toggle) in DetailView")
        self.toggle_favorite()

    def handle_back(self, event):
        """Handles the Backspace key press to return to the PokedexView."""
        logging.debug("Going back to PokedexView from DetailView")
        self.app.show_view("PokedexView")  # Corrected: using self.app

    def toggle_favorite(self):
        """Toggles the favorite status of the Pokemon."""
        logging.debug("Toggling favorite status in DetailView")
        self.is_favorite = not self.is_favorite
        self.data_manager.update_favorite_status(self.pokemon_id, self.is_favorite)

        # Update the title label to reflect the favorite status
        title_label = ttk.Label(self, text=f"{self.pokemon_data[1].capitalize()} - #{self.pokemon_id} {'★' if self.is_favorite else ''}", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
