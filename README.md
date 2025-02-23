# Movietool

A small tool to create videos (e.g. youtube videos) using AI.

Usage:

```
    movietool.sh test_project

```

in projects/test_project we expect a script.txt. This file contains your video definition.  It contains text and xml based overlays. the text is rendered via Elevenlabs API (currently the only option) into audio files.
You can also render a "talking head" using the Heygen API. The overlays are rendered using moviepy. It is all concattenated into a final video.

Movietool runs inside docker compose, so to install it on your machine you need to install docker. 
