import os
from injector import inject
from dsl_parser import Scene, Paragraph
from scene_cache import SceneCache
from paragraph_audio_renderer import ParagraphAudioRenderer
from heygen_client import HeygenClient  # Our Heygen client.
from moviepy.editor import VideoFileClip, concatenate_videoclips

class ActorRenderer:
    @inject
    def __init__(self,
                 cache: SceneCache,
                 paragraph_audio_renderer: ParagraphAudioRenderer,
                 heygen_client: HeygenClient):
        """
        Initializes the ActorRenderer.

        Args:
            cache (SceneCache): Used for caching generated scene video files.
            paragraph_audio_renderer (ParagraphAudioRenderer): Responsible for generating paragraph-level audio.
            heygen_client (HeygenClient): Client for invoking Heygen API.
        """
        self.cache = cache
        self.paragraph_audio_renderer = paragraph_audio_renderer
        self.heygen_client = heygen_client
        # For now, actor_config is hardcoded; later it can be replaced with a proper configuration class.
        self.actor_config = {
            "narrator": {
                "audio_provider": "elevenlabs",
                "video_provider": "heygen",
                "heygen_voice_id": "heygen_voice_narrator",
                "heygen_avatar_id": "default_avatar",
                "heygen_avatar_style": "normal",
                "heygen_speed": 1.0,
            },
            "actor1": {
                "audio_provider": "heygen",
                "video_provider": "heygen",
                "heygen_voice_id": "1bd001e7e50f421d891986aad5158bc8",
                "heygen_avatar_id": "Angela-inTshirt-20220820",
                "heygen_avatar_style": "normal",
                "heygen_speed": 1.1,
            }
        }

    def render(self, scene: Scene) -> str:
        """
        Generates the complete scene video by processing each paragraph.

        For each paragraph:
          1. Look up the actor configuration.
          2. If audio_provider is 'elevenlabs', generate an audio file via ParagraphAudioRenderer.
             Otherwise, skip audio generation.
          3. Check if a video for the paragraph is already cached.
          4. If not, call HeygenClient.generate_video with the paragraph text, actor config, and (optionally) the audio file.
          5. Poll for the video status and download the resulting video clip, then store it in the cache.
        Finally, concatenate all paragraph video clips into a final scene video.

        Args:
            scene (Scene): The scene to process.

        Returns:
            str: The local file path to the final concatenated scene video.
        """
        scene_cache_path = self.cache.prepare_scene_cache(scene)
        final_video_path = os.path.join(scene_cache_path, "scene.mp4")
        if os.path.exists(final_video_path):
            print(f"Scene video already cached: {final_video_path}")
            return final_video_path

        print(f"Rendering scene video for scene {scene.get_md5()}...")
        paragraph_video_files = []

        for paragraph in scene.paragraphs:
            actor = paragraph.actor.lower()
            config = self.actor_config.get(actor)
            if not config:
                print(f"No configuration found for actor '{actor}'. Skipping paragraph.")
                continue

            # Determine if we need to generate audio.
            if config.get("audio_provider") == "elevenlabs":
                audio_file = self.paragraph_audio_renderer.render(scene, paragraph)
            else:
                audio_file = None  # For 'heygen' audio_provider, use text only.

            # Check if a video for this paragraph is already cached.
            video_cache_path = self.cache.get_paragraph_video_path(scene, paragraph)
            if os.path.exists(video_cache_path):
                print(f"Using cached video for paragraph '{paragraph.text[:30]}...': {video_cache_path}")
                paragraph_video_files.append(video_cache_path)
                continue

            # Request video generation via Heygen.
            try:
                video_id = self.heygen_client.generate_video(paragraph.text, config, audio_file=audio_file)
                # Use a unique filename per paragraph.
                output_filename = os.path.basename(video_cache_path)
                video_file = self.heygen_client.check_video_status_and_download(video_id, output_filename)
                # Optionally, move the file to the cache path if not already there.
                if video_file != video_cache_path:
                    os.rename(video_file, video_cache_path)
                    video_file = video_cache_path
                paragraph_video_files.append(video_file)
            except Exception as e:
                print(f"Error generating video for paragraph '{paragraph.text[:30]}...': {e}")

        if not paragraph_video_files:
            raise Exception("No video clips were generated for the scene.")

        # Concatenate video clips using MoviePy.
        try:
            clips = [VideoFileClip(vf) for vf in paragraph_video_files]
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(final_video_path, codec="libx264")
            final_clip.close()
            for clip in clips:
                clip.close()
        except Exception as e:
            raise Exception(f"Error concatenating video clips: {e}")

        print(f"Final scene video rendered and cached at: {final_video_path}")
        return final_video_path
