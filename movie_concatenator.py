import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips

def concatenate_scenes(scene_files, output_file):
    """
    Concatenates multiple scene video files into a single final movie.

    Args:
        scene_files (list): List of file paths to scene videos.
        output_file (str): The path where the final concatenated movie should be saved.
    """
    clips = []
    for scene_file in scene_files:
        if os.path.exists(scene_file):
            try:
                clip = VideoFileClip(scene_file)
                clips.append(clip)
            except Exception as e:
                print(f"Error loading {scene_file}: {e}")
        else:
            print(f"Warning: {scene_file} does not exist and will be skipped.")

    if not clips:
        print("Error: No valid scene clips to concatenate.")
        return

    # Concatenate the clips using the "compose" method (handles clips of different sizes)
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_file, codec="libx264", audio=False)

    # Cleanup: close all clips to free resources
    final_clip.close()
    for clip in clips:
        clip.close()

if __name__ == "__main__":
    # Example usage:
    sample_scene_files = [
        "./projects/test_project/cache/scene_xxx/scene.mp4",
        "./projects/test_project/cache/scene_yyy/scene.mp4"
    ]
    output = "./projects/test_project/final_movie.mp4"
    concatenate_scenes(sample_scene_files, output)
