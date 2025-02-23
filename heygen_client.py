import requests
import time
import json
import os
from typing import Optional, Dict

class HeygenClient:
    def __init__(self, api_key: str, download_dir: str = "./heygen_downloads"):
        """
        Initializes the HeygenClient with the provided API key.

        Args:
            api_key (str): Your Heygen API key.
            download_dir (str): Directory where downloaded videos will be stored.
        """
        self.api_key = api_key
        self.generate_url = "https://api.heygen.com/v2/video/generate"
        self.status_url = "https://api.heygen.com/v1/video_status.get"
        self.upload_url = "https://upload.heygen.com/v1/asset"
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    def upload_asset(self, file_path: str, content_type: str = "audio/mpeg") -> str:
        """
        Uploads a local asset (e.g., an audio file) to Heygen.

        Args:
            file_path (str): Path to the local file.
            content_type (str): The MIME type (default: "audio/mpeg").

        Returns:
            str: The asset ID returned by Heygen.
        """
        upload_headers = {
            "Content-Type": content_type,
            "X-Api-Key": self.api_key,
        }
        with open(file_path, "rb") as file:
            response = requests.post(self.upload_url, headers=upload_headers, data=file)
        if response.status_code != 200:
            raise Exception(f"Failed to upload asset: {response.status_code} {response.text}")
        result = response.json()
        asset_id = result.get("data", {}).get("asset_id")
        if not asset_id:
            raise Exception("No asset_id returned from upload.")
        print(f"Uploaded asset. Asset ID: {asset_id}")
        return asset_id

    def generate_video(self, input_text: str, actor_config: Dict, audio_file: Optional[str] = None) -> str:
        """
        Generates a video via Heygen using the provided input text and actor configuration.
        If an audio_file is provided (for Elevenlabs voices), the file is first uploaded and the payload
        is built using AudioVoiceSettings. Otherwise, it uses TextVoiceSettings.

        Args:
            input_text (str): The text to be rendered as voice.
            actor_config (Dict): A dictionary containing actor-specific settings.
                Expected keys:
                  - heygen_voice_id
                  - heygen_avatar_id
                  - heygen_avatar_style (default "normal")
                  - heygen_speed (optional, default 1.0)
            audio_file (Optional[str]): Local path to an audio file. If provided, it will be uploaded.

        Returns:
            str: The video ID returned by Heygen.
        """
        if audio_file:
            audio_asset_id = self.upload_asset(audio_file, content_type="audio/mpeg")
            voice_settings = {
                "type": "audio",
                "audio_asset_id": audio_asset_id,
                "speed": actor_config.get("heygen_speed", 1.0)
            }
        else:
            voice_settings = {
                "type": "text",
                "input_text": input_text,
                "voice_id": actor_config.get("heygen_voice_id"),
                "speed": actor_config.get("heygen_speed", 1.0)
            }

        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": actor_config.get("heygen_avatar_id"),
                        "avatar_style": actor_config.get("heygen_avatar_style", "normal")
                    },
                    "voice": voice_settings
                }
            ],
            "dimension": {
                "width": 1280,
                "height": 720
            }
        }

        response = requests.post(self.generate_url, headers=self.headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"Heygen generate_video failed: {response.status_code} {response.text}")

        result = response.json()
        if result.get("error"):
            raise Exception(f"Heygen error: {result['error']}")

        video_id = result.get("data", {}).get("video_id")
        if not video_id:
            raise Exception("Heygen generate_video did not return a video_id.")

        print(f"Heygen video generation requested. Video ID: {video_id}")
        return video_id

    def check_video_status_and_download(self, video_id: str, output_filename: str, max_attempts: int = 100, interval: int = 10) -> str:
        """
        Polls the Heygen status API every `interval` seconds until the video is completed.
        When completed, downloads the video to a local file.

        Args:
            video_id (str): The video ID to check.
            output_filename (str): The name of the file to save the video.
            max_attempts (int): Maximum number of polling attempts.
            interval (int): Seconds between polling attempts.

        Returns:
            str: The local file path of the downloaded video.
        """
        params = {"video_id": video_id}
        for attempt in range(max_attempts):
            response = requests.get(self.status_url, headers=self.headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Heygen check_video_status failed: {response.status_code} {response.text}")

            result = response.json()
            data = result.get("data", {})
            status = data.get("status")
            print(f"Video status for {video_id}: {status} (attempt {attempt+1}/{max_attempts})")

            if status == "completed":
                video_url = data.get("video_url")
                if not video_url:
                    raise Exception("Video status completed but no video_url found.")
                local_path = self.download_video(video_url, output_filename)
                print(f"Video completed. Downloaded to: {local_path}")
                return local_path
            elif status == "failed":
                error_info = data.get("error", {})
                raise Exception(f"Video generation failed: {error_info}")

            time.sleep(interval)

        raise Exception("Video not ready after maximum polling attempts.")

    def download_video(self, video_url: str, output_filename: str) -> str:
        """
        Downloads the video from the given URL and saves it locally.

        Args:
            video_url (str): The URL of the video.
            output_filename (str): The desired output filename (e.g., 'scene.mp4').

        Returns:
            str: The local file path of the downloaded video.
        """
        local_path = os.path.join(self.download_dir, output_filename)
        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download video: {response.status_code}")

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return local_path

# --- Example Usage ---
if __name__ == "__main__":
    # Replace <your-api-key> with your actual Heygen API key.
    heygen_api_key = "<your-api-key>"
    client = HeygenClient(api_key=heygen_api_key)

    # Sample actor configuration for Heygen.
    actor_config = {
        "heygen_voice_id": "1bd001e7e50f421d891986aad5158bc8",
        "heygen_avatar_id": "Angela-inTshirt-20220820",
        "heygen_avatar_style": "normal",
        "heygen_speed": 1.1,
    }

    # Example input text.
    input_text = "Welcome to the HeyGen API!"

    # For Elevenlabs-based voices, provide a local audio file.
    # For Heygen text-based voice, pass None.
    local_audio_file = "path/to/local/audio.mp3"  # Replace with actual path if available, or None

    # Request video generation.
    video_id = client.generate_video(input_text, actor_config, audio_file=local_audio_file)

    # Poll for the video status and download when ready.
    try:
        local_video_file = client.check_video_status_and_download(video_id, output_filename="scene.mp4")
        print("Final video downloaded at:", local_video_file)
    except Exception as e:
        print("Error during video generation or download:", e)
