import io
import os
import pandas as pd
from flask import Flask, request, send_file, jsonify
import chardet
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def upload_file():
    return '''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ITS Internal Assistant</title>
        <link rel="shortcut icon" href="/static/img/favicon.png">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Poppins', sans-serif;
                background-image: linear-gradient(to right, #002046, #2b79b9);
                color: #53565A;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                overflow: hidden;
            }
            .container {
                background-color: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                width: 90%;
                max-width: 500px;
                text-align: center;
            }
            .drop-zone {
                border: 2px dashed #9B7DD4;
                border-radius: 20px;
                padding: 20px;
                text-align: center;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .drop-zone:hover {
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
            .drop-zone img {
                max-width: 100px;
                margin-bottom: 10px;
            }
            .drop-zone p {
                margin: 0;
                color: #53565A;
            }
            #file-input {
                display: none;
            }
            .convert-btn {
                margin-top: 20px;
                padding: 14px 28px;
                background-color: #6BA539;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 1.2em;
                cursor: pointer;
                transition: background-color 0.3s, transform 0.1s;
            }
            .convert-btn:hover {
                background-color: #5a8e30;
                transform: translateY(-2px);
            }
            .convert-btn:active {
                transform: translateY(0);
            }
            footer {
                margin-top: 40px;
                text-align: center;
                font-size: 0.9em;
                color: #ffffff;
            }
            .file-name {
                margin-top: 10px;
                font-style: italic;
            }
            .modal {
                display: none;
                position: fixed;
                z-index: 1;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.4);
                justify-content: center;
                align-items: center;
            }
            .modal-content {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                width: 300px;
                text-align: center;
            }
            .modal button {
                background-color: #6BA539;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <form id="file-form" action="/convert" method="post" enctype="multipart/form-data">
                <div class="drop-zone" id="drop-zone">
                    <img src="/static/img/cloud.png" alt="Upload icon">
                    <p>Drag & Drop files here or click to upload</p>
                    <input type="file" name="file" id="file-input" multiple required>
                </div>
                <div class="file-name" id="file-name"></div>
                <button type="submit" class="convert-btn">Convert</button>
                <div id="spinner"></div>
            </form>
        </div>
        <div id="success-modal" class="modal">
            <div class="modal-content">
                <p>Hang on, we're turning your file into something beautiful (or at least readable)!</p>
                <button id="ok-btn">OK</button>
            </div>
        </div>
        <footer>
            <p>An ITS Internal Solution</p>
        </footer>
        <script>
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-input');
            const fileName = document.getElementById('file-name');
            const spinner = document.getElementById('spinner');
            const successModal = document.getElementById('success-modal');
            const okBtn = document.getElementById('ok-btn');
            const form = document.getElementById('file-form');

            dropZone.addEventListener('click', () => fileInput.click());
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.backgroundColor = '#f0f0f0';
            });
            dropZone.addEventListener('dragleave', () => {
                dropZone.style.backgroundColor = 'white';
            });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.style.backgroundColor = 'white';
                fileInput.files = e.dataTransfer.files;
                updateFileNames();
            });
            fileInput.addEventListener('change', updateFileNames);

            function updateFileNames() {
                if (fileInput.files.length > 0) {
                    const fileNames = Array.from(fileInput.files).map(file => file.name).join(', ');
                    fileName.textContent = `Selected files: ${fileNames}`;
                } else {
                    fileName.textContent = '';
                }
            }

            function showSuccessModal() {
                successModal.style.display = 'flex';
            }

            okBtn.addEventListener('click', () => {
                successModal.style.display = 'none';
            });

            form.addEventListener('submit', function(event) {
                event.preventDefault();
                const formData = new FormData(form);
                spinner.style.display = 'block';
                fetch('/convert', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        showSuccessModal();
                        const disposition = response.headers.get('Content-Disposition');
                        const filenameMatch = disposition ? disposition.match(/filename="(.+)"/) : null;
                        const todayDate = new Date().toISOString().split('T')[0];
                        const filename = filenameMatch && filenameMatch[1] ? filenameMatch[1] : `atmos_workday_conversion_${todayDate}.xlsx`;
                        console.log(filename);
                        return response.blob().then(blob => {
                            const downloadUrl = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = downloadUrl;
                            a.download = filename;
                            a.click();
                            URL.revokeObjectURL(downloadUrl);
                        });
                    } else {
                        throw new Error('Conversion failed');
                    }
                })
                .catch(error => {
                    spinner.style.display = 'none';
                    alert("An error occurred during conversion.");
                });
            });

            okBtn.addEventListener('click', () => {
                successModal.style.display = 'none';
                window.location.reload();
            });
        </script>
    </body>
    </html>
    '''

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return "No file part", 400
    files = request.files.getlist('file')
    if not files:
        return "No selected file", 400
    try:
        combined_df = pd.DataFrame()
        for file in files:
            file_bytes = file.read()
            result = chardet.detect(file_bytes)
            encoding = result['encoding']
            file_io = io.BytesIO(file_bytes)
            df = pd.read_csv(file_io, delimiter='|', encoding=encoding)
            df.columns = ['Username*', 'Task Code/Course ID*', 'Task/Course Name', 'Date Taken*', 'Date Qualified', 'Date Expired', 'Status*', 'Is Qualified*', 'Proctor']
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        output_filename = f"atmos_converted_{datetime.today().strftime('%Y-%m-%d')}.xlsx"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            combined_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=output_filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)
