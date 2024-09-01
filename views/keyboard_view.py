import tkinter as tk
from tkinter import ttk
import logging


class OnScreenKeyboard(tk.Frame):
    def __init__(self, master, textvariable, exit_command=None):
        super().__init__(master)
        logging.debug("Initializing OnScreenKeyboard")
        self.master = master
        self.textvariable = textvariable
        self.exit_command = exit_command  # Command to execute when exiting the keyboard

        self.key_rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", '\\'],
            ['SHIFT', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 'BACKSPACE'],
            ['SPACE', 'ENTER']
        ]
        self.current_row = 0
        self.current_col = 0
        self.shift_on = False
        self.focused_button = None  # Store the currently focused button

        self.create_keyboard()

    def create_keyboard(self):
        """Creates the on-screen keyboard buttons."""
        for row_index, row in enumerate(self.key_rows):
            row_frame = tk.Frame(self)
            row_frame.pack(pady=2)
            for col_index, key in enumerate(row):
                button = tk.Button(
                    row_frame,
                    text=key,
                    width=4,
                    command=lambda k=key: self.press_key(k),
                    highlightthickness=2,  # For focus visualization
                    highlightbackground="black",  # Default unfocused color
                    highlightcolor="blue"  # Focused color
                )
                button.grid(row=row_index, column=col_index, padx=2)
                button.bind("<FocusIn>", lambda e, b=button: self.on_focus(b))

        # Initial focus on the first key
        self.key_rows[self.current_row][self.current_col].focus_set()
        self.focused_button = self.key_rows[self.current_row][self.current_col]  # Set initial focused button

    def press_key(self, key):
        """Handles pressing a key on the on-screen keyboard."""
        if key == 'SHIFT':
            self.shift_on = not self.shift_on
            self.update_keyboard()
        elif key == 'BACKSPACE':
            self.textvariable.set(self.textvariable.get()[:-1])
        elif key == 'ENTER':
            if self.exit_command:
                self.exit_command()  # Execute the exit command if provided
        elif key == 'SPACE':
            self.textvariable.set(self.textvariable.get() + ' ')
        else:
            if self.shift_on:
                key = key.upper()
            self.textvariable.set(self.textvariable.get() + key)

    def update_keyboard(self):
        """Updates the keyboard key text based on shift state."""
        for row_index, row in enumerate(self.key_rows):
            for col_index, key in enumerate(row):
                if key.isalpha():  # Only update alphabetic keys
                    button = self.key_rows[row_index][col_index]
                    button.config(text=key.upper() if self.shift_on else key.lower())

    def on_focus(self, button):
        """Handles focus events on keyboard buttons."""
        if self.focused_button:
            self.focused_button.config(highlightbackground="black")  # Reset previous focus
        self.focused_button = button
        self.focused_button.config(highlightbackground="blue")  # Highlight current focus


    def handle_up(self, event):
        """Handles the Up arrow key press."""
        self.current_row = (self.current_row - 1) % len(self.key_rows)
        self.current_col = min(self.current_col, len(self.key_rows[self.current_row]) - 1)  # Adjust for shorter rows
        self.key_rows[self.current_row][self.current_col].focus_set()

    def handle_down(self, event):
        """Handles the Down arrow key press."""
        self.current_row = (self.current_row + 1) % len(self.key_rows)
        self.current_col = min(self.current_col, len(self.key_rows[self.current_row]) - 1)  # Adjust for shorter rows
        self.key_rows[self.current_row][self.current_col].focus_set()

    def handle_left(self, event):
        """Handles the Left arrow key press."""
        self.current_col = (self.current_col - 1) % len(self.key_rows[self.current_row])
        self.key_rows[self.current_row][self.current_col].focus_set()

    def handle_right(self, event):
        """Handles the Right arrow key press."""
        self.current_col = (self.current_col + 1) % len(self.key_rows[self.current_row])
        self.key_rows[self.current_row][self.current_col].focus_set()
