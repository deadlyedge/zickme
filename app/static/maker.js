$(document).ready(function () {
    $('.alert').hide();
    $('#maker').addClass('active');
    const webcamElement = document.getElementById('video');
    const canvasElement = document.getElementById('canvas');
    const webcam = new Webcam(webcamElement, 'environment', canvasElement);  //
    var picture = null;
    var logo = new Image();
    logo.src = 'static/zickme.logo.svg';

    webcam.start()
    .then(result =>{
        console.log("webcam started");
    })
    .catch(err => {
        console.log(err);
    });

    $("#passArea").on('keyup focusout', function(){
        var username = $(this).val().trim();
        if (username != '') {
            $.ajax({
                url: 'passCheck',
                type: 'post',
                data: JSON.stringify({username: username}),
                contentType: "application/json",
                success: function(response){
                    $('#pass_response').html(response);
                }
            });
        } else {
            $("#pass_response").html("");
        }
    });

    $('#snap, #video').click(function() {
        let snapped = webcam.snap();
        picture = canvasElement.toDataURL('image/jpeg');
        $('#imageSnapped').attr('src', picture);
        $('#showPicture').show();
        $('#passArea').focus();
    });

    $('#submit').click(function(event) {
        event.preventDefault();
        if( !$('#passArea').val() ) {
            alert('需要填写PASS');
            $('#passArea').focus();
            return false;
        };
        if( $('#pass_response').text() ) {
            alert('PASS不可用，请重新填写');
            $('#passArea').focus();
            return false;
        };
        if( !$('#wordsArea').val() ) {
            alert('也需要填写你想说的话');
            $('#wordsArea').focus();
            return false;
        };
        if(picture == null){
            let snapped = webcam.snap();
            picture = canvasElement.toDataURL('image/jpeg');
            $('#imageSnapped').attr('src', picture);
        };
        var data = {
            passArea: $('#passArea').val(),
            wordsArea: $('#wordsArea').val(),
            picture: picture
        };
        $('#submit').prop('disabled', true);

        $.ajax({
            type: 'POST',
            url: 'maker',
            data: JSON.stringify(data),
            contentType: "application/json",
            success: function (response) {
                $(".alert").show();
                $(".alert").text('Your words ' + response + ' is saved!');
                savePic();
                // alert('Your words ' + response + ' is saved!');
                // window.location.href = '/'
            },
            error: function (e) {
                alert(e.responseText);
                $('#passArea').focus();
            }
        });

        function savePic() {
          var image = canvasElement.getContext('2d');
          image.globalAlpha = 0.5;
          image.fillStyle = 'black';
          image.fillRect(0, canvasElement.height - 24, canvasElement.width, 24);
          image.drawImage(logo, 10, 10, 40, 40);
          image.globalAlpha = 1;
          image.textBaseline="ideographic";
          image.font = 'bold 18px DejaVu Sans Mono';
          image.fillStyle = 'white';
          image.fillText('长按保存截图 !' + $('#passArea').val() + ':', 10, canvasElement.height);
          var textImageURL = canvasElement.toDataURL('image/jpeg')
          $('#savePicture').attr('src', textImageURL);
          $('#downloadLink').attr('href', textImageURL);
          $('#forSave, #downloadDiv').show();
          $('#showPicture').hide();
          $('#forSave').focus();
        }

        $('#forSave').click(function() {
          $(this).slideUp();
          $('#downloadLink').focus();
        });

        $("#submit").prop("disabled", false);
    });
});
