import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="IMC Prosperity - Round 1 Dashboard", layout="wide")
st.title("IMC Prosperity - Round 1 Dashboard")
round_displayed = st.selectbox("Choose round:", [1, 2])

@st.cache_data
def load_data(round):
    prices_dfs = []
    prices_dfs.append(pd.read_csv(f"DASHBOARD/prices_round_{round}_day_{round_displayed-1}.csv", sep=";"))
    prices_dfs.append(pd.read_csv(f"DASHBOARD/prices_round_{round}_day_{round_displayed-2}.csv", sep=";"))
    prices_dfs.append(pd.read_csv(f"DASHBOARD/prices_round_{round}_day_{round_displayed-3}.csv", sep=";"))
    # Load Trades
    trades_dfs = []
    trades_dfs.append(pd.read_csv(f"DASHBOARD/trades_round_{round}_day_{round_displayed-1}.csv", sep=";"))
    trades_dfs.append(pd.read_csv(f"DASHBOARD/trades_round_{round}_day_{round_displayed-2}.csv", sep=";"))
    trades_dfs.append(pd.read_csv(f"DASHBOARD/trades_round_{round}_day_{round_displayed-3}.csv", sep=";"))

    return prices_dfs, trades_dfs

product = st.selectbox("Select product:", ["Ash-coated osmium", "Intarian pepper root"])
day = st.selectbox("Select day:", [round_displayed-1, round_displayed-2, round_displayed-3])
prices_dfs, trades_dfs = load_data(round=round_displayed)

# Sidebar for options
with st.sidebar:
    st.header("Settings")
    circle_size = st.slider("Circle size", min_value=0, max_value=50, step=1, value=15)
    circle_opacity = st.slider("Circle opacity", min_value=0, max_value=10, step=1, value=7)

if product == "Ash-coated osmium":
    st.header("Market data for ash-coated osmium")
    prices_df = prices_dfs[-(day-round_displayed+1)]
    prices_df = prices_df[(prices_df["product"] == "ASH_COATED_OSMIUM")].ffill()
    trades_df = trades_dfs[-(day-round_displayed+1)]
    trades_df = trades_df[trades_df["symbol"] == "ASH_COATED_OSMIUM"]

    # Plot market data
    fig = go.Figure()

    # Bid line
    fig.add_trace(go.Scatter(
        x=prices_df["timestamp"], 
        y=prices_df["bid_price_1"], 
        name="Bid Price",
        mode="lines",
        line=dict(color="blue")
    ))

    # Ask line
    fig.add_trace(go.Scatter(
        x=prices_df["timestamp"], 
        y=prices_df["ask_price_1"], 
        name="Ask Price",
        mode="lines",
        line=dict(color="red")
    ))

    # WallMid - averaging bid/asks from the bigger liquidity providers in the 2nd columns
    wall_mid = (prices_df["bid_price_2"] + prices_df["ask_price_2"])/2
    fig.add_trace(go.Scatter(
        x = prices_df["timestamp"],
        y = wall_mid,
        name="WallMid",
        mode="lines",
        line=dict(color="black")
    ))

   # 1. Ensure wall_mid has the timestamp associated with it for the merge
    # We create a temporary DataFrame so we have a 'timestamp' column to join on
    wall_df = pd.DataFrame({
        "timestamp": prices_df["timestamp"],
        "mid_price": (prices_df["bid_price_2"] + prices_df["ask_price_2"]) / 2
    })

    # 2. Merge - This aligns every trade with the WallMid at that exact moment
    merged = trades_df.merge(wall_df, on="timestamp", how="left")

    # 3. Create the 'Trade' trace using the MERGED dataframe
    # This ensures x and y are the same length
    fig.add_trace(go.Scatter(
        x=merged["timestamp"], 
        y=merged["price"],  # Use 'merged' here, not trades_df
        name="Trades",
        mode="markers",
        marker=dict(
            # Visualizing size based on quantity
            size=circle_size * merged["quantity"] / 10, 
            opacity=circle_opacity / 10,
            # Bonus: Color trades green if they happened ABOVE the wall mid
            color=["green" if p > m else "red" for p, m in zip(merged["price"], merged["mid_price"])]
        )
    )) 

    st.plotly_chart(fig)
    
    # Stats
    st.write(f"Mean: {wall_mid.mean()}")
    st.write(f"Standard deviation: {wall_mid.std()}")

    st.header("Normalised bid/ask with WallMid")
    fig2 = go.Figure()

    # Normalised bid line
    fig2.add_trace(go.Scatter(
        x=prices_df["timestamp"],
        y=prices_df["bid_price_1"] - wall_mid,
        name="Normalised bid price",
        mode="lines",
        line=dict(color="blue")
    ))
    
    # Normalised bid line from big liquidity providers
    fig2.add_trace(go.Scatter(
        x=prices_df["timestamp"],
        y=prices_df["bid_price_2"] - wall_mid,
        name="Normalised bid price (big liquidity provider)",
        mode="lines",
        line=dict(color="cyan")
    ))

    # Normalised ask line
    fig2.add_trace(go.Scatter(
        x=prices_df["timestamp"], 
        y=prices_df["ask_price_1"] - wall_mid, 
        name="Normalised ask price",
        mode="lines",
        line=dict(color="red")
    ))
    
    # Normalised ask line from big liquidity providers
    fig2.add_trace(go.Scatter(
        x=prices_df["timestamp"],
        y=prices_df["ask_price_2"] - wall_mid,
        name="Normalised ask price (big liquidity provider)",
        mode="lines",
        line=dict(color="orange")
    ))

    st.plotly_chart(fig2)

