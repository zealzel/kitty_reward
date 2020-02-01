import os
import sys
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from xls_processer import xls_process

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/source/'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/output/'
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

app = Flask(__name__, static_url_path="/static")
DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file attached in request')
            return redirect(request.url)
        file = request.files['file']

        print('filename', file.filename)

        if file.filename == '':
            print('No file selected')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            award_type = request.form['award_type']
            process_file(os.path.join(UPLOAD_FOLDER, filename), award_type)
            return redirect(url_for('uploaded_file'))
    return render_template('index.html')


def process_file(filepath, award_type):
    print('processing...')
    print('award_type: ', award_type)
    xls_process(filepath, award_type)
    print('process done')


def zipfile():
    import zipfile
    with zipfile.ZipFile('output/final_result.zip', 'w') as f:
        f.write('output/final_result.xlsx')
        f.write('output/final_result.txt')


#@app.route('/uploads/<path:filename>')
@app.route('/uploads')
def uploaded_file():
    filename = 'final_result.zip'
    zipfile()
    print('ready to download', DOWNLOAD_FOLDER, filename)
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5223))
    app.run(host='0.0.0.0', port=port)
