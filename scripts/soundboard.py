import os
import threading
import customtkinter as ctk

from tkinter import simpledialog
from pydub import AudioSegment

from scripts.audio_player import AudioPlayer
from scripts.database import init_db, get_all_tracks, add_track, get_selected_tracks, save_selected_tracks

from scripts.audio_download import download_audio
from scripts.track_component import TrackComponent

class Soundboard:
    def __init__(self, root):
        self.root = root
        self.root.title("SOUNdbOARD")
        self.root.geometry("840x540")

        init_db()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.volume = 0.3
        self.player = AudioPlayer()

        self.build_ui()

        # Load tracks on startup
        self.load_tracks()
        self.load_selected_tracks()

    def build_ui(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_frame.pack(pady=0, padx=0, fill="both", expand=True)

        # Top frame for left and right panels
        self.top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_frame.pack(fill="both", expand=True)

        # Left panel (all tracks)
        self.left_panel = ctk.CTkFrame(self.top_frame, corner_radius=8)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=10)

        # Label for left panel
        self.left_label = ctk.CTkLabel(self.left_panel, text="All Tracks", font=("Arial", 14, "bold"))
        self.left_label.pack(pady=(0, 10))

        # Frame to hold all tracks
        self.all_tracks_frame = ctk.CTkScrollableFrame(self.left_panel, width=300, height=350)
        self.all_tracks_frame.pack(fill="both", expand=True, padx=5)

        # Right panel (selected tracks)
        self.right_panel = ctk.CTkFrame(self.top_frame, corner_radius=8)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(0, 0), pady=10)

        # Label for right panel
        self.right_label = ctk.CTkLabel(self.right_panel, text="Selected Tracks", font=("Arial", 14, "bold"))
        self.right_label.pack(pady=(0, 10))

        # Frame to hold selected tracks
        self.selected_tracks_frame = ctk.CTkScrollableFrame(self.right_panel, width=300, height=350)
        self.selected_tracks_frame.pack(fill="both", expand=True, padx=5)

        # Bottom panel for buttons and volume control
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.pack(fill="x", pady=(10, 0))

        # Buttons
        self.download_button = ctk.CTkButton(
            self.bottom_frame,
            text="Download Track",
            command=self.download_track,
            corner_radius=6,
            fg_color="#2a2a2a",
            hover_color="#327380",
            height=36
        )
        self.download_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Volume control
        self.volume_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.volume_frame.pack(pady=10, padx=10, fill="x")

        self.volume_label = ctk.CTkLabel(
            self.volume_frame,
            text="Volume:",
            text_color="white"
        )
        self.volume_label.pack(side="left", padx=(0, 10))

        self.volume_slider = ctk.CTkSlider(
            self.volume_frame,
            from_=0,
            to=100,
            command=self.set_volume,
            progress_color="#327380",
            button_color="#24525B",
            button_hover_color="#327380",
            width=400
        )
        self.volume_slider.pack(side="left", fill="x", expand=True)
        self.volume_slider.set(30)

    def load_tracks(self):
        for widget in self.all_tracks_frame.winfo_children():
            widget.destroy()

        for track in get_all_tracks():
            track_label = ctk.CTkLabel(
                self.all_tracks_frame,
                text=track[1],
                corner_radius=5,
                fg_color="transparent",
                anchor="w",
                width=280,
                height=30,
                text_color="white"
            )
            track_label.pack(fill="x", pady=2, padx=5)
            track_label.track = track
            track_label.bind("<Button-1>", lambda event, t=track: self.on_track_click(t))

    def add_selected_track(self, track):
        track_component = TrackComponent(
            self.selected_tracks_frame,
            track,
            self,
            self.player,
            width=280,
            height=60
        )
        track_component.pack(fill="x", pady=5, padx=5)

    def load_selected_tracks(self):
        for widget in self.selected_tracks_frame.winfo_children():
            widget.destroy()

        for track in get_selected_tracks():
            self.add_selected_track(track)

    # ----------------------------- Track Management -----------------------------

    def on_track_click(self, track):
        for widget in self.selected_tracks_frame.winfo_children():
            if isinstance(widget, TrackComponent) and widget.selected_track_id == track[0]:
                return

        self.add_selected_track(track)
        self.save_selected_tracks()

    def save_selected_tracks(self):
        selected_track_ids = []

        for widget in self.selected_tracks_frame.winfo_children():
            if isinstance(widget, TrackComponent):
                selected_track_ids.append(widget.selected_track_id)

        save_selected_tracks(selected_track_ids)

    # ----------------------------- Downloading -----------------------------

    def download_track(self):
        url = simpledialog.askstring("Download Track", "Enter YouTube URL:")
        if not url:
            return

        self.download_button.configure(state="disabled")
        threading.Thread(target=self.download_and_convert, args=(url,)).start()

    def download_and_convert(self, url):
        try:
            file_path = download_audio(url)
            sound = AudioSegment.from_file(file_path, format="webm")
            wav_path = file_path.replace('.webm', '.wav')
            sound.export(wav_path, format="wav")
            duration = len(sound) / 1000
            os.remove(file_path)

            track_name = os.path.splitext(os.path.basename(wav_path))[0]
            add_track(track_name, wav_path, duration=duration)
            self.root.after(0, self.load_tracks)
        except Exception as e:
            print(f"Error downloading track: {e}")
        finally:
            self.root.after(0, lambda: self.download_button.configure(state="normal"))

    # ----------------------------- Playback Control -----------------------------

    def track_started(self, active_component):
        for widget in self.selected_tracks_frame.winfo_children():
            if isinstance(widget, TrackComponent) and widget is not active_component:
                widget.pause() # type: ignore[attr-defined]

    def set_volume(self, volume):
        self.volume = float(volume) / 100
        for widget in self.selected_tracks_frame.winfo_children():
            if isinstance(widget, TrackComponent):
                self.player.set_volume(widget.selected_track_id, self.volume)