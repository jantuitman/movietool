import os
from injector import inject
from dsl_parser import Scene  # Import Scene model from dsl_parser.py
from paragraph_audio_renderer import ParagraphAudioRenderer
from scene_cache import SceneCache
from moviepy.video.VideoClip import TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

def moviepy_render_scene_with_audio(scene: Scene, output_path: str, audio_file: str) -> str:
    """
    Renders a scene video with audio. It loads the audio from audio_file to determine
    the video duration, creates a white background and centered text clip, and then
    sets the audio for the video.
    """
    # Load the complete scene audio clip.
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration
    width, height = 1920, 1080  # FullHD resolution
    fps = 30

    # Create a white background clip with the same duration as the audio.
    background = ColorClip(size=(width, height), color=(255, 255, 255), duration=duration)

    # Generate text for the clip using the scene's MD5 hash.
    text = f"Dummy Scene: {scene.get_md5()}"
    text_clip = TextClip(
        text=text,
        font="DejaVuSans",
        font_size=48,
        color='black',
        size=(width, None),  # Let the height be computed automatically
        method="caption",
        text_align="center",
        horizontal_align="center",
        vertical_align="center",
        duration=duration
    ).with_duration(duration).with_position("center")

    # Composite the text over the background.
    video = CompositeVideoClip([background, text_clip])
    # Attach the audio to the video.
    video = video.set_audio(audio_clip)

    # Define output filename and write the video file.
    rendered_file = os.path.join(output_path, "scene.mp4")
    video.write_videofile(rendered_file, fps=fps, codec="libx264", logger=None)

    # Cleanup resources.
    audio_clip.close()
    video.close()
    return rendered_file


class SceneRenderer:
    @inject
    def __init__(self, paragraph_audio_renderer: ParagraphAudioRenderer, scene_cache: SceneCache):
        """
        Initializes the SceneRenderer with injected dependencies:
          - audio_renderer: instance of ParagraphAudioRenderer
          - cache: instance of SceneCache (injected)
        The project directory must be set separately using set_project_dir().
        """
        self.audio_renderer = paragraph_audio_renderer
        self.cache = scene_cache
        self.project_dir = None

    def set_project_dir(self, project_dir: str):
        """
        Sets the project directory for the renderer and propagates the configuration
        to the injected SceneCache via its set_project_dir method.
        """
        self.project_dir = project_dir
        self.cache.set_project_dir(project_dir)

    def render(self, scene: Scene) -> str:
        """
        Renders a scene video with its audio. Checks the cache to avoid re-rendering.
        Requires that set_project_dir() has been called beforehand.
        """
        if not self.project_dir:
            raise ValueError("Project directory not set. Call set_project_dir() before rendering.")

        # Prepare the cache directory for the scene.
        scene_cache_path = self.cache.prepare_scene_cache(scene)
        rendered_file = os.path.join(scene_cache_path, "scene.mp4")
        if os.path.exists(rendered_file):
            print(f"Fetching rendered scene from cache: {rendered_file}")
            return rendered_file

        print(f"Rendering scene and saving to cache: {scene_cache_path}")

        # Render (or fetch) the complete scene audio using the ParagraphAudioRenderer.
        audio_file = self.audio_renderer.render_scene(scene)

        # Render the video clip with the audio.
        rendered_file = moviepy_render_scene_with_audio(scene, scene_cache_path, audio_file)
        return rendered_file

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

    # In actual usage, the ParagraphAudioRenderer and SceneCache instances would be provided by the ServiceConfigurator.
    from elevenlabs_client import ElevenLabs  # Assuming this module exists.
    # Dummy instantiation for demonstration purposes.
    dummy_client = ElevenLabs(api_key="DUMMY_API_KEY")
    from scene_cache import SceneCache
    dummy_cache = SceneCache()  # Now assuming SceneCache has a set_project_dir method.
    audio_renderer = ParagraphAudioRenderer(dummy_cache, dummy_client)

    renderer = SceneRenderer(audio_renderer, dummy_cache)
    renderer.set_project_dir(project_dir)
    video_file = renderer.render(scene)
    print("Rendered scene video file:", video_file)
