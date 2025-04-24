"""Mock document service for testing."""

from fastapi import UploadFile
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import DocumentProcessingError
from resume_customizer.services.document.processor import DocumentProcessor


class DocumentService:
    """Mock service for document operations.
    
    This class provides a high-level interface for document operations
    like validation, extraction, and cleaning.
    """
    
    async def validate_file(self, file: UploadFile) -> None:
        """Validate a document file.
        
        Args:
            file: The document file to validate
            
        Raises:
            DocumentProcessingError: If the file is invalid
        """
        if not file:
            raise DocumentProcessingError("No file provided")
        
        # Validate file size
        file.file.seek(0, 2)  # Go to the end of the file
        file_size = file.file.tell()  # Get current position (file size)
        file.file.seek(0)  # Reset file position
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            raise DocumentProcessingError(
                f"File size exceeds maximum allowed ({max_mb:.1f}MB)"
            )
        
        # Validate file type
        filename = file.filename if file.filename else ""
        if not any(filename.lower().endswith(f".{ext}") for ext in settings.ALLOWED_EXTENSIONS):
            allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise DocumentProcessingError(
                f"File type not allowed. Allowed extensions: {allowed}"
            )
    
    async def extract_text_from_file(self, file: UploadFile) -> str:
        """Extract text from a document file.
        
        This method delegates to the DocumentProcessor for actual extraction.
        
        Args:
            file: The document file
            
        Returns:
            str: The extracted text
            
        Raises:
            DocumentProcessingError: If there's an error extracting text
        """
        try:
            text = await DocumentProcessor.extract_text(file)
            
            if not text.strip():
                raise ValueError("Extracted text is empty")
            
            return text
        except UnicodeDecodeError as e:
            raise DocumentProcessingError(f"Could not decode file: {str(e)}")
        except Exception as e:
            raise DocumentProcessingError(f"Error extracting text: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text.
        
        Args:
            text: The text to clean
            
        Returns:
            str: The cleaned text
        """
        return text.strip()
    
    def get_allowed_extensions(self) -> list[str]:
        """Get the list of allowed file extensions.
        
        Returns:
            list[str]: The allowed extensions
        """
        return settings.ALLOWED_EXTENSIONS
    
    def get_max_upload_size(self) -> int:
        """Get the maximum allowed upload size in bytes.
        
        Returns:
            int: The maximum upload size
        """
        return settings.MAX_UPLOAD_SIZE
