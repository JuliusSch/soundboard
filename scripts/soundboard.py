import os
import threading
import customtkinter as ctk
import pygame

from tkinter import simpledialog
from pydub import AudioSegment

from scripts.database import init_db, get_all_tracks, add_track, get_selected_tracks, save_selected_tracks, \
    get_track_path_from_selected_track_id
from scripts.audio_handler import download_audio
from scripts.track_component import TrackComponent


class Soundboard:
    def __init__(self, self_root):
        self.root = self_root
        self.root.title("SOUNdbOARD")
        self.root.geometry("800x540")
        pygame.mixer.init()
        init_db()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.volume = 0.3

        # Main frame
        self.main_frame = ctk.CTkFrame(self_root, corner_radius=0)
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

        self.stop_button = ctk.CTkButton(
            self.bottom_frame,
            text="Stop",
            command=self.stop_playback,
            corner_radius=6,
            fg_color="#2a2a2a",
            hover_color="#327380",
            height=36
        )
        self.stop_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

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

        # Load tracks on startup
        self.load_tracks()
        self.load_selected_tracks()
        self.currently_playing_id = None

    def load_tracks(self):
        # Clear existing tracks
        for widget in self.all_tracks_frame.winfo_children():
            widget.destroy()

        tracks = get_all_tracks()
        for track in tracks:
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
            # Bind click event to add the track to the selected panel
            track_label.bind("<Button-1>", lambda event, t=track: self.on_track_click(t))

    def load_selected_tracks(self):
        # Clear existing selected tracks
        for widget in self.selected_tracks_frame.winfo_children():
            widget.destroy()

        # Load selected tracks from the database
        selected_tracks = get_selected_tracks()

        for track in selected_tracks:
            track_component = TrackComponent(
                self.selected_tracks_frame,
                (track[0], track[1], track[2], track[3], track[4], track[5], track[6]),
                self.play_track,
                self.stop_playback,
                width=280,
                height=60
            )
            track_component.pack(fill="x", pady=5, padx=5)

    def on_track_click(self, track):
        # Check if the track is already in the selected panel
        for widget in self.selected_tracks_frame.winfo_children():
            if isinstance(widget, TrackComponent) and widget.selected_track_id == track[0]:
                return

        track_component = TrackComponent(
            self.selected_tracks_frame,
            track,
            self.play_track,
            self.stop_playback,
            width=280,
            height=60
        )
        track_component.pack(fill="x", pady=5, padx=5)
        self.save_selected_tracks()

    def save_selected_tracks(self):
        track_components = []

        for widget in self.selected_tracks_frame.winfo_children():
            if isinstance(widget, TrackComponent):
                track_components.append(widget)

        ordered_track_ids = [component.track_id for component in track_components]
        save_selected_tracks(ordered_track_ids)

    def download_track(self):
        url = simpledialog.askstring("Download Track", "Enter YouTube URL:")
        if url:
            # Disable the download button to prevent multiple downloads
            self.download_button.configure(state="disabled")

            # Start a new thread for downloading and converting the track
            download_thread = threading.Thread(target=self.download_and_convert, args=(url,))
            download_thread.start()

    def download_and_convert(self, url):
        try:
            # Download the audio file
            file_path = download_audio(url)

            # Convert the downloaded file to WAV
            sound = AudioSegment.from_file(file_path, format="webm")
            wav_path = file_path.replace('.webm', '.wav')
            sound.export(wav_path, format="wav")
            duration = len(sound) / 1000

            # Remove the original .webm file
            os.remove(file_path)

            # Add the track to the database with the new .wav path
            track_name = os.path.splitext(os.path.basename(wav_path))[0]
            add_track(track_name, wav_path, duration=duration)

            # Reload the tracks on the main thread
            self.root.after(0, self.load_tracks)
        except Exception as e:
            print(f"Error downloading track: {e}")
        finally:
            # Re-enable the download button on the main thread
            self.root.after(0, lambda: self.download_button.configure(state="normal"))

    def play_track(self, selected_track_id):
        path = get_track_path_from_selected_track_id(selected_track_id)[0][0]
        if not os.path.exists(path):
            print(f"Error: File not found at {path}")
            return
        try:
            print("currently playing")
            # Check if this track is already playing
            if self.currently_playing_id == selected_track_id:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
                    return
                else:
                    pygame.mixer.music.unpause()
                    return

            # Stop any currently playing sound
            if self.currently_playing_id:
                pygame.mixer.music.stop()

            # Load the audio file directly with pygame.mixer.music
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            self.currently_playing_id = selected_track_id

            # Update all track components to show play button
            for widget in self.selected_tracks_frame.winfo_children():
                if isinstance(widget, TrackComponent):
                    widget.is_playing = (widget.selected_track_id == self.currently_playing_id)
                    widget.play_button.configure(text="⏸" if widget.is_playing else "▶")
                if widget.is_playing:
                    widget.update_progress(self.currently_playing_id)
                else:
                    # Stop progress updates for other tracks
                    if widget.update_id is not None:
                        widget.after_cancel(widget.update_id)
                        widget.update_id = None

        except Exception as e:
            print(f"Error playing track: {e}")
            import traceback
            traceback.print_exc()

    def stop_playback(self):
        pygame.mixer.music.pause()
        #self.currently_playing_id = None

        # Update all track components to show play button
        for widget in self.selected_tracks_frame.winfo_children():
            if isinstance(widget, TrackComponent):
                widget.is_playing = False
                widget.play_button.configure(text="▶")

                # Stop progress updates
                if widget.update_id is not None:
                    widget.after_cancel(widget.update_id)
                    widget.update_id = None

    def set_volume(self, volume):
        self.volume = float(volume) / 100
