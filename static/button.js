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
                cameraId
            );
        }
    }


    catch(error){
        console.log(error);
    }

}