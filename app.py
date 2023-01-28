from webui import WebUI

from argparse import ArgumentParser
import torch

def argument_parse():
    parser = ArgumentParser()
    # parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--device', type=str, default='cuda') #Cuda make you fast!.
    parser.add_argument("--share", action="store_true", default=False, help="share gradio app")
    parser.add_argument("--api", action="store_true", default=False, help="start api server only")
    parser.add_argument("--displaywave", action="store_true", default=False, help="turn on display of sound waves")
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

    if not args.api:
        app = WebUI(args.device, args.displaywave)
        app.render().launch(share=args.share)
    else:
        print("Run API server.")

        import api
        api.run()

    

if __name__ == "__main__":
    main()
