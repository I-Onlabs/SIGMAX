"""
Signal Modules

Pluggable signal modules that provide additional context for trading decisions.

Modules:
- volatility_scanner: RV and turnover metrics
- news_sentiment: NLP analysis of crypto news
- listings_watcher: New listing alerts
- reddit_sentiment: Social media sentiment (optional)

All signals publish SignalEvent messages to stream 13.
"""
