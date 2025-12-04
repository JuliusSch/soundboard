import customtkinter as ctk

from scripts.database import get_selected_tracks, add_selected_track, \
    get_selected_track, set_panel_volume, get_panel_volume, set_panel_fade, set_panel_loop, get_panel_loop, \
    get_panel_fade
from scripts.playable_track import PlayableTrack

class TrackPanel(ctk.CTkFrame):
    def __init__(self, master, panel_id, player, soundboard, title="Selected Tracks", **kwargs):
        super().__init__(master, **kwargs)

        self.panel_id = panel_id
        self.player = player
        self.soundboard = soundboard
        self.panel_volume = get_panel_volume(self.panel_id) or 50
        self.currently_playing = None
        self.do_fade = False
        self.do_loop = False

        self.track_comps = []

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=5, padx=5)

        self.label = ctk.CTkLabel(self.header, text=title, font=("Arial", 14, "bold"))
        self.label.pack(padx=10, side="left")

        # Header buttons
        self.toggle_fade_button = ctk.CTkButton(
            self.header,
            text="🔀",
            font=("Segoe UI Emoji", 12, "bold"),
            command=self.toggle_fade,
            corner_radius=6,
            fg_color="#2a2a2a",
            hover_color="#327380",
            width=24,
            height=24,
        )
        self.toggle_fade_button.pack(padx=5, side="left")

        self.toggle_loop_button = ctk.CTkButton(
            self.header,
            text="🔄",
            font=("Segoe UI Emoji", 12, "bold"),
            command=self.toggle_loop,
            corner_radius=6,
            fg_color="#2a2a2a",
            hover_color="#327380",
            width=24,
            height=24,
        )
        self.toggle_loop_button.pack(padx=5, side="left")

        # Volume slider
        self.volume_slider = ctk.CTkSlider(self.header, from_=0, to=100,
                                           command=self.on_volume_change)
        self.volume_slider.set(self.panel_volume)
        self.volume_slider.pack(padx=5, pady=5, fill="x")

        # Track list area
        self.tracks_frame = ctk.CTkFrame(self)
        self.tracks_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.set_fade(get_panel_fade(self.panel_id) or False)
        self.set_loop(get_panel_loop(self.panel_id) or False)

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

    def toggle_fade(self):
        self.set_fade(not self.do_fade)

    def set_fade(self, do_fade):
        self.do_fade = do_fade
        set_panel_fade(self.panel_id, self.do_fade)
        if self.do_fade:
            self.toggle_fade_button.configure(fg_color="#327380")
        else:
            self.toggle_fade_button.configure(fg_color="#2a2a2a")

    def toggle_loop(self):
        self.set_loop(self.do_loop)

    def set_loop(self, do_loop):
        self.do_loop = do_loop
        set_panel_loop(self.panel_id, self.do_loop)
        if self.do_loop:
            self.toggle_loop_button.configure(fg_color="#327380")
        else:
            self.toggle_loop_button.configure(fg_color="#2a2a2a")

    def on_volume_change(self, value):
        self.panel_volume = float(value)
        set_panel_volume(self.panel_id, self.panel_volume)
        effective_volume = (self.panel_volume / 100) * self.soundboard.volume

        for track_comp in self.track_comps:
            self.player.set_volume(track_comp.track.id, effective_volume)