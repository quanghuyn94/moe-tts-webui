import gradio as gr
import gradio.utils as gr_utils
import gradio.processing_utils as gr_processing_utils
import base64
from googletrans import Translator


class WebUI:
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

    async def translation(self, text):
        outputs = self.translator.translate(text=text, dest='ja')
        return outputs.text

    def enable_auto_translate(self, change):
        return gr.update(visible=change)

    def __init__(self, models_tts : list, models_vc : list, models_soft_vc : list) -> None:
        self.app = gr.Blocks(title="Moe TTS")
        app = self.app
        self.translator = Translator()

        with app:
            gr.Markdown("# Moe TTS And Voice Conversion Using VITS Model\n\n"
                        "[Open In Colab]"
                        "(https://colab.research.google.com/drive/14Pb8lpmwZL-JI5Ub6jpG4sz2-8KS0kbS?usp=sharing)"
                        " without queue and length limitation.\n\n"
                        "Feel free to [open discussion](https://huggingface.co/spaces/skytnt/moe-tts/discussions/new) "
                        "if you want to add your model to this app.\n\n"
                        "Cuda should be used because it's FAST! FUCKKKBOY.")
            with gr.Tabs():
                with gr.TabItem("TTS"):
                    with gr.Tabs():
                        for i, (name, author, cover_path, speakers, lang, example, symbols, tts_fn,
                                to_symbol_fn) in enumerate(models_tts):
                            with gr.TabItem(f"model{i}"):
                                with gr.Column():
                                    with open(cover_path, 'rb') as image_file:
                                        image_content = image_file.read()
                                        base64_image = base64.b64encode(image_content).decode()
                                    cover_markdown = f"""<img src="data:image/png;base64,{base64_image}" alt="my image">"""
                                    gr.Markdown(f"## {name}\n\n"
                                                f"{cover_markdown}\n\n"
                                                f"Model author: {author}\n\n"
                                                f"Language author: {lang}\n\n")
                                    check_box = gr.Checkbox(label="Using Auto translate to ja?", value=False)

                                    tts_translate = gr.TextArea(label="Translate by Google Translate API", elem_id=f"tts-translate-input", visible=False)

                                    tts_input1 = gr.TextArea(label="Text (150 words limitation)", value=example, elem_id=f"tts-input{i}")
                                    
                                    tts_translate.change(fn=self.translation, inputs=tts_translate, outputs=tts_input1)

                                    check_box.change(fn=self.enable_auto_translate, inputs=check_box, outputs=tts_translate)

                                    tts_input2 = gr.Dropdown(label="Speaker", choices=speakers, type="index", value=speakers[0])
                                    tts_input3 = gr.Slider(label="Speed", value=1, minimum=0.5, maximum=2, step=0.1)
                                    

                                    with gr.Accordion(label="Advanced Options", open=False):
                                        temp_text_var = gr.Variable()
                                        symbol_input = gr.Checkbox(value=False, label="Symbol input")
                                        symbol_list = gr.Dataset(label="Symbol list", components=[tts_input1],
                                                                    samples=[[x] for x in symbols],
                                                                    elem_id=f"symbol-list{i}")
                                        symbol_list_json = gr.Json(value=symbols, visible=False)
                                    tts_submit = gr.Button("Generate", variant="primary")
                                    tts_output1 = gr.Textbox(label="Output Message")
                                    tts_output2 = gr.Audio(label="Output Audio", elem_id=f"tts-audio{i}")
                                    
                                    download = gr.Button("Download Audio")
                                    download.click(None, [], [], _js=self.download_audio_js.format(audio_id=f"tts-audio{i}"))

                                    tts_submit.click(tts_fn, [tts_input1, tts_input2, tts_input3, symbol_input], [tts_output1, tts_output2])

                                    symbol_input.change(to_symbol_fn, [symbol_input, tts_input1, temp_text_var], [tts_input1, temp_text_var])

                                    symbol_list.click(None, [symbol_list, symbol_list_json], [],
                                                        _js=f"""
                                    (i,symbols) => {{
                                        let root = document.querySelector("body > gradio-app");
                                        if (root.shadowRoot != null)
                                            root = root.shadowRoot;
                                        let text_input = root.querySelector("#tts-input{i}").querySelector("textarea");
                                        let startPos = text_input.selectionStart;
                                        let endPos = text_input.selectionEnd;
                                        let oldTxt = text_input.value;
                                        let result = oldTxt.substring(0, startPos) + symbols[i] + oldTxt.substring(endPos);
                                        text_input.value = result;
                                        let x = window.scrollX, y = window.scrollY;
                                        text_input.focus();
                                        text_input.selectionStart = startPos + symbols[i].length;
                                        text_input.selectionEnd = startPos + symbols[i].length;
                                        text_input.blur();
                                        window.scrollTo(x, y);
                                        return [];
                                    }}""")

                with gr.TabItem("Voice Conversion"):
                    with gr.Tabs():
                        for i, (name, author, cover_path, speakers, vc_fn) in enumerate(models_vc):
                            with gr.TabItem(f"model{i}"):
                                # cover_markdown = f"![cover](file/{cover_path})\n\n" if cover_path else ""
                                with open(cover_path, 'rb') as image_file:
                                    image_content = image_file.read()
                                    base64_image = base64.b64encode(image_content).decode()
                                cover_markdown = f"""<img src="data:image/png;base64,{base64_image}" alt="my image">"""
                                gr.Markdown(f"## {name}\n\n"
                                            f"{cover_markdown}"
                                            f"model author: {author}")
                                vc_input1 = gr.Dropdown(label="Original Speaker", choices=speakers, type="index",
                                                        value=speakers[0])
                                vc_input2 = gr.Dropdown(label="Target Speaker", choices=speakers, type="index",
                                                        value=speakers[min(len(speakers) - 1, 1)])
                                vc_input3 = gr.Audio(label="Input Audio (30s limitation)")
                                vc_submit = gr.Button("Convert", variant="primary")
                                vc_output1 = gr.Textbox(label="Output Message")
                                vc_output2 = gr.Audio(label="Output Audio", elem_id=f"vc-audio{i}")
                                download = gr.Button("Download Audio")
                                download.click(None, [], [], _js=self.download_audio_js.format(audio_id=f"vc-audio{i}"))
                                vc_submit.click(vc_fn, [vc_input1, vc_input2, vc_input3], [vc_output1, vc_output2])
                with gr.TabItem("Soft Voice Conversion"):
                    with gr.Tabs():
                        for i, (name, author, cover_path, speakers, soft_vc_fn) in enumerate(models_soft_vc):
                            with gr.TabItem(f"model{i}"):
                                # cover_markdown = f"![cover](file/{cover_path})\n\n" if cover_path else ""
                                cover_markdow = ""
                                gr.Markdown(f"## {name}\n\n"
                                            f"{cover_markdown}"
                                            f"model author: {author}")
                                vc_input1 = gr.Dropdown(label="Target Speaker", choices=speakers, type="index",
                                                        value=speakers[0])
                                source_tabs = gr.Tabs()
                                with source_tabs:
                                    with gr.TabItem("microphone"):
                                        vc_input2 = gr.Audio(label="Input Audio (30s limitation)", source="microphone")
                                    with gr.TabItem("upload"):
                                        vc_input3 = gr.Audio(label="Input Audio (30s limitation)", source="upload")
                                vc_submit = gr.Button("Convert", variant="primary")
                                vc_output1 = gr.Textbox(label="Output Message")
                                vc_output2 = gr.Audio(label="Output Audio", elem_id=f"svc-audio{i}")
                                download = gr.Button("Download Audio")
                                download.click(None, [], [], _js=self.download_audio_js.format(audio_id=f"svc-audio{i}"))
                                # clear inputs
                                source_tabs.set_event_trigger("change", None, [], [vc_input2, vc_input3],
                                                                js="()=>[null,null]")
                                vc_submit.click(soft_vc_fn, [vc_input1, vc_input2, vc_input3],
                                                [vc_output1, vc_output2])
            gr.Markdown(
                "Unofficial demo for \n\n"
                "- [https://github.com/CjangCjengh/MoeGoe](https://github.com/CjangCjengh/MoeGoe)\n"
                "- [https://github.com/Francis-Komizu/VITS](https://github.com/Francis-Komizu/VITS)\n"
                "- [https://github.com/luoyily/MoeTTS](https://github.com/luoyily/MoeTTS)\n"
                "- [https://github.com/Francis-Komizu/Sovits](https://github.com/Francis-Komizu/Sovits)\n"
                "\nMulti translation by Google Translate API."
            )

    def run(self, shared : bool = False):
        self.app.queue(concurrency_count=3).launch(show_api=False, share=shared)