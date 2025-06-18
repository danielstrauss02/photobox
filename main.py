from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import cv2
import threading

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html", media_type="text/html")

# cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

pipeline = "v4l2src device=/dev/video3 ! video/x-raw,framerate=15/1,width=640,height=480 ! jpegenc ! appsink emit-signals=true sync=false caps=image/jpeg"
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

# Lock for thread-safe frame reading
lock = threading.Lock()

def generate_frames():
    while True:
        with lock:
            success, jpeg_frame = cap.read()
        if not success:
            continue
        frame_bytes = jpeg_frame.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/snapshot")
async def snapshot():
    with lock:
        success, jpeg_frame = cap.read()
    if not success:
        return Response(status_code=500)
    return Response(content=jpeg_frame.tobytes(), media_type="image/jpeg")