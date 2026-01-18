"""
Unit tests for the diff parser.

Tests the _parse_diffs method in hooks.py without external dependencies.

Test Cases:
- New file creation (empty SEARCH)
- File modification (SEARCH/REPLACE)
- Multiple blocks in one output
- Duplicate blocks (last wins)
- Triple backticks with language
- Quad backtick support
- Empty REPLACE (deletion)
- Whitespace handling
- No blocks found
- Malformed blocks skipped
- Path extraction
- Multiline content
"""

import pytest
from coding_agent.hooks import CodingAgentHooks


class TestParseDiffs:
    """Tests for the _parse_diffs method."""
    
    @pytest.fixture
    def hooks(self):
        """Create hooks instance for testing."""
        return CodingAgentHooks()
    
    # === Test 1: New file - empty SEARCH creates file ===
    def test_new_file_empty_search(self, hooks):
        """Test that empty SEARCH section creates a new file."""
        text = '''
```python
src/new_file.py
<<<<<<< SEARCH
=======
def hello():
    return "world"
>>>>>>> REPLACE
```
'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 1
        assert operations[0]['action'] == 'create'
        assert operations[0]['path'] == 'src/new_file.py'
        assert 'def hello():' in operations[0]['content']
    
    # === Test 2: Modify file - SEARCH/REPLACE detected ===
    def test_modify_file_search_replace(self, hooks):
        """Test that non-empty SEARCH creates a modify operation."""
        text = '''
```python
src/utils.py
<<<<<<< SEARCH
def old():
    pass
=======
def new():
    return True
>>>>>>> REPLACE
```
'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 1
        assert operations[0]['action'] == 'modify'
        assert operations[0]['path'] == 'src/utils.py'
        assert 'def old():' in operations[0]['search']
        assert 'def new():' in operations[0]['replace']
        assert operations[0]['is_diff'] is True
    
    # === Test 3: Multiple blocks in one output ===
    def test_multiple_blocks_in_output(self, hooks):
        """Test parsing multiple SEARCH/REPLACE blocks in one output."""
        text = '''
Here are the changes:

```python
src/file1.py
<<<<<<< SEARCH
=======
# File 1 content
>>>>>>> REPLACE
```

And another file:

```python
src/file2.py
<<<<<<< SEARCH
old content
=======
new content
>>>>>>> REPLACE
```
'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 2
        paths = [op['path'] for op in operations]
        assert 'src/file1.py' in paths
        assert 'src/file2.py' in paths
    
    # === Test 4: Duplicate blocks - last wins ===
    def test_duplicate_blocks_last_wins(self, hooks):
        """Test that duplicate blocks (same file+search) resolve to last one."""
        text = '''
```python
config.py
<<<<<<< SEARCH
DEBUG = True
=======
DEBUG = False
>>>>>>> REPLACE
```

Actually, let me fix that:

```python
config.py
<<<<<<< SEARCH
DEBUG = True
=======
DEBUG = None
>>>>>>> REPLACE
```
'''
        operations = hooks._parse_diffs(text)
        
        # Should only have one operation (deduped by file+search)
        assert len(operations) == 1
        assert operations[0]['replace'] == 'DEBUG = None'
    
    # === Test 5: Triple backticks with language ===
    def test_triple_backticks_with_language(self, hooks):
        """Test that triple backticks with language identifier work."""
        text = '''
