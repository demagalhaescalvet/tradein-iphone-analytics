#!/usr/bin/env python3
"""
Trade-In iPhone Analytics — Data Processing Pipeline
Reads Excel files and generates JSON data for all dashboard pages.

Usage:
    python process_data.py

Reads from:
    ../data/TD Historico.xlsx
    ../data/Benchmark_TradeIn_PorCapacidad_Marzo2026.xlsx

Writes to:
    ../data/processed/dashboard.json
    ../data/processed/explorer.json
    ../data/processed/sankey.json
    ../data/processed/insights.json
    ../data/processed/curves.json
    ../data/processed/benchmark.json
    ../data/processed/elasticity.json
"""

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
OUT_DIR = SCRIPT_DIR.parent / "src" / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HISTORICO = DATA_DIR / "TD Historico.xlsx"
BENCHMARK = DATA_DIR / "Benchmark_TradeIn_PorCapacidad_Marzo2026.xlsx"


# ── Helpers ────────────────────────────────────────────────────────────
def safe_int(x):
    """Convert to int, handling NaN."""
    if pd.isna(x):
        return None
    return int(round(x))


def safe_float(x, decimals=4):
    """Convert to float with limited decimals."""
    if pd.isna(x) or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return None
    return round(float(x), decimals)


def write_json(name, data):
    """Write JSON file to output directory."""
    path = OUT_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = path.stat().st_size / 1024
    print(f"  ✓ {name}.json ({size_kb:.1f} KB)")


# ── Load & clean raw data ─────────────────────────────────────────────
def load_historico():
    """Load and clean the historical trade-in data."""
    df = pd.read_excel(HISTORICO)

    # Normalize grading
    df["Grading"] = df["Grading"].str.strip().str.title()
    df["Grado"] = df["Grado"].str.strip().str.title()

    # Parse dates
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["ym"] = df["Timestamp"].dt.to_period("M").astype(str)

    # Event type shorthand
    df["event"] = df["Event"].apply(
        lambda x: "purchase" if "Purchase" in x else "return"
    )

    # Model generation number
    def extract_gen(model):
        for token in model.split():
            try:
                return int(token)
            except ValueError:
                continue
        # SE, X, XR, XS
        mapping = {"X": 10, "XR": 10, "XS": 10, "SE": 8}
        for k, v in mapping.items():
            if k in model:
                return v
        return 0

    df["gen"] = df["Propiedad"].apply(extract_gen)

    return df


def load_benchmark():
    """Load and parse the benchmark Excel (report-format)."""
    raw = pd.read_excel(BENCHMARK, header=None, skiprows=4)
    raw.columns = [
        "model", "capacity", "apple", "entel", "aufbau", "mac_a", "mac_b",
        "best_comp", "mac_vs_best"
    ]

    rows = []
    current_model = None
    for _, r in raw.iterrows():
        model_val = r["model"]
        cap_val = r["capacity"]

        # Skip section headers (rows where capacity is NaN and it's a "Series" row)
        if pd.isna(cap_val):
            if pd.notna(model_val) and "Series" not in str(model_val) and "Notas" not in str(model_val):
                current_model = str(model_val).strip()
            elif pd.notna(model_val) and "Series" not in str(model_val):
                pass  # skip notes
            continue

        # If model cell has a value, update current model
        if pd.notna(model_val):
            m = str(model_val).strip()
            if "Series" not in m and "Notas" not in m and m != "":
                current_model = m

        if current_model is None:
            continue

        def parse_price(val):
            if pd.isna(val) or str(val).strip() in ("—", "-", "–", ""):
                return None
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return None

        rows.append({
            "model": current_model,
            "capacity": str(cap_val).strip(),
            "apple": parse_price(r["apple"]),
            "entel": parse_price(r["entel"]),
            "aufbau": parse_price(r["aufbau"]),
            "mac_a": parse_price(r["mac_a"]),
            "mac_b": parse_price(r["mac_b"]),
        })

    return rows


