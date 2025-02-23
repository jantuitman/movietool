import os
import hashlib
import xml.etree.ElementTree as ET
from dsl_parser import Scene, Paragraph  # Importing models from dsl_parser.py

class SceneCache:
    def __init__(self):
        """
        Initializes the cache manager without a project directory.
        The project directory must be set later via set_project_dir().
        """
        self.project_dir = None
        self.cache_dir = None

    def set_project_dir(self, project_dir: str):
        """
        Sets the project directory for the cache.
        The base cache directory will be <project_dir>/cache.
        """
        self.project_dir = project_dir
        self.cache_dir = os.path.join(self.project_dir, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_scene_cache_path(self, scene: Scene) -> str:
        """
        Returns the full cache directory path for the given scene.
        The folder name will be in the format: scene_<md5_of_scene>.
        Requires that set_project_dir() has been called.
        """
        if not self.cache_dir:
            raise ValueError("Project directory not set. Call set_project_dir() first.")
        scene_hash = scene.get_md5()
        return os.path.join(self.cache_dir, f'scene_{scene_hash}')

    def is_scene_rendered(self, scene: Scene) -> bool:
        """
        Checks if the scene has been rendered by verifying the existence of the file 'scene.mp4'
        in the scene's cache folder.
        """
        scene_path = self.get_scene_cache_path(scene)
        rendered_file = os.path.join(scene_path, 'scene.mp4')
        return os.path.exists(rendered_file)

    def prepare_scene_cache(self, scene: Scene) -> str:
        """
        Ensures that the cache directory for the scene exists.
        Returns the cache directory path.
        """
        scene_path = self.get_scene_cache_path(scene)
        os.makedirs(scene_path, exist_ok=True)
        return scene_path

    # --- Paragraph Audio Caching Methods ---

    def get_paragraph_audio_path(self, scene: Scene, paragraph: Paragraph) -> str:
        """
        Returns the full file path for the cached audio of a given paragraph.
        The file is named in the format: <actor>_<md5_of_paragraph>.mp3
        and is stored in the scene's cache directory.
        """
        scene_cache_path = self.get_scene_cache_path(scene)
        # Assuming Paragraph has a get_md5() method to uniquely identify its content.
        audio_filename = f"{paragraph.actor}_{paragraph.get_md5()}.mp3"
        return os.path.join(scene_cache_path, audio_filename)

    def is_paragraph_audio_cached(self, scene: Scene, paragraph: Paragraph) -> bool:
        """
        Checks if the audio file for the given paragraph is already cached.
        """
        audio_path = self.get_paragraph_audio_path(scene, paragraph)
        return os.path.exists(audio_path)

    def prepare_paragraph_audio_cache(self, scene: Scene, paragraph: Paragraph) -> str:
        """
        Ensures that the cache directory for the scene exists and returns the audio file path
        for the given paragraph.
        """
        self.prepare_scene_cache(scene)
        return self.get_paragraph_audio_path(scene, paragraph)

    # --- Complete Scene Audio Caching Methods ---

    def get_scene_audio_complete_path(self, scene: Scene) -> str:
        """
        Returns the full file path for the complete (concatenated) scene audio.
        The file is named 'scene_audio_complete.mp3' and is stored in the scene's cache directory.
        """
        scene_cache_path = self.get_scene_cache_path(scene)
        return os.path.join(scene_cache_path, "scene_audio_complete.mp3")

    def is_complete_scene_audio_cached(self, scene: Scene) -> bool:
        """
        Checks if the complete scene audio is cached.
        It verifies that the final scene audio file exists and that all individual paragraph audios are cached.
        """
        final_audio_path = self.get_scene_audio_complete_path(scene)
        all_paragraphs_cached = all(self.is_paragraph_audio_cached(scene, p) for p in scene.paragraphs)
        return os.path.exists(final_audio_path) and all_paragraphs_cached

        # --- Paragraph Video Caching Methods ---
    def get_paragraph_video_path(self, scene: Scene, paragraph: Paragraph) -> str:
        """
        Returns the full file path for the cached video of a given paragraph.
        The file is named in the format: <actor>_<md5_of_paragraph>.mp4
        and is stored in the scene's cache directory.
        """
        scene_cache_path = self.get_scene_cache_path(scene)
        video_filename = f"{paragraph.actor}_{paragraph.get_md5()}.mp4"
        return os.path.join(scene_cache_path, video_filename)

    def is_paragraph_video_cached(self, scene: Scene, paragraph: Paragraph) -> bool:
        """
        Checks if the video file for the given paragraph is already cached.
        """
        video_path = self.get_paragraph_video_path(scene, paragraph)
        return os.path.exists(video_path)



# --- Example Usage ---
if __name__ == "__main__":
    # Assume the project directory is './projects/test_project'
    project_directory = os.path.abspath('./projects/test_project')

    # For demonstration purposes, let's create a dummy Scene object.
    # In a real scenario, this would come from your DSL parser.
    overlay_xml = ET.fromstring('<chapter title="Chapter 1" start="0" duration="3"/>')
    scene = Scene(overlay=overlay_xml)
    scene.paragraphs.append(
        Paragraph("This is another paragraph without an explicit actor tag,\nso it will use the default actor (narrator).", "narrator")
    )
    scene.paragraphs.append(
        Paragraph("This is a paragraph for demonstration.", "narrator")
    )

    # Create an instance of SceneCache without a project directory.
    cache_manager = SceneCache()
    # Set the project directory.
    cache_manager.set_project_dir(project_directory)

    # Prepare cache directory for the scene.
    scene_cache_path = cache_manager.prepare_scene_cache(scene)
    print("Scene cache path:", scene_cache_path)

    # Example: Check and get paragraph audio paths.
    for paragraph in scene.paragraphs:
        audio_path = cache_manager.get_paragraph_audio_path(scene, paragraph)
        print(f"Audio cache for paragraph ({paragraph.actor}): {audio_path}")
        if cache_manager.is_paragraph_audio_cached(scene, paragraph):
            print("Audio is already cached.")
        else:
            print("Audio not cached yet. Proceed to render audio (e.g., via ElevenLabs API).")
