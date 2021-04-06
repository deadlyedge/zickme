$(document).ready(function () {
    $('#vTag').addClass('active');
    const webcamElement = document.getElementById('videoXP');
    const canvasElement = document.getElementById('canvas');
    const webcam = new Webcam(webcamElement, 'environment', canvasElement);  //
    var picture = null;
    var refreshMeter = null
    $('#passArea').focus()

    webcam.start()
    .then(result =>{
        console.log("webcam started");
    })
    .catch(err => {
        console.log(err);
    });

    function getCanvas(){
        console.log("refresh");
        let snapped = webcam.snap();
        picture = canvasElement.toDataURL('image/jpeg');
        var data = {
            passArea: $('#passArea').val(),
            picture: picture
        };
        $.ajax({
            type: 'POST',
            url: '/vTag',
            data: JSON.stringify(data),
            contentType: "application/json",
            success: function (response) {
                $('#passDiv, #submit').hide();
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

    //var refreshMeter = window.setInterval(getCanvas, 500);

    $('#reset').click(function() {
        picture = null;
        $('#imageSnapped').attr('src', '');
        $('#passArea').val('');
        $('#showWords').text('');
        $('#showWords').hide();
        $('#videoEX, #passDiv, #submit, #snap, .directions').show(500);
        $('#passArea').focus();
        window.clearInterval(refreshMeter);
        //webcam.start()
    });

    $('#submit').click(function(event) {
        event.preventDefault();
        if( !$('#passArea').val() ) {
            alert('需要填写PASS');
            $('#passArea').focus();
            return false;
        };
        refreshMeter = window.setInterval(getCanvas, 1000);
    });
});
