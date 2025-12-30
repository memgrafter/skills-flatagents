import pytest
from calculator import add, subtract, multiply, divide, power, factorial


def test_add_positive_numbers():
    """Test adding two positive numbers."""
    assert add(2.5, 3.5) == 6.0


def test_add_negative_numbers():
    """Test adding two negative numbers."""
    assert add(-2.5, -3.5) == -6.0


def test_add_mixed_signs():
    """Test adding numbers with different signs."""
    assert add(-5.0, 10.0) == 5.0


def test_add_zero():
    """Test adding zero to a number."""
    assert add(0.0, 7.5) == 7.5
    assert add(7.5, 0.0) == 7.5


def test_subtract_positive_numbers():
    """Test subtracting two positive numbers."""
    assert subtract(10.0, 3.0) == 7.0


def test_subtract_negative_numbers():
    """Test subtracting two negative numbers."""
    assert subtract(-5.0, -3.0) == -2.0


def test_subtract_mixed_signs():
    """Test subtracting numbers with different signs."""
    assert subtract(5.0, -3.0) == 8.0
    assert subtract(-5.0, 3.0) == -8.0


def test_subtract_zero():
    """Test subtracting zero from a number."""
    assert subtract(7.5, 0.0) == 7.5
    assert subtract(0.0, 7.5) == -7.5


def test_multiply_positive_numbers():
    """Test multiplying two positive numbers."""
    assert multiply(2.5, 4.0) == 10.0


def test_multiply_negative_numbers():
    """Test multiplying two negative numbers."""
    assert multiply(-2.5, -4.0) == 10.0


def test_multiply_mixed_signs():
    """Test multiplying numbers with different signs."""
    assert multiply(-2.5, 4.0) == -10.0
    assert multiply(2.5, -4.0) == -10.0


def test_multiply_zero():
    """Test multiplying by zero."""
    assert multiply(7.5, 0.0) == 0.0
    assert multiply(0.0, 7.5) == 0.0


def test_divide_positive_numbers():
    """Test dividing two positive numbers."""
    assert divide(10.0, 2.0) == 5.0


def test_divide_negative_numbers():
    """Test dividing two negative numbers."""
    assert divide(-10.0, -2.0) == 5.0


def test_divide_mixed_signs():
    """Test dividing numbers with different signs."""
    assert divide(-10.0, 2.0) == -5.0
    assert divide(10.0, -2.0) == -5.0


def test_divide_by_zero_raises_error():
    """Test that dividing by zero raises ValueError."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10.0, 0.0)


def test_divide_zero_by_nonzero():
    """Test dividing zero by a non-zero number."""
    assert divide(0.0, 5.0) == 0.0


def test_power_positive_exponent():
    """Test raising a number to a positive exponent."""
    assert power(2.0, 3) == 8.0
    assert power(5.0, 1) == 5.0


def test_power_zero_exponent():
    """Test raising a number to the power of zero."""
    assert power(5.0, 0) == 1.0


def test_power_negative_exponent():
    """Test raising a number to a negative exponent."""
    assert power(2.0, -2) == 0.25
    assert power(10.0, -1) == 0.1


def test_power_base_zero():
    """Test raising zero to various powers."""
    assert power(0.0, 3) == 0.0
    assert power(0.0, 1) == 0.0


def test_power_base_one():
    """Test raising one to various powers."""
    assert power(1.0, 5) == 1.0
    assert power(1.0, -3) == 1.0


def test_power_negative_base_even_exponent():
    """Test raising a negative base to an even exponent."""
    assert power(-2.0, 2) == 4.0
    assert power(-3.0, 4) == 81.0


def test_power_negative_base_odd_exponent():
    """Test raising a negative base to an odd exponent."""
    assert power(-2.0, 3) == -8.0
    assert power(-3.0, 1) == -3.0


def test_factorial_zero():
    """Test factorial of zero."""
    assert factorial(0) == 1


def test_factorial_one():
    """Test factorial of one."""
    assert factorial(1) == 1


def test_factorial_positive_numbers():
    """Test factorial of positive numbers."""
    assert factorial(5) == 120
    assert factorial(3) == 6
    assert factorial(4) == 24


def test_factorial_negative_number_raises_error():
    """Test that factorial of negative number raises ValueError."""
    with pytest.raises(ValueError, match="Factorial not defined for negative numbers"):
        factorial(-1)


def test_factorial_large_number():
    """Test factorial of a larger number."""
    assert factorial(6) == 720
    assert factorial(7) == 5040
