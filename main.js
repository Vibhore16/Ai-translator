$(document).ready(function() {
    const inputText = document.getElementById('input_text');
    const submitTextButton = document.getElementById('submit_text');
    const translatedTextDiv = document.getElementById('translated_text');
    const audioFileInput = document.getElementById('audio_file');
    const uploadAudioButton = document.getElementById('upload_audio');
    const startRecognitionButton = document.getElementById('start_recognition');

    // Handle the upload audio button click
    uploadAudioButton.onclick = function() {
        const file = audioFileInput.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('audio', file);

            $.ajax({
                type: 'POST',
                url: '/speech_to_text',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    console.log('Server response: ', response);
                    if (response.error) {
                        alert('Error in speech recognition: ' + response.error);
                    } else {
                        inputText.value = response.text;
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    console.error('AJAX error: ', textStatus, errorThrown);
                    console.error('Response text: ', jqXHR.responseText);
                    alert('Error in speech recognition: ' + errorThrown);
                }
            });
        } else {
            alert('Please select an audio file to upload.');
        }
    };

    // Handle the text translation button click
    submitTextButton.onclick = function() {
        const inputTextValue = inputText.value.trim();
        if (inputTextValue) {
            $.ajax({
                type: 'POST',
                url: '/translate',
                data: { input_text: inputTextValue },
                success: function(response) {
                    if (response.translated_text) {
                        translatedTextDiv.innerHTML = `${response.translated_text}</p>`;
                    }
                },
                error: function(response) {
                    alert('Error in translation: ' + response.responseJSON.error);
                }
            });
        } else {
            alert('Please enter some text to translate.');
        }
    };

    // Handle the start speaking button click
    startRecognitionButton.onclick = function() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            const constraints = { audio: true };
            let chunks = [];

            navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
                const options = { mimeType: 'audio/webm' };
                const mediaRecorder = new MediaRecorder(stream, options);

                mediaRecorder.start();
                console.log('Recorder started');

                mediaRecorder.onstop = function() {
                    console.log('Recorder stopped');

                    const blob = new Blob(chunks, { 'type': 'audio/webm' });
                    chunks = [];
                    const formData = new FormData();
                    formData.append('audio', blob, 'audio.webm');

                    $.ajax({
                        type: 'POST',
                        url: '/speech_to_text',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(response) {
                            console.log('Server response: ', response);
                            if (response.error) {
                                alert('Error in speech recognition: ' + response.error);
                            } else {
                                inputText.value = response.text;
                            }
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            console.error('AJAX error: ', textStatus, errorThrown);
                            console.error('Response text: ', jqXHR.responseText);
                            alert('Error in speech recognition: ' + errorThrown);
                        }
                    });
                };

                mediaRecorder.ondataavailable = function(e) {
                    chunks.push(e.data);
                };

                setTimeout(function() {
                    mediaRecorder.stop();
                }, 5000); // Stop recording after 5 seconds
            }).catch(function(err) {
                console.log('The following error occurred: ' + err);
            });
        } else {
            startRecognitionButton.disabled = true;
            alert('getUserMedia not supported in this browser.');
        }
    };
});
