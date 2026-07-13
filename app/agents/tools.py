"""Provides core functionalities for the tools module."""

from typing import List, Dict, Any
from langchain_core.tools import tool
from pydantic import Field
from app.core.mock_db import db
from app.core.logger import logger


import structlog

@tool
def get_balance() -> List[Dict[str, Any]]:
    """Hesap bakiyem ne kadar, hesabımda ne kadar para var, kredi kartı borcum nedir"""
    user_id = structlog.contextvars.get_contextvars().get("user_id", "test_user_1")
    cards = db.get_user_cards(user_id)
    cards_data = [
        {"card_number": card.card_number, "balance": card.balance, "debt": card.debt}
        for card in cards
    ]
    logger.debug("get_balance_tool_executed", data=cards_data)
    return cards_data


@tool
def make_payment(
    card_id: str = Field(
        description="Kredi Kartı Numarası (Son 4 hanesi veya ilk 4 hanesi veya tam numarası olabilir)"
    ),
    amount: float = Field(description="Ödenecek Tutar"),
) -> Dict[str, Any]:
    """Kredi kartı borcumu ödemek istiyorum, Kartıma para yatır, Borç ödeme"""
    user_id = structlog.contextvars.get_contextvars().get("user_id", "test_user_1")
    if not card_id or not amount:
        return {"error": "Missing parameters for payment."}

    # In a real scenario, this would deduct amount from balance/debt in the DB.
    # We will just return a success payload.
    return {
        "status": "success",
        "action": "MAKE_PAYMENT",
        "card_id": card_id,
        "paid_amount": amount,
        "remaining_debt": 0.0,  # Mocked
    }


@tool
def get_account_types() -> Dict[str, Any]:
    """Kullanıcının sahip olduğu tüm hesapların (vadesiz, vadeli vb.) türlerini, bakiye ve detaylarını listeler.
    Kullanıcı 'hesaplarım neler', 'hesap türlerim' veya 'ne kadar param var' diye sorduğunda kullanılır."""
    user_id = structlog.contextvars.get_contextvars().get("user_id", "test_user_1")
    user = db.get_user(user_id)
    if not user:
        return {"error": "Kullanıcı bulunamadı."}

    accounts = getattr(user, "accounts", {})
    logger.debug("get_account_types_tool_executed", data=accounts)
    return accounts


@tool
def calc_monthly_income_savings(
    account_ids: List[str] = Field(
        description="Aylık faizi hesaplanacak vadeli hesabın/hesapların benzersiz ID'lerinin listesi (örn: ['1', '2']). Kullanıcı tüm hesaplarını istiyorsa hepsini listeye ekle.",
    ),
) -> List[Dict[str, Any]]:
    """Kullanıcının belirli vadeli hesaplarındaki aylık faiz getirisini hesaplar ve detaylarıyla birlikte döner.
    Kullanıcı 'vadeli hesaplarımın getirisi nedir', 'aylık faiz kazancım ne kadar' diye sorduğunda kullanılır."""
    user_id = structlog.contextvars.get_contextvars().get("user_id", "test_user_1")
    user = db.get_user(user_id)
    if not user:
        return [{"error": "Kullanıcı bulunamadı."}]

    accounts = getattr(user, "accounts", {})
    results = []

    for acc_id in account_ids:
        # Find the specific savings account by ID
        target_account = None
        for acc_key, acc_data in accounts.items():
            if acc_key.startswith("vadeli") and acc_data.get("id") == acc_id:
                target_account = acc_data
                break

        if not target_account:
            results.append({
                "error": f"Belirtilen ID'ye ({acc_id}) sahip bir vadeli hesap bulunamadı.",
                "requested_id": acc_id
            })
            continue

        balance = target_account.get("balance", 0.0)
        monthly_interest_rate = target_account.get("monthly_interest_rate", 0.0)

        # Vadeli hesap aylık faiz hesaplaması
        monthly_income = (balance * (monthly_interest_rate / 100)) / 12

        # Hesaplama sonucunu yeni bir sözlüğe kopyalayarak dönüyoruz ki orijinal veriyi bozmayalım
        result = dict(target_account)
        result["monthly_interest_income"] = monthly_income
        results.append(result)

    logger.debug("calc_monthly_income_savings_tool_executed", data=results)
    return results


@tool
def get_user_account_options() -> List[Dict[str, Any]]:
    """Kullanıcının sahip olduğu hesapların sadece isimlerini ve ID'lerini (maskelenmiş güvenli verilerini) döner.
    Bu araç, kullanıcının hesapları arasında belirsizlik (ambiguity) olduğunda, güvenli bir şekilde hesap isimlerini listelemek için kullanılır."""
    user_id = structlog.contextvars.get_contextvars().get("user_id", "test_user_1")
    user = db.get_user(user_id)
    if not user:
        return [{"error": "Kullanıcı bulunamadı."}]

    accounts = getattr(user, "accounts", {})

    # Gelişime Açık Maskeleme (Sanitized Projection)
    # Gerçek bankacılıkta burada yüzlerce veri olabilir. Sadece izin verilen alanları (Allowed Fields) dışarı aktarıyoruz.
    ALLOWED_FIELDS = {"id", "name", "currency", "type"}

    safe_accounts = []
    for acc_key, acc_data in accounts.items():
        # Maskelenmiş yeni bir sözlük (dictionary) oluşturuyoruz
        safe_acc = {}
        for field in ALLOWED_FIELDS:
            if field in acc_data:
                safe_acc[field] = acc_data[field]

        # Ek olarak, key değerini tür (type) olarak ekleyebiliriz (vadesiz, vadeli vb.)
        if "type" not in safe_acc:
            safe_acc["type"] = (
                "Vadeli Hesap" if acc_key.startswith("vadeli") else "Vadesiz Hesap"
            )

        safe_accounts.append(safe_acc)

    logger.debug("get_user_account_options_executed", count=len(safe_accounts))
    return safe_accounts


@tool
def get_credit_card_options() -> List[Dict[str, Any]]:
    """Kullanıcının kredi kartlarının maskelenmiş (sadece son 4 hanesi ve kart ID'si) listesini döner.
    Borç ödeme gibi işlemlerde hangi kartın seçileceği belirsizse bu araçla güvenli bir liste alınır."""
    user_id = structlog.contextvars.get_contextvars().get("user_id", "test_user_1")
    cards = db.get_user_cards(user_id)

    safe_cards = []
    for card in cards:
        safe_cards.append(
            {
                "id": card.card_number,  # Assuming card_number is the ID for now
                "masked_number": f"**** **** **** {card.card_number[-4:]}",
                "name": f"Kredi Kartı ({card.card_number[-4:]})",
            }
        )

    logger.debug("get_credit_card_options_executed", count=len(safe_cards))
    return safe_cards


# We define the list of tools to be imported elsewhere
banking_tools = [
    get_balance,
    make_payment,
    get_account_types,
    calc_monthly_income_savings,
    get_user_account_options,
]
