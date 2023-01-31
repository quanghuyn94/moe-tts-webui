# Basic user manual Web UI
    Basic user manual Web UI.
## Used:

1. Install requirements:

```bash
pip install -r requirements.txt
```

2. Set up plugins:

```bash
cd plugins
python setup.py install
```

3. Web UI:

```bash
python app.py --displaywave
```

3. Or API Server:

```bash
python app.py --api
```
# Web UI

## **Models:**
- This is where you select your models. Choose the saved `models` in the models folder.

## **Audio setting:**
    This is where you set up audio-related settings.
    
- **Using symbols** : Whether or not to use symbols, if selected, `symbols` will be used. **`However`**, in the `Text` section below, you must use `symbols`, or the audio will be faulty, `symbols` can be obtained from above. Default is `False`.
- **Choices speaker** : Select a `speaker` from the list. The default is the `first speaker`.
- **Audio speed** : The `speaker's` speaking speed. Default is `1`.

## **Using Auto translate:**
    This is the section for you to use the translation directly on the website. Turn it on if you need a translation.
- **Choices language**: Select the language to be translated. The translated text will be in the `Text` section.
- **Translate**: Enter the text to be translated, the translated text according to the `Choosing a language` will be displayed in the `Text` section.
## **Text:**
- This is where you enter the text. `Note`, when entering text, you must enter the text in the `speaker's` language. For convenience, use `Auto translate`.
## **Generation:**
- Click here to start the `text to speech` process.
## **Output message:**
- Returns the `success` or `failure` message.
## **Output audio:**
- Returns the audio.
## **Output Wave:**
- Display the audio wave.
## **Download audio:**
- Download the audio.

# API server

## **post : /loadmodel**
- Load a TTS model.
- - @param index (int): The index number of the model in the list, which can be viewed from "/listmodels".
## **post : /generation**
- Generation the text to speech
- - @param request: A GenerationRequest.
- <font color='red'>Importance</font> : The model needs to be loaded first. Using `/loadmodel`.
## **get : /listmodels**
- Get a current list models.