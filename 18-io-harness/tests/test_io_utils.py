"""
Unit tests for harness.io_utils.

Run: python3 -m unittest tests.test_io_utils   (from the 18-io-harness/ directory)
 or: python3 -m unittest discover tests
"""
import io
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path

# Make `harness` importable regardless of how/where this file is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import io_utils


@contextmanager
def _stdin(text: str):
    """Temporarily replace sys.stdin with an in-memory stream, then restore it."""
    original = sys.stdin
    sys.stdin = io.StringIO(text)
    try:
        yield
    finally:
        sys.stdin = original


class StripLineEndingTests(unittest.TestCase):
    def test_strips_trailing_newline(self) -> None:
        self.assertEqual(io_utils.strip_line_ending("abc\n"), "abc")

    def test_no_trailing_newline_unchanged(self) -> None:
        self.assertEqual(io_utils.strip_line_ending("abc"), "abc")

    def test_empty_string(self) -> None:
        self.assertEqual(io_utils.strip_line_ending(""), "")

    def test_only_newline(self) -> None:
        self.assertEqual(io_utils.strip_line_ending("\n"), "")


class ReadStdinAllTests(unittest.TestCase):
    def test_reads_full_text(self) -> None:
        with _stdin("a\nb\nc\n"):
            self.assertEqual(io_utils.read_stdin_all(), "a\nb\nc\n")

    def test_empty_stdin(self) -> None:
        with _stdin(""):
            self.assertEqual(io_utils.read_stdin_all(), "")

    def test_unicode(self) -> None:
        with _stdin("café\n日本語\n"):
            self.assertEqual(io_utils.read_stdin_all(), "café\n日本語\n")


class IterStdinLinesTests(unittest.TestCase):
    def _lines(self, text: str, **kwargs):
        with _stdin(text):
            return list(io_utils.iter_stdin_lines(**kwargs))

    def test_basic_lines(self) -> None:
        self.assertEqual(self._lines("a\nb\nc\n"), ["a", "b", "c"])

    def test_no_trailing_newline_on_last_line(self) -> None:
        self.assertEqual(self._lines("a\nb"), ["a", "b"])

    def test_blank_lines_preserved_as_empty_strings(self) -> None:
        self.assertEqual(self._lines("a\n\nb\n"), ["a", "", "b"])

    def test_crlf_normalized(self) -> None:
        self.assertEqual(self._lines("a\r\nb\r\nc\r\n"), ["a", "b", "c"])

    def test_empty_input_yields_no_lines(self) -> None:
        self.assertEqual(self._lines(""), [])

    def test_unicode(self) -> None:
        self.assertEqual(self._lines("héllo\nworld\n"), ["héllo", "world"])

    def test_skip_blank_option(self) -> None:
        self.assertEqual(self._lines("a\n\nb\n\n", skip_blank=True), ["a", "b"])

    def test_strip_newline_false_keeps_terminator(self) -> None:
        self.assertEqual(self._lines("a\nb\n", strip_newline=False), ["a\n", "b\n"])

    def test_is_a_generator_not_a_list(self) -> None:
        with _stdin("a\nb\n"):
            result = io_utils.iter_stdin_lines()
            self.assertTrue(hasattr(result, "__next__"))


class FileHelperTests(unittest.TestCase):
    def _temp_file(self, content: str, newline: str = "") -> str:
        # newline="" disables translation on write, so the bytes on disk are exactly
        # what we asked for (lets us test CRLF handling deterministically on read).
        fd, path = tempfile.mkstemp()
        with open(fd, "w", encoding="utf-8", newline=newline) as f:
            f.write(content)
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        return path

    def test_read_file_whole(self) -> None:
        path = self._temp_file("a\nb\nc\n")
        self.assertEqual(io_utils.read_file(path), "a\nb\nc\n")

    def test_read_file_empty(self) -> None:
        path = self._temp_file("")
        self.assertEqual(io_utils.read_file(path), "")

    def test_iter_file_lines_basic(self) -> None:
        path = self._temp_file("a\nb\nc\n")
        self.assertEqual(list(io_utils.iter_file_lines(path)), ["a", "b", "c"])

    def test_iter_file_lines_crlf(self) -> None:
        path = self._temp_file("a\r\nb\r\nc\r\n")
        self.assertEqual(list(io_utils.iter_file_lines(path)), ["a", "b", "c"])

    def test_iter_file_lines_no_trailing_newline(self) -> None:
        path = self._temp_file("a\nb\nc")
        self.assertEqual(list(io_utils.iter_file_lines(path)), ["a", "b", "c"])

    def test_iter_file_lines_blank_lines_preserved(self) -> None:
        path = self._temp_file("a\n\nb\n")
        self.assertEqual(list(io_utils.iter_file_lines(path)), ["a", "", "b"])

    def test_iter_file_lines_empty_file(self) -> None:
        path = self._temp_file("")
        self.assertEqual(list(io_utils.iter_file_lines(path)), [])

    def test_iter_file_lines_unicode(self) -> None:
        path = self._temp_file("café\n日本語\n")
        self.assertEqual(list(io_utils.iter_file_lines(path)), ["café", "日本語"])

    def test_write_file_then_read_back(self) -> None:
        fd, path = tempfile.mkstemp()
        Path(path).unlink()  # just reserving a filename; write_file will recreate it
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        io_utils.write_file(path, ["x", "y", "z"])
        self.assertEqual(io_utils.read_file(path), "x\ny\nz\n")

    def test_write_file_empty_iterable(self) -> None:
        fd, path = tempfile.mkstemp()
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        io_utils.write_file(path, [])
        self.assertEqual(io_utils.read_file(path), "")


