import pandas as pd
import plotly.express as px

# 1. Load the merged data you just generated
df = pd.read_csv("clean/merged_chart_data.csv")

# 2. Filter to Current Prices to show the raw monetary divergence
curr = df[df["price_basis"] == "current"].copy()

# Format the date back into readable 'YYYYQ#' labels (e.g. '2015Q4')
curr["quarter_label"] = pd.to_datetime(curr["quarter"]).dt.to_period("Q").astype(str)

# 3. Create the exploratory line chart
fig = px.line(
    curr,
    x="quarter_label",
    y=["GDP", "GNP"],
    title="Exploratory Plot (NAQ03): Divergence Between Irish GDP and GNP (€ Million)",
    labels={"value": "Euro Million", "quarter_label": "Quarter", "variable": "Indicator"},
    template="plotly_white"
)
fig.update_layout(hovermode="x unified")

# 4. Save it as an HTML file AND pop it open in your browser
fig.write_html("exploratory_gdp_gnp.html", include_plotlyjs=True)
fig.show()