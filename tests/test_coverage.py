"""Tests for coverage.py module."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from test_writer.coverage import CoverageResult, TestResult, run_coverage, get_file_coverage, run_tests, find_test_file, generate_test_filename


class TestRunCoverage:
    """Test the run_coverage function."""

    def test_run_coverage_success(self):
        """Test successful coverage run with valid JSON report."""
        mock_report = {
            "totals": {
                "percent_covered": 85.5,
                "num_statements": 100,
                "covered_lines": 85
            },
            "files": {
                "test_file.py": {
                    "missing_lines": [10, 20, 30]
                }
            }
        }

        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage(test_dir="tests", source_dir="src")
            
            assert result.percentage == 85.5
            assert result.total_lines == 100
            assert result.covered_lines == 85
            assert result.missing_lines == {"test_file.py": [10, 20, 30]}
            assert result.raw_report == mock_report

    def test_run_coverage_with_target_file(self):
        """Test coverage run with specific target file."""
        mock_report = {"totals": {}, "files": {}}
        
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            run_coverage(test_dir="tests", source_dir="src", target_file="specific.py")
            
            # Verify the command includes the target file
            call_args = mock_run.call_args[0][0]
            assert "--cov=specific.py" in call_args

    def test_run_coverage_no_json_file(self):
        """Test handling when coverage JSON file is not found."""
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', side_effect=FileNotFoundError):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage()
            
            assert result.percentage == 0.0
            assert result.total_lines == 0
            assert result.covered_lines == 0
            assert result.missing_lines == {}
            assert result.raw_report == {}

    def test_run_coverage_invalid_json(self):
        """Test handling when coverage JSON is invalid."""
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data="invalid json")):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage()
            
            assert result.percentage == 0.0
            assert result.total_lines == 0
            assert result.covered_lines == 0
            assert result.missing_lines == {}
            assert result.raw_report == {}

    def test_run_coverage_empty_report(self):
        """Test handling of empty coverage report."""
        mock_report = {}
        
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage()
            
            assert result.percentage == 0.0
            assert result.total_lines == 0
            assert result.covered_lines == 0
            assert result.missing_lines == {}
            assert result.raw_report == {}

    def test_run_coverage_missing_totals(self):
        """Test handling when totals key is missing from report."""
        mock_report = {
            "files": {
                "test_file.py": {
                    "missing_lines": [1, 2]
                }
            }
        }
        
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage()
            
            assert result.percentage == 0.0
            assert result.total_lines == 0
            assert result.covered_lines == 0

    def test_run_coverage_non_integer_missing_lines(self):
        """Test handling when missing_lines contains non-integer values."""
        mock_report = {
            "totals": {"percent_covered": 50.0, "num_statements": 10, "covered_lines": 5},
            "files": {
                "test_file.py": {
                    "missing_lines": ["1", 2, None]
                }
            }
        }
        
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage()
            
            assert result.missing_lines["test_file.py"] == ["1", 2, None]

    def test_run_coverage_empty_string_parameters(self):
        """Test handling empty string parameters."""
        mock_report = {"totals": {}, "files": {}}
        
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage(test_dir="", source_dir="", target_file="")
            
            assert isinstance(result, CoverageResult)

    def test_run_coverage_100_percent(self):
        """Test handling 100% coverage edge case."""
        mock_report = {
            "totals": {
                "percent_covered": 100.0,
                "num_statements": 50,
                "covered_lines": 50
            },
            "files": {}
        }
        
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage()
            
            assert result.percentage == 100.0
            assert result.total_lines == 50
            assert result.covered_lines == 50
            assert result.missing_lines == {}

    def test_run_coverage_negative_percentage(self):
        """Test handling negative coverage percentage in report."""
        mock_report = {
            "totals": {
                "percent_covered": -10.0,
                "num_statements": 10,
                "covered_lines": 0
            },
            "files": {}
        }
        
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            result = run_coverage()
            
            assert result.percentage == -10.0

    def test_run_coverage_pythonpath_handling(self):
        """Test that PYTHONPATH is correctly set in environment."""
        mock_report = {"totals": {}, "files": {}}
        
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value = MagicMock()
            
            # Save original PYTHONPATH
            original_pythonpath = os.environ.get("PYTHONPATH")
            try:
                # Set a test value
                os.environ["TEST_VAR"] = "test_value"
                
                run_coverage(source_dir="custom_source")
                
                # Check that subprocess was called with modified environment
                env = mock_run.call_args[1]["env"]
                assert "custom_source" in env["PYTHONPATH"]
                assert env["TEST_VAR"] == "test_value"
            finally:
                # Restore original state
                if original_pythonpath is not None:
                    os.environ["PYTHONPATH"] = original_pythonpath
                elif "PYTHONPATH" in os.environ:
                    del os.environ["PYTHONPATH"]
                if "TEST_VAR" in os.environ:
                    del os.environ["TEST_VAR"]


class TestGetFileCoverage:
    """Test the get_file_coverage function."""

    def test_get_file_coverage_found(self):
        """Test getting coverage for a file that exists in report."""
        report = {
            "files": {
                "test_file.py": {
                    "summary": {"percent_covered": 75.0},
                    "missing_lines": [5, 10, 15]
                }
            }
        }
        
        pct, missing = get_file_coverage(report, "test_file.py")
        
        assert pct == 75.0
        assert missing == [5, 10, 15]

    def test_get_file_coverage_not_found(self):
        """Test getting coverage for a file not in report."""
        report = {"files": {}}
        
        pct, missing = get_file_coverage(report, "nonexistent.py")
        
        assert pct == 0.0
        assert missing == []

    def test_get_file_coverage_path_normalization(self):
        """Test that paths are properly normalized."""
        report = {
            "files": {
                "./test_file.py": {
                    "summary": {"percent_covered": 50.0},
                    "missing_lines": [1, 2]
                }
            }
        }
        
        pct, missing = get_file_coverage(report, "test_file.py")
        
        assert pct == 50.0
        assert missing == [1, 2]

    def test_get_file_coverage_missing_summary(self):
        """Test handling when summary is missing from file data."""
        report = {
            "files": {
                "test_file.py": {
                    "missing_lines": [1, 2]
                }
            }
        }
        
        pct, missing = get_file_coverage(report, "test_file.py")
        
        assert pct == 0.0
        assert missing == [1, 2]

    def test_get_file_coverage_missing_missing_lines(self):
        """Test handling when missing_lines is missing from file data."""
        report = {
            "files": {
                "test_file.py": {
                    "summary": {"percent_covered": 100.0}
                }
            }
        }
        
        pct, missing = get_file_coverage(report, "test_file.py")
        
        assert pct == 100.0
        assert missing == []

    def test_get_file_coverage_empty_target_file(self):
        """Test handling when target_file is empty string."""
        report = {"files": {}}
        
        pct, missing = get_file_coverage(report, "")
        
        assert pct == 0.0
        assert missing == []

    def test_get_file_coverage_100_percent(self):
        """Test 100% coverage edge case."""
        report = {
            "files": {
                "test_file.py": {
                    "summary": {"percent_covered": 100.0},
                    "missing_lines": []
                }
            }
        }
        
        pct, missing = get_file_coverage(report, "test_file.py")
        
        assert pct == 100.0
        assert missing == []

    def test_get_file_coverage_0_percent(self):
        """Test 0% coverage edge case."""
        report = {
            "files": {
                "test_file.py": {
                    "summary": {"percent_covered": 0.0},
                    "missing_lines": [1, 2, 3, 4, 5]
                }
            }
        }
        
        pct, missing = get_file_coverage(report, "test_file.py")
        
        assert pct == 0.0
        assert missing == [1, 2, 3, 4, 5]


class TestRunTests:
    """Test the run_tests function."""

    def test_run_tests_success(self):
        """Test successful test run."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Tests passed",
                stderr=""
            )
            
            result = run_tests()
            
            assert result.passed is True
            assert result.exit_code == 0
            assert result.output == "Tests passed"
            assert result.error == ""

    def test_run_tests_failure(self):
        """Test failed test run."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="Some output",
                stderr="Test failed"
            )
            
            result = run_tests()
            
            assert result.passed is False
            assert result.exit_code == 1
            assert result.output == "Some output"
            assert result.error == "Test failed"

    def test_run_tests_with_specific_file(self):
        """Test running tests for a specific file."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            run_tests(test_file="specific_test.py")
            
            # Verify the command includes the specific test file
            call_args = mock_run.call_args[0][0]
            assert "specific_test.py" in call_args

    def test_run_tests_empty_string_parameters(self):
        """Test handling empty string parameters."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = run_tests(test_file="", test_dir="", source_dir="")
            
            assert isinstance(result, TestResult)

    def test_run_tests_pythonpath_handling(self):
        """Test that PYTHONPATH is correctly set in environment."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Save original PYTHONPATH
            original_pythonpath = os.environ.get("PYTHONPATH")
            try:
                # Set a test value
                os.environ["TEST_VAR"] = "test_value"
                
                run_tests(source_dir="custom_source")
                
                # Check that subprocess was called with modified environment
                env = mock_run.call_args[1]["env"]
                assert "custom_source" in env["PYTHONPATH"]
                assert env["TEST_VAR"] == "test_value"
            finally:
                # Restore original state
                if original_pythonpath is not None:
                    os.environ["PYTHONPATH"] = original_pythonpath
                elif "PYTHONPATH" in os.environ:
                    del os.environ["PYTHONPATH"]
                if "TEST_VAR" in os.environ:
                    del os.environ["TEST_VAR"]


