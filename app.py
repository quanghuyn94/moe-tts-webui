from argparse import ArgumentParser
import torch
from webui import WebUI

def argument_parse():
    parser = ArgumentParser()
    # parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--device', type=str, default='cuda') #Cuda make you fast!.
    parser.add_argument("--share", action="store_true", default=False, help="share gradio app")
    parser.add_argument("--displaywave", action="store_true", default=False, help="turn on display of sound waves")
    parser.add_argument("--lang", default='en', type=str, help="turn on display of sound waves")
    args = parser.parse_args()

    return args

def main():
    args = argument_parse()

    if args.device == 'cuda' and not torch.cuda.is_available():
        print("Can't using a CUDA, auto switch to CPU.")
        args.device = "cpu"

    if torch.cuda.is_available() and args.device == 'cuda':
        print(f'TTS : Cuda available, using cuda.')
        print(f'Cuda : Device {torch.cuda.get_device_name(0)} CUDA VERSION : {torch.version.cuda}')
    else:
        print(f'TTS : Using {args.device}...')
    
    
    
    webui = WebUI(args.device, args.lang, args.displaywave)
    webui.render().launch(share=args.share)

    

if __name__ == "__main__":
    main()
