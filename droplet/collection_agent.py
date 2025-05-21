# collection_agent.py - updated Tor handling
from flask import Flask, request, jsonify
import requests
import socks
import socket
import json
import os
import re
import time
import hmac
import hashlib
import logging
import traceback
from datetime import datetime

app = Flask(__name__)

# Configure logging with UTF-8 support
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("collection_agent.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("collection_agent")

# Get configuration from environment
TOR_HOST = os.environ.get('TOR_HOST', 'tor')
TOR_PORT = int(os.environ.get('TOR_PORT', '9150'))
API_SECRET = os.environ.get('API_SECRET', 'test-secret')

# Keep track of whether Tor is set up
tor_setup_complete = False

def setup_tor():
    """Configure requests to use Tor"""
    global tor_setup_complete
    
    if tor_setup_complete:
        logger.debug("Tor already configured, skipping setup")
        return True
        
    try:
        # Configure for SOCKS proxy
        logger.info(f"Setting up Tor SOCKS proxy at {TOR_HOST}:{TOR_PORT}")
        
        # Backup the original socket implementation
        orig_socket = socket.socket
        
        # Configure socks
        socks.set_default_proxy(socks.SOCKS5, TOR_HOST, TOR_PORT)
        socket.socket = socks.socksocket
        
        logger.info(f"Tor proxy configured at {TOR_HOST}:{TOR_PORT}")
        
        # Test the Tor connection to verify it's working
        test_url = "https://check.torproject.org"
        logger.info(f"Testing Tor connection with {test_url}")
        
        response = requests.get(test_url, timeout=30)
        
        if "Congratulations" in response.text and "Tor" in response.text:
            logger.info("Tor connection confirmed working!")
            tor_setup_complete = True
            return True
        else:
            logger.warning("Connected to proxy but not confirmed as Tor")
            logger.debug(f"Response content: {response.text[:200]}...")
            socket.socket = orig_socket  # Restore original socket
            tor_setup_complete = False
            return False
    except Exception as e:
        logger.error(f"Failed to configure Tor proxy: {e}")
        logger.error(traceback.format_exc())
        # Try to restore original socket if available
        if 'orig_socket' in locals():
            socket.socket = orig_socket
        tor_setup_complete = False
        return False

def verify_api_key(api_key):
    """Verify the API key using HMAC"""
    if not api_key:
        return False
        
    try:
        # Extract timestamp and signature
        parts = api_key.split(":", 1)
        if len(parts) != 2:
            logger.warning("Invalid API key format")
            return False
            
        timestamp, signature = parts
        
        # Check if timestamp is reasonably recent (within 15 minutes)
        now = int(time.time())
        then = int(timestamp)
        if abs(now - then) > 900:  # 15 minutes
            logger.warning(f"API key timestamp too old: {now - then} seconds")
            return False
            
        # Verify signature
        expected = hmac.new(
            API_SECRET.encode(), 
            timestamp.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected)
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        return False

def parse_generic(html_content, url=None):
    """Generic parser for any website"""
    # Extract title
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
    title = title_match.group(1) if title_match else "Unknown"
    
    # For testing with check.torproject.org
    is_using_tor = "Congratulations" in html_content and "Tor" in html_content
    
    # Basic victim extraction (placeholder - customize based on site patterns)
    victims = []
    
    # Just a simple extraction for testing
    item_pattern = re.findall(
        r'<div class="[^"]*victim[^"]*".*?>.*?<h\d>(.*?)</h\d>.*?<span class="[^"]*date[^"]*">(.*?)</span>',
        html_content, 
        re.DOTALL | re.IGNORECASE
    )
    
    for name, date in item_pattern:
        victims.append({
            "name": name.strip(),
            "date": date.strip(),
        })
    
    # If no victims found by pattern, create a test entry with the page title
    if not victims and is_using_tor:
        victims.append({
            "name": "Tor Test Successful",
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return {
        "title": title,
        "is_using_tor": is_using_tor,
        "victims": victims,
        "url": url,
        "raw_html": html_content  # Add the raw HTML content to the response
    }

def parse_omegalock(html_content, url=None):
    """
    Custom parser for Omega Lock ransomware site.
    
    This parser extracts victim information from the data table structure
    on the Omegalock leak site, focusing only on essential data needed
    for our schema.
    """
    title = "Omega Lock"
    victims = []
    
    try:
        # Extract title if available
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            
        # Find the data table
        table_match = re.search(r'<table class="datatable center">(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
        
        if table_match:
            table_content = table_match.group(1)
            
            # Extract rows with class 'trow' (these contain victim data)
            victim_rows = re.findall(r'<tr class=[\'"]trow[\'"]>(.*?)</tr>', table_content, re.DOTALL | re.IGNORECASE)
            
            logger.info(f"Found {len(victim_rows)} victim rows in the Omegalock table")
            
            # Process each victim row
            for row in victim_rows:
                try:
                    # Extract all table cells
                    cells = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                    
                    if len(cells) >= 5:  # Ensure we have enough cells
                        # Column 0: Company name
                        company_name = re.sub(r'<.*?>', '', cells[0]).strip()
                        
                        # Column 1: Leak percentage (not used in schema but useful for comment)
                        leak_percentage = re.sub(r'<.*?>', '', cells[1]).strip()
                        
                        # Column 2: Tags/sector information
                        tags = re.sub(r'<.*?>', '', cells[2]).strip()
                        
                        # Column 3: Data size
                        data_size = re.sub(r'<.*?>', '', cells[3]).strip()
                        
                        # Column 4: Last updated date
                        last_updated = re.sub(r'<.*?>', '', cells[4]).strip()
                        
                        # Column 5: Link (if available)
                        link_match = re.search(r'href="([^"]+)"', cells[5] if len(cells) > 5 else "", re.IGNORECASE)
                        link = link_match.group(1) if link_match else ""
                        
                        # Clean up any remaining HTML tags
                        company_name = re.sub(r'<[^>]*>', '', company_name).strip()
                        
                        if company_name:  # Only add if we have a company name
                            victims.append({
                                "name": company_name,
                                "date": last_updated,
                                "group": "omegalock",
                                "sector": tags,  # Use tags as sector
                                "leak_percentage": leak_percentage,
                                "data_size": data_size,
                                "link": link,
                                "source_url": url
                            })
                            logger.debug(f"Extracted victim: {company_name} ({last_updated})")
                    
                except Exception as e:
                    logger.error(f"Error processing victim row: {str(e)}")
                    continue
        else:
            logger.warning("Data table not found in Omegalock HTML")
            
            # Fallback: try to extract companies from table cells
            company_patterns = re.findall(
                r'<td>([\w\s\.\,\&\;\-]+(?:Company|LLC|Inc|Ltd|GmbH|Corp|SA|AG|BV)?)</td>',
                html_content,
                re.IGNORECASE
            )
            
            if company_patterns:
                logger.debug(f"Fallback found {len(company_patterns)} potential company names")
                for company in company_patterns:
                    company_name = company.strip()
                    if company_name and len(company_name) > 5:
                        # Create a minimal victim entry
                        victims.append({
                            "name": company_name,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "group": "omegalock"
                        })
    
    except Exception as e:
        logger.error(f"Error parsing Omega Lock site: {str(e)}")
        logger.error(traceback.format_exc())
    
    return {
        "title": title,
        "victims": victims,
        "url": url,
        "is_using_tor": True,
        "timestamp": datetime.now().isoformat(),
        "raw_html": html_content
    }

# Parser registry - map parser names to functions
PARSERS = {
    "generic": parse_generic,
    "omegalock": parse_omegalock,
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    tor_status = setup_tor()
    return jsonify({
        "status": "ok", 
        "timestamp": time.time(),
        "tor_configured": (TOR_HOST, TOR_PORT),
        "tor_working": tor_status
    })

@app.route('/collect', methods=['POST'])
def collect():
    """Collect data from a target website"""
    # Get API key and verify
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        logger.warning("Unauthorized API request")
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get request data
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required parameters"}), 400
            
        target_url = data['url']
        parser_type = data.get('parser', 'generic')
        request_timeout = int(data.get('timeout', 120))
        
        # Auto-select parser based on URL if set to 'auto'
        if parser_type == 'auto':
            if 'omegalock' in target_url:
                parser_type = 'omegalock'
            else:
                parser_type = 'generic'
                
        logger.info(f"Collecting from: {target_url} using parser: {parser_type}")
        
        # Configure Tor
        if not setup_tor():
            return jsonify({"error": "Failed to configure Tor"}), 500
        
        # Make the request via Tor
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0'
        }
        
        try:
            # For .onion domains, make sure we're using the Tor proxy properly
            if '.onion' in target_url:
                logger.info(f"Requesting .onion domain via Tor: {target_url}")
                
                # Ensure the URL is properly formatted
                if not target_url.startswith(("http://", "https://")):
                    target_url = f"http://{target_url}"
                    
                response = requests.get(
                    target_url, 
                    headers=headers, 
                    timeout=request_timeout,
                    proxies={
                        'http': f'socks5h://{TOR_HOST}:{TOR_PORT}',
                        'https': f'socks5h://{TOR_HOST}:{TOR_PORT}'
                    }
                )
            else:
                # For regular domains, the default Tor setup should work
                response = requests.get(
                    target_url, 
                    headers=headers, 
                    timeout=request_timeout
                )
                
            response.raise_for_status()
            logger.info(f"Successfully retrieved {len(response.text)} bytes from {target_url}")
            
            # Get the appropriate parser function
            parser = PARSERS.get(parser_type)
            if not parser:
                logger.warning(f"Unknown parser type: {parser_type}, falling back to generic")
                parser = parse_generic
                
            # Parse the content
            result = parser(response.text, target_url)
            
            # Add metadata
            result['metadata'] = {
                'timestamp': time.time(),
                'target': target_url,
                'status_code': response.status_code,
                'content_length': len(response.text),
                'parser_used': parser_type
            }
            
            logger.info(f"Successfully collected data from {target_url}")
            return jsonify(result)
            
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            return jsonify({
                "error": f"Failed to retrieve URL: {str(e)}",
                "metadata": {
                    'timestamp': time.time(),
                    'target': target_url
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    # Set debug mode only in development
    app.run(host='0.0.0.0', debug=False)