# ── Dashboard JSON ─────────────────────────────────────────────────────
def generate_dashboard(df):
    """Generate dashboard.json with KPIs, volume, top models, migration, etc."""
    # Filter to meaningful date range (where there's actual activity)
    min_date = df["Timestamp"].min()
    max_date = df["Timestamp"].max()

    returns = df[df["event"] == "return"]
    purchases = df[df["event"] == "purchase"]

    # ── Volume by month ──
    vol_ret = returns.groupby("ym").size()
    vol_pur = purchases.groupby("ym").size()
    all_months = sorted(set(vol_ret.index) | set(vol_pur.index))

    # ── Top models ──
    top_ret = returns["Propiedad"].value_counts().head(10)
    top_pur = purchases["Propiedad"].value_counts().head(10)

    # ── Migration routes ──
    # Link returns and purchases by Unique_Inmmutable_ID
    ret_df = returns[["Unique_Inmmutable_ID", "Propiedad"]].rename(
        columns={"Propiedad": "From"}
    )
    pur_df = purchases[["Unique_Inmmutable_ID", "Propiedad"]].rename(
        columns={"Propiedad": "To"}
    )
    pairs = ret_df.merge(pur_df, on="Unique_Inmmutable_ID")
    migration = (
        pairs.groupby(["From", "To"]).size().reset_index(name="Count")
        .sort_values("Count", ascending=False).head(15)
    )

    # ── Capacity distribution ──
    cap_order = ["64GB", "128GB", "256GB", "512GB", "1TB", "2TB"]
    cap_ret = returns["Capacidad"].value_counts()
    cap_pur = purchases["Capacidad"].value_counts()
    cap_labels = [c for c in cap_order if c in cap_ret.index or c in cap_pur.index]

    # ── Grade distribution ──
    grade_ret_a = len(returns[returns["Grado"] == "Grado A"])
    grade_ret_b = len(returns[returns["Grado"] == "Grado B"])
    grade_pur_a = len(purchases[purchases["Grado"] == "Grado A"])
    grade_pur_b = len(purchases[purchases["Grado"] == "Grado B"])

    # ── Quarterly top models (purchases) ──
    purchases_copy = purchases.copy()
    purchases_copy["quarter"] = purchases_copy["Timestamp"].dt.to_period("Q").astype(str)
    top_purchase_models = purchases["Propiedad"].value_counts().head(6).index.tolist()
    qtr_data = purchases_copy[purchases_copy["Propiedad"].isin(top_purchase_models)]
    qtr_pivot = qtr_data.pivot_table(
        index="quarter", columns="Propiedad", aggfunc="size", fill_value=0
    )
    all_quarters = sorted(qtr_pivot.index.tolist())

    # ── Stats ──
    unique_ids = df["Unique_Inmmutable_ID"].nunique()
    avg_ret_val = safe_int(returns["Product_Value"].mean())
    avg_pur_val = safe_int(purchases["Product_Value"].mean())

    # Compute delta per trade-in
    ret_vals = returns.groupby("Unique_Inmmutable_ID")["Product_Value"].mean()
    pur_vals = purchases.groupby("Unique_Inmmutable_ID")["Product_Value"].mean()
    common_ids = ret_vals.index.intersection(pur_vals.index)
    deltas = pur_vals[common_ids] - ret_vals[common_ids]
    median_delta = safe_int(deltas.median())
    mean_delta = safe_int(deltas.mean())

    data = {
        "volume": {
            "labels": all_months,
            "returns": [int(vol_ret.get(m, 0)) for m in all_months],
            "purchases": [int(vol_pur.get(m, 0)) for m in all_months],
        },
        "topReturns": {
            "labels": top_ret.index.tolist(),
            "values": top_ret.values.tolist(),
        },
        "topPurchases": {
            "labels": top_pur.index.tolist(),
            "values": top_pur.values.tolist(),
        },
        "migration": migration.to_dict("records"),
        "capacity": {
            "labels": cap_labels,
            "returns": [int(cap_ret.get(c, 0)) for c in cap_labels],
            "purchases": [int(cap_pur.get(c, 0)) for c in cap_labels],
        },
        "quarterModels": {
            "quarters": all_quarters,
            "models": {
                model: [int(qtr_pivot.loc[q, model]) if q in qtr_pivot.index and model in qtr_pivot.columns else 0 for q in all_quarters]
                for model in top_purchase_models
            },
        },
        "grade": {
            "returnA": grade_ret_a,
            "returnB": grade_ret_b,
            "purchaseA": grade_pur_a,
            "purchaseB": grade_pur_b,
        },
        "stats": {
            "totalTransactions": len(df),
            "uniqueTradeIns": unique_ids,
            "avgReturnValue": avg_ret_val,
            "avgPurchaseValue": avg_pur_val,
            "medianDelta": median_delta,
            "meanDelta": mean_delta,
            "dateRange": f"{min_date.strftime('%Y-%m-%d')} a {max_date.strftime('%Y-%m-%d')}",
        },
    }

    write_json("dashboard", data)


