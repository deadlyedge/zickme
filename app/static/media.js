const webcamElement = document.getElementById('video');
const canvasElement = document.getElementById('canvas');
const webcam = new Webcam(webcamElement, 'environment', canvasElement);  //

webcam.start()
.then(result =>{
    console.log("webcam started");
})
.catch(err => {
    console.log(err);
});

$('#snap').click(function() {
    let picture = webcam.snap();
    $.ajax({
        type: 'POST',
        url: "{{url_for( callURL )}}",
        data: {'imgBase64': picture},
    });
});

$('#cameraFlip').click(function() {
    webcam.flip();
    webcam.start();
});
