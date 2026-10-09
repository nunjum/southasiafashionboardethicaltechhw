# South Asia Fashion Dashboard

This educational prototype is a single unified dashboard for exploring fictional wage and garment-trade data in Bangladesh, India, and Pakistan, alongside manually curated external background sources.

## Setup

Use Python 3.11 or newer. Create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the dashboard

From the project root, run:

```bash
streamlit run app/dashboard.py
```

Streamlit will print a local browser address. Open that address to use the dashboard.

## Unified dashboard sections

The page updates from one country and city selection. It presents, in order:

1. Project introduction and the persistent fictional-data warning.
2. Country and city selectors.
3. A country-specific profile with a credited placeholder when a verified local image is unavailable.
4. A country-specific historical timeline.
5. Manually curated external news and research sources.
6. Local-currency values and dated USD equivalents.
7. The wage calculator.
8. Country-specific and cross-country trade charts plus the regression demonstration.
9. Sources, methodology, and limitations.

## Wage calculator

1. Select a country and garment-hub city.
2. Enter a monthly factory payout or manufacturing-unit wage in the displayed local currency.
3. Review the legal minimum wage, estimated living wage, entered wage, and living-wage gap percentage.

The gap formula is:

```text
((estimated_living_wage - entered_wage) / estimated_living_wage) * 100
```

## Trade analytics

The model uses `tariff_rate`, `labor_cost`, and `eu_trade_preference` to demonstrate a linear regression against `total_export_volume_usd`. Enter hypothetical feature values to view a model-generated demonstration value.

The trade section includes country-specific and cross-country export-volume charts, tariff-rate, labor-cost, and EU-trade-preference charts, model diagnostics, and a prediction form.

## News and sources

The dashboard contains manually entered links to verified UN, ILO, World Bank, WTO, RMG Sustainability Council, and Better Work pages. The app does not scrape websites or reproduce copyrighted article text. It displays source names, titles, dates, links, topics, and original short summaries. Links and statistics should be checked for updates.

## Design and navigation

The dashboard uses a wide layout, a dark navy and cream visual system with burgundy accents, a sidebar with project context, bordered metric cards, expanders, and responsive chart sections. Country-specific content is stored in reusable data modules rather than duplicated in the page.

## Important limitations

- `data/wage_data.csv` and `data/trade_data.csv` contain fictional mock data, not official statistics.
- The regression output is not a real economic forecast and is not suitable for business, policy, investment, wage, or sourcing decisions.
- The dataset is very small and has no claim of representing actual country, city, tariff, labor-cost, preference, or export relationships.
- Correlation and regression describe associations in the supplied data; they do not prove causation.
- The displayed model metrics are in-sample demonstration metrics, not evidence of predictive accuracy.
- External source links provide background research only and are separate from the fictional datasets.
- Exchange rates are cached from a public endpoint when available; fallback/mock rates are labeled with their date and source. USD conversion is not purchasing-power parity.
- Country images are not bundled unless their public-domain, Creative Commons, or attribution terms can be verified. Current country visuals are clean placeholders documented in `assets/README.md`.