import gradio as gr
import os
from omegaconf import OmegaConf
import base64
from googletrans import Translator
from .basecomponent import BaseComponent

def speakers_to_string(speakers : list) -> str:
    translator = Translator()
    speaker_list = ""
    for i, speaker in enumerate(speakers):

        if speaker == "None":
            continue
        speaker = translator.translate(speaker, dest='ja').pronunciation

        speaker_list = speaker_list + f"{i}. {speaker.title()}, "

    return speaker_list

def symbols_to_string(symbols : list) -> str:
    symbols_list =""
    
    for i, text in enumerate(symbols):

        symbols_list = symbols_list + f"{text}   "

    return symbols_list

class Info(BaseComponent):
    def __init__(self, path) -> None:
        self.path = path

        
    def load_info(self, path : str):
        
        info_path = os.path.join(path, 'info.json')
        config_path = os.path.join(path, 'config.json')

        if not os.path.exists(info_path):
            info_path = os.path.join(path, 'info.yaml')

        if not os.path.exists(config_path):
            config_path = os.path.join(path, 'config.yaml')

        config = OmegaConf.load(config_path)
        speakers = config["speakers"]
        symbols = config["symbols"]

        if not os.path.exists(info_path):

            return (f"""
                <div style="padding-bottom: 10px;">No info
                    <p>Speakers: {speakers_to_string(speakers)}</p>
                    <p>Symbol: {symbols_to_string(symbols)}</p>
                </div>
            """)

        info = OmegaConf.load(info_path)
        
        name = info["title"]
        author = info["author"]
        lang = info["lang"]
        cover = info["cover"]

        cover_path = os.path.join(path, cover) if cover else None
        if cover is not None:
            with open(cover_path, 'rb') as image_file:
                image_content = image_file.read()
                base64_image = base64.b64encode(image_content).decode()
            cover_markdown = f"""<img src="data:image/png;base64,{base64_image}" alt="my image">"""
        else:
            cover_markdown = ""

        html = (f"""
            <div style="padding-bottom: 10px;">
                <h1 style="font-size: 25px;font-style: italic;font-weight: bold;padding-bottom: 10px;">Model name : {name}</h1>
                {cover_markdown}
                <p>Model author: {author}</p>
                <p>Language: {lang}</p>
                <p>Speakers: {speakers_to_string(speakers)}</p>
                <p>Symbol: {symbols_to_string(symbols)}</p>
            </div>
        """)

        return html

    def render(self):
        return gr.HTML(value=self.load_info(self.path))
    
    def update(self):
        return gr.HTML.update(value=self.load_info(self.path))