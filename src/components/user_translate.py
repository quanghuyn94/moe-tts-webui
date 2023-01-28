import gradio as gr
from .basecomponent import BaseComponent

class UserTranslate(BaseComponent):

    def enable_auto_translate(self, change):
        return gr.update(visible=change)

    def render(self):
        enable_auto_translate_box = gr.Checkbox(label="Using Auto translate to ja?", value=False)

        tts_translate = gr.TextArea(label="Translate by Google Translate API", elem_id=f"tts-translate-input", visible=False)

        enable_auto_translate_box.change(fn=self.enable_auto_translate, inputs=enable_auto_translate_box, outputs=tts_translate)

        return tts_translate
