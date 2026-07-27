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


async function refresh() {
    const response =
        await fetch("/api/cameras");

    const cameras = await response.json();

    overlay.innerHTML = "";

    cameras.forEach((camera,index)=>{
        createCamera(camera);
    });

}

refresh();

setInterval(
    refresh,
    5000
);


// window.onload = function() {
//   const testBtn = document.getElementById("test");
//     const helloBtn = document.getElementById("hello");

//     testBtn.addEventListener('click', () => {
//     testBtn.style.color = "blue";
//     helloBtn.style.color = "blue";
//     });  
// }
