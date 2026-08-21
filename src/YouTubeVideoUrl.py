# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


import os
import glob

try:
    from yt_dlp import YoutubeDL
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False


# Legacy itag -> max height, kept for the existing yttrailer_best_resolution
# setup choices (which predate this download-based approach).
RESOLUTION_HEIGHTS = {
    '38': 2160, '37': 1080, '22': 720, '35': 480, '18': 360, '5': 240, '17': 144,
}


class YouTubeVideoUrl():

    @staticmethod
    def download(video_id, dest_dir, resolution_itag='22', use_dash=True):
        """Download a YouTube video into dest_dir and return the local file path.

        YouTube now rejects (403 Forbidden) combined video+audio stream URLs from
        the only client (android/android_vr) that still offers them, unless a PO
        token is supplied - which isn't available here. DASH video-only/audio-only
        streams from the regular web client aren't subject to that restriction, so
        downloading and merging them locally via ffmpeg (rather than streaming an
        extracted URL directly) sidesteps the problem entirely.
        """
        if not HAS_YTDLP:
            raise RuntimeError('python3-yt-dlp is not installed. Install it with: opkg install python3-yt-dlp')
        height = RESOLUTION_HEIGHTS.get(resolution_itag, 720)
        outtmpl = os.path.join(dest_dir, 'trailer_%(id)s.%(ext)s')
        # vcodec must be pinned to avc1 (H.264) explicitly - ext=mp4 only describes
        # the container, and YouTube's higher-quality DASH streams are increasingly
        # AV1/VP9 even in an mp4 container, which this box's hardware decoder can't
        # handle (silently drops video, audio keeps playing).
        if use_dash:
            fmt = (
                f'bestvideo[vcodec^=avc1][height<={height}]+bestaudio[ext=m4a]/'
                f'best[vcodec^=avc1][height<={height}]/best[height<={height}]/best'
            )
        else:
            fmt = f'best[vcodec^=avc1][height<={height}]/best[height<={height}]/best'
        ydl_opts = {
            'format': fmt,
            'merge_output_format': 'mp4',
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_id, download=True)
            path = None
            downloads = info.get('requested_downloads')
            if downloads:
                path = downloads[0].get('filepath')
            if not path or not os.path.isfile(path):
                path = ydl.prepare_filename(info)
            if not os.path.isfile(path):
                candidates = glob.glob(os.path.join(dest_dir, "trailer_" + info.get('id', video_id) + ".*"))
                path = candidates[0] if candidates else None
            if not path or not os.path.isfile(path):
                raise RuntimeError('Downloaded trailer file not found')
            return path
