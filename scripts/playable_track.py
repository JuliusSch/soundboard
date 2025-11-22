import customtkinter as ctk

from scripts.database import remove_selected_track


class PlayableTrack(ctk.CTkFrame):
    def __init__(self, master, track, panel, soundboard, player, **kwargs):
        super().__init__(master, **kwargs)

        self.track = track
        self.panel = panel
        self.player = player
        self.soundboard = soundboard

        self.is_playing = False
        self.is_paused = 0
        self.update_job = None
        self.pending_seek = 0

        self.configure(fg_color="#2a2a2a", corner_radius=6)
        self.build_ui()

    def build_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(0, 0))

        # Delete button
        self.delete_button = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color="#5a5a5a",
            text_color="gray",
            corner_radius=5,
            command=self.remove_self
        )
        self.delete_button.pack(side="right")

        # Progress bar and play button frame
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Track name label
        self.track_label = ctk.CTkLabel(
            self.header_frame,
            text=self.track.title,
            text_color="white",
            anchor="w"
        )
        self.track_label.pack(side = "left", fill="x", expand=True)

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
            text=f"{int(self.track.duration)//60:02d}:{int(self.track.duration)%60:02d}",
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
            self.play()
            self.panel.track_started(self)
        else:
            self.pause()

    def play(self):
        self.player.play(self.track.id, self.track.file_path,
                         (self.panel.panel_volume / 100) * self.soundboard.volume)
        self.is_playing = True
        self.is_paused = False
        self.play_button.configure(text="⏸")
        self.update_progress()

    def pause(self):
        if not self.is_playing:
            return

        self.player.pause(self.track.id)
        self.is_playing = False
        self.is_paused = True
        self.play_button.configure(text="▶")
        if self.update_job:
            self.after_cancel(self.update_job)
            self.update_job = None

    def stop(self):
        self.player.stop(self.track.id)
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
        remove_selected_track(self.track.id)

    def on_hover(self, event):
        self.configure(fg_color="#3a3a3a")

    def on_leave(self, event):
        self.configure(fg_color="#2a2a2a")

    # ----------------------- Progress / Time updates -------------------------------

    def update_progress(self):
        if not self.is_playing:
            return

        position_ms = 0
        if self.pending_seek != 0:
            position_ms = self.pending_seek
            self.pending_seek = 0
            self.player.seek(self.track.id, position_ms)
        else:
            position_ms = self.player.get_position(self.track.id)

        self.set_progress(position_ms)
        self.update_job = self.after(250, self.update_progress)

    def on_seek(self, slider_value):
        if self.track.duration <= 0:
            return
        new_time_ms = (slider_value / 100) * (self.track.duration * 1000)
        self.set_progress(new_time_ms)
        self.player.seek(self.track.id, new_time_ms)
        if not self.is_playing:
            self.pending_seek = new_time_ms

    def set_progress(self, position_ms):
        self.time_label.configure(text=self.format_time(position_ms))
        duration_ms = self.track.duration * 1000 or 1

        progress = (position_ms / duration_ms) * 100
        self.progress_bar.set(progress)


    @staticmethod
    def format_time(ms):
        total_seconds = int(ms // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"