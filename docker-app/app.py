"""Flask API for Crosshatch Docker application."""

import os
import uuid
from pathlib import Path
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import cv2

# Import our crosshatch module
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from crosshatch import CrosshatchProcessor
from crosshatch.config import CrosshatchConfig, SAM2Config

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Create folders
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

# Initialize processor (singleton)
processor = None


def get_processor():
    """Get or create the crosshatch processor."""
    global processor
    if processor is None:
        print("Initializing Crosshatch processor...")

        # Configure SAM2
        sam_config = SAM2Config(
            model_type=os.getenv('SAM2_MODEL', 'small'),
            device=os.getenv('DEVICE', 'cuda')
        )

        # Configure crosshatch
        crosshatch_config = CrosshatchConfig(
            max_dimension=int(os.getenv('MAX_DIMENSION', '1200'))
        )

        processor = CrosshatchProcessor(config=crosshatch_config)
        print("✓ Processor initialized")

    return processor


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'crosshatch-api',
        'version': '2.0.0'
    })


@app.route('/api/crosshatch', methods=['POST'])
def create_crosshatch():
    """
    Create crosshatch effect on uploaded image.

    Form parameters:
        - file: Image file (required)
        - style: 'horizontal' or 'vortex' (optional, default: horizontal)
        - max_dimension: Maximum output dimension (optional, default: 1200)

    Returns:
        Crosshatched image file
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Get parameters
        hatch_style = request.form.get('style', 'horizontal')
        if hatch_style not in ['horizontal', 'vortex']:
            return jsonify({
                'error': 'Invalid style. Must be "horizontal" or "vortex"'
            }), 400

        max_dimension = int(request.form.get('max_dimension', '1200'))
        if max_dimension < 100 or max_dimension > 2400:
            return jsonify({
                'error': 'max_dimension must be between 100 and 2400'
            }), 400

        # Save uploaded file
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
        output_path = os.path.join(OUTPUT_FOLDER, f"{unique_id}_output.jpg")

        file.save(input_path)
        print(f"Saved upload: {input_path}")

        # Validate image
        img = cv2.imread(input_path)
        if img is None:
            os.remove(input_path)
            return jsonify({'error': 'Invalid image file'}), 400

        # Update processor config if needed
        proc = get_processor()
        if proc.config.max_dimension != max_dimension:
            proc.config.max_dimension = max_dimension

        # Process image
        print(f"Processing with style={hatch_style}, max_dimension={max_dimension}")
        proc.quick_process(
            image_path=input_path,
            output_path=output_path,
            hatch_style=hatch_style
        )

        print(f"✓ Created crosshatch: {output_path}")

        # Send file and cleanup
        response = send_file(
            output_path,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f"crosshatch_{filename}"
        )

        # Cleanup files after sending
        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception as e:
                print(f"Cleanup error: {e}")

        return response

    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API documentation."""
    return jsonify({
        'service': 'Crosshatch API v2.0',
        'description': 'Create artistic crosshatch effects on portrait images',
        'endpoints': {
            'GET /health': 'Health check',
            'GET /': 'This documentation',
            'POST /api/crosshatch': {
                'description': 'Create crosshatch effect',
                'parameters': {
                    'file': 'Image file (required)',
                    'style': 'horizontal or vortex (optional, default: horizontal)',
                    'max_dimension': 'Max output dimension (optional, default: 1200)'
                },
                'example': 'curl -X POST -F "file=@portrait.jpg" -F "style=vortex" http://localhost:5000/api/crosshatch -o output.jpg'
            }
        },
        'powered_by': 'SAM2 + PyTorch',
        'github': 'https://github.com/joeljose/Crosshatch'
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=False)
