import unittest
from app.core.state import SessionState
from app.core.contracts import ServiceSpec, ToolSchema, RiskLevel
from app.agents.orchestrator import DomainOrchestrator
from app.agents.worker import ContractSubAgent
from app.llm.gpt_oss_engine import GPTOSSEngine
from app.core.tool_registry import ToolRegistryLoader

class TestIntegrationLoop(unittest.IsolatedAsyncioTestCase):

    async def test_end_to_end_routing_and_extraction(self):
        """
        Simulates the entire flow:
        1. Backend injects GPT context
        2. Orchestrator routes based on context
        3. Worker extracts parameters based on context
        4. Mutating tool triggers CONFIRMATION_PENDING
        """
        # 1. Setup Architecture
        engine = GPTOSSEngine()
        registry = ToolRegistryLoader()
        
        # Mock Tool Registration
        mutating_tool = ToolSchema(
            tool_id="MAKE_PAYMENT",
            domain="PAYMENT_DOMAIN",
            risk_level=RiskLevel.MUTATING_CRITICAL,
            specs=[
                ServiceSpec(name="amount", type="Decimal", description="Amount to pay"),
                ServiceSpec(name="target_account", type="String", description="IBAN")
            ]
        )
        registry.load_tools([mutating_tool])
        
        orchestrator = DomainOrchestrator(supervisor_id="PAYMENT_DOMAIN", llm_engine=engine, tool_registry=registry)
        
        # Normally DomainOrchestrator uses load_dynamic_workers_from_registry, 
        # we will manually register one for this test
        worker = ContractSubAgent(agent_id="MAKE_PAYMENT", llm_engine=engine, tool_schema=mutating_tool)
        orchestrator.register_sub_agent(worker)
        
        # 2. Simulate Backend Injection (User says: "Send 500 to TR123")
        engine.inject_backend_context(
            intent="MAKE_PAYMENT", 
            tool_calls=[
                {
                    "function": {
                        "name": "MAKE_PAYMENT",
                        "arguments": "{\"amount\": 500, \"target_account\": \"TR123\"}"
                    }
                }
            ]
        )
        
        # 3. Create Session State
        state = SessionState(session_id="test_session")
        
        # 4. Orchestrator Routing
        selected_worker = await orchestrator.route("Send 500 to TR123", state)
        self.assertIsNotNone(selected_worker)
        self.assertEqual(selected_worker.agent_id, "MAKE_PAYMENT")
        
        # 5. Worker Processing
        response = await selected_worker.process_message("Send 500 to TR123", state)
        
        # Should be CONFIRMATION_PENDING because it's MUTATING_CRITICAL and we have all parameters
        self.assertEqual(response.status, "CONFIRMATION_PENDING")
        self.assertEqual(state.active_task_status, "CONFIRMATION_PENDING")
        self.assertIn("amount", response.parameters)
        
        # 6. User Confirms
        response_confirmed = await selected_worker.process_message("Evet onaylıyorum", state)
        self.assertEqual(response_confirmed.status, "COMPLETED")
        self.assertEqual(state.active_task_status, "COMPLETED")

if __name__ == '__main__':
    unittest.main()
