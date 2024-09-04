import tkinter as tk

class CustomKeyboard(tk.Toplevel):
    def __init__(self, master, target_entry):
        super().__init__(master)
        self.title("Keyboard")
        self.target_entry = target_entry  # The Entry widget to receive input
        self.shift_on = False

        self.create_keyboard_layout()

    def create_keyboard_layout(self):
        # Create key frames
        letter_frame1 = tk.Frame(self)
        letter_frame1.pack()
        letter_frame2 = tk.Frame(self)
        letter_frame2.pack()
        number_frame = tk.Frame(self)
        number_frame.pack()
        special_frame = tk.Frame(self)
        special_frame.pack()

        # Letter keys (row 1)
        for letter in "ABCDEFGHIJ":
            button = tk.Button(
                letter_frame1,
                text=letter,
                command=lambda l=letter: self.append_to_entry(l),
            )
            button.pack(side=tk.LEFT)

        # Letter keys (row 2)
        for letter in "KLMNOPQRSTUVWXYZ":
            button = tk.Button(
                letter_frame2,
                text=letter,
                command=lambda l=letter: self.append_to_entry(l),
            )
            button.pack(side=tk.LEFT)

        # Number keys
        for number in "0123456789":
            button = tk.Button(
                number_frame,
                text=number,
                command=lambda n=number: self.append_to_entry(n),
            )
            button.pack(side=tk.LEFT)

        # Special keys
        shift_button = tk.Button(special_frame, text="Shift", command=self.toggle_shift)
        shift_button.pack(side=tk.LEFT)
        backspace_button = tk.Button(
            special_frame, text="Backspace", command=self.backspace
        )
        backspace_button.pack(side=tk.LEFT)
        space_button = tk.Button(
            special_frame, text="Space", command=lambda: self.append_to_entry(" ")
        )
        space_button.pack(side=tk.LEFT)
        enter_button = tk.Button(special_frame, text="Enter", command=self.enter_key)
        enter_button.pack(side=tk.LEFT)

    def append_to_entry(self, char):
        """Appends the given character to the target Entry widget."""
        if self.shift_on:
            char = char.upper()
        self.target_entry.insert(tk.END, char)

    def toggle_shift(self):
        """Toggles the Shift key state."""
        self.shift_on = not self.shift_on

    def backspace(self):
        """Removes the last character from the target Entry widget."""
        current_text = self.target_entry.get()
        self.target_entry.delete(len(current_text) - 1, tk.END)

    def enter_key(self):
        """Simulates pressing Enter in the target Entry widget."""
        self.target_entry.event_generate("<Return>")
        self.destroy()  # Close the keyboard
