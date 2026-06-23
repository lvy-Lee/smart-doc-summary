import pytest
from utils import truncate_text, is_valid_url
from consts import MAX_TEXT_LENGTH


class TestTruncateText:
    def test_short_text_unchanged(self):
        text = "hello world"
        assert truncate_text(text) == text

    def test_exact_limit(self):
        text = "a" * MAX_TEXT_LENGTH
        result = truncate_text(text)
        assert result == text
        assert len(result) == MAX_TEXT_LENGTH

    def test_truncates_when_over_limit(self):
        text = "a" * (MAX_TEXT_LENGTH + 100)
        result = truncate_text(text)
        assert len(result) == MAX_TEXT_LENGTH
        assert result == "a" * MAX_TEXT_LENGTH

    def test_custom_limit(self):
        text = "hello world"
        assert truncate_text(text, limit=5) == "hello"

    def test_empty_string(self):
        assert truncate_text("") == ""

    def test_zero_limit(self):
        assert truncate_text("anything", limit=0) == ""


class TestIsValidUrl:
    def test_valid_https(self):
        assert is_valid_url("https://example.com") is True

    def test_valid_http(self):
        assert is_valid_url("http://example.com") is True

    def test_valid_with_path(self):
        assert is_valid_url("https://example.com/path/to/page") is True

    def test_valid_with_query(self):
        assert is_valid_url("https://example.com?q=hello&lang=zh") is True

    def test_no_protocol(self):
        assert is_valid_url("example.com") is False

    def test_no_dot(self):
        assert is_valid_url("https://localhost") is False

    def test_ftp_rejected(self):
        assert is_valid_url("ftp://example.com") is False

    def test_empty_string(self):
        assert is_valid_url("") is False

    def test_only_protocol(self):
        assert is_valid_url("https://") is False


class TestReadFileContent:
    def test_txt_utf8(self, mocker):
        mock_file = mocker.MagicMock()
        mock_file.name = "test.txt"
        mock_file.read.return_value = "你好世界".encode("utf-8")
        from utils import read_file_content
        assert read_file_content(mock_file) == "你好世界"

    def test_txt_utf8_decode_error_fallback_gbk(self, mocker):
        mock_file = mocker.MagicMock()
        mock_file.name = "test.txt"
        mock_file.read.side_effect = [UnicodeDecodeError("utf-8", b"", 0, 0, ""), "gbk文本".encode("gbk")]
        from utils import read_file_content
        assert read_file_content(mock_file) == "gbk文本"

    def test_unsupported_extension(self, mocker):
        mock_file = mocker.MagicMock()
        mock_file.name = "image.png"
        from utils import read_file_content
        assert read_file_content(mock_file) == ""

    def test_pdf(self, mocker):
        mock_file = mocker.MagicMock()
        mock_file.name = "doc.pdf"
        mock_fitz_open = mocker.patch("fitz.open")
        mock_doc = mock_fitz_open.return_value
        mock_page = mocker.MagicMock()
        mock_page.get_text.return_value = "pdf content"
        mock_doc.__iter__.return_value = [mock_page]
        from utils import read_file_content
        result = read_file_content(mock_file)
        assert "pdf content" in result
        mock_doc.close.assert_called_once()

    def test_docx(self, mocker):
        mock_file = mocker.MagicMock()
        mock_file.name = "report.docx"
        mock_docx_document = mocker.patch("docx.Document")
        mock_doc = mock_docx_document.return_value
        para1 = mocker.MagicMock()
        para1.text = "段落1"
        para2 = mocker.MagicMock()
        para2.text = "段落2"
        mock_doc.paragraphs = [para1, para2]
        from utils import read_file_content
        result = read_file_content(mock_file)
        assert result == "段落1\n段落2"


class TestFetchUrlContent:
    def test_successful_fetch(self, mocker):
        mock_get = mocker.patch("requests.get")
        mock_resp = mock_get.return_value
        mock_resp.apparent_encoding = "utf-8"
        mock_resp.text = "<html><body><p>hello</p><p>world</p></body></html>"
        from utils import fetch_url_content
        result = fetch_url_content("https://example.com")
        assert "hello" in result
        assert "world" in result
        mock_get.assert_called_once_with(
            "https://example.com",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )

    def test_strips_noise_tags(self, mocker):
        mock_get = mocker.patch("requests.get")
        mock_resp = mock_get.return_value
        mock_resp.apparent_encoding = "utf-8"
        mock_resp.text = "<html><body><script>alert(1)</script><p>content</p><nav>nav</nav></body></html>"
        from utils import fetch_url_content
        result = fetch_url_content("https://example.com")
        assert "content" in result
        assert "alert" not in result
        assert "nav" not in result

    def test_empty_response(self, mocker):
        mock_get = mocker.patch("requests.get")
        mock_resp = mock_get.return_value
        mock_resp.apparent_encoding = "utf-8"
        mock_resp.text = ""
        from utils import fetch_url_content
        assert fetch_url_content("https://example.com") == ""
