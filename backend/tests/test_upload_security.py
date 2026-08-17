"""Tests for upload validation and filename safety."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi import HTTPException, UploadFile

from app.routers.resumes import (
    MAX_RESUME_BYTES,
    read_upload_within_limit,
    sanitize_filename,
)


class FakeUpload:
    """Minimal stand-in exposing the .file.read(n) interface we rely on."""

    def __init__(self, data: bytes, filename: str = "cv.pdf"):
        import io
        self.file = io.BytesIO(data)
        self.filename = filename


def read(data: bytes):
    return read_upload_within_limit(FakeUpload(data))


class TestSizeLimit:
    def test_accepts_a_file_at_the_limit(self):
        payload = b"%PDF-" + b"x" * (MAX_RESUME_BYTES - 5)
        assert len(read(payload)) == MAX_RESUME_BYTES

    def test_rejects_oversized_file_with_413(self):
        payload = b"%PDF-" + b"x" * MAX_RESUME_BYTES
        with pytest.raises(HTTPException) as exc:
            read(payload)
        assert exc.value.status_code == 413
        assert "5MB" in exc.value.detail

    def test_rejects_empty_file(self):
        with pytest.raises(HTTPException) as exc:
            read(b"")
        assert exc.value.status_code == 400


class TestContentValidation:
    def test_accepts_real_pdf_magic_bytes(self):
        assert read(b"%PDF-1.7\nstuff").startswith(b"%PDF-")

    def test_rejects_non_pdf_content(self):
        """A renamed .docx or an image must not get through."""
        with pytest.raises(HTTPException) as exc:
            read(b"PK\x03\x04 this is a zip/docx")
        assert exc.value.status_code == 400
        assert "not a valid PDF" in exc.value.detail

    def test_rejects_html_disguised_as_pdf(self):
        with pytest.raises(HTTPException):
            read(b"<html><script>alert(1)</script></html>")


class TestFilenameSanitisation:
    @pytest.mark.parametrize("hostile", [
        "../../../etc/passwd",
        "..\\..\\windows\\system32\\config",
        "/absolute/path/cv.pdf",
        "C:\\Users\\someone\\cv.pdf",
    ])
    def test_directory_components_are_stripped(self, hostile):
        out = sanitize_filename(hostile)
        assert "/" not in out and "\\" not in out
        assert not out.startswith("..")

    def test_control_characters_removed(self):
        assert "\x00" not in sanitize_filename("cv\x00.pdf")
        assert "\n" not in sanitize_filename("cv\n.pdf")

    def test_reserved_characters_removed(self):
        out = sanitize_filename('cv<>:"|?*.pdf')
        assert not any(c in out for c in '<>:"|?*')

    def test_absurd_length_is_bounded(self):
        out = sanitize_filename("a" * 5000 + ".pdf")
        assert len(out) <= 120
        assert out.endswith(".pdf")

    def test_empty_and_none_get_a_default(self):
        assert sanitize_filename(None) == "resume.pdf"
        assert sanitize_filename("") == "resume.pdf"
        assert sanitize_filename("...") == "resume.pdf"

    def test_ordinary_name_is_preserved(self):
        assert sanitize_filename("Akash_CV_2026.pdf") == "Akash_CV_2026.pdf"