class TestFindTestFile:
    """Test the find_test_file function."""

    def test_find_test_file_test_prefix_pattern(self):
        """Test finding test file with test_ prefix pattern."""
        with patch('pathlib.Path.exists', return_value=True):
            result = find_test_file("source.py", "tests")
            
            assert result == "tests/test_source.py"

    def test_find_test_file_suffix_pattern(self):
        """Test finding test file with _test suffix pattern."""
        with patch('pathlib.Path.exists') as mock_exists:
            # First pattern fails, second succeeds
            mock_exists.side_effect = [False, True, False]
            
            result = find_test_file("source.py", "tests")
            
            assert result == "tests/source_test.py"

    def test_find_test_file_root_pattern(self):
        """Test finding test file in root directory."""
        with patch('pathlib.Path.exists') as mock_exists:
            # First two patterns fail, third succeeds
            mock_exists.side_effect = [False, False, True]
            
            result = find_test_file("source.py", "tests")
            
            assert result == "test_source.py"

    def test_find_test_file_not_found(self):
        """Test when no test file is found."""
        with patch('pathlib.Path.exists', return_value=False):
            result = find_test_file("nonexistent.py", "tests")
            
            assert result is None

    def test_find_test_file_with_path(self):
        """Test finding test file for source file with path."""
        with patch('pathlib.Path.exists', return_value=True):
            result = find_test_file("src/utils/helper.py", "tests")
            
            assert result == "tests/test_helper.py"

    def test_find_test_file_empty_source_file(self):
        """Test handling when source_file is empty string."""
        with patch('pathlib.Path.exists', return_value=False):
            result = find_test_file("", "tests")
            
            assert result is None

    def test_find_test_file_empty_test_dir(self):
        """Test handling when test_dir is empty string."""
        with patch('pathlib.Path.exists', return_value=True):
            result = find_test_file("source.py", "")
            
            # Should still work with empty test_dir
            assert result is not None

