import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from omegaconf import OmegaConf
import librosa
import numpy as np
import torch
from torch import no_grad, LongTensor
import modules.commons as commons
import modules.utils as utils
import gradio as gr
import gradio.utils as gr_utils
import gradio.processing_utils as gr_processing_utils
from modules.models import SynthesizerTrn
from text import text_to_sequence, _clean_text
from modules.mel_processing import spectrogram_torch
from googletrans import Translator
from extension.bcolors import bcolors
from old.ui import WebUI

limitation = os.getenv("SYSTEM") == "spaces"  # limit text and audio length in huggingface spaces

audio_postprocess_ori = gr.Audio.postprocess
translator = Translator()

def audio_postprocess(self, y):
    data = audio_postprocess_ori(self, y)
    if data is None:
        return None
    return gr_processing_utils.encode_url_or_file_to_base64(data["name"])


gr.Audio.postprocess = audio_postprocess

def torch_gc():
    '''Giải phóng bộ nhớ sau khi sử dụng.'''
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def translate_to(text, lang='en'):
    output = translator.translate(text, dest=lang)

    return output.text, output.pronunciation

def get_text(text, hps, is_symbol):
    text_norm = text_to_sequence(text, hps.symbols, [] if is_symbol else hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = LongTensor(text_norm)
    return text_norm


def create_tts_fn(model : SynthesizerTrn, hps, speaker_ids, lowvram=False, multilang = False):

    def tts_fn(text, speaker, speed, is_symbol):

        
        audio = model.to_speak(text, speaker, speed, is_symbol)

        audio_samples = np.array(audio[1] * (2**15 - 1), dtype=np.int16)

        torch_gc()

        return "Success", (hps.data.sampling_rate, audio_samples)


    return tts_fn


def create_vc_fn(model : SynthesizerTrn, hps, speaker_ids, lowvram=False):

    def vc_fn(original_speaker, target_speaker, input_audio):
        
        if input_audio is None:
            return "You need to upload an audio", None
        sampling_rate, audio = input_audio
        duration = audio.shape[0] / sampling_rate
        if limitation and duration > 30:
            return "Error: Audio is too long", None
        original_speaker_id = speaker_ids[original_speaker]
        target_speaker_id = speaker_ids[target_speaker]

        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        if sampling_rate != hps.data.sampling_rate:
            audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=hps.data.sampling_rate)
        with no_grad():
            y = torch.FloatTensor(audio)
            y = y.unsqueeze(0)
            spec = spectrogram_torch(y, hps.data.filter_length,
                                     hps.data.sampling_rate, hps.data.hop_length, hps.data.win_length,
                                     center=False).to(device)
            spec_lengths = LongTensor([spec.size(-1)]).to(device)
            sid_src = LongTensor([original_speaker_id]).to(device)
            sid_tgt = LongTensor([target_speaker_id]).to(device)
            audio = model.voice_conversion(spec, spec_lengths, sid_src=sid_src, sid_tgt=sid_tgt)[0][
                0, 0].data.cpu().float().numpy()
        del y, spec, spec_lengths, sid_src, sid_tgt

        torch_gc()
        
        return "Success", (hps.data.sampling_rate, audio)

    return vc_fn


def create_soft_vc_fn(model : SynthesizerTrn, hps, speaker_ids, lowvram=False):

    def soft_vc_fn(target_speaker, input_audio1, input_audio2):

        input_audio = input_audio1
        if input_audio is None:
            input_audio = input_audio2
        if input_audio is None:
            return "You need to upload an audio", None
        sampling_rate, audio = input_audio
        duration = audio.shape[0] / sampling_rate
        if limitation and duration > 30:
            return "Error: Audio is too long", None
        target_speaker_id = speaker_ids[target_speaker]

        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        if sampling_rate != 16000:
            audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=16000)
        with torch.inference_mode():
            units = hubert.units(torch.FloatTensor(audio).unsqueeze(0).unsqueeze(0).to(device))
        with no_grad():
            unit_lengths = LongTensor([units.size(1)]).to(device)
            sid = LongTensor([target_speaker_id]).to(device)
            audio = model.infer(units, unit_lengths, sid=sid, noise_scale=.667,
                                noise_scale_w=0.8)[0][0, 0].data.cpu().float().numpy()
        del units, unit_lengths, sid

        torch_gc()

        return "Success", (hps.data.sampling_rate, audio)


    return soft_vc_fn


