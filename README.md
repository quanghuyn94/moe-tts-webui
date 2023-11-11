# The better web ui for MOE-TTS

Preview:

![](preview.png)

## Features:
- Text-to-speech, of course.

## Used:

1. Install requirements:

```bash
pip install -r requirements.txt
```

2. Web UI:

```bash
python app.py --displaywave
```

## Note:

+ You should install **Visual Studio** if you use Windows.
+ The installation of pyopenjtalk may fail. If that happens, you should go to https://github.com/r9y9/pyopenjtalk to seek help.

## Model structure:

+ models/you_model_name/
- - model.pth
- - config.json (.yaml)
- - info.json (.yaml) (Options)
- - cover.jpg (Options)

## Very Thank:
- VITS : [jaywalnut310](https://github.com/jaywalnut310/vits)
- VITS Model : [Francis-Komizu](https://github.com/Francis-Komizu/VITS)
- Demo : [CjangCjengh](https://github.com/CjangCjengh/MoeGoe)
- Demo : [luoyily](https://github.com/luoyily/MoeTTS)
- Demo : [skytnt](https://huggingface.co/spaces/skytnt/moe-tts)
- You. 🫵
