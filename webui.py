from fastapi import FastAPI
import gradio as gr
from googletrans import Translator
import os
from extension.bcolors import bcolors
from modules.models import SynthesizerTrn
from omegaconf import OmegaConf
import base64
import gradio.processing_utils as gr_processing_utils
import numpy as np
from pydub import AudioSegment

from src.language import Language

#Import componets
from src.components.info import Info
from src.components.user_translate import UserTranslate
from src.basecomponent import BaseComponent
from src.components.audiosetting import UsedAudioSetting

translator = Translator()

audio_postprocess_ori = gr.Audio.postprocess

def audio_postprocess(self, y):
    data = audio_postprocess_ori(self, y)
    if data is None:
        return None
    return gr_processing_utils.encode_url_or_file_to_base64(data["name"])


gr.Audio.postprocess = audio_postprocess

def translation(text, lang = 'ja'):
    outputs = translator.translate(text=text, dest=lang)
    return outputs.text, outputs.pronunciation

def sort_key(x):
    if x.isnumeric():
        return (0, int(x))
    else:
        return (1, x)

def to_16bit_audio(audio : np.ndarray):
    audio_samples = np.array(audio * (2**15 - 1), dtype=np.int16)

    return audio_samples

class WebUI (BaseComponent):
    download_audio_js = """
        () =>{{
            let root = document.querySelector("body > gradio-app");
            if (root.shadowRoot != null)
                root = root.shadowRoot;
            let audio = root.querySelector("#{audio_id}").querySelector("audio");
            if (audio == undefined)
                return;
            audio = audio.src;
            let oA = document.createElement("a");
            oA.download = Math.floor(Math.random()*100000000)+'.wav';
            oA.href = audio;
            document.body.appendChild(oA);
            oA.click();
            oA.remove();
        }}
        """
    
    def __init__(self, device : str = 'cuda', lang = "en", displaywave : bool = False, use_api : bool = False) -> None:
        paths = os.listdir('models/')
        
        self.models : list[str] = []
        self.current_model : SynthesizerTrn = None
        self.device = device
        self.displaywave = displaywave 

        paths = sorted(paths, key=sort_key)

        for path in paths:
            model_path = os.path.join("models/", path)
            if os.path.isfile(model_path):
                continue

            self.models.append(str(model_path))

        self.app = gr.Blocks(title="Moe TTS")
        self.lang = Language(f"languages/{lang}.json")
        self.load_static(self.models[0])
        self.speakers = [translation(name, 'ja')[1] for sid, name in enumerate(self.current_model.speakers) if name != "None"]
        self.setup()
        
    def setup(self):
        with self.app:
            gr.Markdown(f"# {self.lang('Moe TTS Better WebUI')}\n\n"
                        f"{self.lang('Feel free to [open discussion]')}(https://huggingface.co/spaces/skytnt/moe-tts/discussions/new) "
                        f"{self.lang('if you want to add your model to this app.')}\n\n")

            models_choices = gr.Dropdown(label="Models", choices=self.models, value=self.models[0], interactive=True, type='index')
            
            info = Info(self.models[0]).render()
            

            with gr.Accordion(label=self.lang("Audio setting")):
                with gr.Row(elem_id="audio_setting_row", variant="panel"):
                    with gr.Column(scale=1):
                        using_symbols = gr.Checkbox(label=self.lang("Using symbols"), value=False)
                        # speakers = gr.Number(label='Speaker index', interactive=True)
                        choices_speakers = gr.Dropdown(label=self.lang('Choices speaker'), choices=self.speakers, value=self.speakers[0], interactive=True, type="value")
                    with gr.Column(scale=6):
                       
                        speed_setting = UsedAudioSetting(label=self.lang("Speed")).render()
                        

            tts_translate, tts_translate_choices = UserTranslate(lang=self.lang, checkbox_label=self.lang("Using Auto translate to"), textarea_label="Translate by Google Translate API").render()

            input_text = gr.TextArea(label=self.lang('Text'))

            submit = gr.Button(self.lang('Generation'))

            tts_output_message = gr.Textbox(label="Output Rate")
            tts_output = gr.Audio(label=self.lang("Output Audio"), elem_id=f"tts-audio")   
            video = gr.Video(label=self.lang("Output Wave"))

            tts_translate.change(fn=self.translate_to, inputs=[tts_translate, tts_translate_choices], outputs=input_text)

            download = gr.Button(self.lang("Download Audio"))
            download.click(None, [], [], _js=self.download_audio_js.format(audio_id=f"tts-audio"))

            models_choices.change(fn=self.load_model, inputs=models_choices, outputs=[info[0], choices_speakers], api_name="load_model")

            submit.click(fn=self.generation, inputs=[input_text, speed_setting, choices_speakers, using_symbols], outputs=[tts_output_message, tts_output, video])

            choices_speakers_api = gr.Number(label="choices_speakers_api", visible=False)
            submit_api = gr.Button("submit_api", visible=False)
            submit_api.click(fn=self.generation, inputs=[input_text, speed_setting, choices_speakers_api, using_symbols], outputs=[tts_output_message, tts_output, video], api_name="generation")

            gr.Markdown(
                "Unofficial demo for \n\n"
                "- [https://github.com/CjangCjengh/MoeGoe](https://github.com/CjangCjengh/MoeGoe)\n"
                "- [https://github.com/Francis-Komizu/VITS](https://github.com/Francis-Komizu/VITS)\n"
                "- [https://github.com/luoyily/MoeTTS](https://github.com/luoyily/MoeTTS)\n"
                "- [https://github.com/Francis-Komizu/Sovits](https://github.com/Francis-Komizu/Sovits)\n"
                "\nMulti translation by Google Translate API.\n\n"
            )

    def translate_to(self, text : str, language : str):

        languages = {"English" : "en", "Japanese": "ja"}

        text = translation(text, lang=languages[language])[0]

        return gr.update(value=text)

        
    def enable_auto_translate(self, change):
        return gr.update(visible=change)

    def generation(self, text, speed : float = 1, speaker: str = "", using_symbols : bool = False):

        speaker_id = int(self.speakers.index(speaker))
        print("Using speaker: " + translation(self.current_model.speakers[speaker_id], lang='ja')[1])   

        return self.generation(text, speed, speaker_id, using_symbols)
    
    def generation(self, text, speed : float = 1, speaker_id : int = 0, using_symbols : bool = False):

        if speaker_id >= len(self.current_model.speakers):
            print(f'TTS: Index must be smaller {len(self.current_model.speakers)}.')
            return f"Index must be smaller {len(self.current_model.speakers)}", None, None

        audio = self.current_model.to_speak(text, speaker_id, speed=speed, is_symbol=using_symbols)

        audio_samples = to_16bit_audio(audio[1])

        if self.displaywave:
            return audio[0], (audio[0], audio_samples), gr.update(value=gr.make_waveform((audio[0], audio_samples)))
        
        return audio[0], (audio[0], audio_samples), None


    def load_model(self, index : int):
        path = self.models[index]

        if self.current_model is not None:
            print(f'{bcolors.WARNING}TTS : {bcolors.ENDC}{bcolors.FAIL}Free memory.{bcolors.ENDC}')
            self.current_model.free_mem()

        print(f'TTS : Load {path}...')

        self.current_model = self.load_static(path)

        info = Info(path)

        self.speakers = [translation(name, 'ja')[1] for sid, name in enumerate(self.current_model.speakers) if name != "None"]

        return info.update(), gr.update(choices=self.speakers, value=self.speakers[0])

    def load_static(self, path : str):

        config_path = os.path.join(path, 'config.json')

        if not os.path.exists(config_path):
            config_path = os.path.join(path, 'config.yaml')

        print(f'TTS : Load {path}...')

        model = SynthesizerTrn.from_pre_trained(path, self.device)

        self.current_model : SynthesizerTrn = model

        hps = OmegaConf.load(config_path)

        model.speakers = [translation(name, 'ja')[1] for sid, name in enumerate(hps.speakers) if name != "None"]

        return model

    def get_current_model(self):
        return self.current_model

    def render(self):
        return self.app
