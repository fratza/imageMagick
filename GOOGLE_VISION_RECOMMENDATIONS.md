# Google Vision OCR Preprocessing Recommendations

This document provides recommendations for optimizing image preprocessing specifically for Google Vision OCR. Google Vision has different characteristics than other OCR engines like Tesseract, so the preprocessing pipeline should be adjusted accordingly.

## Recommended Preprocessing Pipeline for Google Vision

Google Vision OCR is more advanced than many traditional OCR engines and often performs better with less aggressive preprocessing. Here's the recommended pipeline order for Google Vision:

```
1. deskew → 2. enhance → 3. denoise
```

Note that binarization is often **not recommended** for Google Vision as it can reduce the information available to the advanced ML models that Google Vision uses.

## Preprocessing Parameters for Google Vision

| Step     | Parameter | Recommended Value | Notes                                                   |
| -------- | --------- | ----------------- | ------------------------------------------------------- |
| deskew   | max_angle | 10                | Standard value works well                               |
| enhance  | factor    | 1.2-1.5           | Use moderate enhancement (lower than for Tesseract)     |
| denoise  | level     | 1                 | Use minimal denoising (lower than for Tesseract)        |
| binarize | threshold | 160               | Only if needed; use higher threshold than for Tesseract |

## Why This Pipeline Works Better for Google Vision

1. **Deskew First**: Straightening text is always beneficial for any OCR engine.

2. **Enhance Before Denoise**: Google Vision benefits from preserving more image details, so enhancing contrast before denoising helps maintain important text features.

3. **Light Denoising**: Google Vision's ML models can handle some noise, so aggressive denoising can actually remove useful information.

4. **Avoid Binarization**: Unlike traditional OCR engines, Google Vision often performs better on grayscale images where subtle variations in text and background are preserved.

## Example Usage with the API

Using the `google_vision_client.py` script:

```bash
python google_vision_client.py --image document.pdf --api http://localhost:5000 --credentials path/to/google-credentials.json --output extracted_text.txt
```

Or making a direct API call with the recommended pipeline:

```bash
curl -X POST \
  http://localhost:5000/api/preprocess/pipeline \
  -F "file=@document.pdf" \
  -F "steps=deskew" \
  -F "steps=enhance" \
  -F "steps=denoise" \
  -F "params={\"enhance_factor\": 1.5, \"denoise_level\": 1}" \
  -o processed_images.zip
```

## Testing and Comparison

To determine the optimal preprocessing for your specific documents with Google Vision:

1. Process your sample documents with different pipelines:

   - No preprocessing (raw image)
   - Default pipeline (deskew → denoise → binarize → enhance)
   - Google Vision recommended pipeline (deskew → enhance → denoise)

2. Send each version to Google Vision OCR

3. Compare the results based on:
   - Character accuracy
   - Word accuracy
   - Structural preservation (paragraphs, tables, etc.)

The `google_vision_client.py` script can help automate this testing process.

## Additional Considerations for Google Vision

1. **Resolution**: Google Vision works well with images of at least 300 DPI. Very high resolution isn't always necessary.

2. **File Format**: PNG is generally preferred over JPEG to avoid compression artifacts.

3. **Image Size**: For best results, ensure text is at least 10 pixels in height.

4. **Color vs. Grayscale**: Google Vision can extract text from color images effectively, so conversion to grayscale is optional.

5. **Document Type Detection**: Google Vision can automatically detect document types, so preserving the overall document structure is beneficial.

By following these recommendations, you can optimize your preprocessing pipeline specifically for Google Vision OCR to achieve the best possible text recognition results.
