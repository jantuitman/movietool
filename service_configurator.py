import os
import injector
from dsl_parser import Parser
from scene_renderer import SceneRenderer
from paragraph_renderer import ParagraphRenderer
from scene_cache import SceneCache
from elevenlabs.client import ElevenLabs  # Assuming this module exists.

class ServiceConfigurator:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ServiceConfigurator, cls).__new__(cls)
            cls._instance.mocks = {}
            cls._instance.injector = injector.Injector(cls._instance.configure)
        return cls._instance

    def configure(self, binder: injector.Binder):
        # Retrieve the ElevenLabs API key from an environment variable.
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable not set.")
        print("ELEVENLABS_API_KEY:", api_key)
        # Bind the ElevenLabs client as a singleton.
        binder.bind(ElevenLabs, to=ElevenLabs(api_key=api_key), scope=injector.singleton)

        # Bind SceneCache as a singleton.
        binder.bind(SceneCache, to=SceneCache, scope=injector.singleton)

        # Bind ParagraphAudioRenderer as a singleton.
        # Its constructor requires a SceneCache and an ElevenLabs client, which will be resolved.
        binder.bind(ParagraphRenderer, to=ParagraphRenderer, scope=injector.singleton)

        # Bind SceneRenderer as a singleton.
        # Since SceneRenderer requires a project directory, which is provided at runtime,
        # ensure that the SceneRenderer instance later receives it via set_project_dir() or similar.
        binder.bind(SceneRenderer, to=SceneRenderer, scope=injector.singleton)

        # Bind the DSL Parser. It is assumed that Parser is stateless or light enough to be transient.
        binder.bind(Parser, to=Parser)

    def get_service(self, service_cls):
        if service_cls in self.mocks:
            return self.mocks[service_cls]
        return self.injector.get(service_cls)

    def add_mock(self, service_class, mock):
        self.mocks[service_class] = mock
