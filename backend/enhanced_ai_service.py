"""
Enhanced AI Service - Now with LangChain Integration
Combines negotiation engine with LangChain AI agent, MCP integration and Gemini fallback
"""

import os
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from pydantic import BaseModel, Field

# Local imports
from models import NegotiationSession, ChatMessage
from negotiation_engine import AdvancedNegotiationEngine
from scraper_service import MarketplaceScraper
# from mcp_integration import JSONContextManager, NegotiationContext  # Temporarily disabled
from gemini_service import GeminiOnlyService
from langchain_agent import LangChainNegotiationAgent, NegotiationContext as LangChainContext

logger = logging.getLogger(__name__)

# Simple local NegotiationContext class
@dataclass
class NegotiationContext:
    """Simple context for negotiation decisions"""
    product: Dict[str, Any]
    target_price: int
    max_budget: int
    seller_messages: List[str]
    chat_history: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    session_data: Dict[str, Any]
    negotiation_phase: str

class NegotiationResponse(BaseModel):
    """Structured response from the AI agent"""
    message: str = Field(description="Message to send to seller")
    action_type: str = Field(description="Type of action: offer, counter_offer, accept, reject, question")
    price_offer: Optional[int] = Field(description="Price offer if making an offer", default=None)
    confidence: float = Field(description="Confidence in this response (0-1)")
    reasoning: str = Field(description="Internal reasoning for this response")
    tactics_used: List[str] = Field(description="Negotiation tactics employed")
    next_steps: List[str] = Field(description="Recommended next steps")


class EnhancedAIService:
    """Enhanced AI service combining traditional negotiation engine with MCP and Gemini"""
    
    def __init__(self, use_langchain: bool = True, use_mcp: bool = False):
        self.use_langchain = use_langchain  # Now enabled with proper integration
        self.use_mcp = use_mcp
        self.langchain_agent = None
        self.mcp_context_manager = None
        self.negotiation_engine = AdvancedNegotiationEngine()
        self.scraper_service = MarketplaceScraper()
        self.gemini_service = GeminiOnlyService()
        
        # Initialize services
        self.initialize_services()
    
    def initialize_services(self):
        """Initialize AI services"""
        try:
            # Initialize LangChain agent
            if self.use_langchain:
                try:
                    google_api_key = os.getenv("GOOGLE_API_KEY")
                    if google_api_key:
                        self.langchain_agent = LangChainNegotiationAgent(google_api_key)
                        logger.info("✅ LangChain negotiation agent initialized successfully")
                    else:
                        logger.warning("Google API key not found, disabling LangChain")
                        self.use_langchain = False
                        self.langchain_agent = None
                except Exception as e:
                    logger.error(f"LangChain initialization error: {e}")
                    logger.info("Falling back to Gemini-only service")
                    self.use_langchain = False
                    self.langchain_agent = None
            
            # MCP temporarily disabled
            self.use_mcp = False
            # if self.use_mcp:
            #     try:
            #         self.mcp_context_manager = JSONContextManager()
            #         logger.info("MCP context manager initialized")
            #     except Exception as e:
            #         logger.error(f"MCP initialization error: {e}")
            #         self.use_mcp = False
            
        except Exception as e:
            logger.error(f"Error initializing AI services: {e}")
            self.use_langchain = False
            self.use_mcp = False
    
    async def make_negotiation_decision(
        self,
        session_data: Dict[str, Any],
        seller_message: str,
        chat_history: List[Dict[str, Any]],
        product: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make an intelligent negotiation decision using all available AI systems
        """
        try:
            # Step 1: Prepare context for AI systems
            context = await self._prepare_negotiation_context(
                session_data, seller_message, chat_history, product
            )
            
            # Step 2: Try LangChain agent first (highest priority)
            if self.use_langchain and self.langchain_agent:
                try:
                    # Convert context to LangChain format
                    langchain_context = LangChainContext(
                        product=product,
                        target_price=context.target_price,
                        max_budget=context.max_budget,
                        current_offer=session_data.get("last_offer"),
                        seller_messages=context.seller_messages,
                        chat_history=context.chat_history,
                        market_data=context.market_data,
                        session_data=context.session_data,
                        negotiation_phase=context.negotiation_phase
                    )
                    
                    langchain_decision = await self.langchain_agent.generate_negotiation_response(
                        langchain_context
                    )
                    
                    if langchain_decision and langchain_decision.get("confidence", 0) > 0.6:
                        logger.info("🚀 Using LangChain agent decision")
                        self._log_decision(langchain_decision, session_data)
                        return langchain_decision
                    else:
                        logger.info("LangChain confidence low, falling back to engine")
                        
                except Exception as e:
                    logger.error(f"LangChain agent error: {e}")
                    logger.info("Falling back to traditional engine")
            
            # Step 3: Get MCP-enhanced insights - temporarily disabled
            mcp_insights = None
            # if self.use_mcp and self.mcp_context_manager:
            #     try:
            #         mcp_insights = await self._get_mcp_insights(context, session_data)
            #         logger.info("MCP insights obtained")
            #     except Exception as e:
            #         logger.error(f"MCP insights error: {e}")
            #         mcp_insights = None
            
            # Step 4: Get decision from traditional negotiation engine
            engine_decision = await self.negotiation_engine.process_negotiation_turn(
                session_data, seller_message, chat_history, product
            )
            
            # Step 5: Enhance with Gemini if available
            if os.getenv("GEMINI_API_KEY"):
                try:
                    gemini_enhancement = await self._get_gemini_enhancement(
                        context, engine_decision
                    )
                    if gemini_enhancement:
                        engine_decision = self._merge_gemini_enhancement(
                            engine_decision, gemini_enhancement
                        )
                except Exception as e:
                    logger.error(f"Gemini enhancement error: {e}")
            
            # Step 6: Combine with MCP insights
            final_decision = self._combine_with_mcp(engine_decision, mcp_insights)
            
            # Step 7: Log decision for learning
            self._log_decision(final_decision, session_data)
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Error in AI decision making: {e}")
            return await self._fallback_decision(session_data, seller_message, chat_history, product)
    
    async def _prepare_negotiation_context(
        self,
        session_data: Dict[str, Any],
        seller_message: str,
        chat_history: List[Dict[str, Any]],
        product: Dict[str, Any]
    ) -> NegotiationContext:
        """Prepare comprehensive context for AI systems"""
        
        # Extract user parameters
        user_params = session_data.get("user_params", {})
        product_price = product.price if hasattr(product, 'price') else 0
        target_price = user_params.get("target_price", product_price * 0.8)
        max_budget = user_params.get("max_budget", product_price)
        
        # Get market data
        market_data = session_data.get("market_analysis", {})
        if not market_data:
            # Basic market data if not available
            market_data = {
                "average_price": product_price * 0.9,
                "price_range": {"min": product_price * 0.7, "max": product_price * 1.2},
                "market_trend": "stable"
            }
        
        # Determine negotiation phase
        negotiation_phase = self._determine_phase(chat_history, seller_message)
        
        # Analyze seller messages
        seller_messages = [msg.content for msg in chat_history if msg.sender == "seller"]
        if seller_message:
            seller_messages.append(seller_message)
        
        return NegotiationContext(
            product=product,
            target_price=int(target_price),
            max_budget=int(max_budget),
            seller_messages=seller_messages,
            chat_history=chat_history,
            market_data=market_data,
            session_data=session_data,
            negotiation_phase=negotiation_phase
        )
    
    async def _get_mcp_insights(self, context: NegotiationContext, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get insights from MCP context manager"""
        
        try:
            # Update context with latest information
            session_id = session_data.get("session_id", "default")
            await self.mcp_context_manager.update_context(session_id, context)
            
            # Get analytical insights
            insights = await self.mcp_context_manager.get_insights(session_id)
            
            return {
                "market_insights": insights.get("market_analysis", {}),
                "negotiation_insights": insights.get("negotiation_patterns", {}),
                "recommendations": insights.get("recommendations", []),
                "confidence": insights.get("confidence", 0.7)
            }
            
        except Exception as e:
            logger.error(f"MCP insights error: {e}")
            return {}
    
    async def _get_gemini_enhancement(self, context: NegotiationContext, base_decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get enhancement suggestions from Gemini"""
        
        try:
            # Create prompt for Gemini
            product_name = context.product.title if hasattr(context.product, 'title') else 'Unknown'
            product_price = context.product.price if hasattr(context.product, 'price') else 0
            prompt = f"""
            You are an expert negotiation advisor. Analyze this negotiation situation and enhance the proposed response:
            
            Product: {product_name}
            Current Price: ${product_price}
            Target Price: ${context.target_price}
            Max Budget: ${context.max_budget}
            Negotiation Phase: {context.negotiation_phase}
            
            Proposed Action: {base_decision.get('action_type', 'unknown')}
            Proposed Message: {base_decision.get('message', '')}
            Proposed Price: ${base_decision.get('price_offer', 'None')}
            
            Recent seller messages: {context.seller_messages[-2:] if context.seller_messages else ['No messages yet']}
            
            Please suggest improvements to:
            1. Message tone and content
            2. Negotiation strategy
            3. Price positioning
            4. Overall approach
            
            Respond in JSON format with: message_enhancement, strategy_tips, confidence_adjustment
            """
            
            # Get response from Gemini
            response = await self.gemini_service.generate_text(prompt)
            
            if response and response.get("content"):
                try:
                    # Try to parse as JSON
                    import re
                    json_match = re.search(r'\{.*\}', response["content"], re.DOTALL)
                    if json_match:
                        enhancement = json.loads(json_match.group())
                        return enhancement
                except json.JSONDecodeError:
                    pass
                
                # If JSON parsing fails, return structured response
                return {
                    "message_enhancement": response["content"][:200],
                    "strategy_tips": ["Use Gemini's advice"],
                    "confidence_adjustment": 0.1
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini enhancement error: {e}")
            return None
    
    def _merge_gemini_enhancement(self, base_decision: Dict[str, Any], enhancement: Dict[str, Any]) -> Dict[str, Any]:
        """Merge Gemini enhancement with base decision"""
        
        enhanced_decision = base_decision.copy()
        
        # Enhance message if available
        if enhancement.get("message_enhancement"):
            # Keep base message but add enhancement note
            enhanced_decision["message"] = f"{base_decision.get('message', '')} {enhancement['message_enhancement'][:100]}"
        
        # Adjust confidence
        confidence_adj = enhancement.get("confidence_adjustment", 0)
        current_confidence = enhanced_decision.get("confidence", 0.7)
        enhanced_decision["confidence"] = min(1.0, max(0.0, current_confidence + confidence_adj))
        
        # Add strategy tips to tactics
        strategy_tips = enhancement.get("strategy_tips", [])
        current_tactics = enhanced_decision.get("tactics_used", [])
        enhanced_decision["tactics_used"] = current_tactics + strategy_tips[:2]  # Limit to 2 tips
        
        # Update reasoning
        enhanced_decision["reasoning"] = f"{base_decision.get('reasoning', '')} Enhanced with Gemini insights."
        
        return enhanced_decision
    
    def _combine_with_mcp(self, base_decision: Dict[str, Any], mcp_insights: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine base decision with MCP insights"""
        
        if not mcp_insights:
            return base_decision
        
        enhanced_decision = base_decision.copy()
        
        # Adjust confidence based on MCP insights
        mcp_confidence = mcp_insights.get("confidence", 0.7)
        current_confidence = enhanced_decision.get("confidence", 0.7)
        enhanced_decision["confidence"] = (current_confidence + mcp_confidence) / 2
        
        # Add MCP recommendations
        mcp_recommendations = mcp_insights.get("recommendations", [])
        if mcp_recommendations:
            current_next_steps = enhanced_decision.get("next_steps", [])
            enhanced_decision["next_steps"] = current_next_steps + mcp_recommendations[:2]
        
        # Update reasoning
        enhanced_decision["reasoning"] = f"{base_decision.get('reasoning', '')} Informed by MCP analysis."
        
        return enhanced_decision
    
    async def _fallback_decision(
        self,
        session_data: Dict[str, Any],
        seller_message: str,
        chat_history: List[Dict[str, Any]],
        product: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback decision using traditional negotiation engine"""
        
        try:
            # Use the traditional negotiation engine
            decision = await self.negotiation_engine.process_negotiation_turn(
                session_data, seller_message, chat_history, product
            )
            
            # Ensure proper format
            return {
                "message": decision.get("message", "I'm interested in this product. Can we discuss the price?"),
                "action_type": decision.get("action_type", "question"),
                "price_offer": decision.get("price_offer"),
                "confidence": decision.get("confidence", 0.6),
                "reasoning": "Fallback negotiation engine",
                "tactics_used": ["traditional_negotiation"],
                "next_steps": ["await_seller_response"]
            }
            
        except Exception as e:
            logger.error(f"Fallback decision error: {e}")
            
            # Ultimate fallback
            return {
                "message": "I'm interested in this product. What's your best price?",
                "action_type": "question",
                "price_offer": None,
                "confidence": 0.5,
                "reasoning": "Emergency fallback response",
                "tactics_used": ["basic_inquiry"],
                "next_steps": ["await_seller_response"]
            }
    
    def _determine_phase(self, chat_history: List[Any], current_message: str) -> str:
        """Determine the current phase of negotiation"""
        
        if not chat_history:
            return "opening"
        
        message_count = len(chat_history)
        
        # Look for key phrases in recent messages
        recent_messages = [msg.content.lower() if hasattr(msg, 'content') else str(msg).lower() for msg in chat_history[-3:]]
        recent_messages.append(current_message.lower() if current_message else "")
        
        combined_recent = " ".join(recent_messages)
        
        if "final" in combined_recent or "last" in combined_recent:
            return "closing"
        elif "counter" in combined_recent or message_count > 3:
            return "bargaining"
        elif message_count <= 2:
            return "opening"
        else:
            return "negotiation"
    
    def _log_decision(self, decision: Dict[str, Any], session_data: Dict[str, Any]):
        """Log decision for learning and analytics"""
        
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_data.get("session_id"),
                "decision": decision,
                "context_summary": {
                    "user_id": session_data.get("user_id"),
                    "product_id": session_data.get("product", {}).get("id"),
                    "negotiation_round": len(session_data.get("chat_history", []))
                }
            }
            
            # In production, this would go to a proper logging system
            logger.info(f"Decision logged: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging decision: {e}")

    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all AI services"""
        try:
            status = {
                "enhanced_ai_service": "active",
                "langchain_agent": "active" if self.use_langchain and self.langchain_agent else "disabled",
                "mcp_integration": "active" if self.use_mcp else "disabled", 
                "gemini_fallback": "active",
                "negotiation_engine": "active",
                "scraper_service": "active",
                "services": {
                    "langchain": {
                        "enabled": self.use_langchain,
                        "initialized": self.langchain_agent is not None,
                        "tools": ["market_analysis", "price_calculator", "negotiation_strategy"] if self.langchain_agent else []
                    },
                    "mcp": {
                        "enabled": self.use_mcp,
                        "initialized": self.mcp_context_manager is not None
                    },
                    "gemini": {
                        "enabled": True,
                        "initialized": self.gemini_service is not None
                    },
                    "negotiation_engine": {
                        "enabled": True,
                        "initialized": self.negotiation_engine is not None
                    }
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "enhanced_ai_service": "error",
                "error": str(e)
            }


# Helper function for backwards compatibility
async def get_ai_decision(session_data: Dict[str, Any], seller_message: str, chat_history: List[Dict[str, Any]], product: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to get AI decision"""
    service = EnhancedAIService()
    return await service.make_negotiation_decision(session_data, seller_message, chat_history, product)