"""
robustness_checks.py — robustness of Figure 1, Panel B (Hudson Yards commuters by distance).

Stand-alone: reads the outputs of the main pipeline and the raw files in data/raw, writes only
into robustness/results/. Nothing in the main pipeline is changed. Run from the project root
after `master.py`:

    uv run python robustness/robustness_checks.py

Specifications (all compare 2009-2014 with 2015-2020 unless stated):
  S0  original Panel B (rows = home tract x HY destination tract x year, positive flows only,
      edge-to-edge distance), iid 95% CI as in the paper
  S1  S0 with standard errors clustered by home tract
  S2  S0 with centroid-to-centroid distance
  S3  one row per home tract x year (HY destination tracts 99.01-99.03 summed), positive flows only
  S4  all NYC home tracts every year, zeros included (balanced panel)              <- preferred
  S5  S4 with centroid distance
  S6  S4, LODES 2015 counted as pre-opening (jobs are measured in April 2015)
  S7  S4 without 2015 (transition year)
  S8  S4 without 2018 (reporting spike in tract 99.02)
  S9  S4 weighted by workers (= total HY commuters / total workers in a bin)
  S10 S4 with "before" = 2011-14 (low 2009-10 baseline dropped) and without 2018
Further checks:
  E   event study on S4: home-tract and year fixed effects, bin x year effects relative to 2014
      and to the > 10 km bin, SE clustered by home tract
  P   placebo destinations, same construction as S4: (a) Midtown tracts 0.5-3 km from Hudson
      Yards that got no new station, (b) all of Manhattan except Hudson Yards

Outputs: robustness/results/{tables,figures,data}/
"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config  # noqa: E402  (read-only use of the project settings)

OUT = ROOT / "robustness" / "results"
TAB, FIG, DAT = OUT / "tables", OUT / "figures", OUT / "data"
for d in (TAB, FIG, DAT):
    d.mkdir(parents=True, exist_ok=True)

BINS = config.DIST_LABELS
HY = [t for t in config.HY_TRACTS_LODES if t != "36061009900"]   # 009900 has no 2020 geography
PLACEBO_RING = (0.5, 3.0)                                       # km, centroid distance to HY


# ----------------------------------------------------------------------------- helpers
def ols_cluster(y, X, cluster, w=None):
    """OLS (or WLS) with standard errors clustered by `cluster` (Stata-style small-sample factor)."""
    y, X = np.asarray(y, float), np.asarray(X, float)
    if w is not None:
        sw = np.sqrt(np.asarray(w, float))
        y, X = y * sw, X * sw[:, None]
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    u = y - X @ beta
    groups = pd.factorize(np.asarray(cluster))[0]
    G, (N, K) = groups.max() + 1, X.shape
    S = np.zeros((G, K))
    np.add.at(S, groups, X * u[:, None])
    V = XtX_inv @ (S.T @ S) @ XtX_inv * G / (G - 1) * (N - 1) / (N - K)
    return beta, np.sqrt(np.diag(V))


def bin_of(km):
    return pd.cut(km, bins=config.DIST_EDGES, labels=BINS, right=False)


def pre_post(df, spec, post_from=config.SUBWAY_YEAR, drop_years=(), weight=None, cluster=True):
    """Per distance bin: mean before, mean after, difference with 95% CI (clustered by home tract)."""
    d = df[~df["year"].isin(drop_years)].dropna(subset=["y", "bin"])
    d = d.assign(post=(d["year"] >= post_from).astype(float))
    rows = []
    for b in BINS:
        s = d[d["bin"] == b]
        if s["post"].nunique() < 2 or s["GEOID"].nunique() < 2:
            continue  # empty bin
        w = s[weight].values if weight else None
        X = np.column_stack([np.ones(len(s)), s["post"].values])
        if cluster:
            beta, se = ols_cluster(s["y"].values, X, s["GEOID"].values, w)
        else:  # iid, as in the paper: difference of the two CIs is not reported there; use Welch-type SE
            a, p = s.loc[s.post == 0, "y"], s.loc[s.post == 1, "y"]
            beta = [a.mean(), p.mean() - a.mean()]
            se = [np.nan, np.sqrt(a.var() / len(a) + p.var() / len(p))]
        rows.append(dict(spec=spec, bin=b, pre=beta[0], post=beta[0] + beta[1], diff=beta[1],
                         se=se[1], lo=beta[1] - 1.96 * se[1], hi=beta[1] + 1.96 * se[1],
                         pct=100 * beta[1] / beta[0], n_pre=int((s.post == 0).sum()),
                         n_post=int((s.post == 1).sum()), tracts=s["GEOID"].nunique()))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- geography
def geography():
    t = gpd.read_file(f"zip://{config.RAW_TRACTS / config.TRACTS_FILE}").to_crs(config.CRS_FEET)
    nyc = t[t["COUNTYFP"].isin(config.NYC_COUNTIES)].reset_index(drop=True)
    hy_union = nyc[nyc["GEOID"].isin(HY)].union_all()
    hy_c = hy_union.centroid
    nyc["cent"] = nyc.geometry.centroid
    nyc["edge_km"] = (nyc.geometry.distance(hy_union) * config.FEET_TO_KM).round(2)
    nyc["cent_km"] = (nyc["cent"].distance(hy_c) * config.FEET_TO_KM).round(2)
    mn = nyc[(nyc["COUNTYFP"] == "061") & ~nyc["GEOID"].isin(HY)]
    placebo = mn.loc[mn["cent_km"].between(*PLACEBO_RING), "GEOID"].tolist()
    print(f"NYC tracts {len(nyc)}, HY tracts {HY}, placebo Midtown ring {len(placebo)} tracts")
    return nyc, placebo


# ----------------------------------------------------------------------------- flows from raw LODES
def flows(nyc, placebo):
    """Per NYC home tract x year: workers, HY commuters (total and by tract), placebo commuters."""
    cache = DAT / "flows_by_home_tract.csv"
    if cache.exists():
        return pd.read_csv(cache, dtype={"GEOID": str})
    nyc_ids, mn_ids = set(nyc["GEOID"]), set(nyc.loc[nyc["COUNTYFP"] == "061", "GEOID"])
    out = []
    for year in config.YEARS:
        df = pd.read_csv(config.lodes_path(year), usecols=["w_geocode", "h_geocode", "S000"],
                         dtype={"w_geocode": str, "h_geocode": str, "S000": "int64"})
        df["w"], df["h"] = df["w_geocode"].str[:11], df["h_geocode"].str[:11]
        df = df[df["h"].isin(nyc_ids)]
        g = pd.DataFrame({"workers": df.groupby("h")["S000"].sum()})
        for t in HY:
            g[f"hy_{t[-4:]}"] = df[df["w"] == t].groupby("h")["S000"].sum()
        g["placebo_midtown"] = df[df["w"].isin(placebo)].groupby("h")["S000"].sum()
        g["placebo_manhattan"] = df[df["w"].isin(mn_ids - set(HY))].groupby("h")["S000"].sum()
        g = g.fillna(0).astype("int64").rename_axis("GEOID").reset_index().assign(year=year)
        out.append(g)
        print(f"  {year}: {len(g)} home tracts, HY commuters {g.filter(like='hy_').values.sum():,}")
    f = pd.concat(out, ignore_index=True)
    f["hy"] = f.filter(like="hy_").sum(axis=1)
    f.to_csv(cache, index=False)
    return f


# ----------------------------------------------------------------------------- main
def main():
    nyc, placebo = geography()
    f = flows(nyc, placebo)
    geo = nyc[["GEOID", "edge_km", "cent_km"]]

    # Balanced panel of NYC home tracts with residents in every year (zeros kept)
    yrs = f.groupby("GEOID")["year"].nunique()
    full = yrs[yrs == len(config.YEARS)].index
    p = f[f["GEOID"].isin(full) & (f["workers"] > 0)]
    p = p[p["GEOID"].isin(p.groupby("GEOID")["year"].nunique().loc[lambda s: s == len(config.YEARS)].index)]
    p = p.merge(geo, on="GEOID")
    print(f"balanced panel: {p['GEOID'].nunique()} home tracts x {len(config.YEARS)} years")

    # Original rows (S0-S2): data/processed/commute_distance.csv, positive flows only
    o = pd.read_csv(config.PROCESSED / "commute_distance.csv", dtype={"GEOID": str, "w_trct": str})
    o = o[o["hudson_workers"].notna()].copy()
    cent = nyc.set_index("GEOID")["cent"]
    o["cent_km"] = [round(cent[h].distance(cent[w]) * config.FEET_TO_KM, 2) for h, w in zip(o["GEOID"], o["w_trct"])]
    o = o.rename(columns={"hudson_workers_per_1000": "y"})

    # S3: one row per home tract-year, positive flows
    s3 = (p[p["hy"] > 0].assign(y=lambda d: 1000 * d["hy"] / d["workers"], bin=lambda d: bin_of(d["edge_km"])))

    s4 = p.assign(y=1000 * p["hy"] / p["workers"], bin=bin_of(p["edge_km"]))
    s5 = s4.assign(bin=bin_of(s4["cent_km"]))

    res = pd.concat([
        pre_post(o.assign(bin=bin_of(o["distance_km"])), "S0 original (iid)", cluster=False),
        pre_post(o.assign(bin=bin_of(o["distance_km"])), "S1 original, clustered SE"),
        pre_post(o.assign(bin=bin_of(o["cent_km"])), "S2 centroid distance"),
        pre_post(s3, "S3 home tract x year, flows > 0"),
        pre_post(s4, "S4 all tracts, zeros incl."),
        pre_post(s5, "S5 S4 + centroid distance"),
        pre_post(s4, "S6 S4, 2015 = pre", post_from=config.SUBWAY_YEAR + 1),
        pre_post(s4, "S7 S4 without 2015", post_from=config.SUBWAY_YEAR + 1, drop_years=(2015,)),
        pre_post(s4, "S8 S4 without 2018", drop_years=(2018,)),
        pre_post(s4, "S9 S4 worker-weighted", weight="workers"),
        pre_post(s4, "S10 S4, before = 2011-14, without 2018", drop_years=(2009, 2010, 2018)),
    ])
    res.to_csv(TAB / "pre_post_by_spec.csv", index=False)

    # ---- placebo destinations (same construction as S4)
    pl = pd.concat([
        pre_post(s4, "Hudson Yards"),
        pre_post(s4.assign(y=1000 * s4["placebo_midtown"] / s4["workers"]), "Midtown ring 0.5-3 km (placebo)"),
        pre_post(s4.assign(y=1000 * s4["placebo_manhattan"] / s4["workers"]), "Manhattan excl. HY (placebo)"),
    ])
    pl.to_csv(TAB / "placebo_destinations.csv", index=False)

    # ---- event study on S4: y_it = a_i + g_t + sum_{b != >10km} sum_{t != 2014} d_bt 1[bin=b]1[year=t]
    e = s4.sort_values(["GEOID", "year"]).reset_index(drop=True)
    names, cols = [], []
    for b in BINS[:-1]:
        for t in config.YEARS:
            if t == 2014:
                continue
            names.append((b, t))
            cols.append(((e["bin"] == b) & (e["year"] == t)).astype(float).values)
    X = np.column_stack(cols)
    Y = e["y"].values

    def twoway_demean(v):  # exact for a balanced panel
        v = pd.DataFrame(v) if v.ndim > 1 else pd.Series(v)
        gi = v.groupby(e["GEOID"].values).transform("mean")
        gt = v.groupby(e["year"].values).transform("mean")
        return (v - gi - gt + v.mean()).values

    beta, se = ols_cluster(twoway_demean(Y), twoway_demean(X), e["GEOID"].values)
    es = pd.DataFrame([dict(bin=b, year=t, coef=c, se=s, lo=c - 1.96 * s, hi=c + 1.96 * s)
                       for (b, t), c, s in zip(names, beta, se)])
    es.to_csv(TAB / "event_study.csv", index=False)
    pre = es[es["year"] < 2014]
    print("\nEvent study: joint size of pre-period coefficients by bin (mean |coef|, share significant):")
    print(pre.assign(sig=(pre["lo"] > 0) | (pre["hi"] < 0)).groupby("bin", observed=True)
             .agg(mean_abs=("coef", lambda c: c.abs().mean()), share_sig=("sig", "mean")).round(3).to_string())

    # ---- yearly means by bin (S4) and by HY destination tract
    ym = s4.groupby(["year", "bin"], observed=True)["y"].mean().unstack()
    ym.to_csv(TAB / "yearly_mean_by_bin_S4.csv")
    by_dest = f.groupby("year")[[c for c in f.columns if c.startswith("hy_")]].sum()
    by_dest.to_csv(TAB / "hy_commuters_by_destination_tract.csv")

    # ---------------------------------------------------------------- figures
    specs = res["spec"].unique()
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(BINS))
    width = 0.8 / len(specs)
    for k, s in enumerate(specs):
        r = res[res["spec"] == s].set_index("bin").reindex(BINS)
        xs = x - 0.4 + width * (k + 0.5)
        ax.errorbar(xs, r["pct"], yerr=[100 * (r["diff"] - r["lo"]) / r["pre"], 100 * (r["hi"] - r["diff"]) / r["pre"]],
                    fmt="o" if k < 10 else "D", ms=4, capsize=2, label=s,
                    color=f"C{k}" if k < 10 else "black")  # 10 default colours, then black
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x, BINS)
    ax.set_ylabel("Change after vs. before 2015 (% of pre mean), 95% CI")
    ax.set_title("Panel B robustness: change in HY commuters per 1,000 workers, by distance bin")
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    ax.grid(axis="y", alpha=0.4)
    fig.tight_layout(); fig.savefig(FIG / "r1_pre_post_by_spec.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    for b in [b for b in BINS if b in ym.columns]:
        ax.plot(ym.index, ym[b], marker="o", label=b)
    ax.axvline(config.SUBWAY_YEAR, color="#C91441", ls="--")
    ax.set_title("HY commuters per 1,000 workers by year and distance bin (all NYC tracts, zeros incl.)")
    ax.set_xlabel("Year"); ax.set_ylabel("Mean per 1,000 workers"); ax.legend(title="Distance"); ax.grid(alpha=0.4)
    fig.tight_layout(); fig.savefig(FIG / "r2_yearly_means_by_bin.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 5, figsize=(16, 4), sharey=True)
    for ax, b in zip(axes, BINS[:-1]):
        r = es[es["bin"] == b]
        r = pd.concat([r, pd.DataFrame([dict(bin=b, year=2014, coef=0, lo=0, hi=0)])]).sort_values("year")
        ax.fill_between(r["year"], r["lo"], r["hi"], alpha=0.25)
        ax.plot(r["year"], r["coef"], marker="o", ms=3)
        ax.axhline(0, color="k", lw=0.8); ax.axvline(2014.5, color="#C91441", ls="--")
        ax.set_title(b); ax.grid(alpha=0.4)
    axes[0].set_ylabel("Effect relative to 2014 and to >10 km bin")
    fig.suptitle("Event study: tract and year fixed effects, 95% CI clustered by home tract")
    fig.tight_layout(); fig.savefig(FIG / "r3_event_study.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    for s in pl["spec"].unique():
        r = pl[pl["spec"] == s].set_index("bin").reindex(BINS)
        ax.plot(BINS, r["pct"], marker="o", label=s)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("Change after vs. before 2015 (% of pre mean)")
    ax.set_title("Placebo: same change for destinations without a new station")
    ax.legend(); ax.grid(alpha=0.4)
    fig.tight_layout(); fig.savefig(FIG / "r4_placebo_destinations.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    for c in by_dest.columns:
        ax.plot(by_dest.index, by_dest[c], marker="o", label=f"tract 99.{c[-2:]}")
    ax.axvline(config.SUBWAY_YEAR, color="#C91441", ls="--")
    ax.set_title("Jobs held by NYC residents in the Hudson Yards tracts (LODES)"); ax.legend(); ax.grid(alpha=0.4)
    fig.tight_layout(); fig.savefig(FIG / "r5_hy_jobs_by_tract.png", dpi=150); plt.close(fig)

    # ---------------------------------------------------------------- console summary
    pd.set_option("display.width", 200)
    show = res.assign(diff_ci=res.apply(lambda r: f"{r['diff']:+.2f} [{r['lo']:+.2f}, {r['hi']:+.2f}]", axis=1))
    print("\nChange after - before (per 1,000 workers), 95% CI:")
    print(show.pivot(index="spec", columns="bin", values="diff_ci").reindex(columns=BINS).to_string())
    print("\nPre-period means:")
    print(res.pivot(index="spec", columns="bin", values="pre").reindex(columns=BINS).round(2).to_string())
    print("\nPlacebo, % change after vs. before:")
    print(pl.pivot(index="spec", columns="bin", values="pct").reindex(columns=BINS).round(1).to_string())
    print(f"\nHY commuters by destination tract:\n{by_dest.to_string()}")
    print(f"\nwrote {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
