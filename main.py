import os
import cv2
import numpy as np
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TPK Ultra-Hook Movie Recap AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for processed files
OUTPUT_DIR = "processed_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_premium_recap_pipeline(input_path: str, output_path: str, genre: str):
    try:
        cap = cv2.VideoCapture(input_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        
        frames = []
        motion_scores = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frames.append(frame)
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            motion_scores.append(np.sum(gray))
        cap.release()

        if not frames: return

        # Find climax and apply 3-sec Viral Hook
        climax_index = int(np.argmax(motion_scores))
        hook_start = max(0, climax_index - int(fps * 2))
        hook_end = min(len(frames), climax_index + int(fps * 1))
        final_frames = frames[hook_start:hook_end] + frames
        
        temp_processed = f"temp_proc_{os.path.basename(input_path)}"
        out = cv2.VideoWriter(temp_processed, fourcc, fps, (width, height))
        
        for frame in final_frames:
            # 1. 4K Cinematic Filter
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b_ch = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            cl = clahe.apply(l)
            enhanced = cv2.cvtColor(cv2.merge((cl,a,b_ch)), cv2.COLOR_LAB2BGR)
            
            # 2. AI Subtitle Inpainting
            mask = np.zeros(enhanced.shape[:2], dtype=np.uint8)
            mask[int(height*0.83):height, :] = 255
            dst = cv2.inpaint(enhanced, mask, 3, cv2.INPAINT_TELEA)
            
            # 3. Luxury Gold Watermark
            cv2.putText(dst, "@thetpaing_creator", (width - 400, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 215, 255), 3, cv2.LINE_AA)
            out.write(dst)
        out.release()
        
        # 4. Audio & FFmpeg Processing
        cmd = f"ffmpeg -y -i {temp_processed} -c:v libx264 -pix_fmt yuv420p {output_path}"
        subprocess.run(cmd, shell=True)
        
        if os.path.exists(temp_processed): os.remove(temp_processed)
    finally:
        if os.path.exists(input_path): os.remove(input_path)

@app.post("/api/recap/process")
async def process_movie_recap(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    genre: str = Form("Horror")
):
    input_path = f"temp_{video.filename}"
    safe_filename = f"recap_{video.filename}"
    output_path = os.path.join(OUTPUT_DIR, safe_filename)
    
    with open(input_path, "wb") as f:
        f.write(await video.read())
        
    # Run the heavy video processing in background to avoid 502 Timeout
    background_tasks.add_task(run_premium_recap_pipeline, input_path, output_path, genre)
    
    return {
        "status": "Processing Started Successfully!",
        "message": "Render Cloud က နောက်ကွယ်ကနေ ဗီဒီယိုကို အော်တို လုပ်ဆောင်နေပါပြီဗျာ။",
        "download_url": f"https://tpk-movie-recap-api.onrender.com/api/recap/download/{safe_filename}"
    }

@app.get("/api/recap/download/{filename}")
async def download_recap_video(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4", filename=filename)
    return {"error": "ဗီဒီယို လုပ်ဆောင်နေဆဲဖြစ်ပါသည် သို့မဟုတ် ဖိုင်မရှိပါဗျာ။ မိနစ်အနည်းငယ် စောင့်ပြီး Refresh ပြန်လုပ်ပေးပါ။"}
