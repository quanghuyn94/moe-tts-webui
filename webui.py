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

#Import componets
from src.components.info import Info
from src.components.user_translate import UserTranslate
from src.components.basecomponent import BaseComponent
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
    return outputs.text

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

    def enable_auto_translate(self, change):
        return gr.update(visible=change)

    def generation(self, text, speed : float = 1, speaker_id : int = 0, using_symbols : bool = False):
        os.makedirs("outputs", exist_ok=True)
        if speaker_id >= len(self.current_model.speakers):
            print(f'TTS: Index must be smaller {len(self.current_model.speakers)}.')
            return f"Index must be smaller {len(self.current_model.speakers)}", None, None

        audio = self.current_model.to_speak(text, speaker_id, speed=speed, is_symbol=using_symbols)

        audio_samples = to_16bit_audio(audio[1])

        audio_file = AudioSegment(
            audio_samples.tobytes(),
            frame_rate=audio[0],
            sample_width=2,
            channels=1
            )

        path = audio_file.export(f"outputs/{translator.translate(self.current_model.speakers[int(speaker_id)], dest='ja').pronunciation.title()}_{text}.mp3", format="mp3")

        if self.displaywave:
            return "Sucess", (audio[0], audio_samples), gr.update(value=gr.make_waveform((audio[0], audio_samples)))
        
        return "Sucess", (audio[0], audio_samples), None

    def load_model(self, index : int):
        path = self.models[index]

        if self.current_model is not None:
            print(f'{bcolors.WARNING}TTS : {bcolors.ENDC}{bcolors.FAIL}Free memory.{bcolors.ENDC}')
            self.current_model.free_mem()

        print(f'TTS : Load {path}...')

        self.current_model = self.load_static(path)

        info = Info(path)

        return info.update()

    def load_static(self, path : str):

        config_path = os.path.join(path, 'config.json')

        if not os.path.exists(config_path):
            config_path = os.path.join(path, 'config.yaml')

        print(f'TTS : Load {path}...')

        model = SynthesizerTrn.from_pre_trained(path, self.device)

        self.current_model : SynthesizerTrn = model

        hps = OmegaConf.load(config_path)

        model.speakers = [translation(name, 'en') for sid, name in enumerate(hps.speakers) if name != "None"]

        return model

    def __init__(self, device : str = 'cuda', displaywave : bool = False) -> None:
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
        self.load_static(self.models[0])
        self.setup()

    def setup(self):
        with self.app:
            gr.Markdown("# Moe TTS Better WebUI\n\n"
                        "Feel free to [open discussion](https://huggingface.co/spaces/skytnt/moe-tts/discussions/new) "
                        "if you want to add your model to this app.\n\n")

            drop_box = gr.Dropdown(label="Models", choices=self.models, value=self.models[0], interactive=True, type='index')
            
            info = Info(self.models[0]).render()

            with gr.Accordion(label="Audio setting"):
                with gr.Row(elem_id="audio_setting_row", variant="panel"):
                    with gr.Column(scale=1):
                        using_symbols = gr.Checkbox(label="Using symbols", value=False)
                        speakers = gr.Number(label='Speaker index', interactive=True)
                    with gr.Column(scale=6):
                        speed_setting = UsedAudioSetting().render()

            tts_translate = UserTranslate().render()

            input_text = gr.TextArea(label='Text')

            submit = gr.Button('Generation')

            tts_output_message = gr.Textbox(label="Output Message")
            tts_output = gr.Audio(label="Output Audio", elem_id=f"tts-audio")   
            video = gr.Video(label="Output Wave")

            tts_translate.change(fn=translation, inputs=tts_translate, outputs=input_text)

            download = gr.Button("Download Audio")
            download.click(None, [], [], _js=self.download_audio_js.format(audio_id=f"tts-audio"))

            drop_box.change(fn=self.load_model, inputs=drop_box, outputs=info)

            submit.click(fn=self.generation, inputs=[input_text, speed_setting, speakers, using_symbols], outputs=[tts_output_message, tts_output, video])

            gr.Markdown(
                "Unofficial demo for \n\n"
                "- [https://github.com/CjangCjengh/MoeGoe](https://github.com/CjangCjengh/MoeGoe)\n"
                "- [https://github.com/Francis-Komizu/VITS](https://github.com/Francis-Komizu/VITS)\n"
                "- [https://github.com/luoyily/MoeTTS](https://github.com/luoyily/MoeTTS)\n"
                "- [https://github.com/Francis-Komizu/Sovits](https://github.com/Francis-Komizu/Sovits)\n"
                "\nMulti translation by Google Translate API.\n\n"
            )

    def render(self):
        return self.app
