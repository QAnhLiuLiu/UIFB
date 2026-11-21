"""The two detectors used by the server (DINO and YOLO) and the list of models in ../models.

Runs on the NVIDIA GPU when there is one (half precision, fast); otherwise on the CPU (YOLO is usable, DINO is slow).
"""
import os

import numpy as np
import torch
import torch.nn.functional as F
from torchvision.ops import nms

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # everything needed is inside the model folders
from gdino_utils import MEAN, STD, class_scores, load  # noqa: E402

MODELS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PRESETS = {  # id: (checkpoint, classes, default threshold)
    "dino-lettuce": (os.path.join(MODELS, "dino_chi_xa_lach"), ["lettuce"], 0.15),
    "dino-both": (os.path.join(MODELS, "dino_xa_lach_co_dai"), ["lettuce", "weed"], 0.2),
    "yolo": (os.path.join(MODELS, "yolo_xa_lach.pt"), ["lettuce"], 0.15),
}


class DinoDetector:
    def __init__(self, ckpt, classes):
        _, self.model, self.text = load(ckpt, DEVICE, classes)
        self.classes = classes
        self.model.eval()
        self.dtype = torch.float16 if DEVICE == "cuda" else torch.float32
        if DEVICE == "cuda":
            self.model.half()
        self.mean = torch.tensor(MEAN, device=DEVICE).view(1, 3, 1, 1)
        self.std = torch.tensor(STD, device=DEVICE).view(1, 3, 1, 1)

    @torch.no_grad()
    def __call__(self, frame_bgr, thr, short, max_side=1024, iou=0.5):
        H, W = frame_bgr.shape[:2]
        k = min(short / min(W, H), max_side / max(W, H))
        nw, nh = max(32, round(W * k)), max(32, round(H * k))
        x = torch.from_numpy(np.ascontiguousarray(frame_bgr[:, :, ::-1])).to(DEVICE).permute(2, 0, 1)[None].float() / 255
        x = F.interpolate(x, size=(nh, nw), mode="bilinear", align_corners=False, antialias=True)
        x = ((x - self.mean) / self.std).to(self.dtype)
        out = self.model(pixel_values=x, **self.text)
        sc = class_scores(out.logits.float(), self.text["input_ids"], self.model)[0]
        s, lab = sc.max(-1)
        keep = s >= thr
        cx, cy, w, h = (out.pred_boxes[0].float()[keep] * torch.tensor([W, H, W, H], device=DEVICE)).unbind(-1)
        boxes = torch.stack([(cx - w / 2).clamp(0, W), (cy - h / 2).clamp(0, H), (cx + w / 2).clamp(0, W), (cy + h / 2).clamp(0, H)], -1)
        s, lab = s[keep], lab[keep]
        keep = nms(boxes, s, iou)
        return [(self.classes[int(lab[i])], float(s[i]), boxes[i].tolist()) for i in keep.tolist()]


class YoloDetector:
    def __init__(self, ckpt, classes):
        from ultralytics import YOLO
        self.model, self.classes = YOLO(ckpt), classes
        self.model.predict(np.zeros((480, 640, 3), np.uint8), imgsz=640, verbose=False)  # warm-up

    def __call__(self, frame_bgr, thr, short, **_):
        r = self.model.predict(frame_bgr, imgsz=max(320, short // 32 * 32), conf=thr, iou=0.6, max_det=300, verbose=False)[0]
        return [(self.classes[0], float(s), b) for b, s in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist())]
