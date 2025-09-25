#!/usr/bin/env python3
"""
Test script to verify the AI agent response structure fix
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.enhanced_ai_service import EnhancedAIService, NegotiationContext

async def test_ai_response_structure():
    """Test that the AI service returns the correct response structure"""
    
    print("🧪 Testing AI Response Structure Fix")
    print("=" * 50)
    
    # Create mock context for testing
    mock_context = NegotiationContext(
        product={'title': 'Test iPhone', 'price': 50000, 'platform': 'OLX'},
        target_price=45000,
        max_budget=50000,
        seller_messages=['No, The Price is too low for this product'],
        chat_history=[],
        market_data={},
        session_data={'id': 'test_session'},
        negotiation_phase='exploration'
    )
    
    try:
        # Initialize AI service
        ai_service = EnhancedAIService()
        
        # Test decision making
        result = await ai_service.make_decision(
            session_data=mock_context.session_data,
            seller_message=mock_context.seller_messages[0],
            chat_history=mock_context.chat_history,
            product=mock_context.product
        )
        
        print("✅ AI Service Response Structure:")
        print(f"  - Has 'response' key: {'response' in result}")
        print(f"  - Has 'decision' key: {'decision' in result}")
        print(f"  - Has 'confidence' key: {'confidence' in result}")
        print(f"  - Response type: {type(result.get('response'))}")
        print(f"  - Response preview: {str(result.get('response', ''))[:100]}...")
        
        # Check expected structure
        expected_keys = ['response', 'decision', 'confidence', 'tactics_used', 'phase']
        missing_keys = [key for key in expected_keys if key not in result]
        
        if missing_keys:
            print(f"❌ Missing keys: {missing_keys}")
        else:
            print("✅ All expected keys present")
            
        print(f"  - Full result keys: {list(result.keys())}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_response_structure())