def create_to_symbol_fn(hps):
    def to_symbol_fn(is_symbol_input, input_text, temp_text):
        return (_clean_text(input_text, hps.data.text_cleaners), input_text) if is_symbol_input \
            else (temp_text, temp_text)

    return to_symbol_fn


def argument_init():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--device', type=str, default='cuda') #Cuda fuckkkk boyyyyyyyyyyyyy.
    parser.add_argument("--share", action="store_true", default=False, help="share gradio app")
    parser.add_argument("--lowvram", action="store_true", default=False)
    parser.add_argument("--apionly", action="store_true", default=False)
    parser.add_argument("--multilang", action="store_true", default=False, help="Switch to multi language input")
    args = parser.parse_args()

    if args.multilang:
        print("Using multi language.")
    return args

if __name__ == '__main__':
    
    args = argument_init()

    device = torch.device(args.device)

    if torch.cuda.is_available() and args.device == 'cuda':
        print(f'TTS : Cuda available, auto using cuda.')
        print(f'Cuda : Device {torch.cuda.get_device_name(0)} CUDA VERSION : {torch.version.cuda}')
        device = torch.device('cuda')
    else:
        print(f'TTS : Using {args.device}...')
        device = torch.device(args.device)

    
    skip_index = [15]
    models_tts = []
    models_vc = []
    models_soft_vc = []
    max_load = 10

    if args.lowvram:
        print("Using lowvram")

    with open("saved_model/info.json", "r", encoding="utf-8") as f:
        models_info = json.load(f)

    lowvram : bool = args.lowvram 

    print('TTS : Load model...')
    models = models_info.items()
    for i, info in models:
        if int(i) >= max_load:
            break 
        name = info["title"]
        author = info["author"]
        lang = info["lang"]
        example = info["example"]
        config_path = f"saved_model/{i}/config.json"
        model_path = f"saved_model/{i}/model.pth"
        cover = info["cover"]
        cover_path = f"saved_model/{i}/{cover}" if cover else None
        hps = utils.get_hparams_from_file(config_path)
        
        if int(i) in skip_index:
            print(f'{bcolors.WARNING}TSS:{bcolors.ENDC} Skip {info["title"]}')
            continue
        print("====================================")
        print(f'TTS : {i} Load {name}...')

        model = SynthesizerTrn.from_pre_trained(f"saved_model/{i}/")

        speaker_ids = [sid for sid, name in enumerate(hps.speakers) if name != "None"]
        speakers = [str(translate_to(name, lang='ja')[1]).title() for sid, name in enumerate(hps.speakers) if name != "None"]
        
        t = info["type"]
        if t == "vits":
            models_tts.append((name, author, cover_path, speakers, lang, example,
                               hps.symbols, create_tts_fn(model, hps, speaker_ids, lowvram=lowvram, multilang=args.multilang),
                               create_to_symbol_fn(hps)))
            models_vc.append((name, author, cover_path, speakers, create_vc_fn(model, hps, speaker_ids, lowvram=lowvram)))
        elif t == "soft-vits-vc":
            models_soft_vc.append((name, author, cover_path, speakers, create_soft_vc_fn(model, hps, speaker_ids, lowvram=lowvram)))
        print(f'TTS : Load {name} complete.')
        print("====================================")
    hubert = torch.hub.load("bshall/hubert:main", "hubert_soft", trust_repo=True).to(device)
    print('TTS : Load done!')

    if args.apionly == False:
        print('TTS : Using WebUI.')
        ui = WebUI(models_tts=models_tts, models_vc=models_vc, models_soft_vc=models_soft_vc)
        ui.run()
