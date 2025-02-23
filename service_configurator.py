import os
import injector
from dsl_parser import Parser
from paragraph_audio_renderer import ParagraphAudioRenderer
from scene_renderer import SceneRenderer
from actor_renderer import ActorRenderer
from overlay_renderer import OverlayRenderer
from scene_cache import SceneCache
from elevenlabs.client import ElevenLabs  # Assuming this module exists.
from heygen_client import HeygenClient   # Our new Heygen client.

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
        binder.bind(ElevenLabs, to=ElevenLabs(api_key=api_key), scope=injector.singleton)

        # Retrieve the Heygen API key from an environment variable.
        heygen_api_key = os.getenv('HEYGEN_API_KEY')
        if not heygen_api_key:
            raise ValueError("HEYGEN_API_KEY environment variable not set.")
        print("HEYGEN_API_KEY:", heygen_api_key)
        binder.bind(HeygenClient, to=HeygenClient(api_key=heygen_api_key), scope=injector.singleton)

        # Bind SceneCache as a singleton.
        binder.bind(SceneCache, to=SceneCache, scope=injector.singleton)
        binder.bind(ParagraphAudioRenderer, to=ParagraphAudioRenderer, scope=injector.singleton)
        binder.bind(ActorRenderer, to=ActorRenderer, scope=injector.singleton)
        binder.bind(OverlayRenderer, to=OverlayRenderer, scope=injector.singleton)
        binder.bind(SceneRenderer, to=SceneRenderer, scope=injector.singleton)
        binder.bind(Parser, to=Parser)

    def get_service(self, service_cls):
        if service_cls in self.mocks:
            return self.mocks[service_cls]
        return self.injector.get(service_cls)

    def add_mock(self, service_class, mock):
        self.mocks[service_class] = mock
