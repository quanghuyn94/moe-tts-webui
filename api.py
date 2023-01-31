from fastapi import FastAPI, File
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from pydantic import BaseModel
import uvicorn, os
from modules.models import SynthesizerTrn
from pydub import AudioSegment
import numpy as np
from googletrans import Translator


class GenerationRequest(BaseModel):
    text : str
    speaker_id : int

    speed : float = 1
    is_symbol : bool = False
    
app = FastAPI()
translator = Translator()

def to_16bit_audio(audio : np.ndarray):
    audio_samples = np.array(audio * (2**15 - 1), dtype=np.int16)

    return audio_samples

def sort_key(x):
    if x.isnumeric():
        return (0, int(x))
    else:
        return (1, x)

model_names = os.listdir('models/')

model_names  = sorted(model_names, key=sort_key)

model : SynthesizerTrn = SynthesizerTrn.from_pre_trained(f"models/{model_names[0]}")

@app.post("/generation")
def generation(request : GenerationRequest):
    '''Generation text-to-speech.
    :request Is a GenerationRequest. '''
    os.makedirs("outputs", exist_ok=True)
    audio_rate , audio_narray = model.to_speak(request.text, request.speaker_id, request.speed, request.is_symbol)
    audio_narray = to_16bit_audio(audio_narray)

    audio_file = AudioSegment(
        audio_narray.tobytes(),
        frame_rate=audio_rate,
        sample_width=2,
        channels=1
    )

    path = audio_file.export(f"outputs/{translator.translate(model.speakers[request.speaker_id], dest='ja').pronunciation.title()}_{request.text}.mp3", format="mp3")

    return File("outputs/audio.ogg", filename="audio.ogg")

@app.post("/loadmodel")
def load_mode(index : int):
    global model
    if model is not None:
        model.free_mem()

    model = SynthesizerTrn.from_pre_trained(f"models/{model_names[index]}")
    return "Success"

@app.get("/listmodels")
def list_modes():
    return model_names

@app.get("/")
def static():
    return "Not thing"

def run(port : int = 6969):
    uvicorn.run("api:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=4315, log_level="info")


        



