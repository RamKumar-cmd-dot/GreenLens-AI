import json
import pandas as pd
import pytest
from ml.common import DATA, CATEGORIES, FEATURES, TARGETS
from ml.propensity_models import split_customers


def test_integrity():
    customers = pd.read_csv(DATA / "synthetic/customers.csv")
    ids = set(customers.customer_id)
    assert customers.customer_id.is_unique and len(ids) == 5000
    for name in [
        "transactions",
        "customer_assets",
        "customer_behaviour",
        "customer_products",
        "product_takeup_labels",
    ]:
        t = pd.read_csv(DATA / f"synthetic/{name}.csv")
        assert set(t.customer_id) <= ids
        if name != "transactions" and name != "customer_products":
            assert t.customer_id.is_unique and set(t.customer_id) == ids
    t = pd.read_csv(DATA / "synthetic/transactions.csv")
    assert t.transaction_id.is_unique
    assert t.sustainability_category.notna().all() and set(
        t.sustainability_category
    ) == set(CATEGORIES)
    assert (pd.to_datetime(t.transaction_date) < pd.Timestamp("2026-01-01")).all()


def test_splits_and_no_targets():
    s = json.loads((DATA / "processed/splits.json").read_text())
    sets = [set(s[k]) for k in ["train", "validation", "test"]]
    assert [len(v) for v in sets] == [3500, 750, 750]
    assert not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
    assert s == split_customers(set.union(*sets))
    assert not set(FEATURES) & set(TARGETS.values())
    assert not set(TARGETS.values()) & set(
        pd.read_csv(DATA / "processed/customer_360.csv", nrows=0).columns
    )


def test_generation_reproducible(tmp_path):
    from data.generate_synthetic import generate

    generate(100, output=tmp_path / "a")
    generate(100, output=tmp_path / "b")
    for f in (tmp_path / "a").glob("*.csv"):
        assert f.read_bytes() == (tmp_path / "b" / f.name).read_bytes()


def test_generator_refuses_to_replace_existing_cohort():
    from data.generate_synthetic import generate

    with pytest.raises(FileExistsError):
        generate(100, output=DATA / "synthetic")


def test_future_transactions_excluded(tmp_path):
    import shutil
    from ml.feature_engineering import build_features

    for f in (DATA / "synthetic").glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    before = build_features(tmp_path)
    tx = pd.read_csv(tmp_path / "transactions.csv")
    extra = tx.iloc[[0]].copy()
    extra["transaction_date"] = "2026-03-01"
    extra["amount_gbp"] = 1e9
    pd.concat([tx, extra]).to_csv(tmp_path / "transactions.csv", index=False)
    pd.testing.assert_frame_equal(before, build_features(tmp_path))
