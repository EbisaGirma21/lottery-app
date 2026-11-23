"""
Receipt parser for extracting transaction reference numbers and amounts
from uploaded payment proof files (PDF and images).

Supports Ethiopian bank receipt formats:
- CBE: FT-prefixed alphanumeric references (e.g., FT24344T4BX8)
- Telebirr: Numeric transaction IDs (e.g., 100005844221)
- CBE Birr: Similar to CBE
- Awash / BOA: General alphanumeric references

PDF text extraction uses pdfplumber.
Image OCR uses pytesseract (optional, graceful fallback if not installed).
"""
import io
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ReceiptData:
    """Structured data extracted from a payment receipt."""

    extracted_references: List[str] = field(default_factory=list)
    extracted_amount: Optional[Decimal] = None
    raw_text: str = ''
    confidence: str = 'none'  # 'high', 'medium', 'low', 'none'
    extraction_method: str = ''  # 'pdf_text', 'ocr', 'none'
    error: str = ''

    def to_dict(self) -> dict:
        return {
            'extracted_references': self.extracted_references,
            'extracted_amount': str(self.extracted_amount) if self.extracted_amount else None,
            'raw_text_preview': self.raw_text[:500] if self.raw_text else '',
            'confidence': self.confidence,
            'extraction_method': self.extraction_method,
            'error': self.error,
        }


# ─── Reference Number Patterns per Bank ────────────────────────────────────

# CBE: "FT" followed by 8-12 alphanumeric characters
_CBE_REF_PATTERN = re.compile(r'\bFT[A-Z0-9]{8,12}\b', re.IGNORECASE)

# Telebirr: 10-15 digit numeric transaction IDs
_TELEBIRR_REF_PATTERN = re.compile(r'\b\d{10,15}\b')

# Generic alphanumeric reference (fallback for Awash, BOA, etc.)
# Looks for labeled references like "Ref: ABC123", "Reference No: XYZ789"
_LABELED_REF_PATTERN = re.compile(
    r'(?:ref(?:erence)?[\s.:]*(?:no\.?|number|#)?[\s.:]*)'
    r'([A-Z0-9]{6,20})',
    re.IGNORECASE,
)

# Transaction ID / Number labels
_TRANSACTION_ID_PATTERN = re.compile(
    r'(?:transaction[\s]*(?:id|no\.?|number|#|ref)?[\s.:]*)'
    r'([A-Z0-9]{6,20})',
    re.IGNORECASE,
)

# ─── Amount Patterns ───────────────────────────────────────────────────────

# Matches: "ETB 100.00", "Birr 500", "100.00 ETB", "Amount: 1,500.00"
_AMOUNT_PATTERNS = [
    # "ETB 1,234.56" or "Birr 1234.56"
    re.compile(
        r'(?:ETB|Birr|BR)\s*[:\s]*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{1,2})?)',
        re.IGNORECASE,
    ),
    # "1,234.56 ETB" or "1234.56 Birr"
    re.compile(
        r'([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{1,2})?)\s*(?:ETB|Birr|BR)',
        re.IGNORECASE,
    ),
    # "Amount: 1,234.56" or "Total: 500.00"
    re.compile(
        r'(?:amount|total|paid|transferred)[\s.:]*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{1,2})?)',
        re.IGNORECASE,
    ),
]

# Bank-specific pattern mapping
BANK_PATTERNS: Dict[str, List[re.Pattern]] = {
    'telebirr': [_TELEBIRR_REF_PATTERN, _TRANSACTION_ID_PATTERN, _LABELED_REF_PATTERN],
    'cbe': [_CBE_REF_PATTERN, _TRANSACTION_ID_PATTERN, _LABELED_REF_PATTERN],
    'cbe_birr': [_CBE_REF_PATTERN, _TRANSACTION_ID_PATTERN, _LABELED_REF_PATTERN],
    'awash': [_TRANSACTION_ID_PATTERN, _LABELED_REF_PATTERN],
    'boa': [_TRANSACTION_ID_PATTERN, _LABELED_REF_PATTERN],
}


