import os
import hashlib
from injector import inject
from elevenlabs.client import ElevenLabs
from dsl_parser import Scene, Paragraph  # Import your models
from scene_cache import SceneCache
# Fixed imports for MoviePy v2 audio concatenation:
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import concatenate_audioclips

# A simple mapping from actor names to voice IDs.
# Replace these placeholder values with your actual ElevenLabs voice IDs.
VOICE_MAPPING = {
    "narrator": "CXnCOoNzZSoavaaR3tkO",
    "actor1": "CXnCOoNzZSoavaaR3tkO",
    # Add more mappings as needed.
}

class ParagraphRenderer:
    @inject
    def __init__(self, cache: SceneCache, client: ElevenLabs):
        """
        Initializes the ParagraphAudioRenderer.

        Args:
            cache (SceneCache): An instance of the SceneCache for caching audio files.
                               Note: The project directory must be set on this cache
                               instance via set_project_dir() before rendering.
            client (ElevenLabs): An initialized ElevenLabs client.
        """
        self.cache = cache
        self.client = client

    def render(self, scene: Scene, paragraph: Paragraph) -> str:
        """
        Renders audio for a given paragraph if it is not already cached.
        The audio is cached in the scene's cache folder with a filename:
        <actor>_<md5_of_paragraph>.mp3

        Args:
            scene (Scene): The scene that the paragraph belongs to.
            paragraph (Paragraph): The paragraph object (must have 'text', 'actor',
                                   and a get_md5() method).

        Returns:
            str: The file path to the rendered (or cached) audio.
        """
        # Ensure the scene cache directory exists and get the audio file path.
        audio_path = self.cache.prepare_paragraph_audio_cache(scene, paragraph)

        # Check if the audio is already cached.
        if self.cache.is_paragraph_audio_cached(scene, paragraph):
            print(f"Audio already cached at: {audio_path}")
            return audio_path

        print(f"Rendering audio for paragraph: '{paragraph.text[:30]}...' using actor: {paragraph.actor}")

        # Determine the voice ID from the mapping; default to narrator if not found.
        actor_key = paragraph.actor.lower()
        voice_id = VOICE_MAPPING.get(actor_key, VOICE_MAPPING.get("narrator"))

        # Request the audio stream from ElevenLabs.
        audio_stream = self.client.text_to_speech.convert_as_stream(
            text=paragraph.text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2"
        )

        # Stitch the audio chunks together.
        audio_bytes = bytearray()
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                audio_bytes.extend(chunk)

        # Write the audio bytes to the cache.
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        print(f"Audio rendered and cached at: {audio_path}")
        return audio_path

    def render_scene(self, scene: Scene) -> str:
        """
        Renders the complete audio for a scene by concatenating the audio for each paragraph.
        The complete scene audio is cached as 'scene_audio_complete.mp3' in the scene's cache folder.

        If the final file exists and all individual paragraph audios are cached, it returns the cached file.

        Args:
            scene (Scene): The scene whose paragraphs are to be rendered.

        Returns:
            str: The file path to the concatenated scene audio.
        """
        # Check if the complete scene audio is already cached.
        if self.cache.is_complete_scene_audio_cached(scene):
            final_audio_path = self.cache.get_scene_audio_complete_path(scene)
            print(f"Final scene audio already cached at: {final_audio_path}")
            return final_audio_path

        # Render (or fetch) audio for each paragraph.
        audio_file_paths = []
        for paragraph in scene.paragraphs:
            audio_file = self.render(scene, paragraph)
            audio_file_paths.append(audio_file)

        # Load audio clips.
        clips = []
        for path in audio_file_paths:
            try:
                clip = AudioFileClip(path)
                clips.append(clip)
            except Exception as e:
                print(f"Error loading audio clip from {path}: {e}")

        if not clips:
            print("Error: No audio clips to concatenate.")
            return ""

        # Concatenate the audio clips.
        final_clip = concatenate_audioclips(clips)
        final_audio_path = self.cache.get_scene_audio_complete_path(scene)
        final_clip.write_audiofile(final_audio_path, codec="mp3")

        # Cleanup: close the clips to free resources.
        final_clip.close()
        for clip in clips:
            clip.close()

        print(f"Final scene audio rendered and cached at: {final_audio_path}")
        return final_audio_path

