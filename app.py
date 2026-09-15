from flask import Flask, jsonify, render_template
import requests

from flask_cors import CORS
import obs_monitor

import subprocess
import cv2
from flask import Response

from config import Config
import google_sheet
# from flask import request

app = Flask(__name__)

CORS(app)

def generate_video(stream_url):
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print(f"Unable to open stream: {stream_url}")
        return

        print(f"Video stream started: {stream_url}")

    try:
        while True:
            success, frame = cap.read()

            if not success:
                print(f"Unable to read stream: {stream_url}")
                break

            # Encode frame as JPEG
            success, buffer = cv2.imencode(
                ".jpg",
                frame
            )

            if not success:
                continue

            frame_bytes = buffer.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame_bytes
                + b"\r\n"
            )

    finally:
        cap.release()

        print(f"Video stream stopped: {stream_url}")

# Audio
def generate_audio(stream_url):
    command = [
        "ffmpeg",

        # RTSP input
        "-rtsp_transport",
        "tcp",

        "-i",
        stream_url,

        # Only process audio
        "-vn",

        # Convert to MP3
        "-acodec",
        "libmp3lame",

        # Audio settings
        "-ar",
        "44100",

        "-ac",
        "2",

        "-b:a",
        "128k",

        # Stream MP3 continuously
        "-f",
        "mp3",

        # Output to stdout
        "pipe:1"
    ]

    process = None

    try:

        print(
            f"Audio stream started: {stream_url}"
        )

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0
        )

        while True:

            data = process.stdout.read(4096)

            if not data:
                break

            yield data

    except Exception as ex:

        print(
            f"Audio stream error "
            f"{ip_address}: {ex}"
        )

    finally:

        if process is not None:

            process.kill()

            process.wait()

        print(
            f"Audio stream stopped: {stream_url}"
        )

# API
@app.route("/api/cameras")
def api_cameras():
    return jsonify(
        obs_monitor.get_results()
    )

# Overlay Page
@app.route("/overlay")
def overlay():

    return render_template("overlay.html")

# Button Page
@app.route("/button/<int:camera_id>")
def camera_button(camera_id):
    return render_template(
        "button.html",
        camera_id=camera_id
    )


# Button Stop Page
@app.route("/api/camera/<int:camera_id>/stop", methods=["POST"])
def stop_camera(camera_id):    
    camera = google_sheet.get_camera(camera_id)

    if camera is None:
        return jsonify({
            "success": False,
            "message": "Camera not found"
        }), 404

    camera_ids = [1, 2, 3, 4]
    results = []

    for recorder_id in camera_ids:

        url = (
            f"http://{camera['ip_address']}"
            f"/api/recorders/{recorder_id}/control/stop"
        )

    # url = f"http://{camera['ip_address']}/api/recorders/1/control/stop"
        try:
            # Call the external API
            response = requests.post(
                url,
                auth=("admin", "scapture123!"),
                headers={"Content-Type": "application/json"},
                verify=False,
                allow_redirects=False,
                timeout=5)

            results.append({
                "camera": recorder_id,
                "status": response.status_code,
                "response": response.text
            })

        except Exception as ex:
            results.append({
                "camera": recorder_id,
                "error": str(ex)
            })

            # print(f"url: {response.request.url}")
            # print(f"response: {response.status_code}")
            # print(f"Response Headers: {response.headers}")
            # print(f"Response Body: {response.text}")
    return jsonify({
        "success": True,
        "camera": results
    })

# Video streaming
@app.route("/video/<int:camera_id>")
def video(camera_id):
    camera = google_sheet.get_camera(camera_id)

    if camera is None:
        return "Camera not found", 404

    return Response(
        generate_video(camera["stream_url"]),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

# Audio
@app.route("/audio/<int:camera_id>")
def audio(camera_id):
    camera = google_sheet.get_camera(camera_id)

    if camera is None:
        return "Camera not found", 404

    return Response(
        generate_audio(camera["stream_url"]),
        mimetype="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# Main
if __name__ == "__main__":
    google_sheet.refresh_cache()

    # thread = threading.Thread(
    #     target=update_loop,
    #     daemon=True
    # )

    obs_monitor.start()
    print("OBS monitor started")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )