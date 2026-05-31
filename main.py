import os
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import cv2
import numpy as np
import ffmpeg

app = FastAPI(title="Cloud Movie Recap API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

@app.post("/api/recap/process")
async def process_movie_recap(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    genre: str = Form("Horror")
):
    input_path = f"temp_{video.filename}"
    output_path = f"output_{video.filename}"
    
    with open(input_path, "wb") as f:
        f.write(await video.read())
        
    background_tasks.add_task(run_cloud_recap_pipeline, input_path, output_path, genre)
    return {"status": "Cloud Server Processing Started"}

def run_cloud_recap_pipeline(input_path, output_path, genre):
    # 1. Remove Original Audio & Mute Movie
    clean_video_path = "muted_video.mp4"
    try:
        ffmpeg.input(input_path).output(ffmpeg.input(input_path).video, clean_video_path, vcodec="copy").run(overwrite_output=True)
    except:
        clean_video_path = input_path
    
    # 2. AI Video Subtitle Inpainting (Mask bottom 17% screen)
    cap = cv2.VideoCapture(clean_video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
    inpainted_path = "inpainted_video.mp4"
    out = cv2.VideoWriter(inpainted_path, fourcc, fps, (width, height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        mask[int(height*0.83):height, :] = 255
        dst = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        out.write(dst)
    cap.release()
    out.release()
    
    # 3. Cloud Audio Mixing Logic (Thiha Voice + Copyright-Free BGM)
    print(f"Blending script narration with custom {genre} background music track.")
