from flask import Flask, render_template_string, request, send_file
from PIL import Image
import io
import os
import base64
import zipfile

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Triptych Processor - 3 Piece Set</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .upload-form {
            margin: 30px 0;
            padding: 20px;
            border: 2px dashed #ccc;
            border-radius: 5px;
            text-align: center;
        }
        button {
            background: #007bff;
            color: white;
            padding: 10px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #0056b3; }
        .panels-container {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 30px;
            flex-wrap: wrap;
        }
        .panel-box {
            text-align: center;
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            max-width: 350px;
        }
        .panel-box img {
            max-width: 100%;
            max-height: 400px;
            border: 1px solid #ddd;
            border-radius: 5px;
            display: block;
            margin-bottom: 10px;
        }
        .panel-label {
            font-weight: bold;
            color: #555;
            margin-bottom: 10px;
            display: block;
            font-size: 18px;
        }
        .download-btn {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 5px;
        }
        .download-btn:hover { background: #218838; }
        .download-all {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: #e9ecef;
            border-radius: 8px;
        }
        .zip-btn {
            background: #6c757d;
            font-size: 16px;
            font-weight: bold;
        }
        .zip-btn:hover { background: #5a6268; }
        .error { color: #dc3545; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖼️ Triptych Processor</h1>
        <p>Upload an image to split into three separate panels for printing</p>
        
        <div class="upload-form">
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <input type="file" name="image" accept="image/*" required>
                <br><br>
                <button type="submit">Create 3-Piece Set</button>
            </form>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
        </div>

        {% if panels %}
        <h2 style="text-align: center; margin-top: 40px;">Your 3-Piece Set</h2>
        <div class="panels-container">
            {% for panel in panels %}
            <div class="panel-box">
                <span class="panel-label">Panel {{ panel.num }}: {{ panel.name }}</span>
                <img src="data:image/png;base64,{{ panel.data }}" alt="Panel {{ panel.num }}">
                <a href="/download/{{ panel.num }}" class="download-btn">Download Panel {{ panel.num }}</a>
            </div>
            {% endfor %}
        </div>
        
        <div class="download-all">
            <p style="margin-top: 0; color: #666; font-size: 16px;">
                <strong>Download all three panels as separate files</strong><br>
                Perfect for printing as a 3-piece canvas set!
            </p>
            <a href="/download/all" class="download-btn zip-btn">📦 Download All (ZIP)</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'image' not in request.files:
            return render_template_string(HTML_TEMPLATE, error="No file uploaded")
        
        file = request.files['image']
        if file.filename == '':
            return render_template_string(HTML_TEMPLATE, error="No file selected")
        
        # Open image
        image = Image.open(file.stream)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Get dimensions and calculate panel width
        width, height = image.size
        panel_width = width // 3
        
        # Create three separate panels
        panels = []
        panel_names = ['Left', 'Center', 'Right']
        
        for i in range(3):
            # Calculate crop box
            left = i * panel_width
            right = left + panel_width
            
            # Crop panel
            panel = image.crop((left, 0, right, height))
            
            # Save to buffer for display (base64)
            buf = io.BytesIO()
            panel.save(buf, format='PNG')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.getvalue()).decode()
            
            # Save to file for download
            panel_path = f'/tmp/panel_{i+1}.png'
            panel.save(panel_path)
            
            panels.append({
                'num': i + 1,
                'name': panel_names[i],
                'data': img_base64
            })
        
        return render_template_string(HTML_TEMPLATE, panels=panels)
        
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f"Error processing image: {str(e)}")

@app.route('/download/<panel_num>')
def download_panel(panel_num):
    try:
        panel_path = f'/tmp/panel_{panel_num}.png'
        if os.path.exists(panel_path):
            return send_file(panel_path, as_attachment=True, download_name=f'panel_{panel_num}.png')
        else:
            return "Panel not found. Create one first!"
    except Exception as e:
        return f"Download error: {str(e)}"

@app.route('/download/all')
def download_all():
    try:
        zip_path = '/tmp/triptych_3piece_set.zip'
        
        # Create zip file with all three panels
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for i in range(1, 4):
                panel_path = f'/tmp/panel_{i}.png'
                if os.path.exists(panel_path):
                    zipf.write(panel_path, f'panel_{i}.png')
        
        return send_file(zip_path, as_attachment=True, download_name='triptych_3piece_set.zip')
    except Exception as e:
        return f"Error creating zip: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
