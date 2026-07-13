"""Provides core functionalities for the mock_db module."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid


class Card(BaseModel):
    """Defines the Card structure."""

    id: str
    card_number: str
    balance: float
    debt: float


class User(BaseModel):
    """Defines the User structure."""

    user_id: str
    name: str
    cards: List[Card]
    accounts: Optional[Dict[str, Any]] = None


class MockDatabase:
    """
    A mock database to simulate banking data for testing purposes.
    """

    def __init__(self):
        """Executes the   init   operation."""
        # Hardcoded mock data: 1 User with 5 cards
        self.users = {
            "test_user_1": User(
                accounts={
                    "vadesiz": {
                        "name": "TL Vadesiz Hesap",
                        "balance": 15000.0,
                        "currency": "TL",
                    },
                    "vadeli": {
                        "id": "1",
                        "name": "TL Vadeli Hesap",
                        "balance": 20000.0,
                        "monthly_interest_rate": 35.0,
                        "currency": "TL",
                    },
                    "vadeli2": {
                        "id": "2",
                        "name": "USD Vadeli Hesap",
                        "balance": 20000.0,
                        "monthly_interest_rate": 35.0,
                        "currency": "USD",
                    },
                },
                user_id="test_user_1",
                name="Test Kullanıcısı",
                cards=[
                    Card(
                        id=str(uuid.uuid4()),
                        card_number="4543 **** **** 9012",
                        balance=15000.0,
                        debt=2500.0,
                    ),
                    Card(
                        id=str(uuid.uuid4()),
                        card_number="5521 **** **** 1098",
                        balance=5000.0,
                        debt=5000.0,
                    ),
                    Card(
                        id=str(uuid.uuid4()),
                        card_number="4321 **** **** 3333",
                        balance=20000.0,
                        debt=0.0,
                    ),
                    Card(
                        id=str(uuid.uuid4()),
                        card_number="5100 **** **** 6666",
                        balance=10000.0,
                        debt=850.50,
                    ),
                    Card(
                        id=str(uuid.uuid4()),
                        card_number="4999 **** **** 9999",
                        balance=3000.0,
                        debt=1200.75,
                    ),
                ],
            )
        }

    def get_user(self, user_id: str) -> Optional[User]:
        """Executes the Get user operation."""
        return self.users.get(user_id)

    def get_user_cards(self, user_id: str) -> List[Card]:
        """Executes the Get user cards operation."""
        user = self.get_user(user_id)
        if user:
            return user.cards
        return []


# Singleton instance to be used across the app
db = MockDatabase()
