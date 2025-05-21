# utils/onion_curl.py
"""
Utility for fetching content from .onion sites via the Tor proxy.

This module provides a simple 'curl-like' functionality to:
- Retrieve HTML content from .onion sites
- Save or display the content for examination
- Help with parser development
"""

import requests
import hmac
import hashlib
import time
import logging
import os
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

logger = logging.getLogger("utils.onion_curl")

def fetch_onion_content(
    url: str,
    config,
    parser_type: str = "generic",
    timeout: int = 120,
    save_to_file: bool = False,
    output_dir: str = "debug_html",
    include_metadata: bool = True
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Fetch content from an onion site via the Tor proxy.
    
    Args:
        url: The onion URL to fetch
        config: Configuration object for accessing API details
        parser_type: Parser type to use (generic just returns HTML)
        timeout: Request timeout in seconds
        save_to_file: Whether to save the HTML to a file
        output_dir: Directory to save the HTML file to
        include_metadata: Whether to include metadata in the response
        
    Returns:
        Tuple of (HTML content, metadata dict)
    """
    # Ensure the URL is properly formatted
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    
    # Get configuration
    endpoint = config.get_droplet_endpoint()
    api_secret = config.get_droplet_api_secret()
    
    # Generate API key
    timestamp = str(int(time.time()))
    signature = hmac.new(
        api_secret.encode(), 
        timestamp.encode(),
        hashlib.sha256
    ).hexdigest()
    api_key = f"{timestamp}:{signature}"
    
    # Prepare request
    logger.info(f"Fetching content from: {url}")
    
    try:
        # Make request to collection agent
        response = requests.post(
            f"{endpoint}/collect",
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "url": url, 
                "parser": parser_type,
                "timeout": timeout
            },
            timeout=timeout + 30  # Add extra time for agent processing
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Check for error
        if "error" in data:
            logger.error(f"Error fetching content: {data['error']}")
            return None, {"error": data["error"], "url": url, "timestamp": datetime.now().isoformat()}
        
        # Extract raw HTML - this isn't directly provided by the API, but can be inferred
        html_content = data.get("raw_html", "")
        
        # If raw_html isn't available, create a diagnostic message
        if not html_content:
            # The API doesn't directly return raw HTML, so we'll need to adapt the agent code or
            # provide diagnostic information
            logger.warning("Raw HTML not available in response. The collection agent may need to be updated.")
            html_content = f"""
            <!-- 
            NOTE: Raw HTML not directly available. Here's the data received:
            
            Title: {data.get('title', 'Unknown')}
            Timestamp: {data.get('metadata', {}).get('timestamp', 'Unknown')}
            URL: {url}
            Content Length: {data.get('metadata', {}).get('content_length', 'Unknown')}
            
            Victims Found: {len(data.get('victims', []))}
            
            To get raw HTML, update the collection_agent.py to return the raw HTML in the response.
            -->
            
            {data}
            """
        
        # Save to file if requested
        if save_to_file:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Create a filename based on the domain and timestamp
            domain = url.replace("http://", "").replace("https://", "").replace("/", "_")
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{domain}_{timestamp_str}.html"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"Saved HTML to: {filepath}")
            
            # Add filepath to metadata
            data["metadata"] = data.get("metadata", {})
            data["metadata"]["saved_to"] = filepath
        
        # Return the content and metadata
        return html_content, data
        
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return None, {"error": str(e), "url": url, "timestamp": datetime.now().isoformat()}
    except ValueError as e:
        logger.error(f"Error parsing JSON response: {e}")
        return None, {"error": str(e), "url": url, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None, {"error": str(e), "url": url, "timestamp": datetime.now().isoformat()}