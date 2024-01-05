import json
import os
import re

import google.auth.transport.requests
import google.oauth2.id_token
import plotly.express as px
import polars as pl
import streamlit as st
import requests
from loguru import logger


ENDPOINT_URL = os.environ["ENDPOINT_URL"]

st.set_page_config(layout="centered", page_title="Time-Varing Beta Chart")
st.title("Time-Varing Beta Chart")
st.write("時変ベータ値（対日経平均）をカルマンフィルタによって推定してプロットします")

stock_code = st.text_input("銘柄コードを入力してください（半角英数字4桁）")
button = st.button("実行")

st.markdown("---")

@st.cache_data(show_spinner=False, ttl=600)
def authorize(audience: str) -> dict[str, str]:
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)
    headers = {"Authorization": f"Bearer {id_token}"}
    return headers

@st.cache_data(show_spinner="in progress (please wait about 30 seconds) ...", ttl=600)
def fetch(url: str, params: dict[str, str], headers: dict[str, str]) -> dict:
    resp = requests.get(url, params=params, headers=headers)
    data = json.loads(resp.text)
    return data

try:
    if button:
        logger.info(f"input_value: {stock_code}")

        if not bool(re.search("^[0-9][0-9ACDFGHJKLMNPRSTUWXY][0-9][0-9ACDFGHJKLMNPRSTUWXY]$", stock_code)):
            st.error("有効な銘柄コードを入力してください")
            st.stop()

        headers = authorize(ENDPOINT_URL)
        data = fetch(ENDPOINT_URL, params={"stock_code": stock_code}, headers=headers)
        if "message" in data:
            st.error("入力した銘柄コードの銘柄が存在しないか、または存在する株価データが少ないためベータ値を推定できませんでした")
            st.stop()

        beta_filtering = (
            pl.DataFrame(data["filtering"])
            .with_columns(date=pl.col("date").str.strptime(pl.Date, "%Y-%m-%d"))
            .slice(50)
            .melt(
                id_vars="date",
                value_vars=["estimated", "lower", "upper"],
                variable_name="type",
                value_name="beta"
            )
        )
        beta_smoothing = (
            pl.DataFrame(data["smoothing"])
            .with_columns(date=pl.col("date").str.strptime(pl.Date, "%Y-%m-%d"))
            .slice(50)
            .melt(
                id_vars="date",
                value_vars=["estimated", "lower", "upper"],
                variable_name="type",
                value_name="beta"
            )
        )
        stock_close = (
            pl.DataFrame(data["close"])
            .with_columns(date=pl.col("date").str.strptime(pl.Date, "%Y-%m-%d"))
            .slice(50)
        )

        p1 = px.line(
            beta_filtering, x="date", y="beta", color="type",
            title="time-varing beta (filtered); center: estimated (mean), upper and lower: 95%CI"
        )
        p1.update_xaxes(tickformat="%Y/%m/%d")
        p1.update_layout(showlegend=False)

        p2 = px.line(
            beta_smoothing, x="date", y="beta", color="type",
            title="time-varing beta (smoothed); center: estimated (mean), upper and lower: 95%CI"
        )
        p2.update_xaxes(tickformat="%Y/%m/%d")
        p2.update_layout(showlegend=False)

        p3 = px.line(
            stock_close, x="date", y="close_stock",
            title="stock price (close)"
        )
        p3.update_xaxes(tickformat="%Y/%m/%d")

        st.write(
            f'[as of {data["filtering"]["date"][-1]}] {round(data["filtering"]["estimated"][-1], 3)} (95% CI: {round(data["filtering"]["lower"][-1], 3)} - {round(data["filtering"]["upper"][-1], 3)})'
        )
        st.plotly_chart(p1)
        st.plotly_chart(p2)
        st.plotly_chart(p3)

except Exception as e:
    st.error("何らかのエラーが発生しました")
    logger.exception(e)
    st.stop()
