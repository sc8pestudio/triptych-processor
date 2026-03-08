from flask import Flask, request, jsonify
from PIL import Image
import requests
import io
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return "Triptych Processor is running!"

@app.route('/split', methods=['POST'])
def split_image():
    try:
        # Get image URL from request
        data = request.get_json()
        image_url = data.get('image_url')
        
        if not image_url:
            return jsonify({"error": "No image_url provided"}), 400
        
        # Download image
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        
        width, height = img.size
        panel_width = width // 3
        
        # Split into 3 panels
        panels = []
        for i in range(3):
            left = i * panel_width
            right = (i + 1) * panel_width if i < 2 else width
            panel = img.crop((left, 0, right, height))
            
            # Convert to base64
            buffer = io.BytesIO()
            panel.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            panels.append(img_str)
        
        return jsonify({
            "success": True,
            "panels": panels,
            "original_size": f"{width}x{height}",
            "panel_size": f"{panel_width}x{height}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
