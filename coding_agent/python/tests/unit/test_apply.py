"""
Unit tests for the apply changes functionality.

Tests the _apply_changes method in hooks.py.

Test Cases:
- Create new file in working dir
- Create file in nested directory
- Modify existing file - exact match
- Modify - SEARCH not found
- Modify - multiple matches (ambiguous)
- Delete file (empty result)
- Path traversal blocked (../ attack)
- Absolute path blocked
- Working dir constraint enforced
- Content extraction from dict wrapper
- Legacy JSON format fallback
- Multiple operations in one call
"""

import pytest
import tempfile
from pathlib import Path
from coding_agent.hooks import CodingAgentHooks


class TestApplyChanges:
    """Tests for the _apply_changes method."""
    
    @pytest.fixture
    def hooks(self):
        """Create hooks instance for testing."""
        return CodingAgentHooks()
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    # === Test 1: Create new file in working dir ===
    def test_create_new_file_in_working_dir(self, hooks, temp_dir):
        """Test that a new file is created in the working directory."""
        context = {
            'changes': '''
```python
hello.py
<<<<<<< SEARCH
=======
print("Hello!")
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        created = Path(temp_dir) / 'hello.py'
        assert created.exists()
        assert 'print("Hello!")' in created.read_text()
    
    # === Test 2: Create file in nested directory ===
    def test_create_file_in_nested_directory(self, hooks, temp_dir):
        """Test that nested directories are created as needed."""
        context = {
            'changes': '''
```python
src/utils/helpers/math.py
<<<<<<< SEARCH
=======
def add(a, b):
    return a + b
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        created = Path(temp_dir) / 'src/utils/helpers/math.py'
        assert created.exists()
        assert 'def add(a, b):' in created.read_text()
    
    # === Test 3: Modify existing file - exact match ===
    def test_modify_existing_file_exact_match(self, hooks, temp_dir):
        """Test modifying a file when SEARCH matches exactly once."""
        # Create existing file
        existing = Path(temp_dir) / 'config.py'
        existing.write_text('DEBUG = True\nVERBOSE = False\n')
        
        context = {
            'changes': '''
```python
config.py
<<<<<<< SEARCH
DEBUG = True
=======
DEBUG = False
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        content = existing.read_text()
        assert 'DEBUG = False' in content
        assert 'VERBOSE = False' in content
    
    # === Test 4: Modify - SEARCH not found ===
    def test_modify_search_not_found(self, hooks, temp_dir):
        """Test that missing SEARCH content is recorded as an error."""
        existing = Path(temp_dir) / 'app.py'
        existing.write_text('x = 1\n')
        
        context = {
            'changes': '''
```python
app.py
<<<<<<< SEARCH
nonexistent content
=======
replacement
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        # File should be unchanged
        assert existing.read_text() == 'x = 1\n'
        assert len(context.get('apply_errors', [])) > 0
        assert 'not found' in context['apply_errors'][0].lower()
    
    # === Test 5: Modify - multiple matches (ambiguous) ===
    def test_modify_multiple_matches_ambiguous(self, hooks, temp_dir):
        """Test that multiple matches are rejected as ambiguous."""
        existing = Path(temp_dir) / 'code.py'
        existing.write_text('x = 1\ny = 2\nx = 1\n')  # x = 1 appears twice
        
        context = {
            'changes': '''
```python
code.py
<<<<<<< SEARCH
x = 1
=======
x = 99
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        # File should be unchanged due to ambiguity
        content = existing.read_text()
        assert content.count('x = 1') == 2  # Still both occurrences
        assert len(context.get('apply_errors', [])) > 0
        assert 'ambiguous' in context['apply_errors'][0].lower() or 'multiple' in context['apply_errors'][0].lower()
    
    # === Test 6: Delete file (empty result) ===
    def test_delete_file_when_empty(self, hooks, temp_dir):
        """Test that files are deleted when content becomes empty."""
        existing = Path(temp_dir) / 'toremove.py'
        # Write content without trailing newline so SEARCH can match exactly
        existing.write_text('# delete me')
        
        # SEARCH content must match file content EXACTLY
        # Note: regex requires a newline after ======= even for empty replace
        changes_text = '''```python
toremove.py
<<<<<<< SEARCH
# delete me
=======

>>>>>>> REPLACE
```'''
        
        context = {
            'changes': changes_text,
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        # File should be deleted (content becomes empty)
        assert not existing.exists()
        assert any('deleted' in s.lower() for s in context.get('applied_changes', []))
    
    # === Test 7: Path traversal blocked (../ attack) ===
    def test_path_traversal_blocked(self, hooks, temp_dir):
        """Test that ../ path traversal is blocked."""
        context = {
            'changes': '''
```python
../../../etc/passwd
<<<<<<< SEARCH
=======
malicious content
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        # Should have blocked error
        assert len(context.get('apply_errors', [])) > 0
        assert 'blocked' in context['apply_errors'][0].lower()
    
    # === Test 8: Absolute path blocked ===
    def test_absolute_path_blocked(self, hooks, temp_dir):
        """Test that absolute paths outside working dir are blocked."""
        context = {
            'changes': '''
```python
/tmp/malicious.py
<<<<<<< SEARCH
=======
malicious
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        # Should have blocked error
        assert len(context.get('apply_errors', [])) > 0
        assert 'blocked' in context['apply_errors'][0].lower()
    
    # === Test 9: Working dir constraint enforced ===
    def test_working_dir_constraint(self, hooks, temp_dir):
        """Test that user_cwd safety check is enforced."""
        # Create a subdirectory for working_dir
        work_dir = Path(temp_dir) / 'project'
        work_dir.mkdir()
        
        context = {
            'changes': '''
```python
../outside.py
<<<<<<< SEARCH
=======
escape attempt
>>>>>>> REPLACE
```
''',
            'working_dir': str(work_dir),
            'user_cwd': str(work_dir),
        }
        
        hooks._apply_changes(context)
        
        # Should be blocked from escaping user_cwd
        outside = Path(temp_dir) / 'outside.py'
        assert not outside.exists()
    
    # === Test 10: Content extraction from dict wrapper ===
    def test_content_extraction_from_dict(self, hooks, temp_dir):
        """Test that content is extracted from {'content': ...} wrapper."""
        context = {
            'changes': {
                'content': '''
```python
wrapped.py
<<<<<<< SEARCH
=======
# from wrapper
>>>>>>> REPLACE
```
'''
            },
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        created = Path(temp_dir) / 'wrapped.py'
        assert created.exists()
        assert '# from wrapper' in created.read_text()
    
    # === Test 11: Legacy JSON format fallback ===
    def test_legacy_json_format(self, hooks, temp_dir):
        """Test fallback to legacy JSON format with 'files' key."""
        context = {
            'changes': {
                'files': [
                    {'path': 'legacy.py', 'action': 'create', 'content': '# legacy format'}
                ]
            },
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        created = Path(temp_dir) / 'legacy.py'
        assert created.exists()
        assert '# legacy format' in created.read_text()
    
    # === Test 12: Multiple operations in one call ===
    def test_multiple_operations(self, hooks, temp_dir):
        """Test applying multiple file operations in one call."""
        # Create an existing file to modify
        existing = Path(temp_dir) / 'existing.py'
        existing.write_text('old_value = 1\n')
        
        context = {
            'changes': '''
```python
new_file.py
<<<<<<< SEARCH
=======
# new file
>>>>>>> REPLACE
```

```python
existing.py
<<<<<<< SEARCH
old_value = 1
=======
new_value = 2
>>>>>>> REPLACE
```
''',
            'working_dir': temp_dir,
            'user_cwd': temp_dir,
        }
        
        hooks._apply_changes(context)
        
        # Both operations should succeed
        new_file = Path(temp_dir) / 'new_file.py'
        assert new_file.exists()
        assert '# new file' in new_file.read_text()
        
        assert 'new_value = 2' in existing.read_text()
        
        # Should have 2 applied changes
        assert len(context.get('applied_changes', [])) == 2
