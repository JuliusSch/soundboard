import customtkinter as ctk

from scripts.database import get_selected_tracks, add_selected_track, \
    get_selected_track, set_panel_volume, get_panel_volume
from scripts.playable_track import PlayableTrack

class TrackPanel(ctk.CTkFrame):
    def __init__(self, master, panel_id, player, soundboard, title="Selected Tracks", **kwargs):
        super().__init__(master, **kwargs)

        self.panel_id = panel_id
        self.player = player
        self.soundboard = soundboard
        self.panel_volume = get_panel_volume(self.panel_id) or 50
        self.currently_playing = None

        self.track_comps = []

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=5, padx=5)

        self.label = ctk.CTkLabel(self.header, text=title, font=("Arial", 14, "bold"))
        self.label.pack(padx=10, side="left")

        # Volume slider
        self.volume_slider = ctk.CTkSlider(self.header, from_=0, to=100, command=self.on_volume_change)
        self.volume_slider.set(self.panel_volume)
        self.volume_slider.pack(padx=5, pady=5, fill="x")

        # Track list area
        self.tracks_frame = ctk.CTkFrame(self)
        self.tracks_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

    def load_selected_tracks(self):
        for widget in self.tracks_frame.winfo_children():
            widget.destroy()

        for track in get_selected_tracks(self.panel_id):
            self.add_track_comp(track)

    def add_track_comp(self, track):
        component = PlayableTrack(
            self.tracks_frame,
            track,
            self,
            self.soundboard,
            self.player,
            width=280,
            height=60
        )
        component.pack(fill="x", pady=5, padx=5)
        self.track_comps.append(component)

    def try_add_track(self, track_id):
        for existing_track in self.track_comps:
            if track_id == existing_track.track.track_id:
                return

        add_selected_track(track_id, self.panel_id)
        track = get_selected_track(track_id, self.panel_id)
        self.add_track_comp(track)

    def track_started(self, started_component):
        for comp in self.track_comps:
            if comp is not started_component:
                comp.pause()
        self.currently_playing = started_component

    def toggle_looping(self):
        self.loop_enabled = not getattr(self, "loop_enabled", False)

    def toggle_fade(self):
        self.fade_enabled = not getattr(self, "fade_enabled", False)

    def on_volume_change(self, value):
        self.panel_volume = float(value)
        set_panel_volume(self.panel_id, self.panel_volume)
        effective_volume = (self.panel_volume / 100) * self.soundboard.volume

        for track_comp in self.track_comps:
            self.player.set_volume(track_comp.track.id, effective_volume)