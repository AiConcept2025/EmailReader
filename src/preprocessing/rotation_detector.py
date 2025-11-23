"""
Document Rotation Detection Module

Detects and corrects document orientation using PaddleOCR and Tesseract OSD.
"""

import os
import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger('EmailReader.Preprocessing.Rotation')


class RotationDetector:
    """
    Detects and corrects document rotation using multiple methods.

    Supports PaddleOCR angle classification and Tesseract OSD.
    """

    def __init__(self, config: dict = None):
        """
        Initialize rotation detector.

        Args:
            config: Configuration dictionary with rotation detection settings
        """
        self.config = config or {}
        self.method = self.config.get('method', 'paddleocr')
        self.fallback_methods = self.config.get('fallback_methods', ['tesseract'])
        self.confidence_threshold = self.config.get('confidence_threshold', 0.8)

        logger.info("RotationDetector initialized with method: %s", self.method)

        # Lazy loading of OCR engines
        self._paddleocr = None
        self._tesseract_available = None

    def detect_rotation(self, image_path: str) -> Tuple[int, float]:
        """
        Detect rotation angle of document.

        Args:
            image_path: Path to image or PDF file

        Returns:
            Tuple of (rotation_angle, confidence)
            rotation_angle: 0, 90, 180, or 270 degrees
            confidence: 0.0 to 1.0

        Raises:
            RuntimeError: If all detection methods fail
        """
        logger.info("=" * 60)
        logger.info("Starting rotation detection for: %s", os.path.basename(image_path))
        logger.info("Configured method: %s, fallbacks: %s, threshold: %.2f",
                   self.method, self.fallback_methods, self.confidence_threshold)

        # Verify file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Try primary method plus fallbacks
        methods_to_try = [self.method] + self.fallback_methods
        results = []  # Store all results for analysis

        for idx, method in enumerate(methods_to_try, 1):
            try:
                logger.info("Trying method %d/%d: %s", idx, len(methods_to_try), method)

                if method == 'paddleocr':
                    angle, confidence = self._detect_with_paddleocr(image_path)
                elif method == 'tesseract':
                    angle, confidence = self._detect_with_tesseract(image_path)
                else:
                    logger.warning("Unknown rotation detection method: %s, skipping", method)
                    continue

                # Store result
                results.append({
                    'method': method,
                    'angle': angle,
                    'confidence': confidence
                })

                logger.info("✓ Method '%s' result: rotation=%d°, confidence=%.3f",
                          method, angle, confidence)

                # Check if confidence meets threshold
                if confidence >= self.confidence_threshold:
                    logger.info("✓ Confidence %.3f meets threshold %.2f - using this result",
                              confidence, self.confidence_threshold)
                    logger.info("=" * 60)
                    return angle, confidence
                else:
                    logger.warning("✗ Confidence %.3f below threshold %.2f - trying next method",
                                 confidence, self.confidence_threshold)

            except Exception as e:
                logger.error("✗ Method '%s' failed with error: %s", method, str(e), exc_info=True)
                results.append({
                    'method': method,
                    'angle': None,
                    'confidence': 0.0,
                    'error': str(e)
                })
                continue

        # If we get here, no method met the confidence threshold
        # Use the result with highest confidence if any succeeded
        successful_results = [r for r in results if r.get('angle') is not None]

        if successful_results:
            best_result = max(successful_results, key=lambda r: r['confidence'])
            logger.warning("No method met confidence threshold %.2f. Using best result: "
                         "method=%s, angle=%d°, confidence=%.3f",
                         self.confidence_threshold, best_result['method'],
                         best_result['angle'], best_result['confidence'])
            logger.info("=" * 60)
            return best_result['angle'], best_result['confidence']
        else:
            logger.error("All rotation detection methods failed completely. Assuming no rotation.")
            logger.info("Failed methods summary:")
            for result in results:
                if 'error' in result:
                    logger.info("  - %s: %s", result['method'], result['error'])
            logger.info("=" * 60)
            return 0, 0.0

    def _detect_with_paddleocr(self, image_path: str) -> Tuple[int, float]:
        """
        Detect rotation using PaddleOCR textline orientation classifier.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (angle, confidence)
        """
        if self._paddleocr is None:
            logger.debug("Initializing PaddleOCR for rotation detection")
            from paddleocr import PaddleOCR

            # Initialize with textline orientation enabled (PaddleOCR 3.3.2+ API)
            paddleocr_config = self.config.get('paddleocr', {})
            lang = paddleocr_config.get('lang', 'en')

            # Note: PaddleOCR 3.3.2 uses different parameter names:
            # - use_textline_orientation instead of use_angle_cls
            # - No use_gpu parameter (handled automatically by PaddlePaddle)
            # - No show_log parameter
            try:
                # Try with PP-OCRv4 first
                self._paddleocr = PaddleOCR(
                    lang=lang,
                    use_textline_orientation=True,  # Enable orientation detection
                    ocr_version='PP-OCRv4'  # Use latest OCR version
                )
                logger.info("PaddleOCR initialized with PP-OCRv4, lang=%s", lang)
            except ValueError as e:
                # PP-OCRv4 may not support all languages, try PP-OCRv3
                if "No models are available" in str(e):
                    logger.warning("PP-OCRv4 not available for lang='%s', trying PP-OCRv3", lang)
                    try:
                        self._paddleocr = PaddleOCR(
                            lang=lang,
                            use_textline_orientation=True,
                            ocr_version='PP-OCRv3'
                        )
                        logger.info("PaddleOCR initialized with PP-OCRv3, lang=%s", lang)
                    except ValueError:
                        # If still failing, try without specifying version (use default)
                        logger.warning("PP-OCRv3 not available for lang='%s', trying default version", lang)
                        self._paddleocr = PaddleOCR(
                            lang=lang,
                            use_textline_orientation=True
                        )
                        logger.info("PaddleOCR initialized with default version, lang=%s", lang)
                else:
                    logger.error("Failed to initialize PaddleOCR: %s", e)
                    raise
            except Exception as e:
                logger.error("Failed to initialize PaddleOCR: %s", e)
                raise

        # Handle PDF files - convert first page to image
        temp_image = None
        if image_path.lower().endswith('.pdf'):
            temp_image = self._pdf_to_image(image_path)
            image_path_to_use = temp_image
        else:
            image_path_to_use = image_path

        try:
            # Run OCR with orientation classification
            # In PaddleOCR 3.3.2, the ocr() method returns results with orientation info
            logger.debug("Running PaddleOCR on: %s", os.path.basename(image_path_to_use))
            result = self._paddleocr.ocr(image_path_to_use)

            # Extract angle information from results
            # PaddleOCR 3.3.2 returns: [[[box], (text, confidence)], ...]
            if result and len(result) > 0:
                # Get results from first page
                page_result = result[0]
                if page_result and len(page_result) > 0:
                    # Analyze detected text boxes for rotation
                    angles = []
                    confidences = []

                    for line in page_result:
                        if line and len(line) >= 2:
                            # line[0] = box coordinates
                            # line[1] = (text, confidence)
                            box = line[0]
                            text_info = line[1]

                            if text_info and len(text_info) >= 2:
                                text, conf = text_info

                                # Skip very low confidence results
                                if conf < 0.1:
                                    continue

                                # Get angle from box coordinates
                                angle = self._calculate_angle_from_box(box)
                                angles.append(angle)
                                confidences.append(conf)

                    if angles:
                        # Determine dominant angle
                        from collections import Counter
                        angle_counter = Counter(angles)
                        dominant_angle = angle_counter.most_common(1)[0][0]
                        avg_confidence = sum(confidences) / len(confidences)

                        logger.info("PaddleOCR detected %d text lines, dominant angle: %d°, avg confidence: %.2f",
                                  len(angles), dominant_angle, avg_confidence)

                        return dominant_angle, avg_confidence
                    else:
                        logger.warning("PaddleOCR found no valid text lines for rotation detection")
                else:
                    logger.warning("PaddleOCR returned empty page result")
            else:
                logger.warning("PaddleOCR returned no results")

            return 0, 0.0

        finally:
            # Clean up temporary image if created
            if temp_image and os.path.exists(temp_image):
                try:
                    os.unlink(temp_image)
                    logger.debug("Cleaned up temporary image: %s", temp_image)
                except Exception as e:
                    logger.warning("Failed to clean up temporary image %s: %s", temp_image, e)

    def _calculate_angle_from_box(self, box: list) -> int:
        """
        Calculate rotation angle from bounding box coordinates.

        Args:
            box: List of 4 points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

        Returns:
            Rotation angle: 0, 90, 180, or 270
        """
        # Calculate the angle of the text line
        import math

        # Use first two points to determine angle
        x1, y1 = box[0]
        x2, y2 = box[1]

        # Calculate angle in degrees
        angle_rad = math.atan2(y2 - y1, x2 - x1)
        angle_deg = math.degrees(angle_rad)

        # Normalize to 0, 90, 180, 270
        if -45 <= angle_deg < 45:
            return 0
        elif 45 <= angle_deg < 135:
            return 90
        elif angle_deg >= 135 or angle_deg < -135:
            return 180
        else:  # -135 to -45
            return 270

    def _detect_with_tesseract(self, image_path: str) -> Tuple[int, float]:
        """
        Detect rotation using Tesseract OSD (Orientation and Script Detection).

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (angle, confidence)
        """
        temp_image = None
        try:
            import pytesseract
            from PIL import Image, ImageEnhance

            # Handle PDF files - convert first page to image
            if image_path.lower().endswith('.pdf'):
                temp_image = self._pdf_to_image(image_path)
                image_path_to_use = temp_image
            else:
                image_path_to_use = image_path

            # Load image
            image = Image.open(image_path_to_use)

            # Convert to RGB if needed (OSD works better with RGB)
            if image.mode not in ('RGB', 'L'):
                logger.debug("Converting image from %s to RGB for OSD", image.mode)
                image = image.convert('RGB')

            # Enhance image for better OSD results if it's too small or low quality
            width, height = image.size
            logger.debug("Image size: %dx%d", width, height)

            # If image is too small, scale it up for better OSD results
            min_dimension = 300
            if width < min_dimension or height < min_dimension:
                scale_factor = max(min_dimension / width, min_dimension / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                logger.debug("Scaling image from %dx%d to %dx%d for better OSD",
                           width, height, new_width, new_height)
                image = image.resize((new_width, new_height), Image.LANCZOS)

            # Enhance contrast for better OSD
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)

            # Run OSD with PSM 0 (Orientation and Script Detection only)
            logger.debug("Running Tesseract OSD...")
            osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)

            # Extract all OSD information for debugging
            rotation = osd.get('rotate', 0)
            orientation = osd.get('orientation', 0)
            orientation_conf = osd.get('orientation_conf', 0)
            script = osd.get('script', 'Unknown')
            script_conf = osd.get('script_conf', 0)

            logger.debug("Tesseract OSD results - rotate=%d°, orientation=%d, orientation_conf=%.1f, "
                        "script=%s, script_conf=%.1f",
                        rotation, orientation, orientation_conf, script, script_conf)

            # Convert orientation confidence to 0-1 scale
            confidence = orientation_conf / 100.0

            # Tesseract returns the angle to rotate TO correct position
            # We want the current rotation angle
            # If Tesseract says rotate 90, the document is currently at 270
            current_angle = (360 - rotation) % 360

            # Log warning if confidence is very low
            if confidence < 0.5:
                logger.warning("Tesseract OSD has low confidence (%.2f) - results may be unreliable. "
                             "This often happens with documents that have: minimal text, uniform orientation, "
                             "or complex layouts.", confidence)

            logger.info("Tesseract OSD detected: current rotation=%d°, confidence=%.2f",
                       current_angle, confidence)

            return current_angle, confidence

        except pytesseract.TesseractError as e:
            error_msg = str(e)
            if "Too few characters" in error_msg or "no script" in error_msg.lower():
                logger.warning("Tesseract OSD failed: Insufficient text in image for orientation detection")
                # Return low confidence result instead of raising
                return 0, 0.01
            else:
                logger.error("Tesseract OSD error: %s", error_msg)
                raise

        except Exception as e:
            logger.error("Tesseract OSD failed with unexpected error: %s", e)
            raise

        finally:
            # Clean up temporary image if created
            if temp_image and os.path.exists(temp_image):
                try:
                    os.unlink(temp_image)
                    logger.debug("Cleaned up temporary image: %s", temp_image)
                except Exception as e:
                    logger.warning("Failed to clean up temporary image %s: %s", temp_image, e)

    def _pdf_to_image(self, pdf_path: str) -> str:
        """
        Convert first page of PDF to temporary image for rotation detection.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Path to temporary image file
        """
        import tempfile
        from pdf2image import convert_from_path

        logger.debug("Converting PDF first page to image for rotation detection")

        # Convert only first page
        images = convert_from_path(pdf_path, first_page=1, last_page=1)

        if not images:
            raise RuntimeError("Failed to convert PDF to image")

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        images[0].save(temp_path, 'PNG')
        logger.debug("PDF converted to temporary image: %s", temp_path)

        return temp_path

    def correct_rotation(self, input_path: str, output_path: str, angle: int) -> str:
        """
        Rotate document to correct orientation.

        Args:
            input_path: Path to input PDF or image
            output_path: Path to save corrected file
            angle: Rotation angle (0, 90, 180, 270)

        Returns:
            Path to corrected file
        """
        if angle == 0:
            logger.info("No rotation needed")
            # If no rotation needed, just copy or return original
            import shutil
            shutil.copy2(input_path, output_path)
            return output_path

        logger.info("Rotating document %d degrees: %s", angle, os.path.basename(input_path))

        # Handle PDF files
        if input_path.lower().endswith('.pdf'):
            return self._rotate_pdf(input_path, output_path, angle)
        else:
            # Handle image files
            return self._rotate_image(input_path, output_path, angle)

    def _rotate_pdf(self, input_path: str, output_path: str, angle: int) -> str:
        """Rotate PDF file."""
        from pdf2image import convert_from_path
        from PIL import Image
        import img2pdf
        import io

        logger.debug("Rotating PDF file %d degrees", angle)

        # Convert PDF to images
        images = convert_from_path(input_path)

        # Rotate images
        rotated_images = []
        for img in images:
            # PIL rotates counter-clockwise, so negate the angle
            rotation_angle = -angle if angle != 0 else 0
            rotated = img.rotate(rotation_angle, expand=True)
            rotated_images.append(rotated)

        # Save rotated images back to PDF
        # Convert PIL images to bytes
        image_bytes = []
        for img in rotated_images:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            image_bytes.append(img_byte_arr.getvalue())

        # Create PDF from images
        with open(output_path, 'wb') as f:
            f.write(img2pdf.convert(image_bytes))

        logger.info("PDF rotated and saved: %s", output_path)
        return output_path

    def _rotate_image(self, input_path: str, output_path: str, angle: int) -> str:
        """Rotate image file."""
        from PIL import Image

        logger.debug("Rotating image file %d degrees", angle)

        image = Image.open(input_path)

        # PIL rotates counter-clockwise
        rotation_angle = -angle if angle != 0 else 0
        rotated = image.rotate(rotation_angle, expand=True)

        rotated.save(output_path)
        logger.info("Image rotated and saved: %s", output_path)
        return output_path
