import argparse
import torch
from safetensors.torch import save_model
from modules.models import SynthesizerTrn
import os
from omegaconf import OmegaConf
import json

def main(args):
    save_dtype = torch.float32
    
    if args.dtype == 'fp16':
        save_dtype = torch.float16
        
    model = SynthesizerTrn.from_pre_trained(args.model_dir, dtype=save_dtype)
    
    # save_dict = model.state_dict()
    
    os.makedirs(args.save_to, exist_ok=True)
    
    save_model(model, os.path.join(args.save_to, "model.safetensors"))
    if args.save_config_as == "yaml":
        OmegaConf.save(model.hps, os.path.join(args.save_to, "config.yaml"))
    else:
        with open(os.path.join(args.save_to, "config.json"), 'w') as f:
            json.dump(model.hps, f)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--model_dir', type=str, required=True)
    parser.add_argument('--save_to', type=str, required=True)
    parser.add_argument('--dtype', type=str, default='fp32')
    parser.add_argument('--save_config_as', type=str, default='yaml')
    
    args = parser.parse_args()
    
    main(args=args)