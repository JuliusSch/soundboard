import vlc
import threading

class AudioPlayer:
    def __init__(self):
        self.instance = vlc.Instance()
        self.players = {}
        self.lock = threading.Lock()

    def play(self, track_id, path, volume=1.0):
        info = self.players.get(track_id)

        if info and info["player"].is_playing():
            return None

        if info is None:
            media = self.instance.media_new(path)
            player = self.instance.media_player_new()
            player.set_media(media)
            player.audio_set_volume(int(volume * 100))
            self.players[track_id] = {"player": player, "path": path}
        else:
            player = info["player"]
            player.audio_set_volume(int(volume * 100))

        player.play()
        return player

    def pause(self, track_id):
        with self.lock:
            info = self.players.get(track_id)
            if info:
                info["player"].pause()

    def resume(self, track_id):
        with self.lock:
            info = self.players.get(track_id)
            if info:
                info["player"].play()

    def stop(self, track_id):
        with self.lock:
            info = self.players.pop(track_id, None)
            if info:
                try:
                    info["player"].stop()
                except Exception:
                    pass

    def stop_all(self):
        with self.lock:
            for tid, info in list(self.players.items()):
                try:
                    info["player"].stop()
                except Exception:
                    pass
            self.players.clear()

    def seek(self, track_id, position_ms):
        info = self.players.get(track_id)
        if info:
            info["player"].set_time(int(position_ms))

    def get_position(self, track_id):
        info = self.players.get(track_id)
        if info:
            return info["player"].get_time()  # ms
        return 0

    def get_duration(self, track_id):
        info = self.players.get(track_id)
        if info:
            return info["player"].get_length()  # ms
        return 0

    def set_volume(self, track_id, volume):
        info = self.players.get(track_id)
        if info:
            info["player"].audio_set_volume(int(volume * 100))

    def is_playing(self, track_id):
        info = self.players.get(track_id)
        return info and info["player"].is_playing()