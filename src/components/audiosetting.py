import gradio as gr

from src.basecomponent import BaseComponent

class UsedAudioSetting(BaseComponent):
    def __init__(self, **promps) -> None:
        super().__init__(**promps)

    def speed_config(self):
        return gr.Slider(label=self.promps.label, value=1, minimum=0.5, maximum=2, step=0.01)

    def render(self):
        return self.speed_config()