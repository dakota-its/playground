import os
import pandas as pd
from flask import Flask, request, send_file
import chardet
from datetime import datetime

app = Flask(__name__)

# Set the base path to ensure directories are created inside the 'automation' folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the absolute path to the current script

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted')

# Ensure the 'uploads' and 'converted' directories are created inside the 'automation' folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def upload_and_convert_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        
        files = request.files.getlist('file')  # Get list of uploaded files
        if not files:
            return "No selected files"

        all_data = []  # List to store data from all files

        for file in files:
            # Save the uploaded file
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            try:
                # Detect encoding
                with open(filepath, 'rb') as f:
                    result = chardet.detect(f.read())
                    encoding = result['encoding']

                print(f"Detected encoding for {file.filename}: {encoding}")  # Debugging the detected encoding

                # Read the pipe-delimited file with the detected encoding
                df = pd.read_csv(filepath, delimiter='|', encoding=encoding)

                # Rename the columns to match your desired format
                df.columns = ['Username*', 'Task Code/Course ID*', 'Task/Course Name', 
                            'Date Taken*', 'Date Qualified', 'Date Expired', 
                            'Status*', 'Is Qualified*', 'Proctor']

                # Append the dataframe to the all_data list
                all_data.append(df)

            except UnicodeDecodeError:
                return f"Error: Unable to decode file {file.filename} with the detected encoding."
            except Exception as e:
                return f"An error occurred while processing {file.filename}: {e}"

        # Concatenate all the dataframes into one
        combined_df = pd.concat(all_data, ignore_index=True)

        # Ensure the 'converted' folder exists before saving
        if not os.path.exists(CONVERTED_FOLDER):
            os.makedirs(CONVERTED_FOLDER)

        # Generate the output filename with today's date
        today_date = datetime.now().strftime('%Y-%m-%d')
        output_filename = f'atmos_converted_{today_date}.xlsx'
        output_path = os.path.join(CONVERTED_FOLDER, output_filename)

        # Convert the combined dataframe to Excel
        combined_df.to_excel(output_path, index=False)

        # Send the converted file for download
        return send_file(output_path, as_attachment=True)

    # If GET request (initial page load), return the upload form
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

        /* Modal Styling */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 2000; /* Ensure the modal is on top */
        }
        .modal-content {
            background-color: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            text-align: center;
            font-size: 1.5em;
            color: #28a745;
            width: 300px;  /* Adjust modal width */
        }
        .ok-button {
            padding: 18px 30px;  /* Increase button size */
            background-color: #6BA539;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.2em;
            cursor: pointer;
            margin-top: 20px;
            width: 100%;  /* Make the button take full width */
            box-sizing: border-box;  /* Ensure it fits inside the modal */
        }
        .ok-button:hover {
            background-color: #5a8e30;
        }
    </style>
</head>
<body>
    <div class="container">
        <form action="/" method="post" enctype="multipart/form-data">
            <div class="drop-zone" id="drop-zone">
                <img src="/static/img/cloud.png" alt="Upload icon">
                <p>Drag & Drop files here or click to upload</p>
                <input type="file" name="file" id="file-input" multiple required>
            </div>
            <div class="file-name" id="file-name"></div>
            <button type="submit" class="convert-btn">Convert</button>
        </form>
    </div>
    <footer>
        <p>An ITS Internal Solution</p>
    </footer>

    <!-- Modal for Success Message -->
    <div id="modal" class="modal">
        <div class="modal-content">
            File converted successfully! The file will download shortly.
            <button class="ok-button" onclick="closeModal()">OK</button>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const fileName = document.getElementById('file-name');
        const modal = document.getElementById('modal');

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
            updateFileNames();  // Update the file names display
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

        // Display success message modal
        function showModal() {
            modal.style.display = 'flex';
        }

        // Close modal and refresh page
        function closeModal() {
            modal.style.display = 'none';
            location.reload();  // Refresh the page after file download
        }

        // Listen for when the file download is triggered and show modal
        document.querySelector('form').onsubmit = function() {
            showModal();
        };
    </script>
</body>
</html>

    '''
    
if __name__ == '__main__':
    app.run(debug=True)
