"""Provides core functionalities for the mapper module."""
import uuid
import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List
from app.core.contracts import ServiceSpec

logger = logging.getLogger(__name__)


class ContractMapper:
    """
    Dynamically maps internal Python parameters to the strict contract
    expected by the Java backend using Vectorial Similarity and strict banking types.
    """

    @staticmethod
    async def map_to_java(
        collected_parameters: Dict[str, Any], specs: List[ServiceSpec]
    ) -> Dict[str, Any]:
        """
        Maps python's collected parameters to Java's expected contract using
        Semantic/Vectorial similarity for key matching, paired with strict type validation.
        """
        mapped_result: Dict[str, Any] = {}
        unmapped_python_keys = list(collected_parameters.keys())

        for spec in specs:
            java_key = spec.name
            expected_type = spec.type.lower()

            # Use Vectorial Similarity to find the most semantically related python key
            best_match_key = await ContractMapper._find_best_semantic_match(
                java_key, spec.description or "", unmapped_python_keys
            )

            if best_match_key:
                value = collected_parameters[best_match_key]

                # After finding semantic match, strictly validate banking types
                valid_value = ContractMapper._validate_and_cast_banking_type(
                    value, expected_type
                )

                if valid_value is not None:
                    mapped_result[java_key] = valid_value
                    unmapped_python_keys.remove(best_match_key)
                    logger.debug(
                        f"Semantic match & Type OK: {best_match_key} -> {java_key}"
                    )
                else:
                    raise ValueError(
                        f"Strict Contract Violation: Semantic match '{best_match_key}' for '{java_key}' failed type validation for '{spec.type}'. Expected precision banking type."
                    )
            else:
                # Missing parameter for expected Java spec
                raise ValueError(
                    f"Strict Contract Violation: No semantic match found for Java expected field '{java_key}'."
                )

        #################################################### BURASINI GÖZDEN GEÇİR ######################################################

        # [PHASE 5] Strict Pydantic Validation
        # Dynamically create a Pydantic model based on the expected Java specs
        # to ensure the final payload is structurally flawless before hitting Java.
        from pydantic import create_model, ValidationError

        pydantic_fields = {}
        for spec in specs:
            java_key = spec.name
            # Map Java/Service types to Python types for Pydantic
            t = spec.type.lower()
            if "uuid" in t:
                from uuid import UUID

                py_type = UUID
            elif "decimal" in t or "bigdecimal" in t or "money" in t:
                from decimal import Decimal

                py_type = Decimal
            elif "int" in t or "long" in t:
                py_type = int
            elif "bool" in t:
                py_type = bool
            else:
                py_type = str

            pydantic_fields[java_key] = (py_type, ...)

        DynamicContractModel = create_model("DynamicContractModel", **pydantic_fields)

        try:
            validated_model = DynamicContractModel(**mapped_result)
            # We return model_dump(mode='json') to ensure UUIDs and Decimals are serialized to strings as Java expects
            return validated_model.model_dump(mode="json")
        except ValidationError as e:
            logger.error(f"Pydantic validation failed for Java contract: {e}")
            raise ValueError(
                "Strict Contract Violation: Final payload failed Pydantic schema validation."
            )
        #################################################### BURASINI GÖZDEN GEÇİR ######################################################

    @staticmethod
    async def _find_best_semantic_match(
        target_key: str, target_description: str, available_keys: List[str]
    ) -> str | None:
        """
        [PHASE 5] Uses Vector Database to find the semantically closest key.
        Enforces a Confidence Threshold. Exact matches are prioritized.
        E.g., target_key='payment_amount_decimal', available_key='tutar' -> High similarity.
        """
        if not available_keys:
            return None

        # Exact match check first for maximum safety and efficiency
        if target_key in available_keys:
            return target_key

        from app.core.vector_db import vdb

        # vdb.find_best_semantic_key now strictly applies a cosine similarity threshold.
        # If no key meets the threshold, it returns None.
        best_match = vdb.find_best_semantic_key(
            target_key, target_description, available_keys
        )

        if best_match:
            logger.info(
                f"Fuzzy Match Used: '{best_match}' selected for Java Key '{target_key}'"
            )

        return best_match

    @staticmethod
    def _validate_and_cast_banking_type(value: Any, expected_type: str) -> Any:
        """
        Zero-tolerance, banking-grade type validation.
        Float is completely avoided for precision fields (money, bigdecimal).
        """
        try:
            if "uuid" in expected_type:
                if isinstance(value, uuid.UUID):
                    return str(value)
                return str(uuid.UUID(str(value)))  # validates and formats for JSON

            elif (
                "decimal" in expected_type
                or "bigdecimal" in expected_type
                or "money" in expected_type
            ):
                # Banking precision: strictly use Decimal
                if isinstance(value, float):
                    logger.warning(
                        "Float received for a BigDecimal field. Potential precision loss. Casting to Decimal."
                    )
                # Convert to Decimal, if it fails InvalidOperation is thrown
                dec_val = Decimal(str(value))
                # Java often expects BigDecimals as string in JSON to preserve scale/precision
                return str(dec_val)

            elif "int" in expected_type or "long" in expected_type:
                return int(value)

            elif "String" in expected_type or "text" in expected_type:
                return str(value)

            elif "boolean" in expected_type:
                if isinstance(value, bool):
                    return value
                if str(value).lower() in ["true", "1", "yes"]:
                    return True
                if str(value).lower() in ["false", "0", "no"]:
                    return False
                raise ValueError("Not a boolean")
            else:
                return value
        except (ValueError, TypeError, InvalidOperation):
            return None
