import unittest
from app.llm.gpt_oss_engine import GPTOSSEngine
from app.core.contracts import ServiceSpec

class TestGPTOSSEngine(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.engine = GPTOSSEngine()

    async def test_inject_backend_context_and_determine_intent(self):
        """Test that injected intent is correctly returned if valid."""
        self.engine.inject_backend_context(intent="PAYMENT_DOMAIN", tool_calls=[])
        
        intent = await self.engine.determine_intent("dummy message", ["PAYMENT_DOMAIN", "CARD_DOMAIN"])
        self.assertEqual(intent, "PAYMENT_DOMAIN")
        
        # Test fallback to UNKNOWN if injected intent is invalid
        intent_invalid = await self.engine.determine_intent("dummy message", ["CARD_DOMAIN"])
        self.assertEqual(intent_invalid, "UNKNOWN")

    async def test_inject_backend_context_and_extract_parameters(self):
        """Test that OpenAI formatted tool calls from backend are correctly parsed."""
        raw_tool_calls = [
            {
                "function": {
                    "name": "select_user_card",
                    "arguments": "{\"card_id\": \"9012\", \"amount\": 500}"
                }
            }
        ]
        
        self.engine.inject_backend_context(intent="CARD_DOMAIN", tool_calls=raw_tool_calls)
        
        extracted = await self.engine.extract_parameters("dummy message", [], {})
        
        self.assertIn("card_id", extracted)
        self.assertEqual(extracted["card_id"], "9012")
        self.assertEqual(extracted["amount"], 500)

if __name__ == '__main__':
    unittest.main()
