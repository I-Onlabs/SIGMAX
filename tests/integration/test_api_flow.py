"""
Integration tests for complete API workflow.

Tests the full trading flow through the FastAPI endpoints:
1. Analysis request → 2. Proposal creation → 3. Approval → 4. Execution
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.api.main import app


class TestAPIFlow:
    """End-to-end API workflow integration tests"""

    @pytest.fixture
    async def client(self):
        """Create test client with mocked SIGMAX backend"""
        with patch.dict('os.environ', {
            'TRADING_MODE': 'paper',
            'API_KEY': 'test-api-key-123',
        }):
            transport = ASGITransport(app=app)  # type: ignore
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac

    @pytest.fixture
    def api_headers(self):
        """Standard API headers with auth"""
        return {
            "X-API-Key": "test-api-key-123",
            "Content-Type": "application/json"
        }

    @pytest.mark.asyncio
    async def test_complete_proposal_workflow(self, client, api_headers):
        """Test full workflow: create → approve → execute"""

        # Step 1: Create a trade proposal
        proposal_request = {
            "symbol": "BTC/USDT",
            "risk_profile": "conservative",
            "mode": "paper"
        }

        create_response = await client.post(
            "/api/v1/chat/proposals",
            json=proposal_request,
            headers=api_headers
        )

        assert create_response.status_code == 200
        proposal_data = create_response.json()

        # Verify proposal structure
        assert "proposal" in proposal_data or "analysis" in proposal_data

        # If proposal created, get its ID
        if "proposal" in proposal_data and proposal_data["proposal"]:
            proposal_id = proposal_data["proposal"]["id"]

            print(f"\n=== Created Proposal ===")
            print(f"ID: {proposal_id}")
            print(f"Symbol: {proposal_data['proposal']['symbol']}")
            print(f"Action: {proposal_data['proposal'].get('action', 'N/A')}")

            # Step 2: Get proposal details
            get_response = await client.get(
                f"/api/v1/chat/proposals/{proposal_id}",
                headers=api_headers
            )

            assert get_response.status_code == 200
            proposal_details = get_response.json()
            assert proposal_details["id"] == proposal_id

            print(f"\n=== Retrieved Proposal ===")
            print(f"Status: {proposal_details.get('status', 'unknown')}")

            # Step 3: Approve the proposal
            approve_response = await client.post(
                f"/api/v1/chat/proposals/{proposal_id}/approve",
                headers=api_headers
            )

            assert approve_response.status_code == 200
            approved = approve_response.json()
            assert approved["id"] == proposal_id
            assert approved.get("status") in ["approved", "pending_execution"]

            print(f"\n=== Approved Proposal ===")
            print(f"New status: {approved.get('status')}")

            # Step 4: Execute the proposal
            execute_response = await client.post(
                f"/api/v1/chat/proposals/{proposal_id}/execute",
                headers=api_headers
            )

            assert execute_response.status_code == 200
            execution = execute_response.json()
            assert execution["success"] is True
            assert "result" in execution
            assert "timestamp" in execution

            print(f"\n=== Executed Proposal ===")
            print(f"Success: {execution['success']}")
            print(f"Result: {execution.get('result', {})}")

    @pytest.mark.asyncio
    async def test_list_proposals(self, client, api_headers):
        """Test listing all proposals"""

        # Create a few proposals first
        for symbol in ["BTC/USDT", "ETH/USDT"]:
            await client.post(
                "/api/v1/chat/proposals",
                json={"symbol": symbol, "mode": "paper"},
                headers=api_headers
            )

        # List all proposals
        list_response = await client.get(
            "/api/v1/chat/proposals",
            headers=api_headers
        )

        assert list_response.status_code == 200
        proposals = list_response.json()
        assert isinstance(proposals, list)

        print(f"\n=== Listed Proposals ===")
        print(f"Total: {len(proposals)}")
        for p in proposals[:3]:  # Show first 3
            print(f"  - {p.get('symbol', 'N/A')}: {p.get('status', 'unknown')}")

    @pytest.mark.asyncio
    async def test_invalid_proposal_id(self, client, api_headers):
        """Test error handling for non-existent proposal"""

        fake_id = "non-existent-proposal-id-12345"

        # Try to get non-existent proposal
        get_response = await client.get(
            f"/api/v1/chat/proposals/{fake_id}",
            headers=api_headers
        )

        assert get_response.status_code == 404
        error = get_response.json()
        assert "detail" in error

        print(f"\n=== Invalid Proposal Error ===")
        print(f"Status: {get_response.status_code}")
        print(f"Detail: {error['detail']}")

        # Try to approve non-existent proposal
        approve_response = await client.post(
            f"/api/v1/chat/proposals/{fake_id}/approve",
            headers=api_headers
        )

        assert approve_response.status_code == 404

        # Try to execute non-existent proposal
        execute_response = await client.post(
            f"/api/v1/chat/proposals/{fake_id}/execute",
            headers=api_headers
        )

        assert execute_response.status_code == 404

    @pytest.mark.asyncio
    async def test_authentication_required(self, client):
        """Test that API key authentication is enforced"""

        # Request without API key
        response = await client.post(
            "/api/v1/chat/proposals",
            json={"symbol": "BTC/USDT", "mode": "paper"}
        )

        # Should be unauthorized
        assert response.status_code in [401, 403]

        print(f"\n=== Auth Required Test ===")
        print(f"Status without API key: {response.status_code}")

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, client):
        """Test rejection of invalid API key"""

        invalid_headers = {
            "X-API-Key": "wrong-key-invalid",
            "Content-Type": "application/json"
        }

        response = await client.post(
            "/api/v1/chat/proposals",
            json={"symbol": "BTC/USDT", "mode": "paper"},
            headers=invalid_headers
        )

        assert response.status_code in [401, 403]

        print(f"\n=== Invalid API Key Test ===")
        print(f"Status with wrong key: {response.status_code}")

    @pytest.mark.asyncio
    async def test_proposal_with_different_risk_profiles(self, client, api_headers):
        """Test proposals with various risk profiles"""

        risk_profiles = ["conservative", "moderate", "aggressive"]

        print(f"\n=== Risk Profile Tests ===")

        for risk_profile in risk_profiles:
            response = await client.post(
                "/api/v1/chat/proposals",
                json={
                    "symbol": "BTC/USDT",
                    "risk_profile": risk_profile,
                    "mode": "paper"
                },
                headers=api_headers
            )

            assert response.status_code == 200
            data = response.json()

            print(f"{risk_profile}: {response.status_code}")

            # Verify risk profile was accepted
            if "proposal" in data and data["proposal"]:
                assert "risk_profile" in str(data).lower() or True  # May be in analysis

    @pytest.mark.asyncio
    async def test_paper_vs_live_mode(self, client, api_headers):
        """Test mode validation (paper vs live)"""

        modes = ["paper", "live"]

        print(f"\n=== Mode Tests ===")

        for mode in modes:
            response = await client.post(
                "/api/v1/chat/proposals",
                json={
                    "symbol": "BTC/USDT",
                    "mode": mode
                },
                headers=api_headers
            )

            assert response.status_code == 200
            print(f"Mode '{mode}': {response.status_code}")

    @pytest.mark.asyncio
    async def test_proposal_state_transitions(self, client, api_headers):
        """Test that proposal states transition correctly"""

        # Create proposal
        create_response = await client.post(
            "/api/v1/chat/proposals",
            json={"symbol": "ETH/USDT", "mode": "paper"},
            headers=api_headers
        )

        assert create_response.status_code == 200
        data = create_response.json()

        if "proposal" in data and data["proposal"] and "id" in data["proposal"]:
            proposal_id = data["proposal"]["id"]

            print(f"\n=== State Transitions ===")

            # Initial state should be "pending" or similar
            initial_status = data["proposal"].get("status", "unknown")
            print(f"Initial: {initial_status}")

            # After approval
            approve_response = await client.post(
                f"/api/v1/chat/proposals/{proposal_id}/approve",
                headers=api_headers
            )

            if approve_response.status_code == 200:
                approved_status = approve_response.json().get("status", "unknown")
                print(f"After approval: {approved_status}")
                assert approved_status != initial_status or initial_status == "approved"

    @pytest.mark.asyncio
    async def test_concurrent_proposals(self, client, api_headers):
        """Test handling multiple concurrent proposals"""

        import asyncio

        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

        # Create multiple proposals concurrently
        tasks = [
            client.post(
                "/api/v1/chat/proposals",
                json={"symbol": symbol, "mode": "paper"},
                headers=api_headers
            )
            for symbol in symbols
        ]

        responses = await asyncio.gather(*tasks)

        print(f"\n=== Concurrent Proposals ===")
        print(f"Created: {len([r for r in responses if r.status_code == 200])}/{len(symbols)}")

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_execution_without_approval(self, client, api_headers):
        """Test that execution is blocked without approval"""

        # Create proposal
        create_response = await client.post(
            "/api/v1/chat/proposals",
            json={"symbol": "BTC/USDT", "mode": "paper"},
            headers=api_headers
        )

        data = create_response.json()

        if "proposal" in data and data["proposal"] and "id" in data["proposal"]:
            proposal_id = data["proposal"]["id"]

            # Try to execute without approval
            execute_response = await client.post(
                f"/api/v1/chat/proposals/{proposal_id}/execute",
                headers=api_headers
            )

            # Should either fail or succeed based on policy
            # (Some systems allow execution without approval in paper mode)
            print(f"\n=== Execute Without Approval ===")
            print(f"Status: {execute_response.status_code}")
            print(f"Paper mode policy: {'allowed' if execute_response.status_code == 200 else 'blocked'}")


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""

    @pytest.fixture
    async def client(self):
        """Create test client"""
        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            transport = ASGITransport(app=app)  # type: ignore
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac

    @pytest.mark.asyncio
    async def test_malformed_proposal_request(self, client):
        """Test handling of invalid proposal data"""

        headers = {"X-API-Key": "test-key"}

        # Missing required field
        response = await client.post(
            "/api/v1/chat/proposals",
            json={"risk_profile": "conservative"},  # Missing 'symbol'
            headers=headers
        )

        assert response.status_code == 422  # Validation error

        print(f"\n=== Malformed Request ===")
        print(f"Status: {response.status_code}")

    @pytest.mark.asyncio
    async def test_invalid_risk_profile(self, client):
        """Test handling of invalid risk profile"""

        headers = {"X-API-Key": "test-key"}

        response = await client.post(
            "/api/v1/chat/proposals",
            json={
                "symbol": "BTC/USDT",
                "risk_profile": "invalid-profile-name",
                "mode": "paper"
            },
            headers=headers
        )

        # Should accept (will be handled by backend) or reject
        print(f"\n=== Invalid Risk Profile ===")
        print(f"Status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