class ReceiptParser:
    """
    Extracts transaction reference numbers and amounts from receipt files.
    """

    @classmethod
    def extract(cls, file_obj, payment_method: str = '') -> ReceiptData:
        """
        Extract receipt data from an uploaded file.

        Args:
            file_obj: Django UploadedFile or file-like object
            payment_method: Payment method key (e.g., 'telebirr', 'cbe')

        Returns:
            ReceiptData with extracted references, amount, and confidence
        """
        if file_obj is None:
            return ReceiptData(error='No file provided.')

        # Determine file type from name or content type
        filename = getattr(file_obj, 'name', '') or ''
        content_type = getattr(file_obj, 'content_type', '') or ''
        filename_lower = filename.lower()

        try:
            # Read file content
            file_obj.seek(0)
            file_bytes = file_obj.read()
            file_obj.seek(0)  # Reset for later use

            if not file_bytes:
                return ReceiptData(error='Uploaded file is empty.')

            # Extract text based on file type
            if filename_lower.endswith('.pdf') or 'pdf' in content_type:
                text = cls._extract_text_from_pdf(file_bytes)
                method = 'pdf_text'
            elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')):
                text = cls._extract_text_from_image(file_bytes)
                method = 'ocr'
            elif 'image' in content_type:
                text = cls._extract_text_from_image(file_bytes)
                method = 'ocr'
            else:
                return ReceiptData(
                    error=f'Unsupported file type: {filename_lower or content_type}. '
                          'Please upload a PDF or image file (JPG, PNG).',
                )

            if not text or not text.strip():
                return ReceiptData(
                    extraction_method=method,
                    confidence='none',
                    error='Could not extract any text from the receipt. '
                          'The file may be empty, corrupted, or a scanned image '
                          'without OCR support.',
                )

            # Extract references and amount
            references = cls._extract_references(text, payment_method)
            amount = cls._extract_amount(text)
            confidence = cls._assess_confidence(references, amount, payment_method)

            return ReceiptData(
                extracted_references=references,
                extracted_amount=amount,
                raw_text=text,
                confidence=confidence,
                extraction_method=method,
            )

        except Exception as exc:
            logger.exception('Receipt parsing error: %s', exc)
            return ReceiptData(error=f'Failed to parse receipt: {str(exc)}')

    @classmethod
    def _extract_text_from_pdf(cls, file_bytes: bytes) -> str:
        """Extract text from a PDF file using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            logger.error('pdfplumber is not installed. Cannot extract text from PDF.')
            return ''

        text_parts = []
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                    # Also try extracting from tables
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if row:
                                row_text = ' '.join(
                                    cell.strip() for cell in row if cell and cell.strip()
                                )
                                if row_text:
                                    text_parts.append(row_text)
        except Exception as exc:
            logger.warning('pdfplumber extraction failed: %s', exc)

        return '\n'.join(text_parts)

    @classmethod
    def _extract_text_from_image(cls, file_bytes: bytes) -> str:
        """Extract text from an image using pytesseract OCR (best-effort)."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            logger.warning(
                'pytesseract or Pillow is not installed. '
                'Image OCR is unavailable. Install with: pip install pytesseract Pillow'
            )
            return ''

        try:
            image = Image.open(io.BytesIO(file_bytes))

            # Pre-process for better OCR: convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')

            text = pytesseract.image_to_string(image, lang='eng')
            return text
        except Exception as exc:
            logger.warning('OCR extraction failed: %s', exc)
            return ''

    @classmethod
    def _extract_references(cls, text: str, payment_method: str = '') -> List[str]:
        """
        Extract candidate transaction reference numbers from text.

        Uses bank-specific patterns first, then falls back to generic patterns.
        Returns deduplicated list ordered by match priority.
        """
        references = []
        seen = set()

        method_key = payment_method.lower().strip() if payment_method else ''

        # For bank-specific primary patterns (like CBE's FT pattern, Telebirr's digit pattern),
        # use findall directly as these match the full reference
        if method_key in ('cbe', 'cbe_birr'):
            cbe_matches = _CBE_REF_PATTERN.findall(text)
            for ref in cbe_matches:
                ref_upper = ref.upper()
                if ref_upper not in seen:
                    references.append(ref_upper)
                    seen.add(ref_upper)

        if method_key == 'telebirr':
            telebirr_matches = _TELEBIRR_REF_PATTERN.findall(text)
            for ref in telebirr_matches:
                if ref not in seen:
                    # Filter out likely non-reference numbers (dates, phone numbers)
                    if not cls._is_likely_non_reference(ref, text):
                        references.append(ref)
                        seen.add(ref)

        # Try labeled/transaction ID patterns (these have capture groups)
        for pattern in [_TRANSACTION_ID_PATTERN, _LABELED_REF_PATTERN]:
            matches = pattern.findall(text)
            for ref in matches:
                ref_clean = ref.strip().upper()
                if ref_clean and ref_clean not in seen and len(ref_clean) >= 6:
                    references.append(ref_clean)
                    seen.add(ref_clean)

        return references

    @classmethod
    def _is_likely_non_reference(cls, number: str, text: str) -> bool:
        """
        Filter out numeric strings that are likely dates, phone numbers,
        or account numbers rather than transaction references.
        """
        # Phone numbers: Ethiopian numbers start with 09 or +251
        if number.startswith(('09', '251')):
            return True

        # Very long numbers (> 15 digits) are likely account numbers
        if len(number) > 15:
            return True

        # Check if the number appears right after date-like labels
        date_context = re.search(
            rf'(?:date|time|dated?)[\s.:]*{re.escape(number)}',
            text,
            re.IGNORECASE,
        )
        if date_context:
            return True

        return False

    @classmethod
    def _extract_amount(cls, text: str) -> Optional[Decimal]:
        """
        Extract the transaction amount from receipt text.
        Returns the first matching amount, prioritizing labeled amounts.
        """
        for pattern in _AMOUNT_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                try:
                    # Remove commas and parse
                    clean = match.replace(',', '').strip()
                    amount = Decimal(clean)
                    # Sanity check: amount should be positive and reasonable
                    if Decimal('0.01') <= amount <= Decimal('10000000'):
                        return amount
                except (InvalidOperation, ValueError):
                    continue

        return None

    @classmethod
    def _assess_confidence(
        cls,
        references: List[str],
        amount: Optional[Decimal],
        payment_method: str,
    ) -> str:
        """
        Assess extraction confidence level.

        - high: Found a bank-specific reference pattern AND amount
        - medium: Found a bank-specific reference pattern OR a labeled reference
        - low: Found some generic reference-like strings
        - none: Found nothing useful
        """
        if not references:
            return 'none'

        method_key = payment_method.lower().strip() if payment_method else ''
        has_bank_specific = False

        # Check if any reference matches bank-specific pattern
        if method_key in ('cbe', 'cbe_birr'):
            has_bank_specific = any(
                _CBE_REF_PATTERN.fullmatch(ref) for ref in references
            )
        elif method_key == 'telebirr':
            has_bank_specific = any(
                _TELEBIRR_REF_PATTERN.fullmatch(ref) for ref in references
            )

        if has_bank_specific and amount is not None:
            return 'high'
        elif has_bank_specific or (len(references) >= 1 and amount is not None):
            return 'medium'
        elif references:
            return 'low'

        return 'none'

    @classmethod
    def cross_validate(
        cls,
        user_reference: str,
        receipt_data: ReceiptData,
        expected_amount: Optional[Decimal] = None,
    ) -> dict:
        """
        Cross-validate user-provided reference against extracted receipt data.

        Returns a dict with:
        - reference_match: bool — user reference found in extracted references
        - amount_match: bool or None — amount matches if both available
        - is_suspicious: bool — flagged for staff review
        - reason: str — explanation
        """
        user_ref = user_reference.strip().upper()
        result = {
            'reference_match': False,
            'amount_match': None,
            'is_suspicious': False,
            'reason': '',
        }

        # If extraction failed or no text extracted
        if receipt_data.confidence == 'none' and receipt_data.error:
            result['reason'] = f'Receipt could not be parsed: {receipt_data.error}'
            # Don't flag as suspicious if we simply can't read the file
            return result

        if not receipt_data.extracted_references:
            result['reason'] = (
                'No transaction references could be extracted from the receipt. '
                'Staff will verify manually.'
            )
            return result

        # Check reference match
        extracted_upper = [ref.upper() for ref in receipt_data.extracted_references]

        # Exact match
        if user_ref in extracted_upper:
            result['reference_match'] = True
        else:
            # Partial / substring match (user may have typed part of the reference)
            for ext_ref in extracted_upper:
                if user_ref in ext_ref or ext_ref in user_ref:
                    result['reference_match'] = True
                    break

        if not result['reference_match']:
            result['is_suspicious'] = True
            result['reason'] = (
                f'User-provided reference "{user_reference}" was NOT found in the uploaded receipt. '
                f'Receipt contains: {", ".join(receipt_data.extracted_references[:5])}. '
                'This payment is flagged for manual staff review.'
            )

        # Check amount match
        if expected_amount and receipt_data.extracted_amount:
            if receipt_data.extracted_amount >= expected_amount:
                result['amount_match'] = True
            else:
                result['amount_match'] = False
                amount_warning = (
                    f'Receipt amount ({receipt_data.extracted_amount} ETB) is less than '
                    f'submitted amount ({expected_amount} ETB).'
                )
                if result['reason']:
                    result['reason'] += f' Additionally: {amount_warning}'
                else:
                    result['reason'] = amount_warning
                result['is_suspicious'] = True

        if result['reference_match'] and not result['is_suspicious']:
            result['reason'] = 'Reference found in receipt. Verification passed.'

        return result
