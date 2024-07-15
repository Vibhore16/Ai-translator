from flask import Flask, render_template, request, jsonify
from transformers import MarianMTModel, MarianTokenizer
from pydub import AudioSegment
from flask_socketio import SocketIO, emit
import speech_recognition as sr
import os
import re

app = Flask(__name__)
socketio = SocketIO(app)

recognizer = sr.Recognizer()

# Load pre-trained model and tokenizer
model_name = 'Helsinki-NLP/opus-mt-ja-en'  # Japanese to English translation model
model = MarianMTModel.from_pretrained(model_name)
tokenizer = MarianTokenizer.from_pretrained(model_name)

def preprocess_text(text):
    """Preprocess the text for better translation results."""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    if request.method == 'POST':
        input_text = request.form['input_text']
        preprocessed_text = preprocess_text(input_text)
        
        # Tokenize input text
        inputs = tokenizer(preprocessed_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        # Perform translation
        translated = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
        
        # Decode the translated text
        translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        
        return jsonify({'translated_text': translated_text})

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    audio_data = sr.AudioData(data, sample_rate=16000, sample_width=2)
    try:
        text = recognizer.recognize_google(audio_data, language='ja-JP')
        emit('recognized_text', {'text': text})
    except sr.UnknownValueError:
        emit('recognized_text', {'text': ''})
    except sr.RequestError as e:
        emit('recognized_text', {'error': str(e)})

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    try:
        if 'audio' not in request.files:
            print("No audio data provided")
            return jsonify({'error': 'No audio data provided'}), 400
        
        audio_file = request.files['audio']
        print("Received audio file: ", audio_file.filename)
        
        temp_audio_path = 'temp_audio'
        audio_file.save(temp_audio_path)
        
        # Determine the format of the uploaded file
        audio_format = audio_file.filename.split('.')[-1].lower()

        # Convert to WAV format using pydub
        audio = AudioSegment.from_file(temp_audio_path, format=audio_format)
        wav_audio_path = 'temp.wav'
        audio.export(wav_audio_path, format='wav')

        recognizer = sr.Recognizer()
        transcription = ""
        with sr.AudioFile(wav_audio_path) as source:
            total_duration = int(source.DURATION)
            step = 30  # Duration of each chunk in seconds
            for start in range(0, total_duration, step):
                source.DURATION = min(step, total_duration - start)
                source_offset = start
                audio_data = recognizer.record(source, duration=source.DURATION, offset=source_offset)
                try:
                    text = recognizer.recognize_google(audio_data, language='ja-JP')
                    transcription += text + " "
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    return jsonify({'error': str(e), 'details': str(e.__class__.__name__) + ': ' + str(e)}), 500

        os.remove(temp_audio_path)
        os.remove(wav_audio_path)
        return jsonify({'text': transcription.strip()})
    except Exception as e:
        print("Error in speech recognition: ", e)
        return jsonify({'error': str(e), 'details': str(e.__class__.__name__) + ': ' + str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True)