```javascript
app.js
<<<<<<< SEARCH
const x = 1;
=======
const x = 2;
>>>>>>> REPLACE
```
'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 1
        assert operations[0]['path'] == 'app.js'
        assert 'const x = 1;' in operations[0]['search']
    
    # === Test 6: Quad backticks for markdown files ===
    def test_quad_backticks_for_markdown(self, hooks):
        """Test that quad backticks work for files containing triple backticks."""
        text = '''
````markdown
README.md
<<<<<<< SEARCH
=======
# Project

```bash
npm install
```
>>>>>>> REPLACE
````
'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 1
        assert operations[0]['path'] == 'README.md'
        assert '```bash' in operations[0]['content']
        assert 'npm install' in operations[0]['content']
    
    # === Test 7: Empty REPLACE - delete content ===
    def test_empty_replace_deletes_content(self, hooks):
        """Test that empty REPLACE section creates modify with empty replace."""
        # Empty REPLACE means the entire SEARCH content is deleted
        text = '''```python
utils.py
<<<<<<< SEARCH
def deprecated():
    pass
=======

>>>>>>> REPLACE
```'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 1
        assert operations[0]['action'] == 'modify'
        assert 'deprecated' in operations[0]['search']
        # Replace content should be minimal (just newline from pattern)
        assert operations[0]['replace'].strip() == ''
    
    # === Test 8: Whitespace handling in SEARCH ===
    def test_whitespace_handling_in_search(self, hooks):
        """Test that whitespace is preserved exactly in SEARCH content."""
        text = '''
```python
app.py
<<<<<<< SEARCH
    def indented():
        pass
=======
    def indented():
        return True
>>>>>>> REPLACE
```
'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 1
        # Whitespace should be preserved
        assert '    def indented():' in operations[0]['search']
        assert '        pass' in operations[0]['search']
    
    # === Test 9: No blocks found returns empty list ===
    def test_no_blocks_returns_empty(self, hooks):
        """Test that text without blocks returns empty list."""
        text = '''
Here's some general text about the code.
No actual diff blocks here.
Just prose.
'''
        operations = hooks._parse_diffs(text)
        
        assert operations == []
    
    # === Test 10: Malformed blocks skipped ===
    def test_malformed_blocks_skipped(self, hooks):
        """Test that malformed blocks are skipped without error."""
        text = '''This text has no valid diff blocks at all.

It just discusses code changes conceptually.

Here is a valid one:

```python
valid.py
<<<<<<< SEARCH
old
=======
new
>>>>>>> REPLACE
```'''
        operations = hooks._parse_diffs(text)
        
        # Only the valid block should be parsed
        assert len(operations) == 1
        assert operations[0]['path'] == 'valid.py'
    
    # === Test 11: Path extraction from block ===
    def test_path_extraction_various_formats(self, hooks):
        """Test path extraction works with various path formats."""
        # Nested path
        text1 = '''
```python
src/components/utils/helpers.py
<<<<<<< SEARCH
=======
# helper
>>>>>>> REPLACE
```
'''
        ops1 = hooks._parse_diffs(text1)
        assert ops1[0]['path'] == 'src/components/utils/helpers.py'
        
        # Simple filename
        text2 = '''
```python
main.py
<<<<<<< SEARCH
=======
# main
>>>>>>> REPLACE
```
'''
        ops2 = hooks._parse_diffs(text2)
        assert ops2[0]['path'] == 'main.py'
    
    # === Test 12: Multiline SEARCH content ===
    def test_multiline_search_content(self, hooks):
        """Test that multiline SEARCH content is captured correctly."""
        text = '''
```python
module.py
<<<<<<< SEARCH
def function_a():
    x = 1
    y = 2
    return x + y

def function_b():
    return True
=======
def function_combined():
    return 3
>>>>>>> REPLACE
```
'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 1
        search = operations[0]['search']
        assert 'function_a' in search
        assert 'function_b' in search
        assert 'x = 1' in search
        assert 'y = 2' in search
    
    # === Test 13: Multiline REPLACE content ===
    def test_multiline_replace_content(self, hooks):
        """Test that multiline REPLACE content is captured correctly."""
        text = '''
```python
module.py
<<<<<<< SEARCH
pass
=======
def new_func():
    """Docstring."""
    x = 1
    y = 2
    z = 3
    return x + y + z
>>>>>>> REPLACE
```
'''
        operations = hooks._parse_diffs(text)
        
        assert len(operations) == 1
        replace = operations[0]['replace']
        assert 'new_func' in replace
        assert 'Docstring' in replace
        assert 'x = 1' in replace
        assert 'return x + y + z' in replace
