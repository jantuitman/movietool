import os
from injector import inject
from dsl_parser import Scene  # Import Scene model from dsl_parser.py
from scene_cache import SceneCache

# Assume these new classes will be defined later.
from actor_renderer import ActorRenderer  # Decides if audio rendering via ElevenLabs is needed.
from overlay_renderer import OverlayRenderer  # Applies overlay (text/video elements) based on Scene.overlay.

class SceneRenderer:
    @inject
    def __init__(self,
                 actor_renderer: ActorRenderer,
                 overlay_renderer: OverlayRenderer,
                 scene_cache: SceneCache):
        """
        Initializes the SceneRenderer with injected dependencies:
          - actor_renderer: handles conversion from audio to video, deciding on ElevenLabs audio rendering if needed.
          - overlay_renderer: overlays text/video elements based on Scene.overlay.
          - scene_cache: manages caching for rendered scenes.
        The project directory must be set later via set_project_dir().
        """
        self.actor_renderer = actor_renderer
        self.overlay_renderer = overlay_renderer
        self.cache = scene_cache
        self.project_dir = None

    def set_project_dir(self, project_dir: str):
        """
        Sets the project directory for the renderer and propagates it to the scene cache.
        """
        self.project_dir = project_dir
        self.cache.set_project_dir(project_dir)

    def render(self, scene: Scene) -> str:
        """
        Renders a scene video by following these steps:
          1. Check if the final video already exists in the scene cache.
          2. Use the ActorRenderer to obtain an intermediate video file for the scene.
             The actor_renderer will decide whether to generate audio with ElevenLabs or use pre-existing audio.
          3. Apply the overlay defined in the Scene via the OverlayRenderer.
          4. Save and return the final video file path.
        Requires that set_project_dir() has been called beforehand.
        """
        if not self.project_dir:
            raise ValueError("Project directory not set. Call set_project_dir() before rendering.")

        # Prepare cache directory for the scene.
        scene_cache_path = self.cache.prepare_scene_cache(scene)
        final_video_path = os.path.join(scene_cache_path, "scene.mp4")
        if os.path.exists(final_video_path):
            print(f"Fetching rendered scene from cache: {final_video_path}")
            return final_video_path

        print(f"Rendering scene and saving to cache: {scene_cache_path}")

        # Step 1: Use the actor renderer to get an intermediate video.
        intermediate_video = self.actor_renderer.render(scene)

        # Step 2: Apply the overlay (e.g., text clips) based on the scene overlay definition.
        final_video = self.overlay_renderer.render(scene, intermediate_video)

        # Optionally, ensure the final video is stored under final_video_path.
        # For example, you might move/rename the output if needed.
        # os.rename(final_video, final_video_path)
        # final_video = final_video_path

        return final_video

# --- Example Usage ---
if __name__ == "__main__":
    import xml.etree.ElementTree as ET
    from dsl_parser import Scene, Paragraph

    # Assume project directory is './projects/test_project'
    project_dir = os.path.abspath('./projects/test_project')

    # Create a dummy scene for demonstration.
    overlay_xml = ET.fromstring('<chapter title="Chapter 1" start="0" duration="3"/>')
    scene = Scene(overlay=overlay_xml)
    scene.paragraphs.append(
        Paragraph("This is a paragraph without an explicit actor tag.", "narrator")
    )
    scene.paragraphs.append(
        Paragraph("This is another paragraph, rendered by actor1.", "actor1")
    )

    # Dummy implementations for demonstration.
    class DummyActorRenderer:
        def render(self, scene: Scene) -> str:
            # Simulate decision logic and return an intermediate video file path.
            cache_path = os.path.join("./dummy_cache", f"intermediate_{scene.get_md5()}.mp4")
            print(f"DummyActorRenderer: returning intermediate video at {cache_path}")
            # In a real implementation, this method would call the Heygen API if needed.
            return cache_path

    class DummyOverlayRenderer:
        def render(self, scene: Scene, video_file: str) -> str:
            # Simulate overlay application and return final video file path.
            final_path = os.path.join("./dummy_cache", f"scene_{scene.get_md5()}.mp4")
            print(f"DummyOverlayRenderer: overlay applied, final video at {final_path}")
            # In a real implementation, this would modify the video file (e.g., add text overlays).
            return final_path

    # Create dummy cache and set the project directory.
    from scene_cache import SceneCache
    dummy_cache = SceneCache()
    dummy_cache.set_project_dir(project_dir)

    dummy_actor_renderer = DummyActorRenderer()
    dummy_overlay_renderer = DummyOverlayRenderer()

    # Instantiate SceneRenderer with dummy implementations.
    from injector import Injector
    renderer = SceneRenderer(dummy_actor_renderer, dummy_overlay_renderer, dummy_cache)
    renderer.set_project_dir(project_dir)
    final_video_file = renderer.render(scene)
    print("Rendered scene video file:", final_video_file)
