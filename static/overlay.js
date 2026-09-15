const overlay = document.getElementById("overlay");

const audioStreams = [];
const audioContexts = [];

/* Create Single Layout */
function createCamera(camera){
    const div = document.createElement("div");

    div.className = "camera";

    // const statusClass = camera.status;
    const statusClass = camera.status.includes("Channel") ? "playing" : "stopped";
        //         <div class="location">
        //     ${camera.num} - Location
        // </div>

    div.innerHTML = `
        <div class="camera-info">
            <div class="status ${statusClass}">
                ${camera.status}
            </div>
        </div>
        <div class="video-container">
            <img
                class="camera-stream"
                src="/video/${camera.num}"
                alt="${camera.location}"
            >
        </div>
        <canvas
            class="audio-waveform"
            id="waveform-${camera.num}"
        ></canvas>
    `;

    overlay.appendChild(div);
    createWaveform(camera.num);
}

/* Create Audio + Waveform */
function createWaveform(cameraId) {

    const canvas =
        document.getElementById(`waveform-${cameraId}`);

    if (!canvas) {
        return;
    }

    const audio =
        new Audio(`/audio/${cameraId}`);

    audio.preload = "none";
    audio.autoplay = false;

    const AudioContext =
        window.AudioContext ||
        window.webkitAudioContext;

    const audioContext =
        new AudioContext();

    const analyser =
        audioContext.createAnalyser();

    analyser.fftSize = 256;

    const bufferLength =
        analyser.frequencyBinCount;

    const dataArray =
        new Uint8Array(bufferLength);

    const source =
        audioContext.createMediaElementSource(audio);

    source.connect(analyser);

    analyser.connect(
        audioContext.destination
    );

    audioStreams.push({
        cameraId: cameraId,
        audio: audio,
        context: audioContext
    });

    audioContexts.push(audioContext);

    const ctx =
        canvas.getContext("2d");


    function resizeCanvas() {

        const rect =
            canvas.getBoundingClientRect();

        canvas.width = rect.width;
        canvas.height = rect.height;
    }

    resizeCanvas();

    window.addEventListener(
        "resize",
        resizeCanvas
    );


    function drawWaveform() {

        requestAnimationFrame(
            drawWaveform
        );

        analyser.getByteTimeDomainData(
            dataArray
        );

        ctx.clearRect(
            0,
            0,
            canvas.width,
            canvas.height
        );

        ctx.beginPath();

        const sliceWidth =
            canvas.width /
            bufferLength;

        let x = 0;

        for (
            let i = 0;
            i < bufferLength;
            i++
        ) {

            const value =
                dataArray[i] /
                128.0;

            const y =
                value *
                canvas.height /
                2;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        ctx.lineTo(
            canvas.width,
            canvas.height / 2
        );

        ctx.stroke();
    }

    drawWaveform();
}

/* Enable All Audio */
document
    .getElementById("enable-audio")
    .addEventListener("click", async () => {

        console.log(
            "Enabling audio streams..."
        );

        let started = 0;

        for (const stream of audioStreams) {

            try {

                if (
                    stream.context.state ===
                    "suspended"
                ) {
                    await stream.context.resume();
                }

                await stream.audio.play();

                started++;

                console.log(
                    `Audio started: camera ${stream.cameraId}`
                );

            } catch (error) {

                console.error(
                    `Audio failed: camera ${stream.cameraId}`,
                    error
                );

            }
        }

        console.log(
            `${started} audio streams started`
        );

        document.getElementById(
            "enable-audio"
        ).textContent =
            `Audio Enabled (${started})`;

    });
