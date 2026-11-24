from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

from chart_layer import apply_layer_to_fig

# resolve paths
ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "clean" / "merged_chart_data.csv"
OUTPUT_DIR = ROOT / "output"

# set colours
INTANGIBLE_COLOUR = "#1F6F8B"
TANGIBLE_COLOUR = "#D9D3C7"


# function for rolling shares
def rolling_shares(df):
    df = df.sort_values(["price_basis", "quarter"]).copy()
    by_basis = df.groupby("price_basis")

    intangible = by_basis["intangible"].transform(lambda s: s.rolling(4).sum())
    total = by_basis["total_invest"].transform(lambda s: s.rolling(4).sum())

    df["intangible_share_4q"] = 100 * intangible / total
    df["tangible_share_4q"] = 100 - df["intangible_share_4q"]

    return df


def _split_into_runs(d, cols):
    has_value = d[cols].notna()
    run_id = (has_value != has_value.shift()).cumsum()
    return [run for _, run in d[has_value].groupby(run_id[has_value])]


def format_quarters(quarter_series):
    """Match Person B's 'YYYYQ#' quarter format so both layers stack on the same X-axis."""
    return pd.to_datetime(quarter_series).dt.to_period("Q").astype(str)


def add_area_layers(fig, df):
    df = rolling_shares(df)

    trace_ids = {"current": [], "constant": []}

    def add(basis, trace):
        fig.add_trace(trace)
        trace_ids[basis].append(len(fig.data) - 1)

    for basis, shown in [("current", True), ("constant", False)]:
        rows = df[df["price_basis"] == basis]
        label = "current prices" if basis == "current" else "real volumes"

        for i, run in enumerate(_split_into_runs(rows, "intangible_share_4q")):
            first = i == 0
            q_labels = format_quarters(run["quarter"])

            add(
                basis,
                go.Scatter(
                    x=q_labels,
                    y=run["intangible_share_4q"],
                    name="Intangible assets",
                    legendgroup="intangible",
                    showlegend=first,
                    mode="lines",
                    line=dict(color=INTANGIBLE_COLOUR, width=1.5),
                    fill="tozeroy",
                    fillcolor=INTANGIBLE_COLOUR,
                    visible=shown,
                    customdata=run["intangible_share"],
                    hovertemplate=(
                        "%{x}<br> Intangible share (4-qtr): %{y:.1f}%"
                        "<br> This quarter alone: %{customdata:.1f}%"
                        f"<extra>{label}</extra>"
                    ),
                ),
            )

            add(
                basis,
                go.Scatter(
                    x=q_labels,
                    y=[100] * len(run),
                    name="Tangible assets",
                    legendgroup="tangible",
                    showlegend=first,
                    mode="lines",
                    line=dict(color=TANGIBLE_COLOUR, width=0),
                    fill="tonexty",
                    fillcolor=TANGIBLE_COLOUR,
                    visible=shown,
                    customdata=run["tangible_share"],
                    hovertemplate=(
                        "%{x}<br> Tangible share (4-qtr): %{customdata:.1f}%"
                        f"<extra>{label}</extra>"
                    ),
                ),
            )

    return trace_ids


def add_toggle(fig, area_traces, line_traces=None):
    line_traces = line_traces or {"current": [], "constant": []}

    current = set(area_traces["current"]) | set(line_traces["current"])
    volume = set(area_traces["constant"]) | set(line_traces["constant"])
    controlled = current | volume

    n = len(fig.data)
    show_current = [i in current or i not in controlled for i in range(n)]
    show_volume = [i in volume or i not in controlled for i in range(n)]

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0,
                y=1.12,
                xanchor="left",
                showactive=True,
                bgcolor="white",
                bordercolor="#999",
                buttons=[
                    dict(label="current prices", method="update", args=[{"visible": show_current}]),
                    dict(label="Real volumes", method="update", args=[{"visible": show_volume}]),
                ],
            )
        ]
    )


if __name__ == "__main__":
    df = pd.read_csv(DATA_FILE, parse_dates=["quarter"])
    fig = go.Figure()

    # stacked area layers (traces 0..k-1)
    area_traces = add_area_layers(fig, df)
    n_before_b = len(fig.data)

    # add GDP/GNP lines, right axis, annotations & slider
    fig = apply_layer_to_fig(fig, df)

    # adds 4 line traces in order: [curr_gnp, curr_gdp, const_gnp, const_gdp]
    line_traces = {
        "current": [n_before_b, n_before_b + 1],
        "constant": [n_before_b + 2, n_before_b + 3],
    }

    # wire the toggle button AFTER both layers are added so both switch together
    add_toggle(fig, area_traces, line_traces)

    fig.update_layout(
        template="simple_white",
        font=dict(family="Arial", size=13),
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="right",
            x=1.0,
        ),
        margin=dict(t=95, r=80),
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    fig.write_html(OUTPUT_DIR / "chart_area.html", include_plotlyjs=True)
    fig.show()
    print("Saved")