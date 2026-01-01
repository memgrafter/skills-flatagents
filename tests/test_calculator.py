import pytest
from calculator import add, subtract, multiply, divide, power, factorial


def test_add_positive_numbers():
    """Test adding two positive numbers."""
    assert add(2, 3) == 5


def test_add_negative_numbers():
    """Test adding two negative numbers."""
    assert add(-2, -3) == -5


def test_add_mixed_numbers():
    """Test adding a positive and negative number."""
    assert add(5, -3) == 2


def test_add_zero():
    """Test adding zero to a number."""
    assert add(10, 0) == 10
    assert add(0, 10) == 10


def test_add_floats():
    """Test adding floating point numbers."""
    assert add(2.5, 3.5) == 6.0


def test_subtract_positive_numbers():
    """Test subtracting two positive numbers."""
    assert subtract(5, 3) == 2


def test_subtract_negative_numbers():
    """Test subtracting two negative numbers."""
    assert subtract(-5, -3) == -2


def test_subtract_mixed_numbers():
    """Test subtracting a negative number from a positive."""
    assert subtract(5, -3) == 8


def test_subtract_zero():
    """Test subtracting zero from a number."""
    assert subtract(10, 0) == 10
    assert subtract(0, 10) == -10


def test_multiply_positive_numbers():
    """Test multiplying two positive numbers."""
    assert multiply(2, 3) == 6


def test_multiply_negative_numbers():
    """Test multiplying two negative numbers."""
    assert multiply(-2, -3) == 6


def test_multiply_mixed_numbers():
    """Test multiplying a positive and negative number."""
    assert multiply(2, -3) == -6


def test_multiply_zero():
    """Test multiplying by zero."""
    assert multiply(10, 0) == 0
    assert multiply(0, 10) == 0


def test_multiply_floats():
    """Test multiplying floating point numbers."""
    assert multiply(2.5, 4) == 10.0


def test_divide_positive_numbers():
    """Test dividing two positive numbers."""
    assert divide(6, 2) == 3.0


def test_divide_negative_numbers():
    """Test dividing two negative numbers."""
    assert divide(-6, -2) == 3.0


def test_divide_mixed_numbers():
    """Test dividing a positive by a negative number."""
    assert divide(6, -2) == -3.0


def test_divide_floats():
    """Test dividing floating point numbers."""
    assert divide(5.5, 2) == 2.75


def test_divide_by_zero_raises_error():
    """Test that dividing by zero raises ValueError."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(5, 0)


def test_power_positive_exponent():
    """Test raising a number to a positive exponent."""
    assert power(2, 3) == 8
    assert power(5, 1) == 5


def test_power_zero_exponent():
    """Test raising a number to the power of zero."""
    assert power(10, 0) == 1


def test_power_negative_exponent():
    """Test raising a number to a negative exponent."""
    assert power(2, -2) == 0.25
    assert power(10, -1) == 0.1


def test_power_base_zero():
    """Test raising zero to various exponents."""
    assert power(0, 3) == 0
    assert power(0, 1) == 0


def test_power_float_base():
    """Test raising a float base to an integer exponent."""
    assert power(2.5, 2) == 6.25


def test_factorial_zero():
    """Test factorial of zero."""
    assert factorial(0) == 1


def test_factorial_one():
    """Test factorial of one."""
    assert factorial(1) == 1


def test_factorial_positive_numbers():
    """Test factorial of positive numbers."""
    assert factorial(3) == 6
    assert factorial(5) == 120


def test_factorial_negative_number_raises_error():
    """Test that factorial of negative number raises ValueError."""
    with pytest.raises(ValueError, match="Factorial not defined for negative numbers"):
        factorial(-1)
