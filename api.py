import dataclasses
import os
import tempfile
from typing import Optional

import requests


@dataclasses.dataclass
class TempFile:
    size: int
    path: str


@dataclasses.dataclass
class Image:
    url: str
    temp: Optional[TempFile]

    def __enter__(self):
        self.temp = save_media_to_tmp(self.url, ".jpg")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.temp.path)


@dataclasses.dataclass
class Audio:
    url: str
    title: str
    temp: Optional[TempFile]

    def __enter__(self):
        self.temp = save_media_to_tmp(self.url, ".mp3")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.temp.path)


@dataclasses.dataclass
class Collection:
    images: list[Image]
    audio: Optional[Audio]

    def __enter__(self):
        for image in self.images:
            image.__enter__()

        self.audio.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for image in self.images:
            image.__exit__(exc_type, exc_val, exc_tb)

        self.audio.__exit__(exc_type, exc_val, exc_tb)


@dataclasses.dataclass
class Video:
    url: str
    temp: Optional[TempFile]

    def __enter__(self):
        self.temp = save_media_to_tmp(self.url, ".mp4")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.temp.path)


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


class TikTokApiClient:
    def __init__(self):
        self.api_url = "https://tikwm.com/api/"

    def get_content(self, tiktok_url: str) -> Collection | Video:
        params = {"url": tiktok_url}

        response = requests.get(self.api_url, params=params, headers=headers)
        response.raise_for_status()
        body = response.json()

        if body.get("code") != 0:
            raise Exception(body.get("msg", "api code error"))

        data = body['data']

        if 'images' in data:
            images = []
            for image_url in data['images']:
                images.append(Image(image_url, None))

            audio = None
            if 'music_info' in data:
                title = data['music_info']['title']
                audio_url = data['music_info']['play']
                audio = Audio(audio_url, title, None)

            return Collection(images, audio)

        elif 'play' in data:
            video_url = data['play']
            return Video(video_url, None)

        raise Exception(body.get("msg", "api code error"))


def save_media_to_tmp(url: str, suffix: str) -> TempFile:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file_path = temp_file.name

    response = requests.get(url, headers=headers, stream=True, timeout=30)
    response.raise_for_status()

    with open(temp_file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    file_size = os.path.getsize(temp_file_path)

    return TempFile(file_size, temp_file_path)
