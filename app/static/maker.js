$(document).ready(function () {
    //init page
    $('.alert').hide();
    $('#maker').addClass('active');
    const webcamElement = document.getElementById('video');
    const canvasElement = document.getElementById('canvas');
    const webcam = new Webcam(webcamElement, 'environment', canvasElement);  // change 'user' to 'environment' for the back cam of phones.
    var picture = null;
    var logo = new Image();
    logo.src = 'static/zickme.logo.png';

    //init webcam
    webcam.start()
    .then(result =>{
        console.log("webcam started");
    })
    .catch(err => {
        console.log(err);
    });

    //check the available of the PASS.
    $("#passArea").on('input focusout', function(){
        $(this).val($(this).val().replace(/\s+/g, " "));    // remove extra spaces when input
        var passCode = $(this).val().trim();    // remove space at begin and end.
        if (passCode != '') {   // this ajax seems in the old format, should be replace to a fashion form.
            $.ajax({
                url: 'passCheck',
                type: 'post',
                data: JSON.stringify({passCode: passCode}),
                contentType: "application/json",
                success: function(response){
                    $('#pass_response').html(response);
                }
            });
        } else {
            $("#pass_response").html("");
        }
    });

    // when the video or the snap button is clicked
    $('#snap, #video').click(function() {
        let snapped = webcam.snap();
        picture = canvasElement.toDataURL('image/jpeg');    // trans canvas data to a variable
        $('#imageSnapped').attr('src', picture);    // show the data in a <img>
        $('#showPicture').show();
        $('#passArea').focus();
    });

    // when submit
    $('#submit').click(function(event) {
        event.preventDefault();     // seems this can exclude something unnecessary
        // if passArea is empty
        if( !$('#passArea').val() ) {
            alert('需要填写PASS');
            $('#passArea').focus();
            return false;
        };
        // if something return from the passCheck
        if( $('#pass_response').text() ) {
            alert('PASS不可用，请重新填写');
            $('#passArea').focus();
            return false;
        };
        // if forgot to write something to say
        if( !$('#wordsArea').val() ) {
            alert('也需要填写你想说的话');
            $('#wordsArea').focus();
            return false;
        };
        // if not snap picture yet, just snap automatically and go on.
        if(picture == null){
            let snapped = webcam.snap();
            picture = canvasElement.toDataURL('image/jpeg');
            $('#imageSnapped').attr('src', picture);
        };
        // form the data to a dict.
        var data = {
            passArea: $('#passArea').val(),
            wordsArea: $('#wordsArea').val(),
            picture: picture
        };
        $('#submit').prop('disabled', true);    // disable the submit button for protection of mouse button from crazy clicking.

        $.ajax({
            type: 'POST',
            url: 'maker',
            data: JSON.stringify(data),     // convert dict to json
            contentType: "application/json",
            success: function (response) {
                $(".alert").show();
                $(".alert").text('Your PASS and your WORDS: ' + response + ' is saved!');
                savePic();      // enter a function which could save the PASS with picture in case you forget them.
            },
            error: function (e) {   // if something bad happens.
                alert(e.responseText);
                $('#passArea').focus();     // which most likely be the pass
            }
        });
        $("#submit").prop("disabled", false);   // re-enable the submit button.
    });

    // save the pass with image
    function savePic() {
      var image = canvasElement.getContext('2d');   //prepare the canvas
      image.globalAlpha = 0.5;
      // draw logo and text background
      image.fillStyle = 'black';
      image.fillRect(0, canvasElement.height - 24, canvasElement.width, 24);
      image.drawImage(logo, 10, 10, 40, 40);
      image.globalAlpha = 1;
      // draw text which is the PASS
      image.textBaseline="ideographic";
      image.font = 'bold 18px Consolas';    // I want to select a font which could clarify 0 and O, but it's failed on iOS.
      image.fillStyle = 'white';
      image.fillText('长按保存截图 !' + $('#passArea').val() + ':', 10, canvasElement.height);
      var textImageURL = canvasElement.toDataURL('image/jpeg')
      $('#savePicture').attr('src', textImageURL);
      $('#downloadLink').attr('href', textImageURL);    // generate a download link
      $('#forSave, #downloadDiv').show();
      $('#showPicture').hide();
      $('#forSave').focus();
    }

    // click to slide the picture up.
    $('#forSave').click(function() {
      $(this).slideUp();
      $('#downloadLink').focus();
    });
});
