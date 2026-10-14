"""Wage comparison logic for the South Asia fashion dashboard prototype.

The CSV values used by this module are fictional demonstration data. They are
not official wage, cost-of-living, or economic statistics.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {
    "country",
    "city",
    "legal_minimum_wage",
    "estimated_living_wage",
    "average_food_cost",
    "average_housing_cost",
    "currency",
    "year",
    "notes",
}

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "wage_data.csv"


def load_wage_data(csv_path: str | Path = DEFAULT_DATA_PATH) -> list[dict[str, Any]]:
    """Load and validate wage records from a CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Wage data file was not found: {path}")

    with path.open(newline="", encoding="utf-8") as data_file:
        reader = csv.DictReader(data_file)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Wage data is missing required columns: {missing}")

        records = []
        for row_number, row in enumerate(reader, start=2):
            try:
                record = dict(row)
                for column in (
                    "legal_minimum_wage",
                    "estimated_living_wage",
                    "average_food_cost",
                    "average_housing_cost",
                ):
                    record[column] = _parse_non_negative_number(record[column], column)
                record["year"] = int(row["year"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid wage data on CSV row {row_number}: {error}") from error

            if not record["country"].strip() or not record["city"].strip():
                raise ValueError(f"Country and city are required on CSV row {row_number}")
            records.append(record)

    if not records:
        raise ValueError("Wage data must contain at least one record")
    return records


def available_countries(records: list[dict[str, Any]]) -> list[str]:
    """Return countries in stable, alphabetical order for a selector."""
    return sorted({record["country"] for record in records})


def available_cities(records: list[dict[str, Any]], country: str) -> list[str]:
    """Return cities available for the selected country."""
    return sorted({record["city"] for record in records if record["country"] == country})


def find_wage_record(
    records: list[dict[str, Any]], country: str, city: str
) -> dict[str, Any]:
    """Find the wage record selected by the user."""
    for record in records:
        if record["country"] == country and record["city"] == city:
            return record
    raise ValueError(f"No wage record was found for {country}, {city}")


def calculate_wage_comparison(
    entered_wage: float | int | str,
    record: dict[str, Any],
) -> dict[str, float]:
    """Compare an entered monthly payout with the two wage benchmarks.

    A positive legal minimum difference means the entered payout is above the
    legal minimum. A positive living wage gap means the payout is below the
    estimated living wage; a negative result means it is above that estimate.
    """
    entered_amount = _parse_non_negative_number(entered_wage, "entered_wage")
    legal_minimum = _parse_non_negative_number(
        record.get("legal_minimum_wage"), "legal_minimum_wage"
    )
    living_wage = _parse_non_negative_number(
        record.get("estimated_living_wage"), "estimated_living_wage"
    )
    if living_wage == 0:
        raise ValueError("estimated_living_wage must be greater than zero")

    living_wage_difference = living_wage - entered_amount
    return {
        "entered_wage": entered_amount,
        "difference_from_legal_minimum": entered_amount - legal_minimum,
        "difference_from_estimated_living_wage": living_wage_difference,
        "living_wage_gap_percentage": (living_wage_difference / living_wage) * 100,
    }


def _parse_non_negative_number(value: Any, field_name: str) -> float:
    """Convert user or CSV input to a finite, non-negative number."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} is required")
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be a number") from error
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    if number < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return number


def main() -> None:
    """Run a small terminal-based example of the calculator."""
    records = load_wage_data()
    countries = available_countries(records)
    print("Wage calculator demonstration using fictional data")
    print("Available countries:", ", ".join(countries))
    country = input("Select a country: ").strip()
    cities = available_cities(records, country)
    if not cities:
        raise ValueError("That country is not available in the wage dataset")
    print("Available cities:", ", ".join(cities))
    city = input("Select a city: ").strip()
    record = find_wage_record(records, country, city)
    entered_wage = input(f"Enter the monthly payout in {record['currency']}: ")
    results = calculate_wage_comparison(entered_wage, record)
    print(f"Difference from legal minimum: {results['difference_from_legal_minimum']:.2f}")
    print(
        "Difference from estimated living wage: "
        f"{results['difference_from_estimated_living_wage']:.2f}"
    )
    print(f"Living-wage gap percentage: {results['living_wage_gap_percentage']:.2f}%")


if __name__ == "__main__":
    main()