#!/usr/bin/env python3
"""
Improved web scraper with better error handling and accurate extraction
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from datetime import datetime
import random
import json

logger = logging.getLogger(__name__)

class ImprovedMarketplaceScraper:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        # Better headers that mimic real browsers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Configure session with better settings
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            enable_cleanup_closed=True,
            ssl=False  # Skip SSL verification for now
        )
        
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=timeout,
            connector=connector
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def scrape_product(self, url: str) -> dict:
        """Scrape product with multiple fallback strategies"""
        domain = urlparse(url).netloc.lower()
        
        logger.info(f"Scraping {domain} URL: {url}")
        
        # Add delay to appear more human-like
        await asyncio.sleep(random.uniform(1, 2))
        
        try:
            async with self.session.get(url) as response:
                logger.info(f"Response status: {response.status}")
                
                if response.status != 200:
                    logger.warning(f"Non-200 status code: {response.status}")
                    return self._create_fallback_product(url)
                
                html = await response.text()
                logger.info(f"HTML content length: {len(html)}")
                
                # Check if we got actual content
                if len(html) < 1000:
                    logger.warning("Received very short HTML content")
                    
                soup = BeautifulSoup(html, 'html.parser')
                
                # Debug: Print some basic info about the page
                title_tag = soup.find('title')
                logger.info(f"Page title: {title_tag.get_text() if title_tag else 'No title'}")
                
                # Parse based on platform
                if 'olx' in domain:
                    return self._parse_olx_improved(soup, url, html)
                elif 'facebook' in domain:
                    return self._parse_facebook(soup, url)
                else:
                    return self._parse_generic(soup, url)
                    
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return self._create_fallback_product(url)
    
    def _parse_olx_improved(self, soup: BeautifulSoup, url: str, html: str) -> dict:
        """Improved OLX parsing with debugging"""
        
        # Debug: Check what we actually received
        logger.info("Analyzing OLX page structure...")
        
        # Check for common OLX indicators
        olx_indicators = [
            'olx.in',
            'data-aut-id',
            'itemTitle',
            'itemPrice'
        ]
        
        found_indicators = []
        for indicator in olx_indicators:
            if indicator in html:
                found_indicators.append(indicator)
        
        logger.info(f"Found OLX indicators: {found_indicators}")
        
        # Try multiple title extraction strategies
        title = None
        title_selectors = [
            'h1[data-aut-id="itemTitle"]',
            'h1[data-testid="ad-title"]',
            '.it-ttl',
            'h1.pds-box-title',
            'h1.kY95w',  # Updated selector
            'h1._1k7g5',  # Another variant
            'h1'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            logger.info(f"Selector '{selector}' found {len(elements)} elements")
            
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 5 and not any(skip in text.lower() for skip in ['olx', 'buy', 'sell', 'login']):
                    title = text
                    logger.info(f"Found title with selector '{selector}': {title}")
                    break
            
            if title:
                break
        
        # Try multiple price extraction strategies
        price = 0
        price_selectors = [
            '[data-aut-id="itemPrice"]',
            '[data-testid="ad-price"]',
            '.notranslate',
            '._6eme8',
            '.kxOcF'  # Updated selector
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            logger.info(f"Price selector '{selector}' found {len(elements)} elements")
            
            for element in elements:
                price_text = element.get_text(strip=True)
                logger.info(f"Price text found: '{price_text}'")
                extracted_price = self._extract_price_number(price_text)
                if extracted_price > 0:
                    price = extracted_price
                    logger.info(f"Extracted price: ₹{price}")
                    break
            
            if price > 0:
                break
        
        # Extract description
        description = ""
        desc_selectors = [
            '[data-aut-id="itemDescriptionText"]',
            '.dOqyp',
            '.ad-description'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                description = element.get_text(strip=True)
                logger.info(f"Found description: {description[:100]}...")
                break
        
        # Extract location
        location = ""
        location_selectors = [
            '[data-aut-id="item-location"]',
            '.rVpZl',
            '.location-text'
        ]
        
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                location = element.get_text(strip=True)
                logger.info(f"Found location: {location}")
                break
        
        # Determine if scraping was successful
        scraping_success = bool(title and price > 0)
        
        result = {
            'title': title or self._extract_title_from_url(url),
            'description': description or 'Product description not available',
            'price': price or self._estimate_price_from_title(title or ''),
            'original_price': price,
            'seller_name': 'OLX Seller',
            'seller_contact': 'Contact via OLX',
            'location': location or 'India',
            'url': url,
            'platform': 'OLX',
            'category': self._categorize_product(title or ''),
            'condition': 'Used',
            'images': [],
            'features': [],
            'posted_date': datetime.now().isoformat(),
            'is_available': True,
            'scraped_successfully': scraping_success
        }
        
        logger.info(f"Scraping result - Success: {scraping_success}, Title: {result['title']}, Price: ₹{result['price']}")
        return result
    
    def _extract_price_number(self, text: str) -> int:
        """Extract price number from text"""
        if not text:
            return 0
        
        # Remove common words
        text = re.sub(r'(per|month|year|day|week|negotiable)', '', text, flags=re.IGNORECASE)
        
        # Find price patterns
        patterns = [
            r'₹\s*([0-9,]+)',
            r'Rs\.?\s*([0-9,]+)',
            r'INR\s*([0-9,]+)',
            r'([0-9,]+)\s*₹',
            r'([0-9,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price = int(match.group(1).replace(',', ''))
                    if 100 <= price <= 10000000:  # Reasonable range
                        return price
                except ValueError:
                    continue
        
        return 0
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract title from URL as fallback"""
        path = urlparse(url).path
        title_parts = re.sub(r'[/_\-]', ' ', path).strip()
        title_parts = re.sub(r'\d+', '', title_parts)
        words = [word.capitalize() for word in title_parts.split() if len(word) > 2]
        return ' '.join(words[:6]) if words else "Marketplace Product"
    
    def _estimate_price_from_title(self, title: str) -> int:
        """Estimate price based on product title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['iphone', 'ipad', 'macbook', 'apple']):
            return 50000
        elif any(word in title_lower for word in ['samsung', 'oneplus', 'phone', 'mobile']):
            return 25000
        elif any(word in title_lower for word in ['laptop', 'computer']):
            return 40000
        elif any(word in title_lower for word in ['car', 'vehicle']):
            return 500000
        elif any(word in title_lower for word in ['bike', 'motorcycle']):
            return 80000
        
        return 15000  # Default
    
    def _categorize_product(self, title: str) -> str:
        """Categorize product based on title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['phone', 'mobile', 'iphone', 'samsung']):
            return 'Electronics'
        elif any(word in title_lower for word in ['laptop', 'computer', 'macbook']):
            return 'Computers'
        elif any(word in title_lower for word in ['car', 'vehicle']):
            return 'Vehicles'
        elif any(word in title_lower for word in ['bike', 'motorcycle']):
            return 'Bikes'
        
        return 'Other'
    
    def _parse_facebook(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse Facebook Marketplace"""
        # Facebook parsing logic here
        return self._create_fallback_product(url)
    
    def _parse_generic(self, soup: BeautifulSoup, url: str) -> dict:
        """Generic parser"""
        return self._create_fallback_product(url)
    
    def _create_fallback_product(self, url: str) -> dict:
        """Create fallback product when scraping fails"""
        title = self._extract_title_from_url(url)
        price = self._estimate_price_from_title(title)
        
        return {
            'title': title,
            'description': 'Product details will be confirmed during negotiation',
            'price': price,
            'original_price': price,
            'seller_name': 'Marketplace Seller',
            'seller_contact': 'Contact via platform',
            'location': 'India',
            'url': url,
            'platform': 'Marketplace',
            'category': self._categorize_product(title),
            'condition': 'Used',
            'images': [],
            'features': ['AI-assisted negotiation'],
            'posted_date': datetime.now().isoformat(),
            'is_available': True,
            'scraped_successfully': False,
            'fallback_used': True
        }

# Test the improved scraper
async def test_improved_scraper():
    test_urls = [
        "https://www.olx.in/item/apple-iphone-13-128gb-blue-excellent-condition-iid-1785123456",
    ]
    
    async with ImprovedMarketplaceScraper() as scraper:
        for url in test_urls:
            result = await scraper.scrape_product(url)
            print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_improved_scraper())