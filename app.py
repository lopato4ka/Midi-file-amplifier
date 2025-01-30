# app.py
from flask import Flask, render_template, request, send_file, flash, redirect
import os
import mido
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit
ALLOWED_EXTENSIONS = {'mid', 'midi'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def amplify_midi_volume(input_file, volume_multiplier=5):
    """Оптимизированная функция усиления громкости MIDI"""
    mid = mido.MidiFile(file=input_file)
    new_mid = mido.MidiFile(type=mid.type, ticks_per_beat=mid.ticks_per_beat)
    
    for track in mid.tracks:
        new_track = mido.MidiTrack()
        for msg in track:
            if not msg.is_meta and msg.type in ('note_on', 'note_off') and msg.velocity > 0:
                msg = msg.copy(velocity=min(int(msg.velocity * volume_multiplier), 127))
            new_track.append(msg)
        new_mid.tracks.append(new_track)
    
    output = BytesIO()
    new_mid.save(file=output)
    output.seek(0)
    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не выбран')
            return redirect(request.url)
        
        file = request.files['file']
        multiplier = request.form.get('multiplier', '5')
        
        if file.filename == '':
            flash('Файл не выбран')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Разрешены только MIDI файлы (.mid, .midi)')
            return redirect(request.url)
        
        try:
            multiplier = int(multiplier)
            if not 1 <= multiplier <= 10:
                raise ValueError
        except ValueError:
            flash('Множитель должен быть числом от 1 до 10')
            return redirect(request.url)

        try:
            filename = secure_filename(file.filename)
            output = amplify_midi_volume(file, multiplier)
            return send_file(
                output,
                as_attachment=True,
                download_name=f"boosted_{multiplier}x_{filename}",
                mimetype="audio/midi"
            )
        except Exception as e:
            app.logger.error(f"Error processing file: {str(e)}")
            flash('Ошибка обработки файла')
            
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)