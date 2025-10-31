import customtkinter as ctk
import pygame


class TrackComponent(ctk.CTkFrame):
    def __init__(self, master, track, play_command, stop_command, **kwargs):
        super().__init__(master, **kwargs)
        self.selected_track_id = track[6]
        self.track_name = track[1]
        self.track_path = track[2]
        self.tags = track[3] # need a use for this
        self.duration = track[4]
        self.play_command = play_command
        self.stop_command = stop_command
        self.is_playing = False
        self.current_position = 0
        self.update_id = None  # ID for the after() update loop

        self.configure(fg_color="#2a2a2a", corner_radius=6)
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

        # Track name label
        self.track_label = ctk.CTkLabel(self, text=self.track_name, text_color="white", anchor="w")
        self.track_label.pack(fill="x", padx=10, pady=(10, 0))

        # Progress bar and play button frame
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Play button
        self.play_button = ctk.CTkButton(
            self.progress_frame,
            text="▶",
            width=50,
            height=30,
            corner_radius=15,
            fg_color="#24525B",
            hover_color="#327380",
            command=self.toggle_play,
            anchor="center"  # Center the text
        )
        self.play_button.pack(side="left", padx=(0, 10))
        self.play_button.pack_propagate(False)

        # Current time label
        self.time_label = ctk.CTkLabel(
            self.progress_frame,
            text="0:00",
            text_color="white",
            width=40
        )
        self.time_label.pack(side="left", padx=(0, 5))

        # Progress bar
        self.progress_bar = ctk.CTkSlider(
            self.progress_frame,
            from_=0,
            to=100,
            command=self.on_progress_change,
            progress_color="#327380",
            button_color="#24525B",
            button_hover_color="#327380",
            height=8,
            width=200
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True)

        # Duration label
        self.duration_label = ctk.CTkLabel(
            self.progress_frame,
            text=self.duration,
            text_color="white",
            width=40
        )
        self.duration_label.pack(side="left", padx=(5, 0))

        # Bind hover events to all widgets
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.track_label.bind("<Enter>", self.on_hover)
        self.track_label.bind("<Leave>", self.on_leave)
        self.progress_frame.bind("<Enter>", self.on_hover)
        self.progress_frame.bind("<Leave>", self.on_leave)
        self.play_button.bind("<Enter>", self.on_hover)
        self.play_button.bind("<Leave>", self.on_leave)
        self.progress_bar.bind("<Enter>", self.on_hover)
        self.progress_bar.bind("<Leave>", self.on_leave)
        self.duration_label.bind("<Enter>", self.on_hover)
        self.duration_label.bind("<Leave>", self.on_leave)
        self.time_label.bind("<Enter>", self.on_hover)
        self.time_label.bind("<Leave>", self.on_leave)

        self.update_duration_label()

    def update_duration_label(self):
        """Update the duration label with formatted time."""
        minutes, seconds = divmod(int(self.duration), 60)
        self.duration_label.configure(text=f"{minutes}:{seconds:02d}")

    def update_progress(self, currently_playing_id=None):
        if self.is_playing and pygame.mixer.music.get_busy() and self.selected_track_id == currently_playing_id:
            # Get current position in seconds

            self.current_position = pygame.mixer.music.get_pos() / 1000

            # Update progress bar
            progress = (self.current_position / self.duration) * 100
            self.progress_bar.set(progress)

            # Update time label
            minutes, seconds = divmod(int(self.current_position), 60)
            self.time_label.configure(text=f"{minutes}:{seconds:02d}")

            # Schedule next update
            self.update_id = self.after(1000, lambda: self.update_progress(currently_playing_id))
        else:
            # Stop updating if not playing
            if self.update_id:
                self.after_cancel(self.update_id)
                self.update_id = None

    def on_hover(self, event):
        self.configure(fg_color="#3a3a3a")

    def on_leave(self, event):
        self.configure(fg_color="#2a2a2a")

    def toggle_play(self):
        if self.is_playing and pygame.mixer.music.get_busy():
            self.stop_command()
            self.play_button.configure(text="▶")
        else:
            self.play_command(self.selected_track_id)
            self.play_button.configure(text="⏸")
            self.update_progress(self.selected_track_id)

    def on_progress_change(self, value):
        if self.duration > 0 and pygame.mixer.music.get_busy():
            # Calculate new position in seconds
            new_position = (float(value) / 100) * self.duration

            # print(new_position)
            # Seek to new position
            print("new position: "+ str(new_position))
            print(pygame.mixer.music.get_pos() / 1000)
            pygame.mixer.music.set_pos(new_position)
            print(pygame.mixer.music.get_pos() / 1000)

            # Update current position
            self.current_position = new_position