#!/usr/bin/env python3
"""
Test the scraping through the API endpoint
"""

import asyncio
import aiohttp
import json

async def test_api_scraping():
    """Test scraping through the API"""
    
    test_data = {
        "product_url": "https://www.olx.in/item/iphone-13-128gb-blue-excellent-condition-iid-1784140851",
        "target_price": 45000,
        "max_budget": 55000,
        "approach": "diplomatic",
        "timeline": "flexible",
        "special_requirements": "Good condition required"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/api/negotiate-url',
                json=test_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                print(f"Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ API Response:")
                    print(f"  Session ID: {result.get('session_id')}")
                    print(f"  Product Title: {result.get('product', {}).get('title')}")
                    print(f"  Product Price: ₹{result.get('product', {}).get('price', 0):,}")
                    print(f"  Scraping Success: {result.get('product', {}).get('scraped_successfully', False)}")
                    print(f"  Status: {result.get('status')}")
                else:
                    error_text = await response.text()
                    print(f"❌ API Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_scraping())