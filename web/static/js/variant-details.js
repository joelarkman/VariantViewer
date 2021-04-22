//  This code interacts with main sample.js code when loaded via ajax into main sample page.

// Initiate tabs

$('.details-tabs .item')
    .tab()
    ;

// Initiate dropdowns
$('.ui.dropdown.classification, .ui.dropdown.report.inclusion')
    .dropdown()
    ;

// Set function of side menu toggle button
$('.menu-toggle-closed').click(function () {
    $('#variant-menu').show()
    $('.menu-toggle-closed').hide()
})

// Hide side menu toggle by default
$('.menu-toggle-closed').hide()

// Set function of tab closer button
$('.tabCloser').click(function () {
    $('.mini-tabs-link').removeClass('active');
    $('.mini-tabs-content').hide();
    $(".basic_message").show();
})

// Hide certain components by default.
$('.js-update-create-comment-active-header').hide()
$('#comment-form').hide()
$('#target-uploading').hide()
$('#upload-form').hide()

// Evidence upload - jquery-file-upload main function.
$(function () {

    // When click on file upload button, load file dialog.
    $(".js-upload-photos").click(function () {
        $("#file-dialog").click();
    });

    // Main file upload function
    $('#fileupload').fileupload({
        dataType: 'json', // data-type for ajax - json

        // Add function called when file is pasted, dropped or selected.
        add: function (e, data) {

            // Hide any warnings from previous uploads.
            $(".filetype-warning").hide()

            // For each file uploaded (limited to one for our purposes)
            $.each(data.files, function (index, file) {

                // Print added file to console.
                console.log('Added file: ' + file.name);

                // Check whether file is image or png. If not, display an error and cancel upload.
                if (!(/\.(gif|jpg|jpeg|tiff|png|pdf)$/i).test(file.name)) {
                    $('#evidence-container').prepend('<div class="ui negative visible message filetype-warning"><p>Only image and pdf filetypes are acceptable as evidence, please try again.</p></div>');
                    common.notifyError('You must select an image file only');
                    return false;
                }


                // Populate the filename field in the form with the file name (strip off final .filetype extension)
                $('#id_filename').val(file.name.replace(/\.[^/.]+$/, ""))

                // If the file is a PDF...
                if (file.type === 'application/pdf') {

                    // Add png icon and file name to pending container.
                    $('#pending-container').html('<i class="huge file pdf outline icon"></i><h5>' + file.name + '</h5>');

                    $('#pending-container').click(function () {

                        // Add the image and a close button to a dimmer and use custom classes to make the image fill the available screen space.
                        $('#lightbox').html('<i class="big inverted times icon close-icon"></i> <object class="lightbox-pdf" data="' + URL.createObjectURL(file) + '" type="application/pdf"><iframe src="https://docs.google.com/viewer?url=' + URL.createObjectURL(file) + '&embedded=true"></iframe></object>');

                        $('#lightbox').dimmer({
                            closable: true
                        }).dimmer('show');

                    })


                } else { // Otherwise (file uploaded is an image)...

                    // Add thumbnail of the image to pending container.
                    $('#pending-container').html('<img id="pending-img" class="thumbnail-img" src="' + URL.createObjectURL(file) + '" style="max-width:100%;max-height:100%;"/>');

                    // Make the image thumbnail launch dimmer containing larger image preview.
                    $('#pending-container').click(function () {

                        // Add the image and a close button to a dimmer and use custom classes to make the image fill the available screen space.
                        $('#lightbox').html('<i class="big inverted times icon close-icon"></i> <img class="lightbox-img" src="' + URL.createObjectURL(file) + '"/>');

                        $('#lightbox').dimmer({
                            closable: true
                        }).dimmer('show');

                    })
                }


            });

            // Once file has been added, checked for filetype and image containers populated... show form and hide upload button.
            $(".js-upload-photos").hide()
            $('#target-uploading').show()
            $('#upload-form').fadeIn()


            // When press the submit button... 
            $('.js-submit-photos').off("click");
            $('.js-submit-photos')
                .click(function () {
                    data.submit(); // submit the added files (uses ajax request linked to url in form action)
                    data.files.splice(0); // clear added files to reset uploader
                    $('.js-submit-photos').off("click");

                    // Hide upload form and show upload button.
                    $(".js-upload-photos").show()
                    $('#target-uploading').hide()
                    $('#upload-form').hide()
                });


            // When press cancel button...
            $('.js-cancel-submit').click(function () {
                data.files.splice(0); // clear added files to reset uploader
                $("#pending-container").html(""); // remove image previews in container
                $("#id_description").val(''); // clear description field of form.
                $("#file-dialog").val('');
                $('.js-submit-photos').off("click");

                // Hide upload form and show upload button.
                $(".js-upload-photos").show()
                $('#target-uploading').hide()
                $('#upload-form').hide()
            })
        },

        // Submit function called when files submitted.
        submit: function (e, data) {
            // replace file name with the value from the form plus the original file extension.
            data.files[0].uploadName = $('#id_filename').val() + '.' + data.files[0].name.split('.').pop();
        },

        // Done function called when ajax request made and response recieved from server.
        done: function (e, data) {

            // If response from server confirmed valid inputs...
            if (data.result.is_valid) {

                // Reload existing files container with new data from server.
                $("#evidence-container").html(data.result.documents)

                // Clear pending container
                $("#pending-container").html("");

                // Reset form fields 
                $("#id_description").val('');
                $("#file-dialog").val('');
            }
        }
    }).bind('fileuploadsubmit', function (e, data) { // Bind extra function to file submission.

        // Add additional fields to ajax call to enable description to be saved as well as file.
        data.formData = {
            "csrfmiddlewaretoken": $('#fileupload').attr('csrf_token'),
            'description': $('#id_description').val()
        };


    });;

    // Add event listener to the window to detect pasting.
    window.addEventListener('paste', e => {
        // Take file from clipboard and add it to file upload function.
        $('#fileupload').fileupload('add', { files: e.clipboardData.files[0] });
    });

    // Hide upload form by default
    $('#upload-form').hide()

});

// Hack to allow paste option appear on right click of upload div
target.onmousedown = e => {
    if (e.button === 2) target.contentEditable = true;
    // wait just enough for 'contextmenu' to fire
    setTimeout(() => target.contentEditable = false, 20);
};


// Close dimmer when you click on its content
// $('#lightbox').click(function () {
//     $('#lightbox')
//         .dimmer('hide');
// })


