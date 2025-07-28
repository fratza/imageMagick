from wand.image import Image
from wand.color import Color
import os
import math
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """
    A class for preprocessing images to improve OCR accuracy using ImageMagick via Wand.
    """
    
    def __init__(self, image_path):
        """
        Initialize the preprocessor with an image path.
        
        Args:
            image_path (str): Path to the input image
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        self.image_path = image_path
        self.image = Image(filename=image_path)
        logger.info(f"Loaded image: {image_path} ({self.image.width}x{self.image.height})")
    
    def deskew(self, max_angle=10):
        """
        Deskew the image to straighten text.
        
        Args:
            max_angle (int): Maximum rotation angle in degrees
        
        Returns:
            self: For method chaining
        """
        try:
            # Convert to grayscale for better deskew detection
            with self.image.clone() as temp:
                temp.type = 'grayscale'
                # Get skew angle
                angle = temp.deskew(threshold=0.4 * temp.quantum_range)
                
                # Only deskew if the angle is within reasonable bounds
                if angle and abs(angle) <= max_angle:
                    logger.info(f"Deskewing image by {angle} degrees")
                    self.image.deskew(threshold=0.4 * self.image.quantum_range)
                else:
                    logger.info("No deskewing needed or angle too extreme")
        except Exception as e:
            logger.error(f"Error during deskew: {str(e)}")
            # Continue without deskewing if there's an error
        
        return self
    
    def denoise(self, level=1):
        """
        Remove noise from the image.
        
        Args:
            level (int): Noise reduction level (1-3)
        
        Returns:
            self: For method chaining
        """
        level = max(1, min(3, level))  # Clamp level between 1 and 3
        
        try:
            # Apply noise reduction
            if level == 1:
                self.image.despeckle()
            elif level == 2:
                self.image.despeckle()
                self.image.despeckle()
            else:  # level == 3
                self.image.noise("gaussian", attenuate=1.0)
                self.image.enhance()
            
            logger.info(f"Applied noise reduction at level {level}")
        except Exception as e:
            logger.error(f"Error during denoise: {str(e)}")
        
        return self
    
    def binarize(self, threshold=128):
        """
        Binarize the image (convert to black and white).
        
        Args:
            threshold (int): Threshold value (0-255)
        
        Returns:
            self: For method chaining
        """
        try:
            # Convert to grayscale first
            self.image.type = 'grayscale'
            
            # Apply threshold
            self.image.threshold(threshold / 255.0 * self.image.quantum_range)
            logger.info(f"Binarized image with threshold {threshold}")
        except Exception as e:
            logger.error(f"Error during binarization: {str(e)}")
        
        return self
    
    def enhance_contrast(self, factor=2.0):
        """
        Enhance contrast to make text more visible.
        
        Args:
            factor (float): Contrast enhancement factor
        
        Returns:
            self: For method chaining
        """
        try:
            # Normalize the image first
            self.image.normalize()
            
            # Apply contrast enhancement
            self.image.contrast(sharpen=True)
            
            if factor > 1.0:
                # Apply additional contrast based on factor
                self.image.sigmoidal_contrast(
                    contrast=factor,
                    mid_point=0.5 * self.image.quantum_range
                )
            
            logger.info(f"Enhanced contrast with factor {factor}")
        except Exception as e:
            logger.error(f"Error during contrast enhancement: {str(e)}")
        
        return self
    
    def resize(self, scale_factor=2.0):
        """
        Resize the image to improve OCR accuracy.
        
        Args:
            scale_factor (float): Scale factor for resizing
        
        Returns:
            self: For method chaining
        """
        try:
            original_width = self.image.width
            original_height = self.image.height
            
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            self.image.resize(new_width, new_height, filter='lanczos')
            logger.info(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
        except Exception as e:
            logger.error(f"Error during resize: {str(e)}")
        
        return self
    
    def sharpen(self, radius=0, sigma=1.0):
        """
        Sharpen the image to make text more defined.
        
        Args:
            radius (float): Radius of the Gaussian operator
            sigma (float): Standard deviation of the Gaussian operator
        
        Returns:
            self: For method chaining
        """
        try:
            self.image.sharpen(radius=radius, sigma=sigma)
            logger.info(f"Sharpened image with radius={radius}, sigma={sigma}")
        except Exception as e:
            logger.error(f"Error during sharpening: {str(e)}")
        
        return self
    
    def remove_borders(self, fuzz=10):
        """
        Remove borders from the image.
        
        Args:
            fuzz (int): Fuzz factor for border detection (0-100)
        
        Returns:
            self: For method chaining
        """
        try:
            # Convert fuzz percentage to quantum range
            fuzz_value = fuzz / 100.0 * self.image.quantum_range
            self.image.trim(color=None, fuzz=fuzz_value)
            logger.info(f"Removed borders with fuzz={fuzz}")
        except Exception as e:
            logger.error(f"Error during border removal: {str(e)}")
        
        return self
    
    def save(self, output_path):
        """
        Save the processed image.
        
        Args:
            output_path (str): Path to save the output image
        
        Returns:
            str: Path to the saved image
        """
        try:
            self.image.save(filename=output_path)
            logger.info(f"Saved processed image to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            raise
    
    def __del__(self):
        """Clean up resources when the object is destroyed."""
        if hasattr(self, 'image') and self.image:
            self.image.close()
