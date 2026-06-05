from mcp_india_stack.tools.fd_maturity import calculate_fd_maturity


def test_fd_maturity_compounding_freq():
    r1 = calculate_fd_maturity(
        principal=1000, annual_interest_rate=5, tenure_days=365, compounding_frequency=12
    )
    assert not r1.get("errors")

    r2 = calculate_fd_maturity(
        principal=1000, annual_interest_rate=5, tenure_days=365, compounding_frequency=2
    )
    assert not r2.get("errors")

    r3 = calculate_fd_maturity(
        principal=1000, annual_interest_rate=5, tenure_days=365, compounding_frequency=1
    )
    assert not r3.get("errors")
