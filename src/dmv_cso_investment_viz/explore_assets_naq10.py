import pandas as pd
import plotly.express as px
#read the clean csv
df=pd.read_csv("clean/naq10_clean.csv")
#get the current prices
current_prices=df[(df["price_basis"]=="current")&(~df["is_aggregate"])].copy()

current_prices["quarter_label"]=pd.to_datetime(current_prices["quarter"]).dt.to_period("Q").astype(str)
current_prices["asset_name"]=current_prices["asset"].str.split("\\(").str[0]


#Create an exploratory line chart

fig=px.line(current_prices,
            x="quarter_label",
            y="value",
            color="asset_name",
            title="Investment by asset type",
            labels={"value":"Euro million","quarter_label":"Quarter","asset_name":"Asset type"},
            template="plotly_white")

#uodate with hovermode
fig.update_layout(hovermode="x unified")
#write to html
fig.write_html("exploratory_naq10.html",include_plotlyjs=True)
fig.show()