elif product == "Intarian pepper root":
    st.header("Market data for Intarian pepper root")
    prices_df = prices_dfs[-(day-round_displayed+1)]
    prices_df = prices_df[(prices_df["product"] == "INTARIAN_PEPPER_ROOT")].ffill()
    trades_df = trades_dfs[-(day-round_displayed+1)]
    trades_df = trades_df[trades_df["symbol"] == "INTARIAN_PEPPER_ROOT"]

    # Plot market data
    fig = go.Figure()

    # Bid line
    fig.add_trace(go.Scatter(
        x=prices_df["timestamp"], 
        y=prices_df["bid_price_1"], 
        name="Bid Price",
        mode="lines",
        line=dict(color="blue")
    ))

    # Ask line
    fig.add_trace(go.Scatter(
        x=prices_df["timestamp"], 
        y=prices_df["ask_price_1"], 
        name="Ask Price",
        mode="lines",
        line=dict(color="red")
    ))

    # WallMid - averaging bid/asks from the bigger liquidity providers in the 2nd columns
    wall_mid = (prices_df["bid_price_2"] + prices_df["ask_price_2"])/2
    fig.add_trace(go.Scatter(
        x = prices_df["timestamp"],
        y = wall_mid,
        name="WallMid",
        mode="lines",
        line=dict(color="black")
    ))

    # 1. Ensure wall_mid has the timestamp associated with it for the merge
    # We create a temporary DataFrame so we have a 'timestamp' column to join on
    wall_df = pd.DataFrame({
        "timestamp": prices_df["timestamp"],
        "mid_price": (prices_df["bid_price_2"] + prices_df["ask_price_2"]) / 2
    })

    # 2. Merge - This aligns every trade with the WallMid at that exact moment
    merged = trades_df.merge(wall_df, on="timestamp", how="left")

    # 3. Create the 'Trade' trace using the MERGED dataframe
    # This ensures x and y are the same length
    fig.add_trace(go.Scatter(
        x=merged["timestamp"], 
        y=merged["price"],  # Use 'merged' here, not trades_df
        name="Trades",
        mode="markers",
        marker=dict(
            # Visualizing size based on quantity
            size=circle_size * merged["quantity"] / 10, 
            opacity=circle_opacity / 10,
            # Bonus: Color trades green if they happened ABOVE the wall mid
            color=["green" if p > m else "red" for p, m in zip(merged["price"], merged["mid_price"])]
        )
    ))

    st.plotly_chart(fig)

    # Stats
    st.write(f"Mean: {wall_mid.mean()}")
    st.write(f"Standard deviation: {wall_mid.std()}")

    st.header("Normalised bid/ask with WallMid")
    fig2 = go.Figure()

    # Normalised bid line
    fig2.add_trace(go.Scatter(
        x=prices_df["timestamp"],
        y=prices_df["bid_price_1"] - wall_mid,
        name="Normalised bid price",
        mode="lines",
        line=dict(color="blue")
    ))

    # Normalised bid line from big liquidity providers
    fig2.add_trace(go.Scatter(
        x=prices_df["timestamp"],
        y=prices_df["bid_price_2"] - wall_mid,
        name="Normalised bid price (big liquidity provider)",
        mode="lines",
        line=dict(color="cyan")
    ))

    # Normalised ask line
    fig2.add_trace(go.Scatter(
        x=prices_df["timestamp"], 
        y=prices_df["ask_price_1"] - wall_mid, 
        name="Normalised ask price",
        mode="lines",
        line=dict(color="red")
    ))
    
    # Normalised ask line from big liquidity providers
    fig2.add_trace(go.Scatter(
        x=prices_df["timestamp"],
        y=prices_df["ask_price_2"] - wall_mid,
        name="Normalised ask price (big liquidity provider)",
        mode="lines",
        line=dict(color="orange")
    ))



    st.plotly_chart(fig2)