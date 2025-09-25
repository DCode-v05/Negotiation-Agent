"""
LangChain Negotiation Agent
Advanced AI agent for intelligent negotiation using LangChain framework
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# LangChain imports
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

# Local imports
from models import NegotiationSession, ChatMessage

logger = logging.getLogger(__name__)

class NegotiationContext(BaseModel):
    """Context for negotiation decisions"""
    product: Dict[str, Any]
    target_price: int
    max_budget: int
    current_offer: Optional[int] = None
    seller_messages: List[str]
    chat_history: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    session_data: Dict[str, Any]
    negotiation_phase: str

class MarketAnalysisTool(BaseTool):
    """Tool for analyzing market conditions"""
    name: str = "market_analysis"
    description: str = "Analyze market conditions and pricing for negotiation strategy"
    
    def _run(
        self, 
        product_name: str, 
        current_price: int,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Analyze market conditions"""
        try:
            # Simulate market analysis (you can integrate real market data here)
            analysis = {
                "market_trend": "stable",
                "suggested_price_range": {
                    "min": int(current_price * 0.7),
                    "max": int(current_price * 0.9)
                },
                "negotiation_leverage": "moderate",
                "competitive_prices": [
                    int(current_price * 0.8),
                    int(current_price * 0.85),
                    int(current_price * 0.9)
                ]
            }
            return json.dumps(analysis)
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return "Market analysis unavailable"

class PriceCalculatorTool(BaseTool):
    """Tool for calculating optimal price offers"""
    name: str = "price_calculator"
    description: str = "Calculate optimal price offers based on negotiation strategy"
    
    def _run(
        self, 
        current_price: int, 
        target_price: int, 
        max_budget: int,
        negotiation_round: int,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Calculate optimal price offer"""
        try:
            # Progressive negotiation strategy
            if negotiation_round <= 2:
                # Start with aggressive offer
                offer = int(target_price * 1.1)
            elif negotiation_round <= 4:
                # Move towards middle ground
                offer = int((target_price + current_price) * 0.6)
            else:
                # Final offers closer to budget
                offer = int(min(max_budget * 0.95, (target_price + current_price) * 0.7))
            
            # Ensure offer is within bounds
            offer = max(target_price, min(offer, max_budget))
            
            result = {
                "suggested_offer": offer,
                "strategy": "progressive",
                "confidence": 0.8,
                "reasoning": f"Round {negotiation_round}: Strategic offer based on target ${target_price} and budget ${max_budget}"
            }
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Price calculation error: {e}")
            return "Price calculation failed"

class NegotiationStrategyTool(BaseTool):
    """Tool for determining negotiation strategy"""
    name: str = "negotiation_strategy"
    description: str = "Determine the best negotiation strategy and tactics to use"
    
    def _run(
        self, 
        seller_message: str,
        negotiation_phase: str,
        price_difference: int,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Determine negotiation strategy"""
        try:
            strategies = {
                "opening": ["anchoring", "information_gathering", "rapport_building"],
                "bargaining": ["reciprocal_concessions", "deadline_pressure", "alternative_options"],
                "closing": ["final_offer", "walk_away_threat", "compromise_seeking"]
            }
            
            # Analyze seller's tone and urgency
            seller_lower = seller_message.lower()
            urgency_indicators = ["final", "last", "deadline", "urgent", "today only"]
            flexibility_indicators = ["consider", "negotiate", "discuss", "flexible"]
            
            is_urgent = any(word in seller_lower for word in urgency_indicators)
            is_flexible = any(word in seller_lower for word in flexibility_indicators)
            
            # Determine strategy
            if price_difference > 30:  # Large gap
                strategy = "aggressive_negotiation"
                tactics = ["anchoring", "alternative_options", "market_comparison"]
            elif price_difference > 15:  # Moderate gap  
                strategy = "collaborative_negotiation"
                tactics = ["reciprocal_concessions", "value_proposition", "rapport_building"]
            else:  # Small gap
                strategy = "closing_negotiation"
                tactics = ["final_offer", "commitment_seeking", "minor_concessions"]
            
            # Adjust based on seller signals
            if is_urgent:
                tactics.append("deadline_leverage")
            if is_flexible:
                tactics.append("creative_solutions")
            
            result = {
                "strategy": strategy,
                "tactics": tactics,
                "seller_analysis": {
                    "urgency": is_urgent,
                    "flexibility": is_flexible
                },
                "recommended_approach": f"Use {strategy} with focus on {', '.join(tactics[:2])}"
            }
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Strategy analysis error: {e}")
            return "Strategy analysis failed"


class LangChainNegotiationAgent:
    """Advanced negotiation agent using LangChain"""
    
    def __init__(self, google_api_key: str = None):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise ValueError("Google API key is required for LangChain agent")
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.google_api_key,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize tools
        self.tools = [
            MarketAnalysisTool(),
            PriceCalculatorTool(),
            NegotiationStrategyTool()
        ]
        
        # Create negotiation prompt template
        self.negotiation_prompt = PromptTemplate(
            input_variables=[
                "product_name", "product_price", "target_price", "max_budget",
                "seller_message", "negotiation_phase", "conversation_flow", "price_mentions", 
                "seller_sentiment", "negotiation_stage", "seller_tactics", "market_data"
            ],
            template="""
You are an expert negotiation strategist helping a buyer negotiate the best deal. You must be strategic, methodical, and use market analysis to your advantage.

PRODUCT DETAILS:
- Product: {product_name}
- Listed Price: ₹{product_price}
- Target Price: ₹{target_price}
- Maximum Budget: ₹{max_budget}

CONVERSATION CONTEXT:
- Negotiation Phase: {negotiation_phase}
- Negotiation Stage: {negotiation_stage}
- Seller Sentiment: {seller_sentiment}
- Seller Tactics Detected: {seller_tactics}

- Full Conversation Flow:
{conversation_flow}

- Price-Related Discussions:
{price_mentions}

- Market Data: {market_data}

SELLER'S LATEST MESSAGE:
"{seller_message}"

CONTEXTUAL RESPONSE STRATEGY - Adapt based on seller behavior:

**SELLER SENTIMENT ANALYSIS**: {seller_sentiment}
- If RESISTANT: Use empathy, market data, alternatives, gentle pressure
- If AGREEABLE: Build on positivity, move closer to target price
- If OPEN: Test flexibility, provide compelling reasons, create urgency

**NEGOTIATION STAGE**: {negotiation_stage}  
- If OPENING: Establish rapport, anchor with target price, show serious interest
- If MIDDLE: Apply strategic pressure, use market comparisons, show flexibility
- If ADVANCED/CLOSING: Make final push, summarize value, create win-win scenario

**SELLER TACTICS DETECTED**: {seller_tactics}
- If "rejection": Counter with alternatives and market data
- If "acceptance": Confirm and close the deal
- If "counter_offer": Evaluate and respond strategically
- If "ultimatum": Test if it's real or negotiating tactic

**DYNAMIC RESPONSE RULES**:
1. NEVER use the same phrasing twice - always vary your language
2. Directly address what the seller just said - show you're listening
3. Adapt your tone to match the seller's energy level
4. Use different persuasion angles: logic, emotion, urgency, social proof
   - Vary your language and approach based on conversation history

4. **HUMAN-LIKE RESPONSE CRAFTING**:
   - Sound conversational and natural, not robotic
   - Reference specific points from the seller's message
   - Show emotional intelligence and adaptability
   - Use varied vocabulary and sentence structures
   - Include personal touches (but stay professional)

IMPORTANT: Your final answer must be ONLY the JSON response, nothing else. Do not include any explanatory text before or after the JSON.

RESPONSE FORMAT (return exactly this JSON structure as your final answer):
{{
    "message": "Your strategic response with specific reasoning and market-based arguments",
    "action_type": "offer|counter_offer|accept|reject|question|final_offer",
    "price_offer": price_amount_or_null,
    "confidence": confidence_score_0_to_1,
    "reasoning": "Step-by-step strategic analysis of your approach",
    "tactics_used": ["list", "of", "tactics"],
    "next_steps": ["recommended", "next", "steps"]
}}

Generate a strategic negotiation response (respond with JSON only):
"""
        )
        
        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
        
        logger.info("LangChain negotiation agent initialized successfully")
    
    async def generate_negotiation_response(
        self, 
        context: NegotiationContext
    ) -> Dict[str, Any]:
        """Generate intelligent negotiation response using LangChain"""
        try:
            # Prepare input for the agent with dynamic conversation context
            recent_messages = context.chat_history[-6:] if context.chat_history else []
            conversation_flow = []
            
            for msg in recent_messages:
                if hasattr(msg, 'sender') and hasattr(msg, 'content'):
                    conversation_flow.append(f"{msg.sender}: {msg.content}")
                elif isinstance(msg, dict):
                    conversation_flow.append(f"{msg.get('sender', 'unknown')}: {msg.get('content', '')}")
            
            conversation_context = "\n".join(conversation_flow) if conversation_flow else "No previous conversation"
            
            # Analyze conversation context for better responses
            price_mentions = []
            seller_sentiment = "neutral"
            negotiation_stage = "initial"
            seller_tactics = []
            
            for i, msg in enumerate(conversation_flow):
                # Extract price mentions
                if any(price_word in msg.lower() for price_word in ['₹', 'rupees', 'price', 'cost', 'budget']):
                    price_mentions.append(msg)
                
                # Analyze seller behavior if it's a seller message
                if msg.startswith("Seller:"):
                    content_lower = msg.lower()
                    
                    # Determine seller sentiment
                    if any(word in content_lower for word in ["no", "can't", "impossible", "too low", "minimum", "sorry"]):
                        seller_sentiment = "resistant"
                        seller_tactics.append("rejection")
                    elif any(word in content_lower for word in ["okay", "yes", "agreed", "fine", "deal", "accept"]):
                        seller_sentiment = "agreeable"
                        seller_tactics.append("acceptance")
                    elif any(word in content_lower for word in ["maybe", "consider", "think", "possible", "let me"]):
                        seller_sentiment = "open"
                        seller_tactics.append("consideration")
                    elif any(word in content_lower for word in ["final", "last", "best", "lowest"]):
                        seller_tactics.append("ultimatum")
                        negotiation_stage = "closing"
                    elif any(word in content_lower for word in ["counter", "what about", "how about"]):
                        seller_tactics.append("counter_offer")
            
            # Determine negotiation stage based on message count
            seller_message_count = len([msg for msg in conversation_flow if msg.startswith("Seller:")])
            if seller_message_count == 1:
                negotiation_stage = "opening"
            elif seller_message_count > 3:
                negotiation_stage = "advanced"
            else:
                negotiation_stage = "middle"
            
            agent_input = {
                "product_name": context.product.get("name", "Unknown Product"),
                "product_price": context.product.get("price", 0),
                "target_price": context.target_price,
                "max_budget": context.max_budget,
                "seller_message": context.seller_messages[-1] if context.seller_messages else "",
                "negotiation_phase": context.negotiation_phase,
                "conversation_flow": conversation_context,
                "price_mentions": "\n".join(price_mentions) if price_mentions else "No price discussions yet",
                "seller_sentiment": seller_sentiment,
                "negotiation_stage": negotiation_stage,
                "seller_tactics": ", ".join(seller_tactics) if seller_tactics else "none detected",
                "market_data": json.dumps(context.market_data)
            }
            
            # Format the prompt
            formatted_prompt = self.negotiation_prompt.format(**agent_input)
            
            # Run the agent
            response = await self._run_agent_async(formatted_prompt)
            
            # Parse response
            parsed_response = self._parse_agent_response(response)
            
            # Add metadata
            parsed_response["source"] = "langchain_agent"
            parsed_response["timestamp"] = datetime.now().isoformat()
            
            logger.info(f"LangChain agent generated response: {parsed_response.get('action_type', 'unknown')}")
            return parsed_response
            
        except Exception as e:
            logger.error(f"LangChain agent error: {e}")
            # Fallback response
            return {
                "message": "I'm analyzing your negotiation. Let me consider the best approach.",
                "action_type": "question",
                "price_offer": None,
                "confidence": 0.5,
                "reasoning": f"Agent error: {str(e)}",
                "tactics_used": ["fallback"],
                "next_steps": ["retry_with_fallback"],
                "source": "langchain_agent_fallback"
            }
    
    async def _run_agent_async(self, prompt: str) -> str:
        """Run agent asynchronously"""
        try:
            # Use the agent with the formatted prompt
            response = self.agent.run(prompt)
            logger.info(f"Agent raw response: {response[:200]}...")
            return response
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            # Return a valid JSON fallback
            fallback_response = {
                "message": "I need to review this further. Let me consider the best approach.",
                "action_type": "question",
                "price_offer": None,
                "confidence": 0.5,
                "reasoning": f"Agent error: {str(e)}",
                "tactics_used": ["fallback"],
                "next_steps": ["retry_with_fallback"]
            }
            return json.dumps(fallback_response)
    
    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        """Parse agent response into structured format"""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["message", "action_type", "confidence", "reasoning"]
                for field in required_fields:
                    if field not in parsed:
                        parsed[field] = self._get_default_value(field)
                
                return parsed
            else:
                # Fallback parsing
                return self._create_fallback_response(response)
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, using fallback")
            return self._create_fallback_response(response)
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            "message": "I need to review this further.",
            "action_type": "respond",
            "price_offer": None,
            "confidence": 0.75,
            "reasoning": "Default response due to parsing issue",
            "tactics_used": ["analytical"],
            "next_steps": ["continue_negotiation"]
        }
        return defaults.get(field, "")
    
    def _create_fallback_response(self, raw_response: str) -> Dict[str, Any]:
        """Create fallback response from raw text"""
        return {
            "message": raw_response[:500] if len(raw_response) > 500 else raw_response,
            "action_type": "respond",
            "price_offer": None,
            "confidence": 0.75,
            "reasoning": "Parsed from unstructured response",
            "tactics_used": ["analytical"],
            "next_steps": ["await_seller_response"]
        }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Agent memory cleared")
    
    def get_memory_summary(self) -> str:
        """Get summary of conversation memory"""
        try:
            messages = self.memory.chat_memory.messages
            return f"Memory contains {len(messages)} messages"
        except:
            return "Memory summary unavailable"