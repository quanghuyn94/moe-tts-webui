import json
from typing import Any
import os
class Language:
    def __init__(self, path) -> None:

        if not os.path.exists(path):
            self.components = {}
            return

        with open(path, 'r', encoding='utf-8') as f:
            self.components = json.load(f)


    def get_components(self, text):
        return self.components[text]

    def __call__(self, text):
        
        if text in self.components:
            return self.components[text]
        self.components[text] = text

        return text
