"""Anti-pattern: illustrative ONLY; do not run on a production table.

Collecting all events on the Spark driver is unsafe when cardinality is unknown.
"""


def totals_on_driver(events):
    totals: dict[str, int] = {}
    for row in events.select("category", "amount").collect():
        # Contract in this small demo: non-null category, integer amount.
        totals[row.category] = totals.get(row.category, 0) + row.amount
    return totals
