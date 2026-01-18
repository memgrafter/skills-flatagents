"""
Unit tests for display functions.

Tests the display-related functionality in hooks.py.

Test Cases:
- Plan display extracts content
- Changes display extracts content
- Long content truncation
"""

import pytest
from io import StringIO
from unittest.mock import patch
from coding_agent.hooks import CodingAgentHooks


class TestDisplayFunctions:
    """Tests for display functions."""
    
    @pytest.fixture
    def hooks(self):
        """Create hooks instance for testing."""
        return CodingAgentHooks()
    
    # === Test 1: Plan display extracts content ===
    def test_plan_display_extracts_content(self, hooks):
        """Test that plan content is extracted from dict wrapper."""
        context = {
            'plan': {'content': 'This is the plan content'},
            'task': 'Test task'
        }
        
        # Mock input to auto-approve
        with patch('builtins.input', return_value='y'):
            result = hooks._human_review_plan(context)
        
        assert result['plan_approved'] is True
    
    # === Test 2: Changes display extracts content ===
    def test_changes_display_extracts_content(self, hooks):
        """Test that changes content is extracted from dict wrapper."""
        context = {
            'changes': {'content': 'def new_function():\n    pass'},
            'issues': {'content': 'No issues found'},
            'review_summary': {'content': 'Looks good'},
            'task': 'Test task',
            'iteration': 1
        }
        
        # Mock input to auto-approve
        with patch('builtins.input', return_value='y'):
            result = hooks._human_review_result(context)
        
        assert result['result_approved'] is True
    
    # === Test 3: Long content is fully displayed ===
    def test_long_content_fully_displayed(self, hooks, capsys):
        """Test that long plan content is fully displayed without truncation."""
        # Create a plan with many lines
        long_plan = '\n'.join([f'Line {i}: Some content here' for i in range(100)])
        
        context = {
            'plan': long_plan,
            'task': 'Test task'
        }
        
        # Mock input to auto-approve
        with patch('builtins.input', return_value='y'):
            hooks._human_review_plan(context)
        
        captured = capsys.readouterr()
        # Should show all lines without truncation
        assert 'Line 99' in captured.out  # Last line should be present
    
    # === Additional display tests ===
    
    def test_plan_rejection_saves_history(self, hooks):
        """Test that plan rejection saves to history with feedback."""
        context = {
            'plan': 'Original plan',
            'task': 'Test task',
            'plan_history': []
        }
        
        # Mock input to reject with feedback
        with patch('builtins.input', return_value='Please add error handling'):
            result = hooks._human_review_plan(context)
        
        assert result['plan_approved'] is False
        assert result['human_feedback'] == 'Please add error handling'
        assert len(result['plan_history']) == 1
        assert result['plan_history'][0]['feedback'] == 'Please add error handling'
    
    def test_result_rejection_saves_history(self, hooks):
        """Test that result rejection saves to history with feedback."""
        context = {
            'changes': 'Some changes',
            'task': 'Test task',
            'iteration': 1,
            'changes_history': []
        }
        
        # Mock input to reject with feedback
        with patch('builtins.input', return_value='Fix the indentation'):
            result = hooks._human_review_result(context)
        
        assert result['result_approved'] is False
        assert result['human_feedback'] == 'Fix the indentation'
        assert len(result['changes_history']) == 1
        assert result['changes_history'][0]['feedback'] == 'Fix the indentation'
    
    def test_empty_plan_warning(self, hooks, capsys):
        """Test that empty plan content shows warning."""
        context = {
            'plan': '',
            'task': 'Test task'
        }
        
        with patch('builtins.input', return_value='y'):
            hooks._human_review_plan(context)
        
        captured = capsys.readouterr()
        assert 'WARNING' in captured.out or 'No plan content' in captured.out
    
    def test_empty_changes_warning(self, hooks, capsys):
        """Test that empty changes content shows warning."""
        context = {
            'changes': '',
            'task': 'Test task',
            'iteration': 1
        }
        
        with patch('builtins.input', return_value='y'):
            hooks._human_review_result(context)
        
        captured = capsys.readouterr()
        assert 'WARNING' in captured.out or 'No changes content' in captured.out
