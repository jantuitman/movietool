FROM python:3.11-bullseye

# Set the working directory in the container
WORKDIR /opt/project

# Update package lists and install the PortAudio development package
RUN apt-get update && apt-get install -y portaudio19-dev

# Install MoviePy
RUN pip install --no-cache-dir moviepy
RUN pip install --no-cache-dir elevenlabs
RUN pip install --no-cache-dir injector
