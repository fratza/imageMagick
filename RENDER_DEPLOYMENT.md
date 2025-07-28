# Deploying the ImageMagick OCR Preprocessing API on Render

This guide explains how to deploy the ImageMagick OCR Preprocessing API on Render and how to use it with PDF files.

## Deployment Steps

1. **Create a Render Account**

   - Sign up at [render.com](https://render.com/) if you don't have an account

2. **Create a New Web Service**

   - From your Render dashboard, click "New" and select "Web Service"
   - Connect your GitHub/GitLab repository or use the "Public Git repository" option
   - Enter the repository URL containing this code

3. **Configure the Web Service**

   - Name: `imagemagick-ocr-api` (or your preferred name)
   - Environment: `Docker`
   - Region: Choose the region closest to your users
   - Branch: `main` (or your default branch)
   - Build Command: Leave as default
   - Start Command: Leave as default (it will use the CMD from the Dockerfile)

4. **Add Environment Variables** (optional)

   - Click on "Environment" and add any variables you want to override from the .env file
   - For example:
     - `PORT`: 10000 (Render will automatically set this)
     - `DEBUG`: False

5. **Set Resource Allocation**

   - Select an appropriate plan based on your needs
   - For testing, the free tier should work, but for production use, consider a paid plan
   - Note that PDF processing can be memory-intensive, so choose accordingly

6. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your Docker container
   - Wait for the deployment to complete (this may take a few minutes)

## Using the API with PDF Files

Once deployed, your API will be available at `https://your-service-name.onrender.com`. You can use the `render_client_example.py` script to test it:

```bash
python render_client_example.py --pdf your_document.pdf --server https://your-service-name.onrender.com
```

### API Endpoints for PDF Processing

All endpoints now support PDF files. When a PDF is uploaded, the API will:

1. Convert the PDF to images (one per page)
2. Apply the requested preprocessing to each image
3. Return a ZIP file containing all processed images

#### Example cURL Command

```bash
curl -X POST \
  https://your-service-name.onrender.com/api/preprocess/pipeline \
  -F "file=@document.pdf" \
  -F "steps=deskew" \
  -F "steps=denoise" \
  -F "steps=binarize" \
  -F "params={\"binarize_threshold\": 128, \"denoise_level\": 2}" \
  -o processed_images.zip
```

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

## Troubleshooting

1. **Memory Issues**

   - If you encounter memory errors when processing large PDFs, consider:
     - Upgrading to a plan with more memory
     - Reducing the DPI in the PDF conversion (modify the `convert_pdf_to_images` function)

2. **Timeout Issues**

   - Render has a default timeout of 30 seconds for the free tier
   - For large PDFs, consider:
     - Upgrading to a paid plan with longer timeouts
     - Processing fewer pages at a time

3. **PDF Conversion Issues**
   - Ensure poppler-utils is properly installed (it should be via the Dockerfile)
   - Check the logs in the Render dashboard for specific errors

## Limitations

- The free tier of Render has limited resources and may not be suitable for processing large PDFs
- The service will spin down after periods of inactivity on the free tier, causing the first request to be slow
- There's a 10MB file upload limit on the free tier