# ── Explorer JSON ──────────────────────────────────────────────────────
def generate_explorer(df):
    """Generate explorer.json with monthly breakdowns, seasonality, etc."""
    returns = df[df["event"] == "return"]
    purchases = df[df["event"] == "purchase"]

    # Monthly aggregation by model and event
    monthly = (
        df.groupby(["ym", "Propiedad", "event"])
        .agg(count=("Product_Value", "size"), avg_value=("Product_Value", "mean"), total_value=("Product_Value", "sum"))
        .reset_index()
    )
    monthly["avg_value"] = monthly["avg_value"].apply(safe_int)
    monthly["total_value"] = monthly["total_value"].apply(safe_int)

    # Migration by month
    ret_m = returns[["Unique_Inmmutable_ID", "Propiedad", "ym", "Product_Value"]].rename(
        columns={"Propiedad": "from_model", "Product_Value": "ret_val"}
    )
    pur_m = purchases[["Unique_Inmmutable_ID", "Propiedad", "ym", "Product_Value"]].rename(
        columns={"Propiedad": "to_model", "ym": "ym_pur", "Product_Value": "pur_val"}
    )
    pairs = ret_m.merge(pur_m, on="Unique_Inmmutable_ID")
    pairs["avg_delta"] = pairs["pur_val"] - pairs["ret_val"]
    mig = (
        pairs.groupby(["ym", "from_model", "to_model"])
        .agg(count=("avg_delta", "size"), avg_delta=("avg_delta", "mean"))
        .reset_index()
    )
    mig["avg_delta"] = mig["avg_delta"].apply(safe_int)

    # Seasonality by calendar month
    df_copy = df.copy()
    df_copy["month"] = df_copy["Timestamp"].dt.month
    season_month = (
        df_copy.groupby(["month", "Propiedad", "event"]).size()
        .reset_index(name="count")
    )

    # Seasonality by day of week
    df_copy["dow"] = df_copy["Timestamp"].dt.dayofweek
    season_dow = (
        df_copy.groupby(["dow", "Propiedad", "event"]).size()
        .reset_index(name="count")
    )

    # Capacity breakdown
    cap = (
        df.groupby(["Propiedad", "event", "Capacidad"]).size()
        .reset_index(name="count")
    )

    data = {
        "models": sorted(df["Propiedad"].unique().tolist()),
        "dateMin": df["Timestamp"].min().strftime("%Y-%m-%d"),
        "dateMax": df["Timestamp"].max().strftime("%Y-%m-%d"),
        "monthly": monthly.to_dict("records"),
        "migration": mig.to_dict("records"),
        "seasonMonth": season_month.to_dict("records"),
        "seasonDow": season_dow.to_dict("records"),
        "capacity": cap.to_dict("records"),
    }

    write_json("explorer", data)


# ── Sankey JSON ────────────────────────────────────────────────────────
def generate_sankey(df):
    """Generate sankey.json with migration flows including value data."""
    returns = df[df["event"] == "return"]
    purchases = df[df["event"] == "purchase"]

    ret_s = returns[["Unique_Inmmutable_ID", "Propiedad", "ym", "Product_Value"]].rename(
        columns={"Propiedad": "from_model", "Product_Value": "ret_val"}
    )
    pur_s = purchases[["Unique_Inmmutable_ID", "Propiedad", "ym", "Product_Value"]].rename(
        columns={"Propiedad": "to_model", "ym": "ym_pur", "Product_Value": "pur_val"}
    )
    pairs = ret_s.merge(pur_s, on="Unique_Inmmutable_ID")
    pairs["delta"] = pairs["pur_val"] - pairs["ret_val"]

    flows = (
        pairs.groupby(["ym", "from_model", "to_model"])
        .agg(
            count=("delta", "size"),
            avg_ret=("ret_val", "mean"),
            avg_pur=("pur_val", "mean"),
            avg_delta=("delta", "mean"),
        )
        .reset_index()
    )
    for col in ["avg_ret", "avg_pur", "avg_delta"]:
        flows[col] = flows[col].apply(safe_int)

    data = {
        "models": sorted(df["Propiedad"].unique().tolist()),
        "dateMin": df["Timestamp"].min().strftime("%Y-%m-%d"),
        "dateMax": df["Timestamp"].max().strftime("%Y-%m-%d"),
        "flows": flows.to_dict("records"),
    }

    write_json("sankey", data)


# ── Insights JSON ──────────────────────────────────────────────────────
def generate_insights(df):
    """Generate insights.json with generational, tier, capacity, retention data."""
    returns = df[df["event"] == "return"]
    purchases = df[df["event"] == "purchase"]

    # Pair returns with purchases
    ret_i = returns[["Unique_Inmmutable_ID", "Propiedad", "ym", "Product_Value", "Grado", "Capacidad", "gen", "Grading"]].rename(
        columns={"Propiedad": "from_model", "Product_Value": "ret_val", "Capacidad": "from_cap", "gen": "from_gen", "Grading": "from_grading"}
    )
    pur_i = purchases[["Unique_Inmmutable_ID", "Propiedad", "ym", "Product_Value", "Capacidad", "gen"]].rename(
        columns={"Propiedad": "to_model", "ym": "ym_pur", "Product_Value": "pur_val", "Capacidad": "to_cap", "gen": "to_gen"}
    )
    pairs = ret_i.merge(pur_i, on="Unique_Inmmutable_ID")

    # Generational jump
    pairs["gen_jump"] = pairs["to_gen"] - pairs["from_gen"]
    gen_data = (
        pairs.groupby(["ym", "gen_jump"]).size()
        .reset_index(name="count")
    )
    gen_data = gen_data.rename(columns={"gen_jump": "gen"})

    # Tier migration
    tier_order = ["Pro Max", "Pro", "Plus", "Standard", "Mini/SE"]

    def get_tier(model):
        if "Pro Max" in model:
            return "Pro Max"
        elif "Pro" in model:
            return "Pro"
        elif "Plus" in model:
            return "Plus"
        elif "mini" in model.lower() or "SE" in model or " e" in model:
            return "Mini/SE"
        else:
            return "Standard"

    pairs["from_tier"] = pairs["from_model"].apply(get_tier)
    pairs["to_tier"] = pairs["to_model"].apply(get_tier)
    tier_data = (
        pairs.groupby(["ym", "from_tier", "to_tier"]).size()
        .reset_index(name="count")
    )
    tier_data = tier_data.rename(columns={"from_tier": "from", "to_tier": "to"})

    # Capacity upgrade
    cap_order_map = {"64GB": 64, "128GB": 128, "256GB": 256, "512GB": 512, "1TB": 1024, "2TB": 2048}
    pairs["from_cap_n"] = pairs["from_cap"].map(cap_order_map)
    pairs["to_cap_n"] = pairs["to_cap"].map(cap_order_map)

    def cap_change(row):
        if row["to_cap_n"] > row["from_cap_n"]:
            return "Upgrade"
        elif row["to_cap_n"] < row["from_cap_n"]:
            return "Downgrade"
        else:
            return "Same"

    pairs["cap_change"] = pairs.apply(cap_change, axis=1)
    cap_data = (
        pairs.groupby(["ym", "cap_change"]).size()
        .reset_index(name="count")
    )
    cap_data = cap_data.rename(columns={"cap_change": "change"})

    # Retention of value (% of purchase price covered by trade-in)
    pairs["retention_pct"] = pairs["ret_val"] / pairs["pur_val"] * 100
    retention = (
        pairs.groupby(["ym", "from_model"])
        .agg(avg_ret=("retention_pct", "mean"), count=("retention_pct", "size"))
        .reset_index()
    )
    retention["avg_ret"] = retention["avg_ret"].round(1)

    # Grading impact on value
    ret_graded = returns[returns["Grading"].notna()].copy()
    ret_graded["from_grading_clean"] = ret_graded["Grading"]
    grading = (
        ret_graded.groupby(["ym", "Propiedad", "from_grading_clean"])
        .agg(avg_val=("Product_Value", "mean"), count=("Product_Value", "size"))
        .reset_index()
    )
    grading = grading.rename(columns={"Propiedad": "from_model"})
    grading["avg_val"] = grading["avg_val"].apply(safe_int)

    # Leakage (returns without matching purchase = trade-in used for non-iPhone)
    ret_ids = set(returns["Unique_Inmmutable_ID"])
    pur_ids = set(purchases["Unique_Inmmutable_ID"])
    returns_copy = returns.copy()
    returns_copy["leaked"] = ~returns_copy["Unique_Inmmutable_ID"].isin(pur_ids)
    leakage = (
        returns_copy.groupby(["ym", "Propiedad"])
        .agg(leaked=("leaked", "sum"), total=("leaked", "size"))
        .reset_index()
    )
    leakage = leakage.rename(columns={"Propiedad": "from_model"})
    leakage["leaked"] = leakage["leaked"].astype(int)

    data = {
        "models": sorted(df["Propiedad"].unique().tolist()),
        "dateMin": df["Timestamp"].min().strftime("%Y-%m-%d"),
        "dateMax": df["Timestamp"].max().strftime("%Y-%m-%d"),
        "tierOrder": tier_order,
        "gen": gen_data.to_dict("records"),
        "tier": tier_data.to_dict("records"),
        "cap": cap_data.to_dict("records"),
        "retention": retention.to_dict("records"),
        "grading": grading.to_dict("records"),
        "leakage": leakage.to_dict("records"),
    }

    write_json("insights", data)


