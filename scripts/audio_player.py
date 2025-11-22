import threading
import sounddevice as sd
import soundfile as sf
import numpy as np
import os

BLOCKSIZE = 1024
CHANNELS = 2
SR = 44100

class Track:
    def __init__(self, path, volume=1.0, loop=False):
        self.path = path
        self.volume = volume
        self.loop = loop
        self.lock = threading.Lock()
        self.is_playing = False

        # Open audio file
        self.sf = sf.SoundFile(path)
        self.frames = self.sf.frames
        self.channels = self.sf.channels
        self.sr = self.sf.samplerate

        self.position = 0  # current frame
        self.stopped = False

    def read_block(self, blocksize=BLOCKSIZE):
        with self.lock:
            if not self.is_playing or self.stopped:
                return np.zeros((blocksize, CHANNELS), dtype=np.float32)

            # Looping logic
            if self.position >= self.frames:
                if self.loop:
                    self.position = 0
                else:
                    self.is_playing = False
                    return np.zeros((blocksize, CHANNELS), dtype=np.float32)

            self.sf.seek(self.position)
            data = self.sf.read(blocksize, dtype='float32', always_2d=True)
            self.position += len(data)

            # Convert channels if needed
            if data.shape[1] < CHANNELS:
                data = np.repeat(data, CHANNELS, axis=1)
            elif data.shape[1] > CHANNELS:
                data = data[:, :CHANNELS]

            return data * self.volume

    def seek(self, frame):
        with self.lock:
            self.position = max(0, min(frame, self.frames))

    def set_volume(self, volume):
        with self.lock:
            self.volume = volume

    def pause(self):
        with self.lock:
            self.is_playing = False

    def resume(self):
        with self.lock:
            self.is_playing = True

    def stop(self):
        with self.lock:
            self.is_playing = False
            self.stopped = True
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
    def play(self, track_id, path, volume=1.0, loop=False):
        with self.lock:
            if track_id in self.tracks:
                track = self.tracks[track_id]
                track.resume()
                track.set_volume(volume)
                track.loop = loop
            else:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Audio file not found: {path}")
                track = Track(path, volume=volume, loop=loop)
                track.resume()
                self.tracks[track_id] = track

    def pause(self, track_id):
        with self.lock:
            track = self.tracks.get(track_id)
            if track:
                track.pause()

    def resume(self, track_id):
        with self.lock:
            track = self.tracks.get(track_id)
            if track:
                track.resume()

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
