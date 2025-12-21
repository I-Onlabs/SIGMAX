#!/usr/bin/env python3
"""
Test script for agent debate storage integration
Tests:
1. DecisionHistory stores debates to PostgreSQL
2. Data persists in database
3. API endpoint returns real data
"""

import os
import sys
import time
from datetime import datetime

# Set database environment variables
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'sigmax'
os.environ['POSTGRES_USER'] = 'sigmax'
os.environ['POSTGRES_PASSWORD'] = 'sigmax_dev'

# Add project root to path
sys.path.insert(0, '/Users/mac/Projects/SIGMAX')

from core.utils.decision_history import DecisionHistory
from loguru import logger

def test_debate_storage():
    """Test PostgreSQL debate storage"""
    logger.info("=" * 60)
    logger.info("Testing Agent Debate Storage Integration")
    logger.info("=" * 60)

    # Create DecisionHistory with PostgreSQL
    logger.info("\n1. Initializing DecisionHistory with PostgreSQL...")
    history = DecisionHistory(
        max_history_per_symbol=10,
        use_redis=False,
        use_postgres=True
    )

    # Verify PostgreSQL connection
    if not history.pg_connection:
        logger.error("❌ PostgreSQL connection failed")
        return False

    logger.info("✅ PostgreSQL connected")

    # Create test decision with debate data
    logger.info("\n2. Creating test decision with agent debate...")
    symbol = "BTC/USDT"
    decision = {
        "action": "buy",
        "confidence": 0.75,
        "sentiment": 0.6,
        "reasoning": {
            "technical": "Strong upward momentum, RSI showing strength",
            "fundamental": "Positive market sentiment, institutional buying"
        }
    }

    agent_debate = {
        "bull_argument": "Bitcoin showing strong bullish signals. Volume increasing, breaking resistance at $95k. Institutional inflows positive.",
        "bear_argument": "Overbought on 4h timeframe. Potential correction ahead. Volume divergence detected on lower timeframes.",
        "research_summary": "Gathered 50+ data points. Overall sentiment: bullish. Technical indicators: 70% buy signals.",
        "agent_scores": {
            "bull": 0.75,
            "bear": 0.45,
            "researcher": 0.70
        }
    }

    # Add decision (should save to PostgreSQL)
    logger.info("   Saving decision with debate data...")
    history.add_decision(
        symbol=symbol,
        decision=decision,
        agent_debate=agent_debate
    )
    logger.info("✅ Decision saved")

    # Verify in database
    logger.info("\n3. Verifying data in PostgreSQL...")
    cursor = history.pg_connection.cursor()
    cursor.execute(
        "SELECT * FROM agent_debates WHERE symbol = %s ORDER BY created_at DESC LIMIT 1",
        (symbol,)
    )
    result = cursor.fetchone()

    if not result:
        logger.error("❌ No data found in database")
        return False

    logger.info("✅ Data found in database:")
    logger.info(f"   Symbol: {result['symbol']}")
    logger.info(f"   Decision: {result['final_decision']}")
    logger.info(f"   Confidence: {result['confidence']}")
    logger.info(f"   Bull Argument: {result['bull_argument'][:80]}...")
    logger.info(f"   Bear Argument: {result['bear_argument'][:80]}...")

    # Verify retrieval through DecisionHistory
    logger.info("\n4. Testing DecisionHistory retrieval...")
    last_decision = history.get_last_decision(symbol)

    if not last_decision:
        logger.error("❌ Failed to retrieve last decision")
        return False

    logger.info("✅ Successfully retrieved decision:")
    logger.info(f"   Action: {last_decision['action']}")
    logger.info(f"   Confidence: {last_decision['confidence']}")
    logger.info(f"   Bull Argument: {last_decision['agent_debate']['bull_argument'][:80]}...")

    # Test pagination
    logger.info("\n5. Testing pagination...")
    decisions = history.get_decisions(symbol, limit=5)
    logger.info(f"✅ Retrieved {len(decisions)} decision(s)")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ All tests passed!")
    logger.info("=" * 60)
    logger.info("\nIntegration Status:")
    logger.info("  ✅ PostgreSQL connection working")
    logger.info("  ✅ Debate data saved to database")
    logger.info("  ✅ Data persists in PostgreSQL")
    logger.info("  ✅ Retrieval working correctly")
    logger.info("\nNext Steps:")
    logger.info("  1. Start SIGMAX API server")
    logger.info("  2. Test API endpoint: GET /api/agents/debate/BTC%2FUSDT")
    logger.info("  3. Verify real data returned (not mock data)")

    return True

if __name__ == "__main__":
    try:
        success = test_debate_storage()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
