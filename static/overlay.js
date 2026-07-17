const overlay = document.getElementById("overlay");

/* OBS Coordinates */
const positions = {
    1:  {x:20,   y:4},
    2:  {x:190,  y:4},
    3:  {x:360,  y:4},
    4:  {x:530, y:4},
    5:  {x:700, y:4},
    6:  {x:870,   y:4},

    7:  {x:360,  y:360},
    8:  {x:680,  y:360},
    9:  {x:1000, y:360},
    10: {x:1320, y:360},

    11: {x:40,   y:535},
    12: {x:360,  y:535},
    13: {x:680,  y:535},
    14: {x:1000, y:535},
    15: {x:1320, y:535},

    16: {x:1640, y:285},
    17: {x:1640, y:560},
    18: {x:1640, y:835},

    19: {x:40, y:1080},
    20: {x:360,y:1080},
    21: {x:680,y:1080},
    22: {x:1000,y:1080},
    23: {x:1320,y:1080},

    24: {x:1640,y:1080},

    25: {x:40,y:1350},
    26: {x:360,y:1350},
    27: {x:680,y:1350},
    28: {x:1000,y:1350},
    29: {x:1320,y:1350},
    30: {x:1640,y:1350}

};

/* Create Single Layout */
function createCamera(camera){
    const pos = positions[camera.num];

    if(!pos)
        return;

    const div = document.createElement("div");

    div.className = "camera";

    div.style.left = pos.x + "px";
    div.style.top = pos.y + "px";

    const statusClass =
        camera.status === "Playing"
        ? "playing"
        : "stopped";

    div.innerHTML = `
        <div class="location">
            ${camera.location}
        </div>

        <div class="status ${statusClass}">
            ${camera.status}
        </div>
    `;

    overlay.appendChild(div);

}


async function refresh() {

    const response =
        await fetch("/api/cameras");

    const cameras =
        await response.json();

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


window.onload = function() {
  const testBtn = document.getElementById("test");
    const helloBtn = document.getElementById("hello");

    testBtn.addEventListener('click', () => {
    testBtn.style.color = "blue";
    helloBtn.style.color = "blue";
    });  
}
