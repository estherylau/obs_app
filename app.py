from flask import Flask
from flask import jsonify
from flask import render_template

from flask_cors import CORS

import threading
import time

from config import Config
import google_sheet
from flask import request

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
# Stop Ping Page
##########################################################
@app.route(
    "/api/camera/<int:camera_id>/stop",
    methods=["POST"]
)
def stop_camera(camera_id):

    result = google_sheet.stop_camera(camera_id)


    if result:

        # immediately update cache
        google_sheet.refresh_cache()

        return jsonify({
            "success":True,
            "camera":camera_id
        })


    return jsonify({
        "success":False,
        "message":"Camera not found"
    }),404


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