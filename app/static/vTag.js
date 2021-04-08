$(document).ready(function () {
    // init page resource
    $('#vTag').addClass('active');
    const webcamElement = document.getElementById('videoXP');
    const canvasElement = document.getElementById('canvas');
    const webcam = new Webcam(webcamElement, 'environment', canvasElement);  //
    var picture = null;
    var refreshMeter = null
    $('#passArea').focus()

    // init webcam
    webcam.start()
    .then(result =>{
        console.log("webcam started");
    })
    .catch(err => {
        console.log(err);
    });

    // get data from canvas
    function getCanvas(){
        console.log("refresh");
        let snapped = webcam.snap();    // get image from webcam
        picture = canvasElement.toDataURL('image/jpeg');
        // make a dict of pass and picture code(image/base64).
        var data = {
            passArea: $('#passArea').val(),
            picture: picture
        };
        // post the dict to have them compared with the original data
        $.ajax({
            type: 'POST',
            url: '/vTag',
            data: JSON.stringify(data),
            contentType: "application/json",
            success: function (response) {
                $('#passDiv, #submit').hide();
                // if success, show the word.
                if(response){
                    $('#showWords').text(response);
                    $('#showWords').show();
                    //webcam.stop();
                    //window.clearInterval(refreshMeter);
                } else {
                    $('#showWords').hide();
                };
                $("#submit").prop("disabled", false);
            }
        });
    }

    // re-init the page
    $('#reset').click(function() {
        picture = null;
        $('#showWords').hide();
        $('#videoEX, #passDiv, #submit, #snap, .directions').show(500);
        $('#passArea').val('');
        $('#showWords').text('');
        window.clearInterval(refreshMeter);
        $('#passArea').focus();
        //webcam.start()
    });

    // submit the pass to start the capture and compare process.
    $('#submit').click(function(event) {
        event.preventDefault();
        if( !$('#passArea').val() ) {
            alert('需要填写PASS');
            $('#passArea').focus();
            return false;
        };
        // refresh capture and compare every 1000ms
        refreshMeter = window.setInterval(getCanvas, 1000);
    });
});
