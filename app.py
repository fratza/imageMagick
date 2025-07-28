import os
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import tempfile
from dotenv import load_dotenv
from preprocessing import ImagePreprocessor
import pdf2image
import shutil
import zipfile
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure temp directory exists
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

def is_pdf(filename):
    """Check if the file is a PDF based on extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def convert_pdf_to_images(pdf_path, output_dir):
    """Convert PDF to images using pdf2image"""
    try:
        images = pdf2image.convert_from_path(pdf_path, dpi=300, output_folder=output_dir)
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(output_dir, f'page_{i+1}.png')
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
        return image_paths
    except Exception as e:
        raise Exception(f"Error converting PDF to images: {str(e)}")

def process_image(image_path, output_path, steps=None, params=None):
    """Process a single image with the specified steps and parameters"""
    preprocessor = ImagePreprocessor(image_path)
    
    if steps:
        for step in steps:
            if step == 'deskew':
                preprocessor.deskew()
            elif step == 'denoise':
                level = params.get('denoise_level', 1) if params else 1
                preprocessor.denoise(level=level)
            elif step == 'binarize':
                threshold = params.get('binarize_threshold', 128) if params else 128
                preprocessor.binarize(threshold=threshold)
            elif step == 'enhance':
                factor = params.get('enhance_factor', 2.0) if params else 2.0
                preprocessor.enhance_contrast(factor=factor)
    else:
        # Default pipeline
        preprocessor.deskew()
        preprocessor.denoise()
        preprocessor.binarize()
        preprocessor.enhance_contrast()
    
    preprocessor.save(output_path)
    return output_path

@app.route('/api/preprocess', methods=['POST'])
def preprocess():
    """General preprocessing endpoint that applies a default pipeline"""
    if 'image' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No image or PDF provided"}), 400
    
    file = request.files.get('image') or request.files.get('file')
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Create temporary directory for this request
    request_temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    
    try:
        if is_pdf(file.filename):
            # Handle PDF file
            pdf_path = os.path.join(request_temp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # Convert PDF to images
            image_paths = convert_pdf_to_images(pdf_path, request_temp_dir)
            
            # Process each image
            processed_paths = []
            for i, image_path in enumerate(image_paths):
                output_path = os.path.join(request_temp_dir, f'processed_page_{i+1}.png')
                process_image(image_path, output_path)
                processed_paths.append(output_path)
            
            # Create a zip file with all processed images
            zip_path = os.path.join(request_temp_dir, 'processed_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, path in enumerate(processed_paths):
                    zipf.write(path, f'page_{i+1}.png')
            
            return send_file(zip_path, mimetype='application/zip', 
                            as_attachment=True, download_name='processed_images.zip')
        else:
            # Handle single image file
            temp_input = os.path.join(request_temp_dir, 'input.png')
            temp_output = os.path.join(request_temp_dir, 'output.png')
            file.save(temp_input)
            
            # Process the image
            process_image(temp_input, temp_output)
            
            return send_file(temp_output, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if os.path.exists(request_temp_dir) and not app.debug:
            shutil.rmtree(request_temp_dir)

@app.route('/api/preprocess/binarize', methods=['POST'])
def binarize():
    """Binarize an image to improve OCR accuracy"""
    if 'image' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No image or PDF provided"}), 400
    
    file = request.files.get('image') or request.files.get('file')
    threshold = request.form.get('threshold', 128, type=int)
    
    # Create temporary directory for this request
    request_temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    
    try:
        if is_pdf(file.filename):
            # Handle PDF file
            pdf_path = os.path.join(request_temp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # Convert PDF to images
            image_paths = convert_pdf_to_images(pdf_path, request_temp_dir)
            
            # Process each image
            processed_paths = []
            for i, image_path in enumerate(image_paths):
                output_path = os.path.join(request_temp_dir, f'processed_page_{i+1}.png')
                process_image(image_path, output_path, steps=['binarize'], 
                            params={'binarize_threshold': threshold})
                processed_paths.append(output_path)
            
            # Create a zip file with all processed images
            zip_path = os.path.join(request_temp_dir, 'processed_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, path in enumerate(processed_paths):
                    zipf.write(path, f'page_{i+1}.png')
            
            return send_file(zip_path, mimetype='application/zip', 
                            as_attachment=True, download_name='processed_images.zip')
        else:
            # Handle single image file
            temp_input = os.path.join(request_temp_dir, 'input.png')
            temp_output = os.path.join(request_temp_dir, 'output.png')
            file.save(temp_input)
            
            # Process the image
            process_image(temp_input, temp_output, steps=['binarize'], 
                        params={'binarize_threshold': threshold})
            
            return send_file(temp_output, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if os.path.exists(request_temp_dir) and not app.debug:
            shutil.rmtree(request_temp_dir)

@app.route('/api/preprocess/deskew', methods=['POST'])
def deskew():
    """Deskew an image to straighten text"""
    if 'image' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No image or PDF provided"}), 400
    
    file = request.files.get('image') or request.files.get('file')
    
    # Create temporary directory for this request
    request_temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    
    try:
        if is_pdf(file.filename):
            # Handle PDF file
            pdf_path = os.path.join(request_temp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # Convert PDF to images
            image_paths = convert_pdf_to_images(pdf_path, request_temp_dir)
            
            # Process each image
            processed_paths = []
            for i, image_path in enumerate(image_paths):
                output_path = os.path.join(request_temp_dir, f'processed_page_{i+1}.png')
                process_image(image_path, output_path, steps=['deskew'])
                processed_paths.append(output_path)
            
            # Create a zip file with all processed images
            zip_path = os.path.join(request_temp_dir, 'processed_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, path in enumerate(processed_paths):
                    zipf.write(path, f'page_{i+1}.png')
            
            return send_file(zip_path, mimetype='application/zip', 
                            as_attachment=True, download_name='processed_images.zip')
        else:
            # Handle single image file
            temp_input = os.path.join(request_temp_dir, 'input.png')
            temp_output = os.path.join(request_temp_dir, 'output.png')
            file.save(temp_input)
            
            # Process the image
            process_image(temp_input, temp_output, steps=['deskew'])
            
            return send_file(temp_output, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if os.path.exists(request_temp_dir) and not app.debug:
            shutil.rmtree(request_temp_dir)

@app.route('/api/preprocess/denoise', methods=['POST'])
def denoise():
    """Remove noise from an image"""
    if 'image' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No image or PDF provided"}), 400
    
    file = request.files.get('image') or request.files.get('file')
    level = request.form.get('level', 1, type=int)
    
    # Create temporary directory for this request
    request_temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    
    try:
        if is_pdf(file.filename):
            # Handle PDF file
            pdf_path = os.path.join(request_temp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # Convert PDF to images
            image_paths = convert_pdf_to_images(pdf_path, request_temp_dir)
            
            # Process each image
            processed_paths = []
            for i, image_path in enumerate(image_paths):
                output_path = os.path.join(request_temp_dir, f'processed_page_{i+1}.png')
                process_image(image_path, output_path, steps=['denoise'], 
                            params={'denoise_level': level})
                processed_paths.append(output_path)
            
            # Create a zip file with all processed images
            zip_path = os.path.join(request_temp_dir, 'processed_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, path in enumerate(processed_paths):
                    zipf.write(path, f'page_{i+1}.png')
            
            return send_file(zip_path, mimetype='application/zip', 
                            as_attachment=True, download_name='processed_images.zip')
        else:
            # Handle single image file
            temp_input = os.path.join(request_temp_dir, 'input.png')
            temp_output = os.path.join(request_temp_dir, 'output.png')
            file.save(temp_input)
            
            # Process the image
            process_image(temp_input, temp_output, steps=['denoise'], 
                        params={'denoise_level': level})
            
            return send_file(temp_output, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if os.path.exists(request_temp_dir) and not app.debug:
            shutil.rmtree(request_temp_dir)

@app.route('/api/preprocess/enhance', methods=['POST'])
def enhance():
    """Enhance text contrast in an image"""
    if 'image' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No image or PDF provided"}), 400
    
    file = request.files.get('image') or request.files.get('file')
    factor = request.form.get('factor', 2.0, type=float)
    
    # Create temporary directory for this request
    request_temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    
    try:
        if is_pdf(file.filename):
            # Handle PDF file
            pdf_path = os.path.join(request_temp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # Convert PDF to images
            image_paths = convert_pdf_to_images(pdf_path, request_temp_dir)
            
            # Process each image
            processed_paths = []
            for i, image_path in enumerate(image_paths):
                output_path = os.path.join(request_temp_dir, f'processed_page_{i+1}.png')
                process_image(image_path, output_path, steps=['enhance'], 
                            params={'enhance_factor': factor})
                processed_paths.append(output_path)
            
            # Create a zip file with all processed images
            zip_path = os.path.join(request_temp_dir, 'processed_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, path in enumerate(processed_paths):
                    zipf.write(path, f'page_{i+1}.png')
            
            return send_file(zip_path, mimetype='application/zip', 
                            as_attachment=True, download_name='processed_images.zip')
        else:
            # Handle single image file
            temp_input = os.path.join(request_temp_dir, 'input.png')
            temp_output = os.path.join(request_temp_dir, 'output.png')
            file.save(temp_input)
            
            # Process the image
            process_image(temp_input, temp_output, steps=['enhance'], 
                        params={'enhance_factor': factor})
            
            return send_file(temp_output, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if os.path.exists(request_temp_dir) and not app.debug:
            shutil.rmtree(request_temp_dir)

@app.route('/api/preprocess/pipeline', methods=['POST'])
def pipeline():
    """Apply a custom pipeline of preprocessing steps"""
    if 'image' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No image or PDF provided"}), 400
    
    file = request.files.get('image') or request.files.get('file')
    steps = request.form.getlist('steps')
    
    # Get parameters
    params = {}
    if 'params' in request.form:
        try:
            import json
            params = json.loads(request.form.get('params'))
        except:
            pass
    
    # Create temporary directory for this request
    request_temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    
    try:
        if is_pdf(file.filename):
            # Handle PDF file
            pdf_path = os.path.join(request_temp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # Convert PDF to images
            image_paths = convert_pdf_to_images(pdf_path, request_temp_dir)
            
            # Process each image
            processed_paths = []
            for i, image_path in enumerate(image_paths):
                output_path = os.path.join(request_temp_dir, f'processed_page_{i+1}.png')
                process_image(image_path, output_path, steps=steps, params=params)
                processed_paths.append(output_path)
            
            # Create a zip file with all processed images
            zip_path = os.path.join(request_temp_dir, 'processed_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, path in enumerate(processed_paths):
                    zipf.write(path, f'page_{i+1}.png')
            
            return send_file(zip_path, mimetype='application/zip', 
                            as_attachment=True, download_name='processed_images.zip')
        else:
            # Handle single image file
            temp_input = os.path.join(request_temp_dir, 'input.png')
            temp_output = os.path.join(request_temp_dir, 'output.png')
            file.save(temp_input)
            
            # Process the image
            process_image(temp_input, temp_output, steps=steps, params=params)
            
            return send_file(temp_output, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if os.path.exists(request_temp_dir) and not app.debug:
            shutil.rmtree(request_temp_dir)

@app.route('/api/preprocess/google_vision', methods=['POST'])
def google_vision():
    """
    Dedicated endpoint for Google Vision OCR preprocessing.
    Applies the optimal preprocessing steps in the recommended order:
    1. deskew → 2. enhance → 3. denoise
    """
    if 'image' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No image or PDF provided"}), 400
    
    file = request.files.get('image') or request.files.get('file')
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Get optional parameters with Google Vision optimized defaults
    enhance_factor = request.form.get('enhance_factor', 1.5)
    try:
        enhance_factor = float(enhance_factor)
    except ValueError:
        enhance_factor = 1.5
        
    denoise_level = request.form.get('denoise_level', 1)
    try:
        denoise_level = int(denoise_level)
    except ValueError:
        denoise_level = 1
    
    # Create temporary directory for this request
    request_temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    
    try:
        if is_pdf(file.filename):
            # Handle PDF file
            pdf_path = os.path.join(request_temp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # Convert PDF to images
            image_paths = convert_pdf_to_images(pdf_path, request_temp_dir)
            
            # Process each image with Google Vision optimized pipeline
            processed_paths = []
            for i, image_path in enumerate(image_paths):
                output_path = os.path.join(request_temp_dir, f'processed_page_{i+1}.png')
                
                # Apply Google Vision optimized pipeline
                steps = ['deskew', 'enhance', 'denoise']
                params = {
                    'enhance_factor': enhance_factor,
                    'denoise_level': denoise_level
                }
                process_image(image_path, output_path, steps=steps, params=params)
                processed_paths.append(output_path)
            
            # Create a zip file with all processed images
            zip_path = os.path.join(request_temp_dir, 'processed_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, path in enumerate(processed_paths):
                    zipf.write(path, f'page_{i+1}.png')
            
            return send_file(zip_path, mimetype='application/zip', 
                            as_attachment=True, download_name='processed_images.zip')
        else:
            # Handle single image file
            temp_input = os.path.join(request_temp_dir, 'input.png')
            temp_output = os.path.join(request_temp_dir, 'output.png')
            file.save(temp_input)
            
            # Apply Google Vision optimized pipeline
            steps = ['deskew', 'enhance', 'denoise']
            params = {
                'enhance_factor': enhance_factor,
                'denoise_level': denoise_level
            }
            process_image(temp_input, temp_output, steps=steps, params=params)
            
            return send_file(temp_output, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if os.path.exists(request_temp_dir) and not app.debug:
            shutil.rmtree(request_temp_dir)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
