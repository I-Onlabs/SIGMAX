"""
Order Book Shard Service

Maintains single-writer L2 order books for assigned symbols.
Handles:
- MdUpdate subscription from ingestion service
- Order book state management
- TopOfBook and BookDelta publishing
- Book metrics (imbalance, spread, microprice)
"""
