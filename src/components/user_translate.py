import gradio as gr
from ..basecomponent import BaseComponent

class UserTranslate(BaseComponent):
    def __init__(self, lang, **promps) -> None:
        super().__init__(**promps)
        self.languages = ["English", "Japanese"]
        self.lang = lang

    def enable_auto_translate(self, change):
        return gr.update(visible=change), gr.update(visible=change)

    def laguage_change(self, value):
        ''''''
        return gr.update(label=self.promps["checkbox_label"] + " " + value)

    def render(self):
        enable_auto_translate_box = gr.Checkbox(label=self.promps["checkbox_label"] + " Japanese", value=False)

        tts_translate_target = gr.Dropdown(label=self.lang("Choices language (Defaut: Japanese)"), choices=self.languages, value="Japanese", elem_id=f"tts-translate-target", visible=False, type="value")

        tts_translate = gr.TextArea(label=self.promps["textarea_label"], elem_id=f"tts-translate-input", visible=False)

        enable_auto_translate_box.change(fn=self.enable_auto_translate, inputs=enable_auto_translate_box, outputs=[tts_translate, tts_translate_target])

        tts_translate_target.change(fn=self.laguage_change, inputs=[tts_translate_target], outputs=[enable_auto_translate_box])

        return tts_translate, tts_translate_target
