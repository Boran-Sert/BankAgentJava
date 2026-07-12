"""Provides core functionalities for the tools module."""
from typing import List, Dict, Any
from langchain_core.tools import tool
from pydantic import Field
from app.core.mock_db import db
from app.core.logger import logger



@tool
def get_balance(user_id: str = "test_user_1") -> List[Dict[str, Any]]:
    """Hesap bakiyem ne kadar, hesabımda ne kadar para var, kredi kartı borcum nedir"""
    cards = db.get_user_cards(user_id)
    cards_data = [{"card_number": card.card_number, "balance": card.balance, "debt": card.debt} for card in cards]
    logger.debug("get_balance_tool_executed", data=cards_data)
    return cards_data
    


@tool
def make_payment(
    card_id: str = Field(description="Kredi Kartı Numarası (Son 4 hanesi veya ilk 4 hanesi veya tam numarası olabilir)"),
    amount: float = Field(description="Ödenecek Tutar"),
    user_id: str = "test_user_1"
) -> Dict[str, Any]:
    """Kredi kartı borcumu ödemek istiyorum, Kartıma para yatır, Borç ödeme"""
    if not card_id or not amount:
        return {"error": "Missing parameters for payment."}
    
    # In a real scenario, this would deduct amount from balance/debt in the DB.
    # We will just return a success payload.
    return {
        "status": "success",
        "action": "MAKE_PAYMENT",
        "card_id": card_id,
        "paid_amount": amount,
        "remaining_debt": 0.0 # Mocked
    }

# We define the list of tools to be imported elsewhere
banking_tools = [get_balance, make_payment]
