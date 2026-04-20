import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data
def load_customers() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "customers.csv")
    df["return_rate"] = df["total_returns"] / df["lifetime_orders"].clip(lower=1)
    return df


@st.cache_data
def load_items() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "items.csv")
    df["price_tier"] = df["price"].apply(
        lambda p: "high" if p > 150 else ("mid" if p >= 30 else "low")
    )
    return df


@st.cache_data
def load_history() -> pd.DataFrame:
    path = DATA_DIR / "returns_history.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def customer_to_dict(row: pd.Series) -> dict:
    return row.to_dict()


def item_to_dict(row: pd.Series) -> dict:
    return row.to_dict()