# ── Curves JSON ────────────────────────────────────────────────────────
def generate_curves(df):
    """Generate curves.json with value curves by model and grade."""
    returns = df[df["event"] == "return"].copy()

    # Only models with enough data
    model_counts = returns["Propiedad"].value_counts()
    valid_models = model_counts[model_counts >= 10].index.tolist()
    ret_valid = returns[returns["Propiedad"].isin(valid_models)]

    # Value curves by model and Grado
    val_curves = (
        ret_valid.groupby(["ym", "Propiedad", "Grado"])
        .agg(avg_val=("Product_Value", "mean"), med_val=("Product_Value", "median"), count=("Product_Value", "size"))
        .reset_index()
    )
    val_curves["avg_val"] = val_curves["avg_val"].apply(safe_int)
    val_curves["med_val"] = val_curves["med_val"].apply(safe_int)

    # Grading curves (using Grading field, not Grado)
    ret_graded = ret_valid[ret_valid["Grading"].notna()].copy()
    ret_graded["grading_clean"] = ret_graded["Grading"]
    grading_curves = (
        ret_graded.groupby(["ym", "Propiedad", "grading_clean"])
        .agg(avg_val=("Product_Value", "mean"), count=("Product_Value", "size"))
        .reset_index()
    )
    grading_curves["avg_val"] = grading_curves["avg_val"].apply(safe_int)

    # Volume time series
    vol = df.groupby("ym").size().reset_index(name="total_vol")
    ret_vol = returns.groupby("ym").size().reset_index(name="return_vol")
    volume = vol.merge(ret_vol, on="ym", how="left").fillna(0)
    volume["return_vol"] = volume["return_vol"].astype(int)

    # Correlations: value vs volume per model
    correlations = []
    for model in valid_models:
        m_val = val_curves[val_curves["Propiedad"] == model].groupby("ym")["avg_val"].mean()
        m_vol = ret_valid[ret_valid["Propiedad"] == model].groupby("ym").size()
        common = m_val.index.intersection(m_vol.index)
        if len(common) >= 4:
            corr = np.corrcoef(m_val[common].values, m_vol[common].values)[0, 1]
            correlations.append({
                "model": model,
                "corr_val_vol": safe_float(corr),
                "n_months": len(common),
            })

    # Overall correlation
    all_val = ret_valid.groupby("ym")["Product_Value"].mean()
    all_vol = ret_valid.groupby("ym").size()
    common_all = all_val.index.intersection(all_vol.index)
    overall_corr = safe_float(np.corrcoef(all_val[common_all].values, all_vol[common_all].values)[0, 1])

    data = {
        "models": sorted(valid_models),
        "dateMin": df["Timestamp"].min().strftime("%Y-%m-%d"),
        "dateMax": df["Timestamp"].max().strftime("%Y-%m-%d"),
        "overallCorr": overall_corr,
        "valCurves": val_curves.to_dict("records"),
        "gradingCurves": grading_curves.to_dict("records"),
        "volume": volume.to_dict("records"),
        "correlations": correlations,
    }

    write_json("curves", data)


