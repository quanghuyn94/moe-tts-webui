import gradio as gr

from src.components.basecomponent import BaseComponent

class UsedAudioSetting(BaseComponent):
    def speed_config(self):
        return gr.Slider(label="Speed", value=1, minimum=0.5, maximum=2, step=0.01)

    def render(self):
        with gr.Column():
            speed_config = self.speed_config()
            
        return speed_config