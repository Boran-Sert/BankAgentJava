"""Provides core functionalities for the grounding module."""

from app.graph.state import AgentState
from app.core.logger import logger
from langchain_core.messages import AIMessage
from app.core.mock_db import db


def grounding_node(state: AgentState) -> dict:
    """
    Translates raw text parameters into concrete backend identifiers (e.g. UUIDs).
    """
    logger.info(
        "node_execution", node="grounding_node", session_id=state.get("session_id")
    )

    collected = state.get("collected_parameters", {})
    grounded = state.get("grounded_parameters", {})
    user_id = state.get("user_id", "test_user_1")  # Doğru default "test_user_1" olmalı

    # In a real app, we would query the database here using state['user_id']
    # For now, we mock the grounding.
    new_grounded = {}
    for key, value in collected.items():
        if key not in grounded:
            # 1. Önce doğrudan geçişi yapıyoruz
            new_grounded[key] = value

            # 2. Eğer bu bir account_id veya account_ids ise MANUEL DB DOĞRULAMASI yapıyoruz
            if key in ["account_id", "account_ids"]:
                user = db.get_user(user_id)
                # Eğer user None dönerse diye güvenlik kontrolü:
                if not user:
                    continue

                accounts = getattr(user, "accounts", {})
                
                # Değer tekil bir string de olabilir, liste de olabilir. Hepsini listeye çevirip kontrol edelim.
                values_to_check = value if isinstance(value, list) else [value]
                
                invalid_ids = []
                for val in values_to_check:
                    is_valid = any(acc.get("id") == val for acc in accounts.values())
                    if not is_valid:
                        invalid_ids.append(val)

                if invalid_ids:
                    # HESAP YOKSA: Sistemi çökertme (raise ValueError yapma!).
                    # Bunun yerine LangGraph'ı durdurup kullanıcıya mesaj dön.
                    invalid_str = ", ".join(invalid_ids)
                    error_msg = AIMessage(
                        content=f"Sistemde '{invalid_str}' numaralı bir hesabınız bulunmamaktadır. Lütfen geçerli hesapları seçiniz."
                    )

                    # Hatalı olan bu ID'yi hafızadan silmeliyiz ki AI tekrar sorabilsin
                    collected_copy = dict(collected)
                    if key in collected_copy:
                        del collected_copy[key]

                    return {
                        "messages": [error_msg],
                        "collected_parameters": collected_copy,
                        "grounding_error": True,
                    }

    if new_grounded:
        merged = {**grounded, **new_grounded}
        logger.info("parameters_grounded", grounded_count=len(new_grounded))
        return {"grounded_parameters": merged}

    return {}
