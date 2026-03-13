import pytest
from unittest.mock import patch, AsyncMock
import sys
from io import StringIO

from shell_analyzer.main import main, VALID_STYLES


@pytest.fixture
def mock_valid_styles():
    with patch('shell_analyzer.main.VALID_STYLES', VALID_STYLES):
        yield


def test_main_default_style(mock_valid_styles):
    """main() with default style ('compact') calls run() and prints result."""
    mock_result = "Mocked Result"

    with patch('sys.argv', ['main.py', 'echo', 'hello']):
        with patch('shell_analyzer.main.run', new_callable=AsyncMock, return_value=mock_result) as mock_run:
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                mock_run.assert_called_once_with("echo hello", "compact")
                assert fake_out.getvalue().strip() == mock_result


def test_main_custom_style_detailed(mock_valid_styles):
    """main() parses --style detailed correctly."""
    mock_result = "Detailed Mocked Result"

    # Use '--' to stop argparse treating '-la' as a flag
    with patch('sys.argv', ['main.py', '--style', 'detailed', '--', 'ls', '-la']):
        with patch('shell_analyzer.main.run', new_callable=AsyncMock, return_value=mock_result) as mock_run:
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                mock_run.assert_called_once_with("ls -la", "detailed")
                assert fake_out.getvalue().strip() == mock_result


def test_main_custom_style_minimal_short_flag(mock_valid_styles):
    """main() with -s minimal short flag."""
    mock_result = "/home/user"

    with patch('sys.argv', ['main.py', '-s', 'minimal', 'pwd']):
        with patch('shell_analyzer.main.run', new_callable=AsyncMock, return_value=mock_result) as mock_run:
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                mock_run.assert_called_once_with("pwd", "minimal")
                assert fake_out.getvalue().strip() == mock_result


def test_main_invalid_style(mock_valid_styles):
    """main() exits on invalid style."""
    with patch('sys.argv', ['main.py', '--style', 'invalid_style', 'ls']):
        with pytest.raises(SystemExit):
            main()


def test_main_command_joining(mock_valid_styles):
    """Command args are joined into a single string."""
    # Use '--' to stop argparse treating '-m' as a flag
    with patch('sys.argv', ['main.py', '--', 'git', 'commit', '-m', "'Initial commit'"]):
        with patch('shell_analyzer.main.run', new_callable=AsyncMock) as mock_run:
            main()
            assert mock_run.call_args[0][0] == "git commit -m 'Initial commit'"


def test_main_empty_command_handling(mock_valid_styles):
    """main() exits when no command is provided (nargs='+')."""
    with patch('sys.argv', ['main.py']):
        with pytest.raises(SystemExit):
            main()


def test_main_prints_output(mock_valid_styles):
    """main() prints the result returned by run() to stdout."""
    mock_result = "Test Output 123"

    with patch('sys.argv', ['main.py', 'test']):
        with patch('shell_analyzer.main.run', new_callable=AsyncMock, return_value=mock_result):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                assert fake_out.getvalue() == f"{mock_result}\n"
