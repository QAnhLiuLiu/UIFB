"""Detection server for the FarmBot UI (index.html in the folder above).

    double-click 2_CHAY.bat     (or:  .venv\\Scripts\\python.exe server\\detect_server.py)

Then open  http://127.0.0.1:8001/  - the server also serves the UI. In the card "Mô hình nhận diện" pick a model,
press "Tải model", turn the camera on, and the plants are boxed live.

API (used by the UI):
  GET  /models               list of models and which one is loaded
  POST /load  {"model":id}   load a model (the previous one is freed)
  POST /detect?thr=&short=   body = JPEG image  ->  {"dets":[{"label","score","box":[x0,y0,x1,y1]}],"ms","w","h"}

--host 0.0.0.0 lets other devices on the same network use this computer's model. There is no login, so only do
that on a network you trust.
"""
import argparse, gc, os, sys, threading, time

import cv2
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detectors  # noqa: E402

UI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the UIFB folder (index.html)
NAMES = {"dino-lettuce": "DINO – chỉ xà lách (chính xác)",
         "dino-both": "DINO – xà lách + cỏ dại",
         "yolo": "YOLO – chỉ xà lách (nhanh)"}
state = {"id": None, "det": None}
lock = threading.Lock()  # one job at a time

app = FastAPI(title="FarmBot detection server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def free():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


@app.get("/models")
def models():
    items = [{"id": k, "name": NAMES.get(k, k), "classes": classes, "thr": thr, "available": os.path.exists(ckpt)}
             for k, (ckpt, classes, thr) in detectors.PRESETS.items()]
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU (không có GPU NVIDIA – DINO sẽ chậm)"
    return {"models": items, "loaded": state["id"], "gpu": gpu}


@app.post("/load")
async def load_model(request: Request):
    mid = (await request.json()).get("model")
    if mid not in detectors.PRESETS:
        return JSONResponse({"ok": False, "error": "Model không tồn tại"}, status_code=400)
    ckpt, classes, _ = detectors.PRESETS[mid]
    if not os.path.exists(ckpt):
        return JSONResponse({"ok": False, "error": "Không thấy file model: " + ckpt}, status_code=404)

    def work():
        with lock:
            if state["id"] == mid:
                return {"ok": True, "loaded": mid, "load_ms": 0}
            state["det"] = state["id"] = None
            free()
            t = time.time()
            det = (detectors.YoloDetector if mid == "yolo" else detectors.DinoDetector)(ckpt, classes)
            det(np.zeros((480, 640, 3), np.uint8), 0.5, 480)  # warm-up: the first call is slow
            state["det"], state["id"] = det, mid
            return {"ok": True, "loaded": mid, "load_ms": round((time.time() - t) * 1000)}

    try:
        return await run_in_threadpool(work)
    except Exception as e:  # e.g. out of GPU memory
        free()
        return JSONResponse({"ok": False, "error": str(e)[:300]}, status_code=500)


@app.post("/detect")
async def detect(request: Request, thr: float = 0.15, short: int = 480):
    data = await request.body()

    def work():
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            return JSONResponse({"error": "Ảnh không hợp lệ"}, status_code=400)
        with lock:
            det = state["det"]
            if det is None:
                return JSONResponse({"error": "Chưa tải model"}, status_code=409)
            t = time.time()
            dets = det(frame, thr, short)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            ms = (time.time() - t) * 1000
        H, W = frame.shape[:2]
        return {"dets": [{"label": l, "score": round(s, 3), "box": [round(v, 1) for v in b]} for l, s, b in dets],
                "ms": round(ms, 1), "w": W, "h": H}

    return await run_in_threadpool(work)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--preload", choices=list(detectors.PRESETS), default=None, help="load this model at start-up")
    args = ap.parse_args()
    print("Thiet bi:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU (khong co GPU NVIDIA)", flush=True)
    if args.preload:
        ckpt, classes, _ = detectors.PRESETS[args.preload]
        state["det"] = (detectors.YoloDetector if args.preload == "yolo" else detectors.DinoDetector)(ckpt, classes)
        state["id"] = args.preload
    # Chỉ phục vụ đúng file giao diện (không mở cả thư mục, để không lộ model / code khi chạy --host 0.0.0.0)
    @app.get("/", include_in_schema=False)
    def ui():
        return FileResponse(os.path.join(UI_DIR, "index.html"), headers={"Cache-Control": "no-cache"})

    print(f"Mo trinh duyet: http://127.0.0.1:{args.port}/   (Ctrl+C hoac dong cua so nay de tat)", flush=True)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
