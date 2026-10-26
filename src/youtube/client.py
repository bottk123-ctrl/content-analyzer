"""Клиент YouTube Data API v3.

Выгружаем последние видео канала пользователя:
``channels.list(mine)`` -> id плейлиста загрузок -> ``playlistItems.list`` ->
``videos.list`` со статистикой.

Стоимость по квоте за одну выгрузку ~3-4 единицы из суточных 10 000.
"""

from __future__ import annotations

from itertools import islice

import requests

API_BASE = "https://www.googleapis.com/youtube/v3"
_MAX_PER_PAGE = 50
_DEFAULT_MAX_VIDEOS = 50


class YouTubeAPIError(RuntimeError):
    """Ошибка обращения к YouTube API с понятным для UI сообщением."""


def _get(endpoint: str, access_token: str, params: dict) -> dict:
    """GET-запрос к API с обработкой типовых ошибок."""
    resp = requests.get(
        f"{API_BASE}/{endpoint}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
        timeout=20,
    )

    if resp.status_code == 401:
        raise YouTubeAPIError("Токен доступа отклонён. Войдите заново.")
    if resp.status_code == 403:
        raise YouTubeAPIError(
            "YouTube API отклонил запрос: возможно, исчерпана квота "
            "или у приложения нет прав. " + resp.text
        )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise YouTubeAPIError(f"Ошибка YouTube API: {resp.text}") from exc

    return resp.json()


def get_my_channel(access_token: str) -> dict:
    """Канал авторизованного пользователя (snippet + contentDetails + statistics)."""
    data = _get(
        "channels",
        access_token,
        {"part": "snippet,contentDetails,statistics", "mine": "true"},
    )
    items = data.get("items", [])
    if not items:
        raise YouTubeAPIError(
            "У этого Google-аккаунта нет YouTube-канала или он пуст."
        )
    return items[0]


def get_uploaded_video_ids(
    access_token: str,
    uploads_playlist_id: str,
    max_videos: int = _DEFAULT_MAX_VIDEOS,
) -> list[str]:
    """ID последних загруженных видео (новые первыми), с пагинацией."""
    ids: list[str] = []
    page_token: str | None = None

    while len(ids) < max_videos:
        params: dict = {
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": min(_MAX_PER_PAGE, max_videos - len(ids)),
        }
        if page_token:
            params["pageToken"] = page_token

        data = _get("playlistItems", access_token, params)
        ids.extend(
            item["contentDetails"]["videoId"]
            for item in data.get("items", [])
            if item.get("contentDetails", {}).get("videoId")
        )

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return ids[:max_videos]


def _chunked(items: list[str], size: int):
    it = iter(items)
    while chunk := list(islice(it, size)):
        yield chunk


def get_videos(access_token: str, video_ids: list[str]) -> list[dict]:
    """Детали и статистика видео по их ID (пачками до 50 за запрос)."""
    results: list[dict] = []
    for chunk in _chunked(video_ids, _MAX_PER_PAGE):
        data = _get(
            "videos",
            access_token,
            {"part": "snippet,statistics", "id": ",".join(chunk)},
        )
        results.extend(data.get("items", []))
    return results


def fetch_channel_videos(
    access_token: str, max_videos: int = _DEFAULT_MAX_VIDEOS
) -> tuple[dict, list[dict]]:
    """Полная выгрузка: (данные канала, список видео со статистикой)."""
    channel = get_my_channel(access_token)
    uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    video_ids = get_uploaded_video_ids(access_token, uploads_playlist_id, max_videos)
    videos = get_videos(access_token, video_ids)
    return channel, videos
