#!/usr/bin/env python3
"""
Test script to debug web scraping issues
"""

import asyncio
import sys
import os
sys.path.append('/home/denistanb05/Mr. Tech/Deni/Mr. Tech/AI/Projects/Negotiation Agent/Negotiate Bot/backend')

from scraper_service import MarketplaceScraper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scraping():
    """Test scraping with sample URLs"""
    
    test_urls = [
        "https://www.olx.in/item/iphone-13-128gb-blue-iid-1784140851",
        "https://www.olx.in/item/samsung-galaxy-s21-5g-256gb-phantom-black-iid-1774627371",
        "https://www.olx.in/item/macbook-air-m1-256gb-space-grey-iid-1785234567"
    ]
    
    async with MarketplaceScraper() as scraper:
        for url in test_urls:
            logger.info(f"\n🔍 Testing URL: {url}")
            try:
                result = await scraper.scrape_product(url)
                if result:
                    logger.info(f"✅ Title: {result.get('title', 'N/A')}")
                    logger.info(f"💰 Price: ₹{result.get('price', 0):,}")
                    logger.info(f"📍 Location: {result.get('location', 'N/A')}")
                    logger.info(f"👤 Seller: {result.get('seller_name', 'N/A')}")
                    logger.info(f"🔧 Scraped Successfully: {result.get('scraped_successfully', False)}")
                    logger.info(f"📝 Description: {result.get('description', 'N/A')[:100]}...")
                else:
                    logger.error("❌ No result returned")
            except Exception as e:
                logger.error(f"❌ Error: {e}")
            
            logger.info("-" * 80)

if __name__ == "__main__":
    asyncio.run(test_scraping())