"""
Integration tests for human review gates.

Tests the plan and result review functionality.

Test Cases:
- Plan approval sets flag
- Plan rejection saves history
- Result approval sets flag
- Result rejection saves history
- Feedback passed to context
"""

import pytest
from unittest.mock import patch
from coding_agent.hooks import CodingAgentHooks


class TestHumanReviewGates:
    """Tests for human-in-the-loop review functionality."""
    
    @pytest.fixture
    def hooks(self):
        """Create hooks instance for testing."""
        return CodingAgentHooks()
    
    # === Test 1: Plan approval sets flag ===
    def test_plan_approval_sets_flag(self, hooks):
        """Test that plan approval sets plan_approved to True."""
        context = {
            'plan': 'Step 1: Create file\nStep 2: Add function',
            'task': 'Add new feature'
        }
        
        with patch('builtins.input', return_value='y'):
            result = hooks._human_review_plan(context)
        
        assert result['plan_approved'] is True
        assert result['human_feedback'] is None
    
    def test_plan_approval_with_yes(self, hooks):
        """Test that 'yes' input approves the plan."""
        context = {
            'plan': 'Some plan content',
            'task': 'Test task'
        }
        
        with patch('builtins.input', return_value='yes'):
            result = hooks._human_review_plan(context)
        
        assert result['plan_approved'] is True
    
    def test_plan_approval_with_empty(self, hooks):
        """Test that empty input approves the plan."""
        context = {
            'plan': 'Some plan content',
            'task': 'Test task'
        }
        
        with patch('builtins.input', return_value=''):
            result = hooks._human_review_plan(context)
        
        assert result['plan_approved'] is True
    
    # === Test 2: Plan rejection saves history ===
    def test_plan_rejection_saves_history(self, hooks):
        """Test that plan rejection saves to plan_history with feedback."""
        context = {
            'plan': 'Original plan',
            'task': 'Test task',
            'plan_history': []
        }
        
        with patch('builtins.input', return_value='Need more error handling'):
            result = hooks._human_review_plan(context)
        
        assert result['plan_approved'] is False
        assert result['human_feedback'] == 'Need more error handling'
        assert len(result['plan_history']) == 1
        assert result['plan_history'][0]['content'] == 'Original plan'
        assert result['plan_history'][0]['feedback'] == 'Need more error handling'
    
    def test_plan_rejection_appends_to_existing_history(self, hooks):
        """Test that rejection appends to existing plan_history."""
        context = {
            'plan': 'Second attempt',
            'task': 'Test task',
            'plan_history': [
                {'content': 'First attempt', 'feedback': 'Too complex'}
            ]
        }
        
        with patch('builtins.input', return_value='Still needs work'):
            result = hooks._human_review_plan(context)
        
        assert len(result['plan_history']) == 2
        assert result['plan_history'][1]['content'] == 'Second attempt'
    
    # === Test 3: Result approval sets flag ===
    def test_result_approval_sets_flag(self, hooks):
        """Test that result approval sets result_approved to True."""
        context = {
            'changes': 'def new_function():\n    pass',
            'task': 'Add function',
            'iteration': 1
        }
        
        with patch('builtins.input', return_value='y'):
            result = hooks._human_review_result(context)
        
        assert result['result_approved'] is True
        assert result['human_feedback'] is None
    
    # === Test 4: Result rejection saves history ===
    def test_result_rejection_saves_history(self, hooks):
        """Test that result rejection saves to changes_history with feedback."""
        context = {
            'changes': 'Some code changes',
            'issues': 'Found issues',
            'task': 'Test task',
            'iteration': 1,
            'changes_history': []
        }
        
        with patch('builtins.input', return_value='Add unit tests'):
            result = hooks._human_review_result(context)
        
        assert result['result_approved'] is False
        assert result['human_feedback'] == 'Add unit tests'
        assert len(result['changes_history']) == 1
        assert result['changes_history'][0]['content'] == 'Some code changes'
        assert result['changes_history'][0]['feedback'] == 'Add unit tests'
        assert result['changes_history'][0]['issues'] == 'Found issues'
    
    # === Test 5: Feedback passed to context ===
    def test_feedback_passed_to_context(self, hooks):
        """Test that human feedback is properly stored in context."""
        context = {
            'plan': 'Initial plan',
            'task': 'Test task'
        }
        
        feedback = 'Please add logging and error handling to all functions'
        with patch('builtins.input', return_value=feedback):
            result = hooks._human_review_plan(context)
        
        assert result['human_feedback'] == feedback
        assert result['plan_approved'] is False
    
    def test_content_extracted_from_dict_wrapper(self, hooks):
        """Test that content is extracted from dict wrapper format."""
        context = {
            'plan': {'content': 'Wrapped plan content'},
            'task': 'Test task'
        }
        
        with patch('builtins.input', return_value='y'):
            result = hooks._human_review_plan(context)
        
        # Should successfully process wrapped content
        assert result['plan_approved'] is True
    
    def test_result_with_all_wrapped_fields(self, hooks):
        """Test result review with all fields wrapped in dict format."""
        context = {
            'changes': {'content': 'New code here'},
            'issues': {'content': 'No issues'},
            'review_summary': {'content': 'Looks good'},
            'task': 'Test task',
            'iteration': 2
        }
        
        with patch('builtins.input', return_value='y'):
            result = hooks._human_review_result(context)
        
        assert result['result_approved'] is True
