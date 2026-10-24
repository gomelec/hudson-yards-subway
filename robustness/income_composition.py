"""
income_composition.py — did the subway change the earnings and neighbourhood wealth of Hudson Yards commuters?

Stand-alone extension of robustness_checks.py (reuses its geography and placebo definitions).
Run from the project root after master.py:

    uv run python robustness/income_composition.py

Data: LODES 8 OD earnings groups per home-work block pair (jobs, not people):
  SE01 <= $1,250/month, SE02 $1,251-3,333, SE03 > $3,333 (nominal, not inflation-adjusted).

Measures
  I1  share of high earners (SE03) among commuters to Hudson Yards, by year, compared with the
      same share for the placebo destinations (Midtown ring 0.5-3 km, Manhattan excl. HY).
      The nominal thresholds make SE03 rise everywhere over time, so the comparison is HY minus placebo.
  I2  origin-neighbourhood wealth: share of SE03 among all workers living in a home tract,
      averaged over 2009-2011 (before the redevelopment), fixed over time. Tracts are grouped into
      quintiles (Q1 poorest ... Q5 richest) across NYC.
      (a) HY commuters per 1,000 workers by origin quintile, before vs. after 2015 (all tracts, zeros
          included, SE clustered by home tract; also without 2018 and with "before" = 2011-14)
      (b) share of HY / placebo commuters coming from Q5 tracts, by year
      (c) average origin wealth of commuters (commuter-weighted), by year

Outputs: robustness/results/{tables,figures}/income_*
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import robustness_checks as rc  # noqa: E402

SE = ["SE01", "SE02", "SE03"]
DEST = {"hy": "Hudson Yards", "ring": "Midtown ring 0.5-3 km (placebo)", "mn": "Manhattan excl. HY (placebo)"}
Q = ["Q1 poorest", "Q2", "Q3", "Q4", "Q5 richest"]


def flows_by_earnings(nyc, placebo):
    """Per NYC home tract x year: resident workers by earnings group, and commuters by earnings group
    to HY, the Midtown ring and Manhattan excl. HY."""
    cache = rc.DAT / "flows_by_home_tract_earnings.csv"
    if cache.exists():
        return pd.read_csv(cache, dtype={"GEOID": str})
    nyc_ids = set(nyc["GEOID"])
    dest_sets = {"hy": set(rc.HY), "ring": set(placebo),
                 "mn": set(nyc.loc[nyc["COUNTYFP"] == "061", "GEOID"]) - set(rc.HY)}
    out = []
    for year in config.YEARS:
        df = pd.read_csv(config.lodes_path(year), usecols=["w_geocode", "h_geocode", "S000"] + SE,
                         dtype={"w_geocode": str, "h_geocode": str})
        df["w"], df["h"] = df["w_geocode"].str[:11], df["h_geocode"].str[:11]
        df = df[df["h"].isin(nyc_ids)]
        g = df.groupby("h")[["S000"] + SE].sum().add_prefix("res_")
        for key, ids in dest_sets.items():
            g = g.join(df[df["w"].isin(ids)].groupby("h")[["S000"] + SE].sum().add_prefix(f"{key}_"))
        g = g.fillna(0).astype("int64").rename_axis("GEOID").reset_index().assign(year=year)
        out.append(g)
        print(f"  {year}: HY commuters {g['hy_S000'].sum():,}, of which SE03 {g['hy_SE03'].sum():,}")
    f = pd.concat(out, ignore_index=True)
    f.to_csv(cache, index=False)
    return f


def main():
    nyc, placebo = rc.geography()
    f = flows_by_earnings(nyc, placebo)

    # ---------------------------------------------------------------- I1 earnings of commuters
    tot = f.groupby("year").sum(numeric_only=True)
    i1 = pd.DataFrame({DEST[k]: 100 * tot[f"{k}_SE03"] / tot[f"{k}_S000"] for k in DEST})
    i1["All NYC resident workers"] = 100 * tot["res_SE03"] / tot["res_S000"]
    i1["HY minus Midtown ring (pp)"] = i1[DEST["hy"]] - i1[DEST["ring"]]
    i1.round(2).to_csv(rc.TAB / "income_i1_high_earner_share_by_destination.csv")

    # ---------------------------------------------------------------- I2 origin wealth
    base = f[f["year"].between(2009, 2011)].groupby("GEOID")[["res_S000", "res_SE03"]].sum()
    base = base[base["res_S000"] >= 100]  # stable share; drops near-empty tracts
    base["wealth"] = 100 * base["res_SE03"] / base["res_S000"]
    base["quintile"] = pd.qcut(base["wealth"], 5, labels=Q)
    base[["wealth", "quintile"]].to_csv(rc.TAB / "income_origin_tract_wealth_2009_2011.csv")
    print("\nOrigin wealth (share of resident workers earning > $3,333/month, 2009-11) by quintile:")
    print(base.groupby("quintile", observed=True)["wealth"].agg(["min", "median", "max", "count"]).round(1).to_string())

    p = f.merge(base[["wealth", "quintile"]].reset_index(), on="GEOID")
    p = p[p["res_S000"] > 0]
    full = p.groupby("GEOID")["year"].nunique()
    p = p[p["GEOID"].isin(full[full == len(config.YEARS)].index)]

    # (a) HY commuters per 1,000 resident workers, by origin quintile, before vs after
    def by_quintile(d, label, post_from=config.SUBWAY_YEAR, drop=()):
        d = d[~d["year"].isin(drop)].assign(post=lambda x: (x["year"] >= post_from).astype(float))
        rows = []
        for q in Q:
            s = d[d["quintile"] == q]
            X = np.column_stack([np.ones(len(s)), s["post"]])
            beta, se = rc.ols_cluster(s["y"].values, X, s["GEOID"].values)
            rows.append(dict(spec=label, quintile=q, pre=beta[0], post=beta[0] + beta[1], diff=beta[1],
                             lo=beta[1] - 1.96 * se[1], hi=beta[1] + 1.96 * se[1], pct=100 * beta[1] / beta[0],
                             pct_lo=100 * (beta[1] - 1.96 * se[1]) / beta[0], pct_hi=100 * (beta[1] + 1.96 * se[1]) / beta[0],
                             tracts=s["GEOID"].nunique()))
        return pd.DataFrame(rows)

    res = []
    for key in DEST:
        d = p.assign(y=1000 * p[f"{key}_S000"] / p["res_S000"])
        res += [by_quintile(d, f"{DEST[key]} | 2009-14 vs 2015-20"),
                by_quintile(d, f"{DEST[key]} | without 2018", drop=(2018,)),
                by_quintile(d, f"{DEST[key]} | 2011-14 vs 2015-20 without 2018", drop=(2009, 2010, 2018))]
    ia = pd.concat(res)
    ia.to_csv(rc.TAB / "income_i2a_commuters_by_origin_quintile.csv", index=False)

    # (b) share of commuters from Q5 tracts, (c) commuter-weighted origin wealth, by year
    yb = {}
    for key in DEST:
        g = p.groupby(["year", "quintile"], observed=True)[f"{key}_S000"].sum().unstack()
        yb[DEST[key]] = 100 * g[Q[-1]] / g.sum(axis=1)
    ib = pd.DataFrame(yb)
    ib.round(2).to_csv(rc.TAB / "income_i2b_share_from_richest_quintile.csv")
    ic = pd.DataFrame({DEST[k]: p.groupby("year").apply(lambda d, k=k: np.average(d["wealth"], weights=d[f"{k}_S000"]),
                                                          include_groups=False) for k in DEST})
    ic.round(2).to_csv(rc.TAB / "income_i2c_mean_origin_wealth.csv")

    # ---------------------------------------------------------------- figures
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
    ax = axes[0]
    for c in [DEST["hy"], DEST["ring"], DEST["mn"], "All NYC resident workers"]:
        ax.plot(i1.index, i1[c], marker="o", label=c)
    ax.axvline(config.SUBWAY_YEAR, color="#C91441", ls="--")
    ax.set_title("High earners (> $3,333/month) among commuters, %"); ax.legend(fontsize=8); ax.grid(alpha=0.4)
    ax = axes[1]
    ax.plot(i1.index, i1["HY minus Midtown ring (pp)"], marker="o", color="k")
    ax.axhline(0, color="grey", lw=0.8); ax.axvline(config.SUBWAY_YEAR, color="#C91441", ls="--")
    ax.set_title("Hudson Yards minus Midtown ring, percentage points"); ax.grid(alpha=0.4)
    fig.tight_layout(); fig.savefig(rc.FIG / "income_i1_high_earner_share.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
    ax = axes[0]
    for c in ib.columns:
        ax.plot(ib.index, ib[c], marker="o", label=c)
    ax.axvline(config.SUBWAY_YEAR, color="#C91441", ls="--")
    ax.set_title("Commuters living in the richest 20% of NYC tracts, %"); ax.legend(fontsize=8); ax.grid(alpha=0.4)
    ax = axes[1]
    x = np.arange(len(Q)); specs = [s for s in ia["spec"].unique()]
    w = 0.8 / len(specs)
    for k, s in enumerate(specs):
        r = ia[ia["spec"] == s].set_index("quintile").reindex(Q)
        ax.errorbar(x - 0.4 + w * (k + 0.5), r["pct"], yerr=[r["pct"] - r["pct_lo"], r["pct_hi"] - r["pct"]],
                    fmt="o" if s.startswith("Hudson") else "s", ms=4, capsize=2, label=s,
                    color=f"C{k}")
    ax.axhline(0, color="k", lw=0.8); ax.set_xticks(x, Q)
    ax.set_title("Commuters per 1,000 resident workers: change after vs. before 2015, %")
    ax.legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.08)); ax.grid(axis="y", alpha=0.4)
    fig.tight_layout(); fig.savefig(rc.FIG / "income_i2_origin_wealth.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---------------------------------------------------------------- console
    pd.set_option("display.width", 220)
    print("\nI1 high-earner share of commuters (%):"); print(i1.round(1).to_string())
    show = ia.assign(v=ia.apply(lambda r: f"{r['pct']:+.0f}% [{r['pct_lo']:+.0f},{r['pct_hi']:+.0f}]", axis=1))
    print("\nI2a change in commuters per 1,000 resident workers by origin quintile:")
    print(show.pivot(index="spec", columns="quintile", values="v").reindex(columns=Q).to_string())
    print("\nI2b share of commuters from richest quintile (%):"); print(ib.round(1).to_string())
    print("\nI2c commuter-weighted origin wealth (% high earners among residents of origin tract, 2009-11):")
    print(ic.round(1).to_string())


if __name__ == "__main__":
    main()
