{{ ... }}

## Using the API with Google Vision OCR

The API now includes a dedicated endpoint optimized for Google Vision OCR preprocessing:

```
/api/preprocess/google_vision
```

This endpoint applies the recommended preprocessing steps in the optimal order for Google Vision:

1. Deskew (straighten text)
2. Enhance contrast (with moderate factor: 1.5)
3. Denoise (with light denoising: level 1)

Note that binarization is intentionally omitted as Google Vision often performs better with grayscale images.

### Example cURL Command for Google Vision Endpoint

```bash
curl -X POST \
  https://your-service-name.onrender.com/api/preprocess/google_vision \
  -F "file=@document.pdf" \
  -o processed_images.zip
```

You can optionally customize the parameters:

```bash
curl -X POST \
  https://your-service-name.onrender.com/api/preprocess/google_vision \
  -F "file=@document.pdf" \
  -F "enhance_factor=1.2" \
  -F "denoise_level=1" \
  -o processed_images.zip
```

### Using the Google Vision Client Script

The included `google_vision_client.py` script makes it easy to:

1. Send an image/PDF to your preprocessing API
2. Get the processed image(s)
3. Send them to Google Vision OCR
4. Extract the text

```bash
python google_vision_client.py \
  --image document.pdf \
  --api https://your-service-name.onrender.com \
  --credentials path/to/google-credentials.json \
  --output extracted_text.txt
```

Note: You'll need to install the Google Cloud Vision client library:

```bash
pip install google-cloud-vision
```

{{ ... }}
