import tkinter as tk
import random
import numpy as np
import pygame
from PIL import Image, ImageTk
import pandas as pd

# Global constants for the game
NAMES = ["Mihir Chhiber", "Michael Chun", "Jacky Teo", "Soh Lay Suan", "Ruiyi Lim", "Angela Kwek"]
DISPLAY_ITEMS = ["IPhone 16", "Dyson Fan", "Airtag"]

class SlotMachineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Slot Machine")
        # Set the entire Tkinter app window to be 25% smaller
        self.root.geometry("900x750") # Reduced by 25% from 1200x1000
        self.root.resizable(False, False) # Prevent window resizing to maintain layout integrity
        self.root.configure(bg="#202020") # Set a dark background for the root window

        # --- Load and resize background image ---
        # Attempt to load the background image 'sgx4.jpg'.
        # The image will be resized to fit the new 900x750 window.
        try:
            bg_image_raw = Image.open("sgx4.jpg")
            bg_image_resized = bg_image_raw.resize((900, 750), Image.LANCZOS) # High-quality resizing for new window size
            self.bg_photo = ImageTk.PhotoImage(bg_image_resized)
        except FileNotFoundError:
            print("Error: sgx4.jpg not found. Please ensure the image file is in the same directory.")
            # Fallback: if image not found, use a placeholder
            self.bg_photo = None
            self.root.configure(bg="darkgrey") # Set a fallback background color

        # Create a canvas to display the background image
        self.canvas_bg = tk.Canvas(root, width=900, height=750, highlightthickness=0) # Updated to new window size
        self.canvas_bg.pack(fill="both", expand=True) # Make it fill the entire root window
        if self.bg_photo:
            self.canvas_bg.create_image(0, 0, image=self.bg_photo, anchor="nw")
        else:
            # Draw a solid rectangle if the image couldn't be loaded
            self.canvas_bg.create_rectangle(0, 0, 900, 750, fill="darkgrey", outline="")


        # --- Initialize pygame mixer for sounds ---
        # Add error handling in case sound files are missing or pygame fails to initialize
        try:
            pygame.mixer.init()
            self.spin_sound = pygame.mixer.Sound("spin.wav")
            self.win_sound = pygame.mixer.Sound("win.wav")
        except pygame.error:
            print("Error: Pygame sounds could not be loaded. Ensure 'spin.wav' and 'win.wav' exist and are valid.")
            self.spin_sound = None # Set to None if sounds can't be loaded
            self.win_sound = None


        # --- Reel canvas for displaying spinning names (original size) ---
        # Calculate position to center it horizontally within the 900px window
        # And vertically align it with the slot machine's reel area on the background image
        reel_canvas_width = 300 # Adjusted width to better fit the middle box in the image
        reel_canvas_height = 247 # Adjusted height to better fit the middle box in the image
        reel_x = ((900 - reel_canvas_width) / 2)-5 # Centers the canvas horizontally
        reel_y = 315 # Adjusted Y position to align perfectly with the middle box in the image

        # Set the background of the reel canvas to a light grey that matches
        # the slot area in the 'sgx4.jpg' image, giving a "transparent" effect for the text.
        self.reel_canvas = tk.Canvas(root, width=reel_canvas_width, height=reel_canvas_height,
                                     bg="#dfc89a", # Light grey color to blend with the image slots
                                     highlightthickness=0) # Remove default border
        self.reel_canvas.place(x=reel_x, y=reel_y)

        # --- Scrollable item display and navigation buttons ---
        # Positioned to be within the black box area at the bottom of the slot machine image
        display_y = 665 # Adjusted Y position to fit within the black rectangle at the bottom

        self.display_index = 0 # Current index for DISPLAY_ITEMS

        self.display_label = tk.Label(root, text=DISPLAY_ITEMS[self.display_index],
                                      font=("Helvetica", 22, "bold"), # Slightly reduced font size
                                      fg="white", # White text for better visibility on black background
                                      bg="#222b2a", # Black background to match the image's black box
                                      relief="flat") # No border for a cleaner look
        self.display_label.place(relx=0.5, y=display_y, anchor="center") # Centered horizontally

        # Define common button styles for prev/next buttons
        button_font = ("Helvetica", 16, "bold") # Slightly reduced font size
        button_bg = "#222b2a" # Background color matching the black box
        button_fg = "#FFD700" # Gold color for the arrow symbols
        button_width = 3 # Compact width for buttons

        self.prev_button = tk.Button(root, text="⬅️", font=button_font, command=self.show_prev_item,
                                     bg=button_bg, fg=button_fg, width=button_width, relief="flat")
        # Place to the left of the centered display label, adjusted for new window size
        self.prev_button.place(x=290, y=display_y, anchor="center") # Adjusted proportionally

        self.next_button = tk.Button(root, text="➡️", font=button_font, command=self.show_next_item,
                                     bg=button_bg, fg=button_fg, width=button_width, relief="flat")
        # Place to the right of the centered display label, adjusted for new window size
        self.next_button.place(x=610, y=display_y, anchor="center") # Adjusted proportionally

        # --- Spin button ---
        # Repositioned to be centered below the reels and above the item display
        spin_button_y = 600 # Adjusted Y proportionally for the smaller window

        self.spin_button = tk.Button(root, text="SPIN", font=("Helvetica", 14, "bold"), # Slightly reduced font size
                                     bg="#ff5c5c", fg="white", # Original colors
                                     command=self.start_spin,
                                     relief="raised", bd=3) # Restored default border for visibility
        self.spin_button.place(x=560, y=spin_button_y, anchor="center") # Centered horizontally

    def show_prev_item(self):
        """Updates the display label to show the previous item in the list."""
        self.display_index = (self.display_index - 1) % len(DISPLAY_ITEMS)
        self.display_label.config(text=DISPLAY_ITEMS[self.display_index])

    def show_next_item(self):
        """Updates the display label to show the next item in the list."""
        self.display_index = (self.display_index + 1) % len(DISPLAY_ITEMS)
        self.display_label.config(text=DISPLAY_ITEMS[self.display_index])

    def start_spin(self):
        """Initiates the reel spinning animation and plays the spin sound."""
        self.spin_button.config(state="disabled") # Disable button during spin
        if self.spin_sound:
            self.spin_sound.play() # Play spin sound if loaded
        self.animate_reel()

    def animate_reel(self):
        """
        Animates the slot machine reel with a slowing effect.
        Names from the NAMES list are shuffled and displayed sequentially.
        """
        total_duration = 5000  # Total animation duration in milliseconds (5 seconds)
        steps = 50 # Number of animation steps
        delays = self.generate_slowing_delays(total_duration, steps) # Generate progressively longer delays

        self.shuffled_names = NAMES[:] # Create a copy of the names list
        random.shuffle(self.shuffled_names) # Randomize the order
        self.current_index = 0 # Index to track position in the shuffled names

        # Get the current reel canvas dimensions for drawing lines and text
        reel_canvas_width = self.reel_canvas.winfo_width()
        reel_canvas_height = self.reel_canvas.winfo_height()

        def spin_step(i):
            """Recursive function for each step of the spin animation."""
            self.reel_canvas.delete("all") # Clear previous text and lines

            # Get the current three names to display, handling wraparound for continuous effect
            name_top = self.shuffled_names[(self.current_index) % len(self.shuffled_names)]
            name_mid = self.shuffled_names[(self.current_index + 1) % len(self.shuffled_names)]
            name_bot = self.shuffled_names[(self.current_index + 2) % len(self.shuffled_names)]

            # Draw the names on the reel canvas, centered horizontally and vertically spaced
            text_x = reel_canvas_width / 2 # Center X position on the reel_canvas
            
            # Adjusted Y positions and font sizes for the new reel_canvas_height
            self.reel_canvas.create_text(text_x, reel_canvas_height / 4, text=name_top, font=("Courier New", 25), fill="grey")
            self.reel_canvas.create_text(text_x, reel_canvas_height / 2, text=name_mid, font=("Courier New", 29, "bold"), fill="black") # Middle name is bolder
            self.reel_canvas.create_text(text_x, reel_canvas_height * 3 / 4, text=name_bot, font=("Courier New", 25), fill="grey")

            # Add horizontal lines between names, adjusted for new reel size
            line_color = "darkgrey"
            line_width = 2
            # Line between top and middle name
            self.reel_canvas.create_line(0, reel_canvas_height / 3, reel_canvas_width, reel_canvas_height / 3, fill=line_color, width=line_width)
            # Line between middle and bottom name
            self.reel_canvas.create_line(0, reel_canvas_height * 2 / 3, reel_canvas_width, reel_canvas_height * 2 / 3, fill=line_color, width=line_width)


            self.current_index += 1 # Move to the next set of names

            if i < steps:
                # Schedule the next step after the calculated delay
                self.root.after(int(delays[i]), lambda: spin_step(i + 1))
            else:
                # Animation finished, display the final result clearly
                self.reel_canvas.delete("all")
                # The 'final_mid_name' is the one that was in the 'name_mid' position at the last step
                final_mid_name = self.shuffled_names[(self.current_index) % len(self.shuffled_names)]
                final_top_name = self.shuffled_names[(self.current_index - 1) % len(self.shuffled_names)]
                final_bot_name = self.shuffled_names[(self.current_index + 1) % len(self.shuffled_names)]

                # Draw final names with adjusted positions and fonts
                self.reel_canvas.create_text(text_x, reel_canvas_height / 4, text=final_top_name, font=("Courier New", 25), fill="grey")
                self.reel_canvas.create_text(text_x, reel_canvas_height / 2, text=f"{final_mid_name}", font=("Courier New", 29, "bold"), fill="black")
                self.reel_canvas.create_text(text_x, reel_canvas_height * 3 / 4, text=final_bot_name, font=("Courier New", 25), fill="grey")

                # Add horizontal lines for the final display as well
                self.reel_canvas.create_line(0, reel_canvas_height / 3, reel_canvas_width, reel_canvas_height / 3, fill=line_color, width=line_width)
                self.reel_canvas.create_line(0, reel_canvas_height * 2 / 3, reel_canvas_width, reel_canvas_height * 2 / 3, fill=line_color, width=line_width)

                # Play win sound if loaded, and stop it after a short duration
                if self.win_sound:
                    self.win_sound.play()
                    self.root.after(1500, self.win_sound.stop) # Stop sound after 1.5 seconds

                self.spin_button.config(state="normal") # Re-enable the spin button

        spin_step(0) # Start the animation

    def generate_slowing_delays(self, total_ms, steps):
        """
        Generates a list of progressively increasing delays to simulate a slowing effect.
        Uses a quadratic easing function.
        """
        x = np.linspace(0, 1, steps) # Create a sequence from 0 to 1 with 'steps' elements
        eased = x ** 2 # Apply a quadratic easing function
        scaled = eased / sum(eased) # Scale the eased values so their sum is 1
        return scaled * total_ms # Multiply by total duration to get delays in milliseconds

# --- Main application entry point ---
if __name__ == "__main__":
    root = tk.Tk() # Create the main Tkinter window
    app = SlotMachineApp(root) # Instantiate the SlotMachineApp
    root.mainloop() # Start the Tkinter event loop
