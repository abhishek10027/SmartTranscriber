import os
import whisper
import yt_dlp
import uuid
import glob
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

model = whisper.load_model("base")

def download_from_url(url):
    download_id = uuid.uuid4().hex
    output_template = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{download_id}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    files = glob.glob(output_template.replace('%(ext)s', '*.mp3'))
    if not files:
        raise FileNotFoundError("Audio file not downloaded correctly.")
    
    return files[0]

@app.route('/', methods=['GET', 'POST'])
def index():
    transcript = ""
    error = None

    if request.method == 'POST':
        try:
            if 'file' in request.files and request.files['file'].filename != '':
                file = request.files['file']
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                result = model.transcribe(file_path)
                transcript = result['text']
                os.remove(file_path)
            elif 'link' in request.form and request.form['link'].strip():
                link = request.form['link'].strip()
                downloaded_file = download_from_url(link)
                result = model.transcribe(downloaded_file)
                transcript = result['text']
                os.remove(downloaded_file)
            else:
                error = "Please upload a file or provide a valid link."
        except Exception as e:
            error = f"Something went wrong: {str(e)}"

    return render_template("index.html", transcript=transcript, error=error)

if __name__ == '__main__':
    app.run(debug=True)