# ── Benchmark JSON ─────────────────────────────────────────────────────
def generate_benchmark(bench_rows):
    """Generate benchmark.json from parsed benchmark data."""
    models = list(dict.fromkeys(r["model"] for r in bench_rows))
    capacities = list(dict.fromkeys(r["capacity"] for r in bench_rows))

    data = {
        "models": models,
        "capacities": capacities,
        "data": bench_rows,
    }

    write_json("benchmark", data)


# ── Elasticity JSON ────────────────────────────────────────────────────
def generate_elasticity(df):
    """Generate elasticity.json with price-volume elasticity per model."""
    returns = df[df["event"] == "return"].copy()

    model_counts = returns["Propiedad"].value_counts()
    valid_models = model_counts[model_counts >= 20].index.tolist()

    elasticity_results = []
    series_data = {}

    for model in valid_models:
        m_data = returns[returns["Propiedad"] == model].copy()
        monthly = (
            m_data.groupby("ym")
            .agg(price=("Product_Value", "mean"), vol=("Product_Value", "size"))
            .reset_index()
            .sort_values("ym")
        )

        if len(monthly) < 4:
            continue

        monthly["progVol"] = monthly["vol"].cumsum()
        monthly["priceChg"] = monthly["price"].pct_change().apply(lambda x: safe_float(x))
        monthly["volChg"] = monthly["vol"].pct_change().apply(lambda x: safe_float(x))

        # Adjusted volume (detrended)
        monthly["volAdj"] = monthly["vol"] / monthly["vol"].mean()
        monthly["volAdj"] = monthly["volAdj"].apply(lambda x: safe_float(x))

        # Simple elasticity via regression
        price_vals = monthly["price"].values
        vol_vals = monthly["vol"].values

        # Normalize
        if price_vals.std() > 0 and vol_vals.std() > 0:
            price_norm = (price_vals - price_vals.mean()) / price_vals.std()
            vol_norm = (vol_vals - vol_vals.mean()) / vol_vals.std()

            # Linear regression
            n = len(price_norm)
            slope = np.sum(price_norm * vol_norm) / np.sum(price_norm ** 2) if np.sum(price_norm ** 2) > 0 else 0
            y_pred = slope * price_norm
            ss_res = np.sum((vol_norm - y_pred) ** 2)
            ss_tot = np.sum((vol_norm - vol_norm.mean()) ** 2)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            # p-value approximation (t-test)
            if n > 2 and ss_res > 0:
                se = np.sqrt(ss_res / (n - 2)) / np.sqrt(np.sum(price_norm ** 2))
                t_stat = slope / se if se > 0 else 0
                # Approximate p-value using normal distribution
                p_val = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
            else:
                p_val = 1.0

            # Elasticity = %change in volume / %change in price
            elasticity = slope  # Already normalized, this is the standardized coefficient

            elasticity_results.append({
                "model": model,
                "elasticity": safe_float(elasticity),
                "slope": safe_float(slope),
                "rSq": safe_float(r_sq),
                "pVal": safe_float(p_val),
                "n": n,
                "avgVol": safe_int(vol_vals.mean()),
                "significant": p_val < 0.05,
            })

        # Series data
        monthly["price"] = monthly["price"].apply(safe_int)
        series_data[model] = monthly[["ym", "price", "vol", "progVol", "priceChg", "volChg", "volAdj"]].to_dict("records")

    data = {
        "models": sorted(valid_models),
        "dateMin": df["Timestamp"].min().strftime("%Y-%m-%d"),
        "dateMax": df["Timestamp"].max().strftime("%Y-%m-%d"),
        "elasticity": elasticity_results,
        "series": series_data,
    }

    write_json("elasticity", data)


