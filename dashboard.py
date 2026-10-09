"""Interactive Streamlit dashboard for the fictional fashion-trade prototype."""

from __future__ import annotations

from html import escape
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

try:
    from .wage_calculator import (
        available_cities,
        available_countries,
        calculate_wage_comparison,
        find_wage_record,
        load_wage_data,
    )
except ImportError:
    from wage_calculator import (
        available_cities,
        available_countries,
        calculate_wage_comparison,
        find_wage_record,
        load_wage_data,
    )

try:
    from .currency_converter import get_exchange_rates, local_to_usd
except ImportError:
    from currency_converter import get_exchange_rates, local_to_usd

from data.country_content import COUNTRY_CONTENT
from data.news_sources import NEWS_SOURCES
from data.timelines import TIMELINES


TRADE_DATA_PATH = PROJECT_ROOT / "data" / "trade_data.csv"
TRADE_FEATURES = ["tariff_rate", "labor_cost", "eu_trade_preference"]
TRADE_TARGET = "total_export_volume_usd"
TRADE_REQUIRED_COLUMNS = {"country", "year", *TRADE_FEATURES, TRADE_TARGET}

def apply_dashboard_style() -> None:
    """Apply the intentionally small visual layer for the dashboard."""
    st.markdown(
        """
        <style>
        :root {
            --navy: #102a43;
            --navy-soft: #243b53;
            --cream: #f7f1e8;
            --paper: #fffdf9;
            --burgundy: #8f2d3d;
            --muted: #627d98;
        }
        .stApp { background: var(--cream); }
        [data-testid="stHeader"] { background: rgba(247, 241, 232, 0.88); }
        [data-testid="stSidebar"] {
            background: var(--navy);
            border-right: 1px solid var(--navy-soft);
        }
        [data-testid="stSidebar"] * { color: #f7f1e8; }
        [data-testid="stSidebar"] hr { border-color: rgba(247, 241, 232, 0.2); }
        .block-container { padding-top: 3.5rem; padding-bottom: 4rem; }
        h1, h2, h3 { color: var(--navy); letter-spacing: 0.01em; }
        .hero {
            background: linear-gradient(110deg, var(--navy) 0%, #1f405d 72%, var(--burgundy) 100%);
            border-radius: 10px;
            padding: 2.5rem 3rem;
            margin-bottom: 1.75rem;
            color: #fffdf9;
        }
        .hero h1 { color: #fffdf9; font-size: 2.7rem; margin: 0 0 .35rem; }
        .hero p { color: #f7f1e8; max-width: 760px; margin: 0; font-size: 1.08rem; }
        [data-testid="stMetric"] {
            background: var(--paper);
            border: 1px solid #e5d9cc;
            border-top: 4px solid var(--burgundy);
            border-radius: 8px;
            padding: 1rem;
        }
        [data-baseweb="tab-list"] { gap: 1.5rem; }
        [data-baseweb="tab"] { color: var(--navy-soft); font-weight: 600; }
        [aria-selected="true"] { color: var(--burgundy) !important; }
        [data-testid="stAlert"] { border-radius: 8px; }
        .source-card {
            background: var(--paper);
            border: 1px solid #e5d9cc;
            border-left: 4px solid var(--burgundy);
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin: .75rem 0;
        }
        .source-card h4 { color: var(--navy); margin: 0 0 .35rem; }
        .source-meta { color: var(--muted); font-size: .85rem; }
        .country-placeholder {
            min-height: 270px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 1.5rem;
            border-radius: 8px;
            background: linear-gradient(145deg, var(--navy) 0%, var(--navy-soft) 66%, var(--burgundy) 100%);
            color: var(--cream);
        }
        .placeholder-kicker, .placeholder-city { color: #d9e2ec; font-size: .9rem; }
        .placeholder-title { color: #fffdf9; font-size: 2rem; font-weight: 700; margin: .35rem 0; }
        .placeholder-mark { color: #f7c6c9; font-size: .72rem; letter-spacing: .16em; margin-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def get_wage_data() -> list[dict[str, object]]:
    """Cache the validated wage records until the source file changes."""
    return load_wage_data()


@st.cache_data
def get_trade_data() -> pd.DataFrame:
    """Load and validate the fictional trade dataset."""
    if not TRADE_DATA_PATH.exists():
        raise FileNotFoundError(f"Trade data file was not found: {TRADE_DATA_PATH}")

    data = pd.read_csv(TRADE_DATA_PATH)
    missing_columns = TRADE_REQUIRED_COLUMNS - set(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Trade data is missing required columns: {missing}")

    for column in ["year", *TRADE_FEATURES, TRADE_TARGET]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["country", "year", *TRADE_FEATURES, TRADE_TARGET])
    if data.empty:
        raise ValueError("Trade data has no complete records after validation")
    if (data["eu_trade_preference"] < 0).any() or (data["eu_trade_preference"] > 1).any():
        raise ValueError("eu_trade_preference values must be between 0 and 1")
    if (data[TRADE_FEATURES] < 0).any().any() or (data[TRADE_TARGET] < 0).any():
        raise ValueError("Trade numeric values cannot be negative")
    return data


def train_trade_model(data: pd.DataFrame) -> tuple[LinearRegression, dict[str, float]]:
    """Fit the prototype model and return simple in-sample diagnostics."""
    model = LinearRegression()
    model.fit(data[TRADE_FEATURES], data[TRADE_TARGET])
    predictions = model.predict(data[TRADE_FEATURES])
    metrics = {
        "r2": float(r2_score(data[TRADE_TARGET], predictions)),
        "mae": float(mean_absolute_error(data[TRADE_TARGET], predictions)),
    }
    return model, metrics


def render_wage_calculator() -> None:
    """Render Module A and reuse the tested wage-calculation functions."""
    st.header("Wage and cost-of-living calculator", icon=":material/payments:")
    st.caption("All wage and cost figures below are fictional mock data.")

    try:
        wage_records = get_wage_data()
        countries = available_countries(wage_records)
    except (FileNotFoundError, ValueError) as error:
        st.error(f"Could not load wage data: {error}")
        return

    country = st.selectbox("Country", countries, key="wage_country")
    cities = available_cities(wage_records, country)
    city = st.selectbox("Garment hub city", cities, key="wage_city")
    record = find_wage_record(wage_records, country, city)
    currency = record["currency"]
    entered_wage = st.number_input(
        f"Factory payout or manufacturing-unit wage ({currency} per month)",
        min_value=0.0,
        value=float(record["legal_minimum_wage"]),
        step=100.0,
        format="%.2f",
    )

    try:
        results = calculate_wage_comparison(entered_wage, record)
    except ValueError as error:
        st.error(f"Please enter a valid non-negative wage: {error}")
        return

    columns = st.columns(4, border=True)
    columns[0].metric("Legal minimum", f"{record['legal_minimum_wage']:,.2f} {currency}")
    columns[1].metric(
        "Estimated living wage",
        f"{record['estimated_living_wage']:,.2f} {currency}",
    )
    columns[2].metric("Entered wage", f"{results['entered_wage']:,.2f} {currency}")
    columns[3].metric("Living-wage gap", f"{results['living_wage_gap_percentage']:.2f}%")

    st.write(
        f"Difference from legal minimum: "
        f"{results['difference_from_legal_minimum']:,.2f} {currency}"
    )
    st.write(
        f"Difference from estimated living wage: "
        f"{results['difference_from_estimated_living_wage']:,.2f} {currency}"
    )
    with st.expander("How is the living-wage gap calculated?"):
        st.markdown(
            "`((estimated living wage - entered wage) / estimated living wage) * 100`. "
            "A positive percentage means the entered wage is below the estimate; "
            "a negative percentage means it is above the estimate."
        )


def render_trade_analysis() -> None:
    """Render Module B, including model diagnostics and a what-if input."""
    st.header("Garment export predictive analytics", icon=":material/monitoring:")
    st.caption("This is a regression demonstration based entirely on fictional mock data.")

    try:
        trade_data = get_trade_data()
        model, metrics = train_trade_model(trade_data)
    except (FileNotFoundError, ValueError) as error:
        st.error(f"Could not load or model trade data: {error}")
        return

    st.warning(
        "The model uses fictional mock data and is not a real economic forecast. "
        "Regression and correlation can show associations, but they do not prove causation."
    )
    st.write(
        "The prototype uses tariff rate, labor cost, and EU trade preference as inputs "
        "to estimate total garment export volume in USD."
    )

    metric_columns = st.columns(2, border=True)
    metric_columns[0].metric("Training R-squared", f"{metrics['r2']:.3f}")
    metric_columns[1].metric("Training mean absolute error", f"${metrics['mae']:,.0f}")
    st.caption("These are in-sample demonstration metrics, not evidence of forecast accuracy.")

    export_chart = (
        trade_data.pivot(index="year", columns="country", values=TRADE_TARGET)
        .reset_index()
        .sort_values("year")
    )
    with st.container(border=True):
        st.subheader("Mock export volume by country and year")
        st.line_chart(
            export_chart,
            x="year",
            y=sorted(trade_data["country"].unique()),
            y_label="Export volume (USD)",
            x_label="Year",
            height=340,
        )
        st.caption("This chart shows fictional values and is not a historical economic series.")

    coefficient_data = pd.DataFrame(
        {"feature": TRADE_FEATURES, "coefficient": model.coef_}
    )
    with st.expander("Prototype model details"):
        st.dataframe(coefficient_data, hide_index=True, width="stretch")
        st.write(f"Intercept: ${model.intercept_:,.0f}")
        st.dataframe(trade_data, hide_index=True, width="stretch")

    st.subheader("Demonstration prediction")
    st.caption("Enter hypothetical feature values to see the model's mock-data output.")
    prediction_columns = st.columns(3)
    tariff_rate = prediction_columns[0].number_input(
        "Tariff rate (%)", min_value=0.0, value=10.0, step=0.1
    )
    labor_cost = prediction_columns[1].number_input(
        "Labor cost index", min_value=0.0, value=105.0, step=1.0
    )
    eu_trade_preference = prediction_columns[2].number_input(
        "EU trade preference (0-1)", min_value=0.0, max_value=1.0, value=0.70, step=0.01
    )

    if st.button("Calculate demonstration prediction"):
        prediction_input = pd.DataFrame(
            [[tariff_rate, labor_cost, eu_trade_preference]], columns=TRADE_FEATURES
        )
        predicted_volume = float(model.predict(prediction_input)[0])
        if predicted_volume < 0:
            st.error("The model returned a negative volume, so this output is not meaningful.")
        else:
            st.metric("Predicted export volume (mock estimate)", f"${predicted_volume:,.0f}")


def format_usd(amount: float, currency: str, exchange_data: dict[str, object]) -> str:
    """Format a local amount as USD, or return a readable unavailable label."""
    try:
        return f"${local_to_usd(amount, currency, exchange_data):,.2f}"
    except ValueError:
        return "Unavailable"


def render_country_profile(country: str, city: str) -> None:
    """Render country-specific context and a properly attributed placeholder image."""
    content = COUNTRY_CONTENT[country]
    st.header("Country profile", icon=":material/public:")
    image_column, profile_column = st.columns([0.9, 1.6], gap="large")
    with image_column:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="country-placeholder">
                    <div class="placeholder-kicker">Selected country</div>
                    <div class="placeholder-title">{escape(country)}</div>
                    <div class="placeholder-city">{escape(city)} garment hub</div>
                    <div class="placeholder-mark">IMAGE PLACEHOLDER</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(content["image_credit"])
            st.markdown(f"[Verify image context and credit]({content['image_source']})")
    with profile_column:
        st.subheader(f"{country}'s apparel economy")
        st.write(content["profile"])
        st.markdown(f"**Selected hubs:** {content['hubs']}")
        st.caption(f"Context reference: {content['context_source']}")


def render_timeline(country: str) -> None:
    """Render concise country-specific events with source links."""
    st.header("Historical timeline", icon=":material/history:")
    st.caption("Short original descriptions are provided for context; source pages contain the full material.")
    for event in TIMELINES[country]:
        with st.container(border=True):
            year_column, event_column = st.columns([0.18, 1], vertical_alignment="top")
            year_column.markdown(f"### {event['year']}")
            event_column.markdown(f"**{event['title']}**")
            event_column.write(event["description"])
            event_column.caption(f"Source: {event['source_name']}")
            event_column.markdown(f"[Open source]({event['source_url']})")


def render_country_sources(country: str) -> None:
    """Render manually curated research for the selected country."""
    st.header("News and historical sources", icon=":material/library_books:")
    st.caption("External background research, separate from the fictional datasets. This app performs no scraping.")
    st.info(
        "News links and statistics should be checked for updates. Summaries are original and do not reproduce copyrighted article text.",
        icon=":material/info:",
    )
    for source in NEWS_SOURCES[country]:
        with st.container(border=True):
            st.markdown(f"**{source['source_name']}**")
            st.markdown(f"### {source['article_title']}")
            st.caption(f"{source['publication_date']} · {source['topic']}")
            st.write(source["short_summary"])
            st.markdown(f"[Open source]({source['source_url']})")


def render_currency_comparison(
    record: dict[str, object], exchange_data: dict[str, object]
) -> None:
    """Show local values first and their explicitly dated USD equivalents."""
    currency = str(record["currency"])
    try:
        preview = calculate_wage_comparison(st.session_state.get("entered_wage", 0), record)
    except ValueError:
        preview = {
            "entered_wage": 0.0,
            "difference_from_legal_minimum": 0.0,
            "difference_from_estimated_living_wage": 0.0,
        }
    local_values = {
        "Legal minimum wage": float(record["legal_minimum_wage"]),
        "Estimated living wage": float(record["estimated_living_wage"]),
        "Entered wage": float(preview["entered_wage"]),
        "Food cost": float(record["average_food_cost"]),
        "Housing cost": float(record["average_housing_cost"]),
        "Difference from legal minimum": float(preview["difference_from_legal_minimum"]),
        "Difference from estimated living wage": float(preview["difference_from_estimated_living_wage"]),
    }
    comparison = pd.DataFrame(
        {
            "Metric": list(local_values),
            f"Local value ({currency})": [f"{value:,.2f}" for value in local_values.values()],
            "USD equivalent": [format_usd(value, currency, exchange_data) for value in local_values.values()],
        }
    )
    st.header("Currency comparison", icon=":material/currency_exchange:")
    st.dataframe(comparison, hide_index=True, width="stretch")
    live_label = "live cached rate" if exchange_data["live"] else "fallback/mock rate"
    st.caption(
        f"USD conversion uses the {live_label} from {exchange_data['source']} on {exchange_data['rate_date']}. "
        "Exchange-rate conversion is not purchasing-power parity and does not imply equivalent living standards."
    )


def render_unified_wage_calculator(
    record: dict[str, object], exchange_data: dict[str, object]
) -> None:
    """Render the existing wage math with local and USD output."""
    currency = str(record["currency"])
    st.header("Wage calculator", icon=":material/payments:")
    st.caption("The calculation reuses app/wage_calculator.py and uses fictional wage benchmarks.")
    entered_wage = st.number_input(
        f"Factory payout or manufacturing-unit wage ({currency} per month)",
        min_value=0.0,
        step=100.0,
        key="entered_wage",
    )
    try:
        results = calculate_wage_comparison(entered_wage, record)
    except ValueError as error:
        st.error(f"Please enter a valid non-negative wage: {error}")
        return

    values = [
        ("Entered wage", results["entered_wage"]),
        ("Legal minimum wage", float(record["legal_minimum_wage"])),
        ("Estimated living wage", float(record["estimated_living_wage"])),
        ("Difference from legal minimum", results["difference_from_legal_minimum"]),
        ("Difference from estimated living wage", results["difference_from_estimated_living_wage"]),
    ]
    metric_columns = st.columns(5, border=True)
    for column, (label, value) in zip(metric_columns, values):
        column.metric(label, f"{value:,.2f} {currency}", border=True)
    st.metric("Living-wage gap percentage", f"{results['living_wage_gap_percentage']:.2f}%", border=True)
    st.dataframe(
        pd.DataFrame(
            {
                "Metric": [label for label, _ in values],
                f"Local value ({currency})": [f"{value:,.2f}" for _, value in values],
                "USD equivalent": [format_usd(value, currency, exchange_data) for _, value in values],
            }
        ),
        hide_index=True,
        width="stretch",
    )
    with st.expander("How the living-wage gap is calculated"):
        st.write(
            "The gap is ((estimated living wage - entered wage) / estimated living wage) * 100. "
            "A positive result means the entered wage is below the estimate."
        )


def render_unified_trade_analysis(country: str) -> None:
    """Render country-specific and cross-country trade charts plus the existing model."""
    st.header("Trade analytics", icon=":material/monitoring:")
    st.warning(
        "Educational demonstration only: trade_data.csv is fictional mock data. "
        "Regression and correlation do not prove causation and this is not a real forecast.",
        icon=":material/warning:",
    )
    try:
        trade_data = get_trade_data()
        model, metrics = train_trade_model(trade_data)
    except (FileNotFoundError, ValueError) as error:
        st.error(f"Could not load or model trade data: {error}")
        return

    country_data = trade_data[trade_data["country"] == country].sort_values("year")
    cross_country = (
        trade_data.pivot(index="year", columns="country", values=TRADE_TARGET)
        .reset_index()
        .sort_values("year")
    )
    chart_columns = st.columns(2)
    with chart_columns[0]:
        with st.container(border=True):
            st.subheader(f"{country} export volume")
            st.line_chart(country_data.set_index("year")[TRADE_TARGET], height=280)
    with chart_columns[1]:
        with st.container(border=True):
            st.subheader("Cross-country export volume")
            st.line_chart(cross_country.set_index("year"), height=280)

    for feature, label in [
        ("tariff_rate", "Tariff rate"),
        ("labor_cost", "Labor-cost index"),
        ("eu_trade_preference", "EU trade-preference score"),
    ]:
        feature_chart = trade_data.pivot(index="year", columns="country", values=feature).sort_index()
        with st.container(border=True):
            st.subheader(label)
            st.line_chart(feature_chart, height=220)

    metric_columns = st.columns(2, border=True)
    metric_columns[0].metric("Training R-squared", f"{metrics['r2']:.3f}")
    metric_columns[1].metric("Training mean absolute error", f"${metrics['mae']:,.0f}")
    st.caption("These are in-sample demonstration metrics, not evidence of forecast accuracy.")
    with st.expander("Regression details and prediction interface"):
        st.write("Features: tariff_rate, labor_cost, and eu_trade_preference. Target: total_export_volume_usd.")
        st.dataframe(
            pd.DataFrame({"feature": TRADE_FEATURES, "coefficient": model.coef_}),
            hide_index=True,
            width="stretch",
        )
        prediction_columns = st.columns(3)
        tariff_rate = prediction_columns[0].number_input("Tariff rate (%)", min_value=0.0, value=10.0, step=0.1, key="trade_tariff")
        labor_cost = prediction_columns[1].number_input("Labor-cost index", min_value=0.0, value=105.0, step=1.0, key="trade_labor")
        eu_trade_preference = prediction_columns[2].number_input("EU trade preference (0-1)", min_value=0.0, max_value=1.0, value=0.70, step=0.01, key="trade_preference")
        if st.button("Calculate demonstration prediction", key="trade_predict"):
            prediction_input = pd.DataFrame([[tariff_rate, labor_cost, eu_trade_preference]], columns=TRADE_FEATURES)
            predicted_volume = float(model.predict(prediction_input)[0])
            if predicted_volume < 0:
                st.error("The model returned a negative volume, so this output is not meaningful.")
            else:
                st.metric("Predicted export volume (mock estimate)", f"${predicted_volume:,.0f}")


def render_sources_and_methodology(country: str, exchange_data: dict[str, object]) -> None:
    """Close the page with provenance, conversion, and limitations."""
    st.header("Sources and methodology", icon=":material/menu_book:")
    with st.expander("Data, currency, model, and copyright notes", expanded=True):
        st.markdown(
            "- `wage_data.csv` and `trade_data.csv` are fictional demonstration datasets.\n"
            "- Local currency is primary; USD values use a cached exchange-rate response when available.\n"
            "- The current currency source is shown beside the comparison table, with mock fallbacks labeled.\n"
            "- USD conversion is not purchasing-power parity or a comparison of living standards.\n"
            "- The regression is small, in-sample, and educational; association does not prove causation.\n"
            "- External sources are manually curated and separate from all fictional values.\n"
            "- No copyrighted article text is copied. No local image is bundled without verified licensing."
        )
    st.caption(
        f"Selected country: {country}. Exchange-rate source: {exchange_data['source']}; date: {exchange_data['rate_date']}."
    )


def main() -> None:
    st.set_page_config(
        page_title="South Asia Fashion Dashboard",
        page_icon=":material/insights:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_dashboard_style()
    with st.sidebar:
        st.markdown("## South Asia Fashion Dashboard")
        st.caption("South Asia fashion intelligence")
        st.divider()
        st.markdown("### About this project")
        st.caption(
            "An educational dashboard for exploring wages, apparel trade, and external context "
            "across Bangladesh, India, and Pakistan."
        )
        st.caption("Version 1.0 · Mock-data prototype")

    st.markdown("# South Asia Fashion Dashboard")
    st.markdown(
        "Explore garment wages, cost-of-living benchmarks, export relationships, and verified external context for Bangladesh, India, and Pakistan."
    )
    st.warning(
        "Fictional-data prototype: all wages, costs, trade values, charts, and model outputs "
        "are mock values and are not suitable for real-world decisions.",
        icon=":material/warning:",
    )

    country_column, city_column = st.columns(2)
    country = country_column.selectbox("Country", list(COUNTRY_CONTENT), key="country_selector")
    city = city_column.selectbox("Garment hub city", COUNTRY_CONTENT[country]["cities"], key="city_selector")
    wage_records = load_wage_data()
    try:
        record = find_wage_record(wage_records, country, city)
    except ValueError:
        st.error(f"No wage record is available for {country}, {city}.")
        st.stop()
    selection_key = f"{country}:{city}"
    if st.session_state.get("wage_selection") != selection_key:
        st.session_state["wage_selection"] = selection_key
        st.session_state["entered_wage"] = float(record["legal_minimum_wage"])
    exchange_data = get_exchange_rates()

    render_country_profile(country, city)
    render_timeline(country)
    render_country_sources(country)
    render_currency_comparison(record, exchange_data)
    render_unified_wage_calculator(record, exchange_data)
    render_unified_trade_analysis(country)
    render_sources_and_methodology(country, exchange_data)


if __name__ == "__main__":
    main()