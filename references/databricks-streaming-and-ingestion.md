# Azure Databricks — streaming, incremental ingestion and state

Use this file only for `readStream`, Auto Loader, micro-batch ETL, stream joins/aggregation/deduplication, or checkpoint/state incidents.

## Memory surfaces

- Stateful operators maintain state across micro-batches. Without correct event-time watermark/eviction, state may grow indefinitely.
- Watermarks trade late-event tolerance against state size and latency. A shorter watermark can drop valid late data; never tighten it for RAM alone without business approval and a correctness check.
- Output mode, event-time column, grouping/window logic and state provider matter. A watermark's presence is not proof every stateful operator is bounded.
- Batch duration, input rate and outstanding files interact with executor RAM, shuffle and throughput. Monitor the backlog and state-store sizes rather than only driver RSS.
- Checkpoint location/state encodes recovery. Do not delete or redirect a checkpoint as a routine "memory cleanup"; doing so can replay/skip data or change processing semantics.

## Ingestion approach

- For continuously arriving cloud files, consider **Auto Loader** incremental ingestion instead of Python drivers listing/reading every file at once when it fits the existing pipeline.
- Use controlled micro-batches, schemas, and idempotent writes; avoid full historic rereads on every run.
- Check DBR feature support, storage permissions, schema evolution rules and exactly-once/at-least-once assumptions before changes.
- On serverless notebooks/jobs, streaming trigger support differs from classic; check the current supported `AvailableNow` and other trigger modes before migrating.

References: `https://learn.microsoft.com/en-us/azure/databricks/structured-streaming/watermarks`, `https://learn.microsoft.com/en-us/azure/databricks/structured-streaming/checkpoints`, `https://learn.microsoft.com/en-us/azure/databricks/ingestion/cloud-object-storage/`, and serverless limitations.
