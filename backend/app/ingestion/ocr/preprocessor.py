"""
Image Preprocessor for OCR
==========================

Improves image quality before OCR processing.

Why preprocess?
---------------
Raw scanned images often have problems:
- Skewed (rotated slightly)
- Low contrast (faded text)
- Noise (speckles, artifacts)
- Uneven lighting

These issues reduce OCR accuracy. Preprocessing fixes them.

Processing pipeline:
1. Convert to grayscale (OCR works on black/white)
2. Resize if too small (OCR needs readable text)
3. Denoise (remove speckles)
4. Increase contrast (make text stand out)
5. Binarize (convert to pure black and white)

We use Pillow (PIL) for image processing - it's simple and sufficient.
For more advanced preprocessing, OpenCV would be better but adds complexity.
"""

from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
from typing import Optional
import io


class ImagePreprocessor:
    """
    Preprocesses images to improve OCR accuracy.
    
    Usage:
        preprocessor = ImagePreprocessor()
        
        # From file
        processed = preprocessor.preprocess(Path("scan.png"))
        
        # From PIL Image
        processed = preprocessor.preprocess_image(pil_image)
    
    All methods return PIL Image objects that can be passed directly to OCR.
    """
    
    # Minimum width for good OCR results
    # If image is smaller, we'll upscale it
    MIN_WIDTH = 1000
    
    # Target DPI for OCR (dots per inch)
    # 300 DPI is standard for document scanning
    TARGET_DPI = 300
    
    def preprocess(self, image_path: Path) -> Image.Image:
        """
        Load and preprocess an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed PIL Image
        """
        image = Image.open(image_path)
        return self.preprocess_image(image)
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Apply all preprocessing steps to an image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Step 1: Convert to grayscale
        # OCR doesn't need color - grayscale is faster and often more accurate
        if image.mode != "L":  # "L" is grayscale mode
            image = image.convert("L")
        
        # Step 2: Resize if too small
        image = self._resize_if_needed(image)
        
        # Step 3: Denoise
        # Removes small speckles that confuse OCR
        image = self._denoise(image)
        
        # Step 4: Enhance contrast
        # Makes text stand out from background
        image = self._enhance_contrast(image)
        
        # Step 5: Sharpen
        # Makes text edges clearer
        image = self._sharpen(image)
        
        return image
    
    def preprocess_for_ocr(
        self, 
        image: Image.Image, 
        deskew: bool = False
    ) -> Image.Image:
        """
        Full preprocessing pipeline optimized for OCR.
        
        Args:
            image: PIL Image object
            deskew: Whether to attempt deskewing (rotation correction)
                    Note: Basic implementation, may not be perfect
        
        Returns:
            Preprocessed PIL Image ready for OCR
        """
        # Basic preprocessing
        processed = self.preprocess_image(image)
        
        # Optional deskew
        # This is a simple implementation - production systems use more
        # sophisticated methods (Hough transform, projection profiles)
        if deskew:
            processed = self._simple_deskew(processed)
        
        return processed
    
    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """
        Resize image if it's too small for good OCR.
        
        Small images have small text that OCR struggles with.
        Upscaling helps, but there's a limit - can't create detail that isn't there.
        
        Args:
            image: PIL Image
            
        Returns:
            Resized image (or original if already large enough)
        """
        width, height = image.size
        
        if width < self.MIN_WIDTH:
            # Calculate new size maintaining aspect ratio
            ratio = self.MIN_WIDTH / width
            new_width = self.MIN_WIDTH
            new_height = int(height * ratio)
            
            # LANCZOS is high-quality resampling
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        return image
    
    def _denoise(self, image: Image.Image) -> Image.Image:
        """
        Remove noise from image.
        
        Uses median filter - replaces each pixel with the median of neighbors.
        Effectively removes small speckles while preserving edges.
        
        Args:
            image: PIL Image
            
        Returns:
            Denoised image
        """
        # MedianFilter with size 3 (3x3 neighborhood)
        # Larger size = more smoothing but may blur text
        return image.filter(ImageFilter.MedianFilter(size=3))
    
    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """
        Increase image contrast.
        
        Makes dark pixels darker and light pixels lighter.
        Text becomes more distinct from background.
        
        Args:
            image: PIL Image
            
        Returns:
            Contrast-enhanced image
        """
        enhancer = ImageEnhance.Contrast(image)
        # Factor > 1 increases contrast
        # 1.5 is moderate enhancement - adjust if needed
        return enhancer.enhance(1.5)
    
    def _sharpen(self, image: Image.Image) -> Image.Image:
        """
        Sharpen image to make text edges clearer.
        
        Args:
            image: PIL Image
            
        Returns:
            Sharpened image
        """
        enhancer = ImageEnhance.Sharpness(image)
        # Factor > 1 increases sharpness
        return enhancer.enhance(2.0)
    
    def _simple_deskew(self, image: Image.Image) -> Image.Image:
        """
        Simple deskew attempt.
        
        This is a basic implementation that works for slight rotations.
        For production, consider using OpenCV's more sophisticated methods.
        
        Note: This is a placeholder - proper deskewing requires detecting
        text line angles, which is complex. For now, we return the image as-is.
        Full implementation would use:
        - Hough line detection
        - Projection profile analysis
        - Or a dedicated library like deskew
        
        Args:
            image: PIL Image
            
        Returns:
            Deskewed image (currently returns original)
        """
        # TODO: Implement proper deskewing if needed
        # For now, return as-is
        # Most modern scanners auto-deskew anyway
        return image
    
    def image_to_bytes(self, image: Image.Image, format: str = "PNG") -> bytes:
        """
        Convert PIL Image to bytes.
        
        Useful when you need to pass image data to an API or save temporarily.
        
        Args:
            image: PIL Image
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            Image as bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return buffer.getvalue()