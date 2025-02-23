import re
import xml.etree.ElementTree as ET
import hashlib
from typing import List, Optional

DEFAULT_ACTOR = "narrator"

class Paragraph:
    def __init__(self, text: str, actor: str):
        self.text = text.strip()
        self.actor = actor

    def __repr__(self) -> str:
        return f"Paragraph(actor={self.actor}, text={self.text!r})"

    def get_md5(self) -> str:
        """
        Computes an MD5 hash for the paragraph by combining the actor and text.
        """
        m = hashlib.md5()
        m.update(self.actor.encode('utf-8'))
        m.update(self.text.encode('utf-8'))
        return m.hexdigest()

class Scene:
    def __init__(self, overlay: Optional[ET.Element]):
        self.overlay = overlay  # an ElementTree.Element or None if no overlay was parsed
        self.paragraphs: List[Paragraph] = []    # list of Paragraph objects

    def __repr__(self) -> str:
        overlay_str = ET.tostring(self.overlay).decode('utf-8') if self.overlay is not None else "None"
        return f"Scene(overlay={overlay_str}, paragraphs={self.paragraphs})"

    def get_md5(self) -> str:
        """
        Computes an MD5 hash for the scene by combining the overlay XML (if available)
        and the MD5 hashes of all its paragraphs.
        """
        m = hashlib.md5()
        if self.overlay is not None:
            # Use canonical XML string representation.
            m.update(ET.tostring(self.overlay))
        for paragraph in self.paragraphs:
            m.update(paragraph.get_md5().encode('utf-8'))
        return m.hexdigest()

class Parser:
    def __init__(self) -> None:
        pass

    def parse(self, filename: str) -> List[Scene]:
        """
        Parse a DSL file for a movie project.
        The file is expected to have multiple scenes, where each scene starts
        with an overlay (an XML fragment) followed by paragraphs.
        Paragraphs are separated by blank lines. A paragraph may start with an
        inline actor declaration (<actor name="..."/>), which will be used for that
        paragraph and subsequent paragraphs until a new actor is declared.
        """
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove XML comments.
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Split into blocks using two or more consecutive newlines as paragraph delimiters.
        blocks = re.split(r'\n\s*\n', content.strip())

        scenes: List[Scene] = []
        current_scene: Optional[Scene] = None
        current_actor = DEFAULT_ACTOR

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Attempt to treat the entire block as an XML fragment.
            try:
                element = ET.fromstring(block)
                # If the tag is <actor>, then this is an actor declaration on its own.
                if element.tag.lower() == 'actor':
                    current_actor = element.attrib.get('name', DEFAULT_ACTOR)
                    continue  # actor declarations do not start a new scene nor form a paragraph
                else:
                    # Otherwise, we treat this XML block as an overlay which starts a new scene.
                    current_scene = Scene(overlay=element)
                    scenes.append(current_scene)
                    # Reset the actor for the new scene.
                    current_actor = DEFAULT_ACTOR
                    continue
            except ET.ParseError:
                # Not a complete XML fragment; we'll process it as text.
                pass

            # Check if the block begins with an inline actor declaration.
            # This looks for a self-closing actor tag at the very start of the block.
            actor_pattern = r'^(<actor\s+[^>]+/>)\s*(.*)$'
            m = re.match(actor_pattern, block, re.DOTALL)
            if m:
                actor_xml, remaining_text = m.groups()
                try:
                    actor_elem = ET.fromstring(actor_xml)
                    current_actor = actor_elem.attrib.get('name', DEFAULT_ACTOR)
                except ET.ParseError:
                    current_actor = DEFAULT_ACTOR
                block = remaining_text.strip()  # the rest of the block is the paragraph text

            # If we haven't started a scene yet, create a dummy scene (overlay=None).
            if current_scene is None:
                current_scene = Scene(overlay=None)
                scenes.append(current_scene)

            # Create a paragraph with the current actor.
            paragraph = Paragraph(text=block, actor=current_actor)
            current_scene.paragraphs.append(paragraph)

        return scenes

# --- Example usage ---
if __name__ == "__main__":
    # Suppose 'script.txt' is our DSL file.
    scenes = Parser().parse("projects/test_project/script.txt")
    for scene in scenes:
        print(scene)
