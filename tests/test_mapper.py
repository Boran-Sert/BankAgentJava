import unittest
from unittest.mock import patch, MagicMock
from app.api.mapper import ContractMapper
from app.core.contracts import ServiceSpec

class TestContractMapper(unittest.IsolatedAsyncioTestCase):

    async def test_exact_match_and_pydantic_validation_success(self):
        """Test exact match mapping and successful dynamic Pydantic type validation."""
        specs = [
            ServiceSpec(name="payment_amount", type="Decimal", description="Miktar"),
            ServiceSpec(name="is_active", type="boolean", description="Aktif mi"),
            ServiceSpec(name="user_id", type="UUID", description="User ID")
        ]
        
        collected = {
            "payment_amount": 100.50, # float, should be safely cast to str(Decimal)
            "is_active": "yes",       # string "yes" should be parsed to bool True
            "user_id": "123e4567-e89b-12d3-a456-426614174000"
        }
        
        mapped = await ContractMapper.map_to_java(collected, specs)
        
        self.assertEqual(mapped["payment_amount"], "100.5")
        self.assertEqual(mapped["is_active"], True)
        self.assertEqual(mapped["user_id"], "123e4567-e89b-12d3-a456-426614174000")

    async def test_pydantic_validation_failure(self):
        """Test strict Pydantic validation failure raises ValueError."""
        specs = [
            ServiceSpec(name="payment_amount", type="Decimal", description="Miktar")
        ]
        
        collected = {
            "payment_amount": "invalid_number_string" 
        }
        
        with self.assertRaises(ValueError) as context:
            await ContractMapper.map_to_java(collected, specs)
            
        self.assertIn("Strict Contract Violation", str(context.exception))
        self.assertIn("failed type validation", str(context.exception))

    @patch('app.core.vector_db.VectorDatabaseManager.find_best_semantic_key')
    async def test_semantic_match_fallback(self, mock_find_best_semantic_key):
        """Test fallback to Vector DB semantic match when exact key is missing."""
        # Mock VDB returning the matched key
        mock_find_best_semantic_key.return_value = "tutar"
        
        specs = [
            ServiceSpec(name="payment_amount_decimal", type="Decimal", description="Transfer Amount")
        ]
        
        collected = {
            "tutar": 500.00
        }
        
        mapped = await ContractMapper.map_to_java(collected, specs)
        
        mock_find_best_semantic_key.assert_called_once_with(
            "payment_amount_decimal", "Transfer Amount", unittest.mock.ANY
        )
        self.assertEqual(mapped["payment_amount_decimal"], "500.0")

if __name__ == '__main__':
    unittest.main()
