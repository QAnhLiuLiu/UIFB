"""Grounding DINO helpers (copied from train_gdino.py of the training project): load a checkpoint + class scores."""
import json, os

import numpy as np
import torch

CLASSES = ["lettuce", "weed"]
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def load(init, device, classes=None):
    """Loads a checkpoint folder. The class list comes from `classes`, else from <init>/classes.json."""
    from transformers import AutoProcessor, GroundingDinoForObjectDetection
    cfile = os.path.join(init, "classes.json")
    if classes:
        CLASSES[:] = classes
    elif os.path.exists(cfile):
        CLASSES[:] = json.load(open(cfile))
    processor = AutoProcessor.from_pretrained(init)
    model = GroundingDinoForObjectDetection.from_pretrained(init)
    model.config.auxiliary_loss = True
    text = processor.tokenizer(" . ".join(CLASSES) + " .", return_tensors="pt")
    return processor, model.to(device), {k: v.to(device) for k, v in text.items()}


def class_scores(logits, input_ids, model):
    """(B, Q, T) token logits -> (B, Q, num_classes) probabilities (max over the tokens of each class phrase)."""
    from transformers.models.grounding_dino.modeling_grounding_dino import build_label_maps
    maps = build_label_maps(logits, input_ids)[0].bool()  # (num_classes, T)
    prob = logits.sigmoid()
    return torch.stack([prob[..., m].max(-1).values for m in maps], -1)
