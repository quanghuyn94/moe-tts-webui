from omegaconf import OmegaConf
import json

infos : dict = OmegaConf.load("saved_model/info.json")

for key, value in infos.items():
    OmegaConf.save(value, f"saved_model/{key}/info.yaml")
