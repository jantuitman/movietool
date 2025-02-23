import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

class OverlayRenderer:
    def render(self, scene, intermediate_video: str) -> str:
        """
        Applies an overlay to the intermediate video based on the Scene's overlay XML.
        For now, it generates a "Hello world!" text clip and overlays it for the first 3 seconds
        of the video.

        Args:
            scene: The Scene object (currently not used, but will be in the future).
            intermediate_video (str): Path to the intermediate video file.

        Returns:
            str: The file path to the final video with the overlay applied.
        """
        # Load the intermediate video.
        clip = VideoFileClip(intermediate_video)

        # Create a text clip "Hello world!" lasting 3 seconds.
        txt_clip = TextClip("Hello world!", fontsize=70, color='white', bg_color='black', align='center')
        txt_clip = txt_clip.set_duration(3).set_position('center')

        # Composite: overlay the text clip over the video clip for the first 3 seconds.
        # We assume the text is to be applied on top of the video.
        composite = CompositeVideoClip([clip, txt_clip.set_start(0)])

        # Define output filename in the same directory as the intermediate video.
        base_dir = os.path.dirname(intermediate_video)
        final_video = os.path.join(base_dir, "scene_overlay.mp4")

        # Write the final video.
        composite.write_videofile(final_video, codec="libx264")

        # Cleanup.
        clip.close()
        txt_clip.close()
        composite.close()

        return final_video

# --- Example Usage ---
if __name__ == "__main__":
    # For testing, assume we have an intermediate video file.
    intermediate_video_path = "path/to/intermediate_video.mp4"
    # Dummy scene object (could be None for now, as the overlay is hardcoded).
    scene = None
    renderer = OverlayRenderer()
    final_video_path = renderer.render(scene, intermediate_video_path)
    print("Final video with overlay saved at:", final_video_path)
