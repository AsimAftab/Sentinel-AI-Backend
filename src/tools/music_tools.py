# src/tools/music_tools.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from langchain_core.tools import tool
from dotenv import load_dotenv # <--- ADD THIS IMPORT

load_dotenv() # <--- ADD THIS LINE TO LOAD THE .env FILE

# --- Spotify API Setup ---
# The scope defines the permissions our app requests.
# "user-modify-playback-state" is needed to start/resume playback.
# "user-read-playback-state" is needed to see what's currently playing.
SCOPE = "user-modify-playback-state user-read-playback-state"

# Authenticate with Spotify. This will now read credentials from your .env file.
# It will still open a browser window for you to log in and grant
# permissions the first time you run it.
try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))
except Exception as e:
    print(f"Error authenticating with Spotify: {e}")
    print("Please ensure your .env file exists in the project root and contains the correct Spotify credentials.")
    sp = None

# --- Tool Definitions ---

@tool
def search_and_play_song(song_name: str, artist_name: str = None) -> str:
    """
    Searches for a song on Spotify and plays it on the user's active device.
    You can optionally provide an artist's name to improve the search accuracy.
    """
    if not sp:
        return "Spotify authentication failed. Cannot perform this action."

    try:
        # Check for active devices
        devices = sp.devices()
        if not devices or not devices['devices']:
            return "No active Spotify device found. Please open Spotify on one of your devices and start playing something."
        
        active_device_id = None
        for device in devices['devices']:
            if device['is_active']:
                active_device_id = device['id']
                break
        
        if not active_device_id:
            # If no device is active, use the first available one.
            active_device_id = devices['devices'][0]['id']


        # Construct the search query
        query = f"track:{song_name}"
        if artist_name:
            query += f" artist:{artist_name}"

        # Search for the track
        results = sp.search(q=query, type='track', limit=1)
        tracks = results['tracks']['items']

        if not tracks:
            return f"Could not find the song '{song_name}'."

        # Get the track URI and play it
        track_uri = tracks[0]['uri']
        sp.start_playback(device_id=active_device_id, uris=[track_uri])

        return f"Now playing '{tracks[0]['name']}' by {tracks[0]['artists'][0]['name']}."

    except Exception as e:
        return f"An error occurred: {e}. I might need you to be more specific or check if a song is already playing on Spotify."


# This is the list of tools that will be passed to the agent
music_tools = [search_and_play_song]