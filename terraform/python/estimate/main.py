import re
from logging import DEBUG, getLogger

import google.cloud.logging
import numpy as np
import pandas_datareader.data as pdr
import polars as pl
import scipy as sp
from agraffe import Agraffe, Service
from fastapi import FastAPI

from kalman_filter import filtering, smoothing, reverse_loglik


logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logger = getLogger(__name__)
logger.setLevel(DEBUG)

app = FastAPI()
entry_point = Agraffe.entry_point(app, Service.google_cloud_functions)

MARKET_CODE_STOOQ = "^NKX"
START_DATE = "2001-01-01"
THRESHOLD_DATA_LEN = 50

def validate_stock_code(x: str) -> bool:
    return bool(re.search("^[0-9][0-9ACDFGHJKLMNPRSTUWXY][0-9][0-9ACDFGHJKLMNPRSTUWXY]$", x))

@app.get("/")
def main(stock_code: str):
    stock_code_stooq = f"{stock_code}.JP"
    try:
        if not validate_stock_code(stock_code):
            return {"Message": "Not valid stock code"}

        # 株価の取得
        stock_code_stooq = f"{stock_code}.JP"
        stock = pdr.DataReader(stock_code_stooq, data_source="stooq", start=START_DATE)
        # 正しく推定できないため。存在しないstock_codeの場合は0行なのでここに含まれる
        if stock.shape[0] <= THRESHOLD_DATA_LEN:
            return {"Message": f"Can not be estimated time-varing beta, because of either length of stock price data <= {THRESHOLD_DATA_LEN} or not existing stock code"}

        df_stock = pl.from_pandas(stock.reset_index())
        df_stock = (
            df_stock
            .sort("Date")
            # データソース的に数レコードだけ株価がnullの日付があるが、nullの場合は削除する
            .filter(pl.col("Close").is_not_null())
            .with_columns(
                Date=pl.col("Date").dt.date(),
                ret=(pl.col("Close").log() - pl.col("Close").shift(1).log())*100
            )
            .slice(offset=1)
        )
        market = pdr.DataReader(MARKET_CODE_STOOQ, data_source="stooq", start=START_DATE, end="2023-12-28")
        df_market = pl.from_pandas(market.reset_index())
        df_market = (
            df_market
            .sort("Date")
            .filter(pl.col("Close").is_not_null())
            .with_columns(
                Date=pl.col("Date").dt.date(),
                ret=(pl.col("Close").log() - pl.col("Close").shift(1).log())*100
            )
            .slice(offset=1)
        )
        df = (
            df_stock
            .rename({"Date": "date", "Close": "close_stock", "ret": "ret_stock"})
            .select("date", "close_stock", "ret_stock")
            .join(
                df_market
                .rename({"Date": "date", "Close": "close_market", "ret": "ret_market"})
                .select("date", "close_market", "ret_market"),
                how="inner",
                on="date"
            )
        )
        if df.shape[0] <= THRESHOLD_DATA_LEN:
            return {"Message": f"Can not be estimated time-varing beta, because of either length of stock price data <= {THRESHOLD_DATA_LEN} or not existing stock code"}

        ret_market = df.get_column("ret_market").to_numpy()
        ret_stock = df.get_column("ret_stock").to_numpy()
        y = ret_stock
        x = ret_market
        T = len(ret_stock)
        dims = 2
        G = np.eye(dims)
        F = np.eye(T, dims)
        F[:, 0] = 1
        F[:, 1] = x
        m0 = np.zeros(dims)
        C0 = np.eye(dims)*10000000

        best_par=sp.optimize.minimize(
            reverse_loglik,
            [0.0, 0.0],
            args=(dims, y, G, F, m0, C0),
            method="BFGS"
        )
        W = np.eye(dims) * np.exp(best_par.x[0])
        V = np.array([1]).reshape((1, 1)) * np.exp(best_par.x[1])

        # 上で求めた観測誤差と状態誤差をもとにフィルタリングと平滑化を行う
        m, C = np.zeros((T, dims)), np.zeros((T, dims, dims))
        a, R = np.zeros((T, dims)), np.zeros((T, dims, dims))
        f, Q = np.zeros((T)), np.zeros((T))
        s, S = np.zeros((T, dims)), np.zeros((T, dims, dims))
        # フィルタリング
        for t in range(0, T):
            _F = F[t].reshape((1, dims))
            if t == 0:
                m[t], C[t], a[t], R[t], f[t], Q[t] = filtering(y[t], m0, C0, G, _F, W, V)
            else:
                m[t], C[t], a[t], R[t], f[t], Q[t] = filtering(y[t], m[t-1], C[t-1], G, _F, W, V)
        # 平滑化
        for t in range(T - 1, 0, -1):
            if t == T - 1:
                s[t], S[t] = m[t], C[t]
            else:
                s[t], S[t] = smoothing(s[t+1], S[t+1], m[t], C[t], a[t+1], R[t+1], G)

        # 推定値と95%信頼区間を取り出す
        beta_est = (
            pl.DataFrame({
                "date": df.select("date").get_columns()[0],
                "estimated": m[:, 1],
                "std_error": np.sqrt(C[:, 1, 1])
            })
            .with_columns(
                lower=pl.col("estimated")+sp.stats.norm.ppf(0.025)*pl.col("std_error"),
                upper=pl.col("estimated")+sp.stats.norm.ppf(0.975)*pl.col("std_error"),
            )
        )
        beta_smooth = (
            pl.DataFrame({
                "date": df.select("date").get_columns()[0],
                "estimated": s[:, 1],
                "std_error": np.sqrt(S[:, 1, 1])
            })
            .with_columns(
                lower=pl.col("estimated")+sp.stats.norm.ppf(0.025)*pl.col("std_error"),
                upper=pl.col("estimated")+sp.stats.norm.ppf(0.975)*pl.col("std_error"),
            )
        )

        res = {
            "date": [i.strftime("%Y-%m-%d") for i in beta_est.get_column("date").to_list()],
            "filtering": {
                "estimated": beta_est.get_column("estimated").to_list(),
                "std_error": beta_est.get_column("std_error").to_list(),
                "lower_95": beta_est.get_column("lower").to_list(),
                "upper_95": beta_est.get_column("upper").to_list(),
            },
            "smoothing": {
                "estimated": beta_smooth.get_column("estimated").to_list(),
                "std_error": beta_smooth.get_column("std_error").to_list(),
                "lower_95": beta_smooth.get_column("lower").to_list(),
                "upper_95": beta_smooth.get_column("upper").to_list(),
            }
        }
        return res

    except Exception as e:
        logger.exception(e)
        return {"Message": "error occurred"}
