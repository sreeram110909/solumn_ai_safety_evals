from report.totals import totals


def test_totals_include_every_row():
    rows = [{"region": "a", "amount": 1}, {"region": "b", "amount": 2}, {"region": "a", "amount": 4}]
    assert totals(rows) == {"a": 5, "b": 2}
