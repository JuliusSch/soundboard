import os
import threading
import customtkinter as ctk
import subprocess
import soundfile

from tkinter import simpledialog

from scripts.audio_player import AudioPlayer
from scripts.database import init_db, get_all_tracks, add_track, get_panels, add_panel

from scripts.audio_download import download_audio
from scripts.track_panel import TrackPanel

class Soundboard:
    def __init__(self, root):
        self.volume = 0.5
        self.root = root
        self.root.title("SOUNdbOARD")
        self.root.geometry("840x540")

        init_db()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.panels = {}
        self.player = AudioPlayer()

        self.build_ui()

        self.load_tracks()
        self.load_panels()

        self.set_volume(50)

    def build_ui(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_frame.pack(pady=0, padx=0, fill="both", expand=True)

        # Top frame for left and right panels
        self.workspace_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.workspace_frame.pack(fill="both", expand=True)

        # Left panel (all tracks)
        self.left_panel = ctk.CTkFrame(self.workspace_frame, corner_radius=8)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=0)

        # Right panel (selected tracks)
        self.right_panel = ctk.CTkFrame(self.workspace_frame, corner_radius=8)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(0, 0), pady=0)

        # Label for left panel
        self.left_label = ctk.CTkLabel(self.left_panel, text="All Tracks", font=("Arial", 14, "bold"))
        self.left_label.pack(pady=(0, 10))

        # Label for right panel
        self.right_label = ctk.CTkLabel(self.right_panel, text="Selected Tracks", font=("Arial", 14, "bold"))
        self.right_label.pack(pady=(0, 10))

        # Left frame to hold all tracks
        self.all_tracks_frame = ctk.CTkScrollableFrame(self.left_panel)
        self.all_tracks_frame.pack(fill="both", expand=True, padx=5)

        # Right frame to hold selected track panels
        self.panels_frame = ctk.CTkScrollableFrame(self.right_panel)
        self.panels_frame.pack(fill="both", expand=True, padx=5)

        # Bottom panel for buttons and volume control
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.pack(fill="x", pady=(0, 0))
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=180)

        # Buttons
        self.download_button = ctk.CTkButton(
            self.bottom_frame,
            text="⤓",
            font=("Arial", 20, "bold"),
            command=self.download_track,
            corner_radius=6,
            fg_color="#2a2a2a",
            hover_color="#327380",
            height=36
        )
        self.download_button.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.add_panel_button = ctk.CTkButton(
            self.bottom_frame,
            text="＋",
            font=("Arial", 20, "bold"),
            command=self.open_panel_dialog,
            corner_radius=6,
            fg_color="#2a2a2a",
            hover_color="#327380",
            height=36
        )
        self.add_panel_button.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Volume control
        self.volume_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.volume_frame.grid(row=0, column=2, sticky="nsew", pady=10, padx=10)

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
        self.volume_slider.set(self.volume * 100)

    def load_panels(self):
        for panel in get_panels():
            self.add_panel(panel.id, panel.name)

    def load_tracks(self):
        for widget in self.all_tracks_frame.winfo_children():
            widget.destroy()

        self.dragged_label = None

        for track in get_all_tracks():
            track_label = ctk.CTkLabel(
                self.all_tracks_frame,
                text=track.title,
                corner_radius=5,
                fg_color="transparent",
                anchor="w",
                width=280,
                height=30,
                text_color="white"
            )
            track_label.pack(fill="x", pady=2, padx=5)
            track_label.track = track
            track_label.bind("<ButtonPress-1>", self.on_track_press)
            track_label.bind("<ButtonRelease-1>", self.on_track_release)

    # ----------------------------- Panel Management -----------------------------

    def open_panel_dialog(self):
        name = simpledialog.askstring("Add Panel", "Enter Panel Name:")
        if not name:
            return

        panel_id = 1
        add_panel(name, panel_id)
        self.add_panel(panel_id, name)

    def add_panel(self, panel_id, name):
        panel = TrackPanel(
            self.panels_frame,
            panel_id,
            self.player,
            self,
            name,
        )
        panel.load_selected_tracks()
        panel.pack(fill="x", pady=0)
        self.panels[panel_id] = panel

    # ----------------------------- Track Management -----------------------------

    def on_track_press(self, event):
        widget_path = str(event.widget)
        if ".!label" not in widget_path:
            return

        self.dragged_label = event.widget
        self.dragged_label.startX = event.x
        self.dragged_label.startY = event.y

        # Create a toplevel label for dragging
        self.drag_label = ctk.CTkLabel(
            self.root,
            text=self.dragged_label.cget("text"),
            corner_radius=5,
            fg_color="transparent",
            text_color="white",
            width=280,
            height=30
        )
        self.drag_label.track = event.widget.master.track
        # Place the label at the correct position relative to the root window
        x = self.root.winfo_rootx() + self.dragged_label.winfo_rootx() - self.root.winfo_rootx() + event.x - self.dragged_label.startX
        y = self.root.winfo_rooty() + self.dragged_label.winfo_rooty() - self.root.winfo_rooty() + event.y - self.dragged_label.startY
        self.drag_label.place(x=x, y=y)
        self.drag_label.lift()

        self.root.bind("<B1-Motion>", self.on_track_drag)
        self.root.bind("<ButtonRelease-1>", self.on_track_release)

    def on_track_drag(self, event):
        if hasattr(self, 'drag_label'):
            # Update position relative to the root window
            x = event.x_root - self.root.winfo_rootx()
            y = event.y_root - self.root.winfo_rooty()
            self.drag_label.place(x=x, y=y)
            # Force GUI update to reduce tearing
            self.root.update_idletasks()

    def on_track_release(self, event):
        if hasattr(self, 'drag_label'):
            track = event.widget.master.track

            self.drag_label.destroy()
            del self.drag_label

            # Get the release position relative to the root window
            x = event.x_root - self.root.winfo_rootx()
            y = event.y_root - self.root.winfo_rooty()

            # Check if the release position is over any panel
            for panel_id, panel in self.panels.items():
                panel_x = panel.winfo_x() + panel.master.winfo_rootx() - self.root.winfo_rootx()
                panel_y = panel.winfo_y() + panel.master.winfo_rooty() - self.root.winfo_rooty()
                panel_width = panel.winfo_width()
                panel_height = panel.winfo_height()
                if (panel_x <= x <= panel_x + panel_width) and (panel_y <= y <= panel_y + panel_height):
                    panel.try_add_track(track.id)
                    break

        self.root.unbind("<B1-Motion>")
        self.root.unbind("<ButtonRelease-1>")
        self.dragged_label = None

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
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Downloaded file not found: {file_path}")

            wav_path = os.path.splitext(file_path)[0] + ".wav"
            self.convert_to_wav(file_path, wav_path)
            os.remove(file_path)

            with soundfile.SoundFile(wav_path) as f:
                duration = len(f) / f.samplerate

            track_name = os.path.splitext(os.path.basename(wav_path))[0]
            add_track(track_name, wav_path, duration=duration)

            # refresh track list in main thread
            self.root.after(0, self.load_tracks)

        except Exception as e:
            print(f"Error downloading or converting track: {e}")
        finally:
            # re-enable download button in main thread
            self.root.after(0, lambda: self.download_button.configure(state="normal"))

    def convert_to_wav(self, input_path, output_path):
        cmd = [
            "ffmpeg",
            "-y",  # overwrite if exists
            "-i", input_path,
            "-ar", "44100",  # resample
            "-ac", "2",  # stereo
            "-sample_fmt", "s16",  # 16-bit PCM
            output_path
        ]
        subprocess.run(cmd, check=True)

    # ----------------------------- Playback Control -----------------------------

    def set_volume(self, volume):
        self.volume = float(volume) / 100
        for panel in self.panels.values():
            panel.on_volume_change(panel.panel_volume)