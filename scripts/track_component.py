import customtkinter as ctk

class TrackComponent(ctk.CTkFrame):
    def __init__(self, master, track, soundboard, player, **kwargs):
        super().__init__(master, **kwargs)

        self.selected_track_id = track[6]
        self.track_name = track[1]
        self.track_path = track[2]
        self.tags = track[3] # need a use for this
        self.duration = int(track[4])
        self.soundboard = soundboard
        self.player = player

        self.is_playing = False
        self.is_paused = 0
        self.update_job = None

        self.configure(fg_color="#2a2a2a", corner_radius=6)
        self.build_ui()

    def build_ui(self):
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
            command=self.on_seek,
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
            text=f"{self.duration//60:02d}:{self.duration%60:02d}",
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

        # self.update_duration_label()

    def toggle_play(self):
        if not self.is_playing or self.is_paused:
            self.soundboard.track_started(self)  # pause others
            self.play()
        else:
            self.pause()

    def play(self):
        self.player.play(self.selected_track_id, self.track_path, self.soundboard.volume)
        self.is_playing = True
        self.is_paused = False
        self.play_button.configure(text="⏸")
        self.update_progress()

    def pause(self):
        if not self.is_playing:
            return

        self.player.pause(self.selected_track_id)
        self.is_playing = False
        self.is_paused = True
        self.play_button.configure(text="▶")
        if self.update_job:
            self.after_cancel(self.update_job)
            self.update_job = None

    def stop(self):
        self.player.stop(self.selected_track_id)
        self.is_playing = False
        self.is_paused = False
        self.play_button.configure(text="▶")
        if self.update_job:
            self.after_cancel(self.update_job)
            self.update_job = None
        self.progress_bar.set(0)
        self.time_label.configure(text="0:00")

    def remove_self(self):
        self.stop()
        self.destroy()
        self.soundboard.save_selected_tracks()

    def on_hover(self, event):
        self.configure(fg_color="#3a3a3a")

    def on_leave(self, event):
        self.configure(fg_color="#2a2a2a")

    # ------------------------------------------------------------
    # Progress / Time updates
    # ------------------------------------------------------------

    def update_progress(self, value=None):
        if not self.is_playing:
            return

        position_ms = self.player.get_position(self.selected_track_id)
        duration_ms = self.duration * 1000 or 1

        progress = (position_ms / duration_ms) * 100
        self.progress_bar.set(progress)
        self.time_label.configure(text=self.format_time(position_ms))

        self.update_job = self.after(250, self.update_progress)

    def on_seek(self, slider_value):
        if self.duration <= 0:
            return
        new_time_ms = (slider_value / 100) * (self.duration * 1000)
        self.player.seek(self.selected_track_id, new_time_ms)

    @staticmethod
    def format_time(ms):
        total_seconds = int(ms // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"