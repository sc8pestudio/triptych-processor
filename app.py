from flask import Flask, render_template_string, request, send_file
from PIL import Image
import io
import os

app = Flask(__name__)

# HTML template with upload form
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Triptych Processor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
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
        input[type="file"] {
            margin: 10px 0;
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
        button:hover {
            background: #0056b3;
        }
        .result {
            margin-top: 30px;
            text-align: center;
        }
        .result img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .download-btn {
            display: inline-block;
            margin-top: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
        }
        .error {
            color: #dc3545;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖼️ Triptych Processor</h1>
        <p>Upload an image to split it into three vertical panels</p>
        
        <div class="upload-form">
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <input type="file" name="image" accept="image/*" required>
                <br><br>
                <button type="submit">Create Triptych</button>
            </form>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
        </div>

        {% if triptych %}
        <div class="result">
            <h2>Your Triptych</h2>
            <img src="data:image/png;base64,{{ triptych }}" alt="Triptych">
            <br>
            <a href="/download" class="download-btn">Download Triptych</a>
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
        
        # Create triptych
        width, height = image.size
        panel_width = width // 3
        
        # Create new image with spacing between panels
        spacing = 20
        new_width = (panel_width * 3) + (spacing * 2)
        new_height = height
        
        triptych = Image.new('RGB', (new_width, new_height), (255, 255, 255))
        
        # Paste three panels
        for i in range(3):
            left = i * panel_width
            right = left + panel_width
            panel = image.crop((left, 0, right, height))
            
            x_position = i * (panel_width + spacing)
            triptych.paste(panel, (x_position, 0))
        
        # Save to buffer for display
        buf = io.BytesIO()
        triptych.save(buf, format='PNG')
        buf.seek(0)
        img_base64 = buf.getvalue().hex()
        
        # Also save to a session or temp file for download (simplified)
        triptych.save('/tmp/triptych.png')
        
        return render_template_string(HTML_TEMPLATE, triptych=img_base64)
        
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f"Error processing image: {str(e)}")

@app.route('/download')
def download():
    try:
        return send_file('/tmp/triptych.png', as_attachment=True, download_name='triptych.png')
    except:
        return "No image to download. Create one first!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
