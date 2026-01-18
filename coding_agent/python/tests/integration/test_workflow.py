"""
Integration tests for the Coding Agent.

Tests the full agent workflow with mocked LLM responses.

Test Cases:
- End-to-end file creation
- End-to-end file modification
- Multiple files in one operation
- Nested directory creation
- File deletion via empty content
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from coding_agent.hooks import CodingAgentHooks


class TestEndToEndWorkflow:
    """Tests for the complete agent workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def hooks(self):
        """Create hooks instance for testing."""
        return CodingAgentHooks()
    
    # === Test 1: New file creation - full flow ===
    def test_apply_creates_new_file(self, hooks, temp_dir):
        """Test that apply_changes creates a new file correctly."""
        context = {
            'changes': {
                'content': '''
```python
hello.py
<<<<<<< SEARCH
=======
print("Hello, World!")
>>>>>>> REPLACE
```
'''
            },
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        result = hooks._apply_changes(context)
        
        created_file = Path(temp_dir) / 'hello.py'
        assert created_file.exists()
        assert 'print("Hello, World!")' in created_file.read_text()
    
    # === Test 2: File modification - full flow ===
    def test_apply_modifies_existing_file(self, hooks, temp_dir):
        """Test that apply_changes modifies an existing file correctly."""
        # Create existing file
        existing = Path(temp_dir) / 'app.py'
        existing.write_text('''def main():
    print("old")
    return 0
''')
        
        context = {
            'changes': {
                'content': '''
```python
app.py
<<<<<<< SEARCH
    print("old")
=======
    print("new")
>>>>>>> REPLACE
```
'''
            },
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        result = hooks._apply_changes(context)
        
        content = existing.read_text()
        assert 'print("new")' in content
        assert 'print("old")' not in content
        assert 'def main():' in content  # Other content preserved
    
    # === Test 3: Multiple files in one operation ===
    def test_apply_multiple_files(self, hooks, temp_dir):
        """Test that multiple files can be created/modified in one operation."""
        # Create one existing file
        existing = Path(temp_dir) / 'config.py'
        existing.write_text('DEBUG = True\n')
        
        context = {
            'changes': {
                'content': '''
I'll create two files and modify one.

```python
utils.py
<<<<<<< SEARCH
=======
def helper():
    return "help"
>>>>>>> REPLACE
```

```python
main.py
<<<<<<< SEARCH
=======
from utils import helper
print(helper())
>>>>>>> REPLACE
```

```python
config.py
<<<<<<< SEARCH
DEBUG = True
=======
DEBUG = False
>>>>>>> REPLACE
```
'''
            },
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        result = hooks._apply_changes(context)
        
        # All files should exist with correct content
        utils = Path(temp_dir) / 'utils.py'
        main = Path(temp_dir) / 'main.py'
        config = Path(temp_dir) / 'config.py'
        
        assert utils.exists()
        assert 'def helper():' in utils.read_text()
        
        assert main.exists()
        assert 'from utils import helper' in main.read_text()
        
        assert config.exists()
        assert 'DEBUG = False' in config.read_text()
        
        # Should have 3 operations applied
        assert len(result.get('applied_changes', [])) == 3
    
    # === Test 4: Nested directory creation ===
    def test_apply_creates_nested_directories(self, hooks, temp_dir):
        """Test that deeply nested directories are created as needed."""
        context = {
            'changes': {
                'content': '''
```python
src/components/utils/validators/email.py
<<<<<<< SEARCH
=======
import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))
>>>>>>> REPLACE
```
'''
            },
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        result = hooks._apply_changes(context)
        
        created = Path(temp_dir) / 'src/components/utils/validators/email.py'
        assert created.exists()
        assert 'validate_email' in created.read_text()
        
        # All parent directories should exist
        assert (Path(temp_dir) / 'src').is_dir()
        assert (Path(temp_dir) / 'src/components').is_dir()
        assert (Path(temp_dir) / 'src/components/utils').is_dir()
        assert (Path(temp_dir) / 'src/components/utils/validators').is_dir()
    
    # === Test 5: File deletion via empty content ===
    def test_apply_deletes_file_when_empty(self, hooks, temp_dir):
        """Test that files are deleted when content becomes empty."""
        # Create a file to delete
        to_delete = Path(temp_dir) / 'deprecated.py'
        to_delete.write_text('old_code = True\n')
        
        # SEARCH content must match file exactly
        changes_text = '''```python
deprecated.py
<<<<<<< SEARCH
old_code = True
=======

>>>>>>> REPLACE
```'''
        
        context = {
            'changes': {'content': changes_text},
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        result = hooks._apply_changes(context)
        
        # File should be deleted
        assert not to_delete.exists()
        assert any('deleted' in s.lower() for s in result.get('applied_changes', []))


class TestFileOperations:
    """Tests for file-level operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def hooks(self):
        """Create hooks instance for testing."""
        return CodingAgentHooks()
    
    def test_partial_file_modification(self, hooks, temp_dir):
        """Test that only the matched part of a file is modified."""
        existing = Path(temp_dir) / 'module.py'
        existing.write_text('''# Header comment

def function_a():
    return 1

def function_b():
    return 2

# Footer comment
''')
        
        context = {
            'changes': '''
```python
module.py
<<<<<<< SEARCH
def function_a():
    return 1
=======
def function_a():
    return 100
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        content = existing.read_text()
        assert 'return 100' in content  # Modified
        assert 'return 2' in content    # Unchanged
        assert '# Header comment' in content  # Unchanged
        assert '# Footer comment' in content  # Unchanged


class TestSecurityBoundaries:
    """Tests for security and safety checks."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def hooks(self):
        """Create hooks instance for testing."""
        return CodingAgentHooks()
    
    def test_cannot_escape_working_directory(self, hooks, temp_dir):
        """Test that files cannot be created outside working directory."""
        subdir = Path(temp_dir) / 'project'
        subdir.mkdir()
        
        context = {
            'changes': '''
```python
../../escape.py
<<<<<<< SEARCH
=======
malicious
>>>>>>> REPLACE
```
''',
            'working_dir': str(subdir),
            'user_cwd': str(subdir),
        }
        
        hooks._apply_changes(context)
        
        # File should NOT exist in parent
        escape_file = Path(temp_dir) / 'escape.py'
        assert not escape_file.exists()
        
        # Should have an error recorded
        assert len(context.get('apply_errors', [])) > 0

