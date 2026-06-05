"""Tests for Gratuity calculator."""

from mcp_india_stack.tools.gratuity import calculate_gratuity


class TestGratuity:
    def test_act_7yr(self) -> None:
        result = calculate_gratuity(last_drawn_salary=50000, years_of_service=7)
        assert result["completed_years_for_calculation"] == 7

    def test_rounding_up(self) -> None:
        result = calculate_gratuity(last_drawn_salary=50000, years_of_service=5.6)
        assert result["completed_years_for_calculation"] == 6

    def test_rounding_down(self) -> None:
        result = calculate_gratuity(last_drawn_salary=50000, years_of_service=5.4)
        assert result["completed_years_for_calculation"] == 5

    def test_non_act(self) -> None:
        result = calculate_gratuity(
            last_drawn_salary=50000, years_of_service=7, is_covered_under_act=False
        )
        assert result["is_covered_under_act"] is False
        assert result["gratuity_amount"] > 0

    def test_below_5yr(self) -> None:
        result = calculate_gratuity(last_drawn_salary=50000, years_of_service=3)
        assert result["minimum_service_met"] is False

    def test_above_20l(self) -> None:
        result = calculate_gratuity(last_drawn_salary=250000, years_of_service=15)
        assert result["gratuity_amount"] > 2000000

    def test_negative_salary(self) -> None:
        result = calculate_gratuity(last_drawn_salary=-50000, years_of_service=7)
        assert "errors" in result

    def test_zero_years(self) -> None:
        result = calculate_gratuity(last_drawn_salary=50000, years_of_service=0)
        assert "errors" in result
