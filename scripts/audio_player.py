import threading
import sounddevice as sd
import soundfile as sf
import numpy as np
import os


BLOCKSIZE = 1024
CHANNELS = 2
SR = 44100
FADE_TIME_SECONDS = 0.25


class Track:
    def __init__(self, path, volume=1.0, loop=False):
        self.path = path
        self.base_volume = float(volume)
        self.current_volume = 0.0
        self.target_volume = self.base_volume
        self.loop = loop

        self.lock = threading.Lock()
        self.is_playing = False

        # Fade state
        self.fade_samples_remaining = 0
        self.pending_action = None

        # Open audio file
        self.sf = sf.SoundFile(path)
        self.frames = self.sf.frames
        self.channels = self.sf.channels
        self.sr = self.sf.samplerate

        self.position = 0
        self.stopped = False

    def _apply_fade_and_volume(self, data):
        if data.size == 0:
            return data

        n = data.shape[0]

        if self.fade_samples_remaining > 0:
            n_fade = min(self.fade_samples_remaining, n)

            step = (self.target_volume - self.current_volume) / self.fade_samples_remaining

            gains = self.current_volume + step * np.arange(1, n_fade + 1, dtype=np.float32)
            data[:n_fade] *= gains[:, None]

            self.current_volume = float(gains[-1])
            self.fade_samples_remaining -= n_fade

            if n > n_fade:
                data[n_fade:] *= self.current_volume

            if self.fade_samples_remaining == 0:
                if self.pending_action == "pause" and self.target_volume == 0.0:
                    # We've faded out fully -> actually pause
                    self.is_playing = False
                self.pending_action = None
        else:
            data *= self.current_volume

        return data

    def read_block(self, blocksize=BLOCKSIZE):
        with self.lock:
            if self.stopped:
                return np.zeros((blocksize, CHANNELS), dtype=np.float32)

            if not self.is_playing and self.fade_samples_remaining == 0:
                return np.zeros((blocksize, CHANNELS), dtype=np.float32)

            if self.position >= self.frames:
                if self.loop:
                    self.position = 0
                else:
                    self.is_playing = False
                    self.current_volume = 0.0
                    self.fade_samples_remaining = 0
                    self.pending_action = None
                    return np.zeros((blocksize, CHANNELS), dtype=np.float32)

            self.sf.seek(self.position)
            data = self.sf.read(blocksize, dtype='float32', always_2d=True)
            self.position += len(data)

            if data.shape[1] < CHANNELS:
                data = np.repeat(data, CHANNELS, axis=1)
            elif data.shape[1] > CHANNELS:
                data = data[:, :CHANNELS]

            data = self._apply_fade_and_volume(data)

            if len(data) < blocksize:
                pad = np.zeros((blocksize - len(data), CHANNELS), dtype=np.float32)
                data = np.vstack((data, pad))

            return data

    def seek(self, frame):
        with self.lock:
            self.position = max(0, min(frame, self.frames))

    def set_volume(self, volume):
        with self.lock:
            self.base_volume = float(volume)
            # If no fade is happening, snap both current & target
            if self.fade_samples_remaining == 0:
                self.current_volume = self.base_volume
                self.target_volume = self.base_volume
            else:
                # Fade will continue towards the new target volume
                self.target_volume = self.base_volume

    def pause(self, do_fade):
        with self.lock:
            if do_fade and self.is_playing:
                # Start fade-out to 0, then pause when done
                self.target_volume = 0.0
                if self.current_volume <= 0.0:
                    # Already silent, just pause
                    self.is_playing = False
                    self.fade_samples_remaining = 0
                    self.pending_action = None
                else:
                    self.fade_samples_remaining = int(FADE_TIME_SECONDS * self.sr)
                    if self.fade_samples_remaining <= 0:
                        self.is_playing = False
                        self.current_volume = 0.0
                    else:
                        self.pending_action = "pause"
            else:
                self.is_playing = False
                self.fade_samples_remaining = 0
                self.pending_action = None

    def resume(self, do_fade):
        with self.lock:
            self.stopped = False
            self.is_playing = True
            self.pending_action = None

            if do_fade:
                self.target_volume = self.base_volume
                self.fade_samples_remaining = int(FADE_TIME_SECONDS * self.sr)
                if self.fade_samples_remaining <= 0:
                    self.current_volume = self.base_volume
                    self.fade_samples_remaining = 0
                else:
                    self.current_volume = 0.0
            else:
                self.fade_samples_remaining = 0
                self.current_volume = self.base_volume
                self.target_volume = self.base_volume

    def stop(self):
        with self.lock:
            self.is_playing = False
            self.stopped = True
            self.fade_samples_remaining = 0
            self.pending_action = None
            self.current_volume = 0.0
            self.sf.close()


class AudioPlayer:
    def __init__(self):
        self.tracks = {}  # track_id -> Track
        self.lock = threading.Lock()
        self.stream = sd.OutputStream(
            samplerate=SR,
            channels=CHANNELS,
            blocksize=BLOCKSIZE,
            dtype='float32',
            callback=self._callback,
            latency='low'
        )
        self.stream.start()

    def _callback(self, outdata, frames, time_info, status):
        mix = np.zeros((frames, CHANNELS), dtype=np.float32)
        with self.lock:
            for track in list(self.tracks.values()):
                block = track.read_block(frames)
                mix[:len(block)] += block

        # Prevent clipping
        peak = np.max(np.abs(mix))
        if peak > 1.0:
            mix = mix / peak

        outdata[:] = mix

    # === Playback API ===

    def play(self, track_id, path, volume=1.0, do_loop=False, do_fade=False):
        with self.lock:
            if track_id in self.tracks:
                track = self.tracks[track_id]
                track.set_volume(volume)
                track.loop = do_loop
                track.resume(do_fade)
            else:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Audio file not found: {path}")
                track = Track(path, volume=volume, loop=do_loop)
                track.resume(do_fade)
                self.tracks[track_id] = track

    def pause(self, track_id, do_fade):
        with self.lock:
            track = self.tracks.get(track_id)
            if track:
                track.pause(do_fade)

    def resume(self, track_id, do_fade):
        with self.lock:
            track = self.tracks.get(track_id)
            if track:
                track.resume(do_fade)

    def stop(self, track_id):
        with self.lock:
            track = self.tracks.pop(track_id, None)
            if track:
                track.stop()

    def stop_all(self):
        with self.lock:
            for track in self.tracks.values():
                track.stop()
            self.tracks.clear()

    def seek(self, track_id, position_ms):
        track = self.tracks.get(track_id)
        if track:
            frame = int(position_ms / 1000 * track.sr)
            track.seek(frame)

    def set_volume(self, track_id, volume):
        track = self.tracks.get(track_id)
        if track:
            track.set_volume(volume)

    def get_position(self, track_id):
        track = self.tracks.get(track_id)
        if track:
            return int(track.position / track.sr * 1000)
        return 0

    def get_duration(self, track_id):
        track = self.tracks.get(track_id)
        if track:
            return int(track.frames / track.sr * 1000)
        return 0

    def is_playing(self, track_id):
        track = self.tracks.get(track_id)
        return bool(track and track.is_playing)