class TestGenerateTestFilename:
    """Test the generate_test_filename function."""

    def test_generate_test_filename_basic(self):
        """Test basic test filename generation."""
        with patch('pathlib.Path.mkdir'):
            result = generate_test_filename("source.py", "tests")
            
            assert result == "tests/test_source.py"

    def test_generate_test_filename_with_path(self):
        """Test test filename generation for source file with path."""
        with patch('pathlib.Path.mkdir'):
            result = generate_test_filename("src/utils/helper.py", "tests")
            
            assert result == "tests/test_helper.py"

    def test_generate_test_filename_creates_directory(self):
        """Test that test directory is created if it doesn't exist."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            generate_test_filename("source.py", "new_tests")
            
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_generate_test_filename_default_test_dir(self):
        """Test test filename generation with default test directory."""
        with patch('pathlib.Path.mkdir'):
            result = generate_test_filename("source.py")
            
            assert result == "tests/test_source.py"

    def test_generate_test_filename_empty_source_file(self):
        """Test handling when source_file is empty string."""
        with patch('pathlib.Path.mkdir'):
            result = generate_test_filename("", "tests")
            
            assert result == "tests/test_.py"

    def test_generate_test_filename_empty_test_dir(self):
        """Test handling when test_dir is empty string."""
        with patch('pathlib.Path.mkdir'):
            result = generate_test_filename("source.py", "")
            
            assert result == "test_source.py"

    def test_generate_test_filename_no_extension(self):
        """Test handling source file without extension."""
        with patch('pathlib.Path.mkdir'):
            result = generate_test_filename("source", "tests")
            
            assert result == "tests/test_source.py"

    def test_generate_test_filename_multiple_extensions(self):
        """Test handling source file with multiple extensions."""
        with patch('pathlib.Path.mkdir'):
            result = generate_test_filename("source.tar.gz", "tests")
            
            assert result == "tests/test_source.tar.py"