class ResolveInputTests(unittest.TestCase):
    def test_none_falls_back_to_stdin(self) -> None:
        with _stdin("hello\n"):
            with io_utils.resolve_input(None) as stream:
                self.assertIs(stream, sys.stdin)
                self.assertEqual(stream.read(), "hello\n")

    def test_dash_falls_back_to_stdin(self) -> None:
        with _stdin("hello\n"):
            with io_utils.resolve_input("-") as stream:
                self.assertIs(stream, sys.stdin)

    def test_reads_given_path(self) -> None:
        fd, path = tempfile.mkstemp()
        with open(fd, "w", encoding="utf-8") as f:
            f.write("from a file\n")
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        with io_utils.resolve_input(path) as stream:
            self.assertEqual(stream.read(), "from a file\n")

    def test_closes_a_file_it_opened(self) -> None:
        fd, path = tempfile.mkstemp()
        with open(fd, "w", encoding="utf-8") as f:
            f.write("x\n")
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        with io_utils.resolve_input(path) as stream:
            pass
        self.assertTrue(stream.closed)

    def test_does_not_close_stdin(self) -> None:
        with _stdin("x\n"):
            with io_utils.resolve_input(None) as stream:
                pass
            self.assertFalse(stream.closed)

    def test_same_call_shape_both_channels(self) -> None:
        # The whole point of resolve_input: identical iteration code for both channels.
        def read_all(path):
            with io_utils.resolve_input(path) as stream:
                return [strip for strip in (l.rstrip("\n") for l in stream)]

        fd, path = tempfile.mkstemp()
        with open(fd, "w", encoding="utf-8") as f:
            f.write("a\nb\n")
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))

        with _stdin("a\nb\n"):
            from_stdin = read_all(None)
        from_file = read_all(path)
        self.assertEqual(from_stdin, from_file)


class SplitFieldsTests(unittest.TestCase):
    def test_whitespace_default(self) -> None:
        self.assertEqual(io_utils.split_fields("a  b\tc"), ["a", "b", "c"])

    def test_custom_delimiter(self) -> None:
        self.assertEqual(io_utils.split_fields("a,b,c", delimiter=","), ["a", "b", "c"])

    def test_strip_fields_option(self) -> None:
        self.assertEqual(
            io_utils.split_fields("a, b , c", delimiter=",", strip_fields=True),
            ["a", "b", "c"],
        )

    def test_strip_fields_off_keeps_whitespace(self) -> None:
        self.assertEqual(io_utils.split_fields("a, b", delimiter=","), ["a", " b"])

    def test_empty_line(self) -> None:
        self.assertEqual(io_utils.split_fields(""), [])

    def test_unicode(self) -> None:
        self.assertEqual(io_utils.split_fields("café 日本語"), ["café", "日本語"])


class ParseCommandTests(unittest.TestCase):
    def test_command_with_args(self) -> None:
        self.assertEqual(io_utils.parse_command("SET x 5"), ("SET", ["x", "5"]))

    def test_command_no_args(self) -> None:
        self.assertEqual(io_utils.parse_command("COMMIT"), ("COMMIT", []))

    def test_empty_line(self) -> None:
        self.assertEqual(io_utils.parse_command(""), ("", []))

    def test_blank_line(self) -> None:
        self.assertEqual(io_utils.parse_command("   "), ("", []))

    def test_extra_whitespace_between_tokens(self) -> None:
        self.assertEqual(io_utils.parse_command("  GET   key1  "), ("GET", ["key1"]))

    def test_case_preserved(self) -> None:
        self.assertEqual(io_utils.parse_command("get key1"), ("get", ["key1"]))


class WriteStdoutTests(unittest.TestCase):
    def test_writes_each_line_with_newline(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            io_utils.write_stdout(["a", "b"])
        self.assertEqual(buf.getvalue(), "a\nb\n")

    def test_empty_iterable_writes_nothing(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            io_utils.write_stdout([])
        self.assertEqual(buf.getvalue(), "")

    def test_generator_input(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            io_utils.write_stdout(str(i) for i in range(3))
        self.assertEqual(buf.getvalue(), "0\n1\n2\n")

    def test_respects_redirect_stdout_at_call_time(self) -> None:
        # Regression guard: write_stdout must NOT bind sys.stdout as a default-arg
        # value at import time, or this would silently write to the real stdout.
        buf = io.StringIO()
        with redirect_stdout(buf):
            io_utils.write_stdout(["x"])
        self.assertEqual(buf.getvalue(), "x\n")

    def test_explicit_stream_argument(self) -> None:
        buf = io.StringIO()
        io_utils.write_stdout(["a", "b"], stream=buf)
        self.assertEqual(buf.getvalue(), "a\nb\n")

    def test_unicode(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            io_utils.write_stdout(["café"])
        self.assertEqual(buf.getvalue(), "café\n")


if __name__ == "__main__":
    unittest.main()
