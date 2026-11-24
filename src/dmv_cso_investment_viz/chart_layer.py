import pandas as pd
import plotly.graph_objects as go

def format_quarters(quarters):
    # Convert a list of quarters to a string format "YYYY-QX"
    return pd.to_datetime(quarters).dt.to_period("Q").astype(str)

def build_line_trace(df, column, name, color, dash, visible):
    return go.Scatter(
        x = format_quarters(df["quarter"]),
        y = df[column],
        mode = "lines",
        name = name,
        line = dict(color = color, dash = dash),
        visible = visible
    )

def add_overlay_lines(fig, df):
    # add gdp $ gnp ratio lines fo rboth current prices and constant prices
    current = df[df["price_basis"] == "current"]
    constant = df[df["price_basis"] == "constant"]

    # add lines for current prices
    fig.add_trace(build_line_trace(current, "intangible_gnp_share", "Intangible % of GNP (Domestic)", "#111827", "solid", True))
    fig.add_trace(build_line_trace(current, "intangible_gdp_share", "Intangible % of GDP (Headline)", "#4B5563", "dash", True))

    # Constant volumes lines (revealed when the user clicks the 'Volumes' toggle)
    fig.add_trace(build_line_trace(constant, "intangible_gnp_share", "Intangible % of GNP (Domestic)", "#111827", "solid", False))
    fig.add_trace(build_line_trace(constant, "intangible_gdp_share", "Intangible % of GDP (Headline)", "#4B5563", "dash", False))

def configure_axes_and_sliders(fig, df = None):
    # Configure the axes and add a range slider for the x-axis
    if df is not None:
        all_quarters = sorted(format_quarters(df["quarter"]).unique())
    else:
        all_quarters = sorted({x for trace in fig.data for x in trace.x})

    fig.update_layout(
        xaxis=dict(
            title = "Quarter",
            type = "category",
            categoryorder = "array",
            categoryarray = all_quarters,
            rangeslider = dict(
                visible = True,
                thickness = 0.05,
            ),
        ),
        yaxis2=dict(
            title = "Intangible Share (% of GDP/GNP)",
            overlaying = "y",
            side = "right",
            showgrid = False,
            rangemode = "tozero",
       ),
        hovermode = "x unified"
    )

def add_annotations(fig, df):
    # Add annotations for the last data points of each line
    curr = df[df["price_basis"] == "current"].copy()
    curr["q_label"] = format_quarters(curr["quarter"])
    curr = curr.set_index("q_label")

    milestones = [
        ("2015Q4", "<b>2015 IP Onshoring</b><br>Multinationals relocate IP assets", -65, -45),
        ("2019Q4", "<b>IP & Aircraft Leasing Surge</b><br>Global balance-sheet transfers", -60, -35),
    ]

    for q_label, text, ax, ay in milestones:
        if q_label in curr.index:
            fig.add_annotation(
                x=q_label,
                y=curr.loc[q_label, "intangible_gnp_share"],
                yref="y2",
                text=text,
                showarrow=True,
                arrowhead=2,
                ax=ax,
                ay=ay,
                bgcolor="rgba(255, 255, 255, 0.92)",
                bordercolor="#111827",
                borderwidth=1,
                font=dict(size=11, color="#111827")
            )

def apply_layer_to_fig(fig, df):
   # Apply a single layer to the figure
    add_overlay_lines(fig, df)
    configure_axes_and_sliders(fig, df)  
    add_annotations(fig, df)  
    return fig