#!/usr/bin/env python3
import sys
import os
from movie_concatenator import concatenate_scenes  # Placeholder for final concatenation function

from dsl_parser import Parser
from scene_renderer import SceneRenderer
from service_configurator import ServiceConfigurator

def main():
    # Get project name from command-line arguments; default to 'test_project'
    project_name = sys.argv[1] if len(sys.argv) > 1 else "test_project"

    # The base directory is standardized in our Dockerized environment.
    base_dir = "/opt/project"
    project_dir = os.path.join(base_dir, "projects", project_name)
    script_path = os.path.join(project_dir, "script.txt")

    if not os.path.exists(script_path):
        print(f"Error: {script_path} does not exist.")
        sys.exit(1)

    # Initialize the ServiceConfigurator and retrieve required services.
    configurator = ServiceConfigurator()
    # Retrieve the Parser and SceneRenderer instances via the configurator.
    parser = configurator.get_service(Parser)
    scene_renderer = configurator.get_service(SceneRenderer)

    # Set the project directory on components that require it.
    scene_renderer.set_project_dir(project_dir)

    # Parse the DSL file to obtain scenes.
    scenes = parser.parse(script_path)

    # Render each scene using the SceneRenderer and collect the rendered file paths.
    rendered_scene_files = []
    for scene in scenes:
        scene_file = scene_renderer.render(scene)
        rendered_scene_files.append(scene_file)

    # Concatenate all rendered scene videos into a final movie.
    final_movie_path = os.path.join(project_dir, "final_movie.mp4")
    concatenate_scenes(rendered_scene_files, final_movie_path)

    print("Final movie created at:", final_movie_path)

if __name__ == "__main__":
    main()
