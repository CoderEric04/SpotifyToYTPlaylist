import base64
import os

import requests
from dotenv import load_dotenv

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


def get_token(sp_client_id, sp_client_secret):
    auth_string = f"{sp_client_id}:{sp_client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        json_result = response.json()
        token = json_result["access_token"]
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")
        return None


def get_playlist_items(token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_result = response.json()

        if 'items' in json_result:
            songs = []
            for item in json_result['items']:
                track = item['track']
                song_name = track['name']
                artists = ', '.join(artist['name'] for artist in track['artists'])
                full_name = f"{song_name} by {artists}"
                songs.append(full_name)
            return songs
        else:
            print("No items found in the pla    ylist.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting playlist items: {e}")
        return None


def get_video_id(yt_api_key, videos):

    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=yt_api_key
    )

    video_ids = []

    for video in videos:
        search_response = youtube.search().list(
            q=video,
            type="video",
            part="id",
            maxResults=1
        )
        search_response = search_response.execute()

        if 'items' in search_response:
            video_id = search_response['items'][0]['id']['videoId']
            video_ids.append(video_id)
        else:
            print(f"No video found for query: {video}")

    return video_ids


def create_yt_playlist(video_ids):
    scopes = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "yt.json"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes
    )
    flow.redirect_uri = "http://localhost:8081"

    credentials = flow.run_local_server(port=8081)

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials
    )

    create_request = youtube.playlists().insert(
        part="snippet",
        body={
            "snippet": {
                "title": "Test Playlist",
                "description": "This is a test",
                "privacyStatus": "public"
            }
        }
    )
    response = create_request.execute()

    playlist_id = response["id"]

    for video_id in video_ids:
        add_items_request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            }
        )
        add_items_request.execute()

    return response


def main():
    load_dotenv()

    sp_client_id = os.getenv("SP_CLIENT_ID")
    sp_client_secret = os.getenv("SP_CLIENT_SECRET")
    yt_api_key = os.getenv("YT_API_KEY")

    token = get_token(sp_client_id, sp_client_secret)

    sp_playlist_id = "2J2btKQXPqIadM71st1Zw1"
    result_sp = get_playlist_items(token, sp_playlist_id)

    # for song in result_sp:
    #     print(song)

    video_ids = get_video_id(yt_api_key, result_sp)
    result_yt = create_yt_playlist(video_ids)

    print("Playlist created successfully!")
    print("Playlist ID:", result_yt["id"])


if __name__ == "__main__":
    main()