# ── Migration Matrix JSON ─────────────────────────────────────────────
def generate_migration(df):
    """Generate migration.json with model-to-model matrix data."""
    returns = df[df["event"] == "return"]
    purchases = df[df["event"] == "purchase"]

    ret_m = returns[["Unique_Inmmutable_ID", "Propiedad", "ym", "Product_Value"]].rename(
        columns={"Propiedad": "from_model", "Product_Value": "ret_val"}
    )
    pur_m = purchases[["Unique_Inmmutable_ID", "Propiedad", "Product_Value"]].rename(
        columns={"Propiedad": "to_model", "Product_Value": "pur_val"}
    )
    pairs = ret_m.merge(pur_m, on="Unique_Inmmutable_ID")

    # Sort models by iPhone generation number for logical ordering
    def model_sort_key(name):
        import re
        m = re.search(r'(\d+)', name)
        num = int(m.group(1)) if m else 0
        tier = 0
        if "Pro Max" in name:
            tier = 3
        elif "Pro" in name:
            tier = 2
        elif "Plus" in name:
            tier = 1
        elif "mini" in name.lower() or "SE" in name or "Air" in name or " e" in name.lower():
            tier = -1
        return (num, tier)

    from_models = sorted(pairs["from_model"].unique(), key=model_sort_key)
    to_models = sorted(pairs["to_model"].unique(), key=model_sort_key)

    # Monthly flows: group by ym, from_model, to_model for client-side filtering
    flows = (
        pairs.groupby(["ym", "from_model", "to_model"])
        .agg(count=("pur_val", "size"), avg_ret=("ret_val", "mean"), avg_pur=("pur_val", "mean"))
        .reset_index()
    )
    flows["avg_ret"] = flows["avg_ret"].apply(safe_int)
    flows["avg_pur"] = flows["avg_pur"].apply(safe_int)

    data = {
        "fromModels": from_models,
        "toModels": to_models,
        "dateMin": df["Timestamp"].min().strftime("%Y-%m-%d"),
        "dateMax": df["Timestamp"].max().strftime("%Y-%m-%d"),
        "flows": flows.to_dict("records"),
    }

    write_json("migration", data)


# ── Main ───────────────────────────────────────────────────────────────
def main():
    print("Trade-In iPhone Analytics — Data Pipeline")
    print("=" * 50)

    print("\n📂 Loading historical data...")
    df = load_historico()
    print(f"   {len(df):,} rows loaded ({df['Unique_Inmmutable_ID'].nunique():,} unique trade-ins)")

    print("\n📂 Loading benchmark data...")
    bench = load_benchmark()
    print(f"   {len(bench)} model-capacity combinations loaded")

    print("\n📊 Generating JSON files...")
    generate_dashboard(df)
    generate_explorer(df)
    generate_sankey(df)
    generate_insights(df)
    generate_curves(df)
    generate_benchmark(bench)
    generate_elasticity(df)
    generate_migration(df)

    print("\n✅ All data files generated successfully!")
    print(f"   Output directory: {OUT_DIR}")


if __name__ == "__main__":
    main()
