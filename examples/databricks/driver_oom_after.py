"""Distributed alternative to driver_oom_before.py (illustrative, NOT benchmarked).

Returns a Spark DataFrame, not a Python dict: changing output type is a contract
change. Only use if downstream accepts this contract, or redesign the boundary.
Requires compatible PySpark on the Databricks cluster; never run automatically.
"""


def totals_distributed(events):
    from pyspark.sql import functions as F

    return (
        events.select("category", "amount")
        .groupBy("category")
        .agg(F.sum("amount").alias("total"))
    )
