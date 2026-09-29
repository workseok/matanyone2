"""
A helper function to get a default model for quick testing
"""
from omegaconf import open_dict
from hydra import compose, initialize

import torch
from matanyone2.model.matanyone2 import MatAnyone2
from matanyone2.utils.device import get_default_device

def get_matanyone2_model(ckpt_path, device=None) -> MatAnyone2:
    initialize(version_base='1.3.2', config_path="../config", job_name="eval_our_config")
    cfg = compose(config_name="eval_matanyone_config")

    with open_dict(cfg):
        cfg['weights'] = ckpt_path

    # 호출부에서 device를 넘기지 않으면 get_default_device()로 결정합니다.
    # (mps를 먼저 시도하고, 실패 시 자동으로 cpu로 전환)
    if device is None:
        device = get_default_device()

    matanyone2 = MatAnyone2(cfg, single_object=True).to(device).eval()
    model_weights = torch.load(cfg.weights, map_location=device)
    matanyone2.load_weights(model_weights)

    return matanyone2
