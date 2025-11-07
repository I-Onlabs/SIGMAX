"""
Exchange API Management - REST API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "core"))

from utils.exchange_manager import ExchangeCredentialManager


router = APIRouter(prefix="/api/exchanges", tags=["exchanges"])

# Initialize credential manager
credential_manager = ExchangeCredentialManager()


# Request/Response Models
class AddExchangeRequest(BaseModel):
    """Request to add exchange credentials"""
    exchange: str = Field(..., description="Exchange type (binance, coinbase, etc.)")
    name: str = Field(..., description="User-friendly name")
    api_key: str = Field(..., description="API key")
    api_secret: str = Field(..., description="API secret")
    passphrase: Optional[str] = Field(None, description="Passphrase (if required)")
    testnet: bool = Field(False, description="Use testnet")
    enabled: bool = Field(True, description="Enable this exchange")


class UpdateExchangeRequest(BaseModel):
    """Request to update exchange credentials"""
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None
    testnet: Optional[bool] = None
    enabled: Optional[bool] = None


class ExchangeResponse(BaseModel):
    """Exchange credential response"""
    id: str
    exchange: str
    name: str
    api_key: str  # Masked
    api_secret: str  # Masked
    passphrase: Optional[str]  # Masked
    network: str
    enabled: bool
    testnet: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    last_connected: Optional[str]
    connection_status: str


class ConnectionTestResponse(BaseModel):
    """Connection test response"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    balance: Optional[Dict[str, Any]] = None
    network: Optional[str] = None


# Endpoints

@router.get("/", response_model=List[ExchangeResponse])
async def get_all_exchanges():
    """
    Get all exchange credentials (with masked keys)

    Returns:
        List of exchange credentials
    """
    try:
        credentials = credential_manager.get_all_credentials(decrypted=False)
        return credentials

    except Exception as e:
        logger.error(f"Failed to get exchanges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{credential_id}", response_model=ExchangeResponse)
async def get_exchange(credential_id: str):
    """
    Get specific exchange credential

    Args:
        credential_id: Exchange credential ID

    Returns:
        Exchange credential
    """
    credential = credential_manager.get_credential(credential_id)

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange credential not found"
        )

    # Mask credentials
    cred_dict = credential.to_dict()
    cred_dict["api_key"] = credential_manager._mask_key(
        credential_manager._decrypt(credential.api_key)
    )
    cred_dict["api_secret"] = "***********"
    cred_dict["passphrase"] = "***********" if credential.passphrase else None

    return cred_dict


@router.post("/", response_model=ExchangeResponse, status_code=status.HTTP_201_CREATED)
async def add_exchange(request: AddExchangeRequest):
    """
    Add new exchange credentials

    Args:
        request: Exchange credentials

    Returns:
        Created credential
    """
    try:
        credential = credential_manager.add_credential(
            exchange=request.exchange,
            name=request.name,
            api_key=request.api_key,
            api_secret=request.api_secret,
            passphrase=request.passphrase,
            testnet=request.testnet,
            enabled=request.enabled
        )

        # Return masked version
        cred_dict = credential.to_dict()
        cred_dict["api_key"] = credential_manager._mask_key(request.api_key)
        cred_dict["api_secret"] = "***********"
        cred_dict["passphrase"] = "***********" if request.passphrase else None

        return cred_dict

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to add exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{credential_id}", response_model=ExchangeResponse)
async def update_exchange(credential_id: str, request: UpdateExchangeRequest):
    """
    Update exchange credentials

    Args:
        credential_id: Exchange credential ID
        request: Fields to update

    Returns:
        Updated credential
    """
    try:
        # Filter out None values
        updates = {k: v for k, v in request.dict().items() if v is not None}

        credential = credential_manager.update_credential(credential_id, **updates)

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exchange credential not found"
            )

        # Return masked version
        cred_dict = credential.to_dict()
        cred_dict["api_key"] = credential_manager._mask_key(
            credential_manager._decrypt(credential.api_key)
        )
        cred_dict["api_secret"] = "***********"
        cred_dict["passphrase"] = "***********" if credential.passphrase else None

        return cred_dict

    except Exception as e:
        logger.error(f"Failed to update exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange(credential_id: str):
    """
    Delete exchange credentials

    Args:
        credential_id: Exchange credential ID
    """
    success = credential_manager.delete_credential(credential_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange credential not found"
        )

    return None


@router.post("/{credential_id}/test", response_model=ConnectionTestResponse)
async def test_exchange_connection(credential_id: str):
    """
    Test exchange connection

    Args:
        credential_id: Exchange credential ID

    Returns:
        Connection test result
    """
    try:
        result = credential_manager.test_connection(credential_id)
        return result

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/supported/list")
async def get_supported_exchanges():
    """
    Get list of supported exchanges

    Returns:
        List of supported exchanges with metadata
    """
    from utils.exchange_manager import ExchangeType

    exchanges = [
        {
            "id": "binance",
            "name": "Binance",
            "testnet_available": True,
            "requires_passphrase": False
        },
        {
            "id": "coinbase",
            "name": "Coinbase",
            "testnet_available": True,
            "requires_passphrase": True
        },
        {
            "id": "kraken",
            "name": "Kraken",
            "testnet_available": False,
            "requires_passphrase": False
        },
        {
            "id": "bybit",
            "name": "Bybit",
            "testnet_available": True,
            "requires_passphrase": False
        },
        {
            "id": "hyperliquid",
            "name": "Hyperliquid",
            "testnet_available": True,
            "requires_passphrase": False
        },
        {
            "id": "alpaca",
            "name": "Alpaca",
            "testnet_available": True,
            "requires_passphrase": False
        },
        {
            "id": "okx",
            "name": "OKX",
            "testnet_available": True,
            "requires_passphrase": True
        }
    ]

    return {"exchanges": exchanges}
