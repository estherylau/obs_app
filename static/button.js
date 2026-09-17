const buttonLayout = document.getElementById("location");

/* Create Single Layout */
function createCamera(camera){
    const div = document.createElement("div");

    div.className = "device-label";
    div.innerHTML = `
        <div class="loca">
            ${camera.num} - ${camera.location}
        </div>
    `;

    buttonLayout.appendChild(div);
}


async function stopCamera(cameraId)
{
    console.log(
        "Stopping camera:",
        cameraId
    );

    try {

        const response =
            await fetch(
                `/api/camera/${cameraId}/stop`,
                {
                    method:"POST"
                }
            );

        const result =
            await response.json();


        if(result.success){
            console.log(
                "Stopped:",
                result
            );
        }
    }


    catch(error){
        console.log(error);
    }

}