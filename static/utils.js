async function refresh() {
    const response =
        await fetch("/api/cameras");

    const cameras = await response.json();
    console.log("what is cameras: ", cameras);

    const overlay = document.getElementById('overlay');
    const buttonLayout = document.getElementById("location");

    if (overlay) {
        overlay.innerHTML = "";

        cameras.forEach((camera,index)=>{
            createCamera(camera);
        });
    }

    if (buttonLayout) {
        buttonLayout.innerHTML = "";

        const pearlNumber = Number(
            window.location.pathname.split("/").pop()
        );

        const currentPearl = cameras.find((camera, idx) => (idx + 1)=== pearlNumber);
        createCamera(currentPearl);
    }
}

refresh();

setInterval(
    refresh,
    5000
);