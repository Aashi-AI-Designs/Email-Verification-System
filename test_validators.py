def test_validate_email_format():
    assert validate_email_format("john@example.com") == (True, "Valid format")
    assert validate_email_format("invalid-email") == (False, "Invalid email format")