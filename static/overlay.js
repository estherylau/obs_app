const overlay = document.getElementById("overlay");

/* Create Single Layout */
function createCamera(camera){
    const div = document.createElement("div");

    div.className = "camera";

    const statusClass =
        camera.status === "Playing"
        ? "playing"
        : "stopped";

        //         <div class="location">
        //     ${camera.num} - Location
        // </div>

    div.innerHTML = `
        <div class="status ${statusClass}">
            ${camera.status}
        </div>
    `;

    overlay.appendChild(div);
}
