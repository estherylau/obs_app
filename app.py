from flask import Flask
from flask import jsonify
import requests
from flask import render_template

from flask_cors import CORS

import threading
import time

from config import Config
import google_sheet
from flask import request

import camera_monitor

app = Flask(__name__)

CORS(app)

##########################################################
# Background Thread
##########################################################

def update_loop():
    while True:
        try:
            google_sheet.refresh_cache()
            print("Google Sheet refreshed")

            camera_monitor.start()
            print("Start camera monitoring")

        except Exception as ex:
            print(ex)

        time.sleep(Config.REFRESH_SECONDS)


##########################################################
# API
##########################################################

@app.route("/api/cameras")
def api_cameras():
    return jsonify(
        google_sheet.get_cache()
    )


##########################################################
# Overlay Page
##########################################################

@app.route("/overlay")
def overlay():

    return render_template("overlay.html")



##########################################################
# Button Page
##########################################################
@app.route("/button/<int:camera_id>")
def camera_button(camera_id):

    return render_template(
        "button.html",
        camera_id=camera_id
    )


##########################################################
# Button Stop Page
##########################################################
@app.route("/api/camera/<int:camera_id>/stop", methods=["POST"])
def stop_camera(camera_id):
    print('TODO stop video')
    
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


##########################################################
# Main
##########################################################

if __name__ == "__main__":
    google_sheet.refresh_cache()

    thread = threading.Thread(
        target=update_loop,
        daemon=True
    )

    thread.start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )