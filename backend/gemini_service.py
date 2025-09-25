import google.generativeai as genai
import os
import random
from typing import List, Optional, Dict, Any
from models import ChatMessage, Product, NegotiationApproach
from negotiation_engine import NegotiationTactic, NegotiationPhase
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class GeminiOnlyService:
    """Gemini-only AI service for negotiation responses"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("WARNING: GEMINI_API_KEY not configured. Using fallback responses only.")
            self.model = None
        else:
            self.setup_client()
        
    def setup_client(self):
        """Setup Gemini AI client"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("INFO: Gemini AI service initialized successfully")
        except Exception as e:
            logger.error(f"ERROR: Failed to initialize Gemini AI: {e}")
            self.model = None
    
    async def generate_strategic_response(
        self,
        session_data: Dict[str, Any],
        seller_message: str,
        tactics: List[NegotiationTactic],
        decision: Dict[str, Any],
        product: Product
    ) -> str:
        """Generate strategic response using advanced context and tactics"""
        
        if not self.model:
            return self._get_enhanced_fallback_response(session_data, seller_message, tactics, decision, product)
        
        try:
            # Build enhanced context for AI
            context = self._build_strategic_context(
                session_data, seller_message, tactics, decision, product
            )
            
            # Generate response using Gemini
            response = await self._call_gemini_api(context)
            return response
            
        except Exception as e:
            logger.error(f"Error generating strategic AI response: {e}")
            return self._get_enhanced_fallback_response(session_data, seller_message, tactics, decision, product)
    
    async def generate_response(
        self,
        approach,  # Can be string or NegotiationApproach enum
        target_price: int,
        max_budget: int,
        chat_history: List[ChatMessage],
        product: Product
    ) -> str:
        """Legacy method for backward compatibility"""
        
        # Convert string to enum if needed
        if isinstance(approach, str):
            try:
                approach = NegotiationApproach(approach.lower())
            except ValueError:
                approach = NegotiationApproach.DIPLOMATIC  # Default fallback
        
        if not self.model:
            return self._get_fallback_response(approach, target_price, chat_history, product)
        
        try:
            # Build context for AI
            context = self._build_negotiation_context(
                approach, target_price, max_budget, chat_history, product
            )
            
            # Generate response using Gemini
            response = await self._call_gemini_api(context)
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(approach, target_price, chat_history, product)
    
    def _build_negotiation_context(
        self,
        approach: NegotiationApproach,
        target_price: int,
        max_budget: int,
        chat_history: List[ChatMessage],
        product: Product
    ) -> str:
        """Build context prompt for Gemini AI"""
        
        # Get the latest seller message
        seller_messages = [msg for msg in chat_history if msg.sender == "seller"]
        last_seller_message = seller_messages[-1].content if seller_messages else ""
        
        # Build conversation history
        conversation_history = ""
        for msg in chat_history[-6:]:  # Last 6 messages for context
            sender_label = "Seller" if msg.sender == "seller" else "You (Buyer)"
            conversation_history += f"{sender_label}: {msg.content}\n"
        
        # Define approach strategies
        approach_strategies = {
            NegotiationApproach.ASSERTIVE: {
                "style": "direct and confident",
                "tactics": "Make firm offers, emphasize market research, be persistent but polite",
                "personality": "business-like and decisive"
            },
            NegotiationApproach.DIPLOMATIC: {
                "style": "balanced and respectful",
                "tactics": "Find mutual benefits, acknowledge seller's position, propose win-win solutions",
                "personality": "professional and understanding"
            },
            NegotiationApproach.CONSIDERATE: {
                "style": "empathetic and budget-conscious",
                "tactics": "Explain budget constraints, show genuine interest, be patient",
                "personality": "humble and appreciative"
            }
        }
        
        strategy = approach_strategies.get(approach, approach_strategies[NegotiationApproach.DIPLOMATIC])
        
        prompt = f"""
You are an AI negotiation agent representing a buyer who wants to purchase: {product.title}

PRODUCT DETAILS:
- Current asking price: ₹{product.price:,}
- Your target price: ₹{target_price:,}
- Your maximum budget: ₹{max_budget:,}
- Product condition: {product.condition}
- Seller: {product.seller_name}
- Location: {product.location}

NEGOTIATION APPROACH: {approach.value.upper()}
- Style: {strategy["style"]}
- Tactics: {strategy["tactics"]}
- Personality: {strategy["personality"]}

CONVERSATION HISTORY:
{conversation_history}

LATEST SELLER MESSAGE: "{last_seller_message}"

INSTRUCTIONS:
1. Respond as a human buyer (never mention you're an AI)
2. Use the {approach.value} negotiation approach consistently
3. Stay within your budget constraints (max ₹{max_budget:,})
4. Work towards your target price of ₹{target_price:,}
5. Keep responses conversational and natural (50-80 words)
6. Include relevant details about pickup/payment when appropriate
7. Be respectful but persistent in negotiations
8. If the seller's price is too high, explain your position clearly
9. If a good deal is reached, move towards closing (exchange contact details)

CURRENT SITUATION ANALYSIS:
- Current offer/price being discussed: Look at the conversation
- Progress towards target: Calculate if you're getting closer
- Seller's flexibility: Assess from their responses

Generate your next response as the buyer:
"""
        
        return prompt
    
    def _build_strategic_context(
        self,
        session_data: Dict[str, Any],
        seller_message: str,
        tactics: List[NegotiationTactic],
        decision: Dict[str, Any],
        product: Product
    ) -> str:
        """Build enhanced strategic context for Gemini AI with advanced tactics"""
        
        session = session_data['session']
        strategy = session_data.get('strategy', {})
        market_analysis = session_data.get('market_analysis', {})
        performance_metrics = session_data.get('performance_metrics', {})
        
        # Get conversation history
        conversation_history = ""
        for msg in session.messages[-8:]:  # Last 8 messages for context
            sender_label = "Seller" if msg.sender == "seller" else "You (Buyer)"
            conversation_history += f"{sender_label}: {msg.content}\n"
        
        # Build tactics description
        tactics_description = self._build_tactics_description(tactics)
        
        # Market intelligence context
        market_context = ""
        if market_analysis:
            avg_price = market_analysis.get('average_price')
            price_range = market_analysis.get('price_range', {})
            if avg_price:
                market_context = f"""
MARKET INTELLIGENCE:
- Average market price: ₹{avg_price:,}
- Price range: ₹{price_range.get('min', 0):,} - ₹{price_range.get('max', 0):,}
- Market trend: {market_analysis.get('market_trend', 'stable')}
- Similar listings: {market_analysis.get('similar_listings_count', 0)}
"""
        
        # Performance context
        performance_context = ""
        if performance_metrics:
            messages_sent = performance_metrics.get('messages_sent', 0)
            effectiveness = performance_metrics.get('negotiation_effectiveness', 0)
            performance_context = f"""
NEGOTIATION PROGRESS:
- Messages exchanged: {messages_sent}
- Negotiation effectiveness: {effectiveness:.1%}
- Time to first response: {performance_metrics.get('time_to_first_response', 'N/A')}
"""
        
        # Decision context
        decision_context = f"""
CURRENT DECISION: {decision.get('action', 'continue')}
- Confidence level: {decision.get('confidence', 0.5):.1%}
- Reasoning: {decision.get('reasoning', 'Continue negotiation')}
"""
        
        if 'offer' in decision:
            decision_context += f"- Recommended offer: ₹{decision['offer']:,}\n"
        
        prompt = f"""
You are an advanced AI negotiation agent representing a buyer for: {product.title}

PRODUCT DETAILS:
- Current asking price: ₹{product.price:,}
- Your target price: ₹{session.user_params.target_price:,}
- Your maximum budget: ₹{session.user_params.max_budget:,}
- Product condition: {product.condition}
- Seller: {product.seller_name}
- Location: {product.location}
- Platform: {product.platform}

NEGOTIATION APPROACH: {session.user_params.approach.value.upper()}
{market_context}
{performance_context}
{decision_context}

CONVERSATION HISTORY:
{conversation_history}

LATEST SELLER MESSAGE: "{seller_message}"

STRATEGIC TACTICS TO USE:
{tactics_description}

ADVANCED INSTRUCTIONS:
1. You are a sophisticated AI agent (never mention being AI to seller)
2. Use the specified tactics naturally in your response
3. Follow the decision guidance while maintaining conversational flow
4. Incorporate market intelligence to support your position
5. Keep responses human-like and conversational (60-100 words)
6. Show empathy while being strategic
7. Use specific numbers and facts to build credibility
8. Maintain the negotiation approach consistently
9. If price is discussed, use market data to justify your position
10. Always work towards your target price while respecting maximum budget

CURRENT NEGOTIATION PHASE: {session_data.get('phase', NegotiationPhase.EXPLORATION).value}

Generate your strategic response as the buyer:
"""
        
        return prompt
    
    def _build_tactics_description(self, tactics: List[NegotiationTactic]) -> str:
        """Build description of tactics to use"""
        
        tactic_descriptions = {
            NegotiationTactic.ANCHORING: "Anchor with market research and comparable prices",
            NegotiationTactic.SCARCITY: "Mention time constraints or alternative options",
            NegotiationTactic.BUNDLING: "Request additional value (accessories, delivery, warranty)",
            NegotiationTactic.RECIPROCITY: "Show appreciation for seller's flexibility and respond in kind",
            NegotiationTactic.SOCIAL_PROOF: "Reference what others are paying for similar items",
            NegotiationTactic.URGENCY: "Express time sensitivity or immediate purchase capability",
            NegotiationTactic.AUTHORITY: "Reference expert advice or professional recommendations",
            NegotiationTactic.COMMITMENT: "Show readiness to close the deal immediately"
        }
        
        if not tactics:
            return "No specific tactics - focus on natural conversation and relationship building"
        
        descriptions = []
        for tactic in tactics:
            desc = tactic_descriptions.get(tactic, f"Use {tactic.value} approach")
            descriptions.append(f"- {desc}")
        
        return "\n".join(descriptions)
    
    async def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API asynchronously"""
        try:
            # Run the synchronous Gemini call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise
    
    def _get_fallback_response(
        self, 
        approach,  # Can be string or NegotiationApproach enum
        target_price: int, 
        chat_history: List[ChatMessage],
        product: Product
    ) -> str:
        """Fallback responses when AI is not available"""
        
        # Convert string to enum if needed
        if isinstance(approach, str):
            try:
                approach = NegotiationApproach(approach.lower())
            except ValueError:
                approach = NegotiationApproach.DIPLOMATIC  # Default fallback
        
        # Get last seller message
        seller_messages = [msg for msg in chat_history if msg.sender == "seller"]
        
        if not seller_messages:
            # Opening message
            if approach == NegotiationApproach.ASSERTIVE:
                return f"Hello {product.seller_name}! I'm interested in your listing. Based on current market rates, I'd like to offer ₹{target_price:,}. Is this acceptable?"
            elif approach == NegotiationApproach.DIPLOMATIC:
                return f"Good day {product.seller_name}! I'm very interested in your product. Would you consider an offer of ₹{target_price:,}? I believe it's a fair price given the current market."
            else:  # CONSIDERATE
                return f"Hi {product.seller_name}! I'm really interested in your listing. My budget is a bit tight at ₹{target_price:,}. Would this work for you?"
        
        # Response to seller
        last_message = seller_messages[-1].content.lower()
        message_count = len(seller_messages)
        
        # Keywords for different responses
        if "hi" in last_message or "hello" in last_message or "available" in last_message:
            # Greeting/availability check
            if approach == NegotiationApproach.ASSERTIVE:
                return f"Hello {product.seller_name}! Yes, I'm very interested. I can offer ₹{target_price:,} for immediate purchase. When can we meet?"
            elif approach == NegotiationApproach.DIPLOMATIC:
                return f"Hi there {product.seller_name}! Yes, I'm interested in your listing. The item looks great. Would ₹{target_price:,} work for you?"
            else:  # CONSIDERATE
                return f"Hello {product.seller_name}! Yes, I'm interested. I'm hoping to stay within ₹{target_price:,} if possible. Could we work something out?"
        
        elif "price" in last_message or "cost" in last_message or "amount" in last_message:
            # Price discussion
            if approach == NegotiationApproach.ASSERTIVE:
                return f"Based on market research, ₹{target_price:,} is what I can offer. It's competitive and fair."
            elif approach == NegotiationApproach.DIPLOMATIC:
                return f"I've been looking at similar items, and ₹{target_price:,} seems reasonable. What do you think?"
            else:  # CONSIDERATE
                return f"I understand the value, but my budget is limited to ₹{target_price:,}. Is there any flexibility?"
        
        elif "no" in last_message or "cannot" in last_message or "firm" in last_message or "minimum" in last_message:
            # Seller rejected - increase offer slightly
            counter_offer = min(int(target_price * 1.15), target_price + 5000)
            if approach == NegotiationApproach.ASSERTIVE:
                return f"I understand. Let me stretch my budget to ₹{counter_offer:,}. This is really my maximum."
            elif approach == NegotiationApproach.DIPLOMATIC:
                return f"I appreciate your position. Could we perhaps meet at ₹{counter_offer:,}? That would really help both of us."
            else:  # CONSIDERATE
                return f"I really want this item. Could you please consider ₹{counter_offer:,}? It would mean a lot to me."
        
        elif "yes" in last_message or "okay" in last_message or "accept" in last_message or "deal" in last_message:
            # Seller accepted
            return "Excellent! That works perfectly for me. When would be convenient for pickup? I can arrange payment immediately."
        
        elif "meet" in last_message or "pickup" in last_message or "delivery" in last_message:
            # Logistics discussion
            return "Perfect! I'm flexible with timing. I can come today or tomorrow, whatever works best for you. Should I bring cash or is online transfer preferred?"
        
        elif "condition" in last_message or "working" in last_message or "problem" in last_message:
            # Product condition inquiry
            return "Thank you for the details. As long as everything is as described, I'm happy to proceed with ₹{target_price:,}. Can we finalize this?"
        
        else:
            # General response
            if approach == NegotiationApproach.ASSERTIVE:
                return f"Let me be direct - I can offer ₹{target_price:,} and arrange pickup today. This is a fair market price."
            elif approach == NegotiationApproach.DIPLOMATIC:
                return f"I've researched similar listings and ₹{target_price:,} seems to be the going rate. Would you consider this offer?"
            else:  # CONSIDERATE
                return f"I'm really hoping we can work something out at ₹{target_price:,}. This would really help with my budget constraints."
    
    def _get_enhanced_fallback_response(
        self, 
        session_data: Dict[str, Any],
        seller_message: str,
        tactics: List[NegotiationTactic],
        decision: Dict[str, Any],
        product: Product
    ) -> str:
        """Enhanced fallback responses using advanced context"""
        
        session = session_data['session']
        approach = session.user_params.approach
        target_price = session.user_params.target_price
        max_budget = session.user_params.max_budget
        
        action = decision.get('action', 'continue')
        
        # Handle specific decisions
        if action == 'accept':
            return random.choice([
                "Perfect! That works for me. When can we arrange the pickup?",
                "Excellent! I accept your offer. How should we proceed with payment?",
                "Great! That's exactly what I was hoping for. Let's finalize this deal."
            ])
        
        elif action == 'walk_away':
            return random.choice([
                "I appreciate your time, but that's beyond my budget. Thank you for considering my offers.",
                "Thank you for the negotiation. Unfortunately, we couldn't reach a mutually beneficial agreement.",
                "I understand your position, but I'll need to explore other options. Best of luck with your sale!"
            ])
        
        elif action in ['counter_offer', 'final_offer']:
            offer = decision.get('offer', target_price)
            
            # Use tactics in fallback responses
            if NegotiationTactic.ANCHORING in tactics:
                return f"Based on current market rates, I think ₹{offer:,} is a fair price. Similar items are selling in this range."
            
            elif NegotiationTactic.URGENCY in tactics:
                return f"I can make a quick decision if we can agree on ₹{offer:,}. I'm ready to complete the purchase today."
            
            elif NegotiationTactic.SCARCITY in tactics:
                return f"I'm considering a few options, but yours is my preference. Would ₹{offer:,} work? I can decide immediately."
            
            elif NegotiationTactic.BUNDLING in tactics:
                return f"For ₹{offer:,}, could you include original accessories or help with delivery? That would seal the deal."
            
            elif NegotiationTactic.RECIPROCITY in tactics:
                return f"I appreciate your flexibility on this. Meeting me at ₹{offer:,} would really help within my budget."
            
            else:
                # Default counter offer
                if approach == NegotiationApproach.ASSERTIVE:
                    return f"Let me be direct - ₹{offer:,} is my best offer based on market research. Can we make this work?"
                elif approach == NegotiationApproach.DIPLOMATIC:
                    return f"I've done some research and ₹{offer:,} seems fair for both of us. What do you think?"
                else:  # CONSIDERATE
                    return f"I really want this item. Could you please consider ₹{offer:,}? It would mean a lot to me."
        
        # Default exploratory response
        message_lower = seller_message.lower()
        
        if "hi" in message_lower or "hello" in message_lower:
            return f"Hello {product.seller_name}! I'm very interested in your {product.title}. Is ₹{target_price:,} something we could work with?"
        
        elif "price" in message_lower or "offer" in message_lower:
            market_analysis = session_data.get('market_analysis', {})
            if market_analysis.get('average_price'):
                avg_price = market_analysis['average_price']
                return f"I've researched similar items averaging ₹{avg_price:,}. Could we settle at ₹{target_price:,}?"
            else:
                return f"Based on my budget and research, ₹{target_price:,} would work best for me. Is there flexibility here?"
        
        else:
            return "I'm definitely interested. Let's see if we can find a price that works for both of us."


# Utility function to test Gemini API connection
async def test_gemini_connection():
    """Test function to verify Gemini API is working"""
    service = GeminiAIService()
    
    if not service.model:
        print("[ERROR] Gemini API not configured properly")
        return False
    
    try:
        test_prompt = "Say 'Hello from Gemini AI!' in a friendly way."
        response = await service._call_gemini_api(test_prompt)
        print(f"[INFO] Gemini API test successful: {response}")
        return True
    except Exception as e:
        print(f"[ERROR] Gemini API test failed: {e}")
        return False