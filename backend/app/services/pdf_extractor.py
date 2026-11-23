import asyncio
import io
import pymupdf as fitz


class PDFExtractionError(Exception):
    pass


class PDFExtractor:
    MAX_PAGES = 30

    def extract_text(self, content: bytes) -> str:
        """
        Extract text from PDF byte stream page-by-page using PyMuPDF.
        Raises PDFExtractionError if the document is malformed, oversized, or empty.
        """
        if not content:
            raise PDFExtractionError("PDF file content is empty")

        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            raise PDFExtractionError(f"Failed to open PDF document: {str(e)}")

        try:
            if doc.page_count == 0:
                raise PDFExtractionError("PDF document has 0 pages")

            if doc.page_count > self.MAX_PAGES:
                raise PDFExtractionError(
                    f"PDF document exceeds maximum page limit of {self.MAX_PAGES} pages (found {doc.page_count})"
                )

            extracted_pages = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text("text") or ""
                cleaned = page_text.strip()
                if cleaned:
                    extracted_pages.append(f"--- Page {page_num + 1} ---\n{cleaned}")

            full_text = "\n\n".join(extracted_pages).strip()

            if not full_text:
                raise PDFExtractionError(
                    "No extractable text found in PDF (document may be scanned or image-only without OCR)"
                )

            return full_text
        finally:
            doc.close()

    async def extract_text_async(self, content: bytes) -> str:
        """Non-blocking async wrapper for PyMuPDF text extraction."""
        return await asyncio.to_thread(self.extract_text, content)


pdf_extractor = PDFExtractor()
