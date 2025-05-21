# tests/test_omegalock_parser.py
"""
Test cases for the Omegalock parser.

This module contains tests for verifying that the Omegalock parser
correctly extracts victim data from HTML content.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

from cli_modules.ui import clear_screen, print_header
from test_framework import TestCase
from tests.test_registry import register_test_case

# Sample HTML for testing
SAMPLE_HTML = """
<html>
        <head>
                <link rel="icon" type="image/ico" href="/assets/favicon.ico"/>
                <title>0mega | Blog</title>
                <link rel='stylesheet' href='/assets/main.css'>
        </head>
        <body>
                <div class="center block">
                        <h4 class="theading">Leaked Data</h4>
                        <p class="tstat">(5 cases total)</p>
                        <table class="datatable center">
                        <tr>
                                <td><b>company name</b></td>
                                <td><b>leaked</b></td>
                                <td><b>tags</b></td>
                                <td><b>total data size</b></td>
                                <td><b>last updated</b></td>
                                <td class="tab"><b>downloads</b></td>
                        </tr>

                        <tr class='trow'>
                                <td>Test Company Inc</td>
                                <td>100%</td>
                                <td>Software, Technology</td>
                                <td>500 GB</td>
                                <td>2024-03-15</td>
                                <td><a href="/post/6.html" target="_blank">open</a></td>
                        </tr>
                        <tr class='trow'>
                                <td>Another Victim LLC</td>
                                <td>75%</td>
                                <td>Manufacturing, Industrial</td>
                                <td>250 GB</td>
                                <td>2024-03-10</td>
                                <td><a href="/post/5.html" target="_blank">open</a></td>
                        </tr>
                        </table>
                </div>
        </body>
</html>
"""

@register_test_case
class OmegalockParserTestCase(TestCase):
    """Tests for the Omegalock parser implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import the parser function - we'll mock it for testing
        self.datetime_mock = datetime(2024, 3, 20)
        
        # Create a mock for the parser's dependencies
        self.re_mock = MagicMock()
        self.datetime_mock = MagicMock()
        self.logger_mock = MagicMock()
    
    def test_omegalock_parser(self):
        """
        Test the Omegalock parser with sample HTML.
        
        This tool allows testing the parser against sample HTML to ensure
        it correctly extracts victim data for Omegalock.
        """
        clear_screen()
        print_header("TEST OMEGALOCK PARSER")
        
        try:
            # Import necessary modules
            from config import Config
            import re
            from datetime import datetime
            
            # First check if we have sample HTML - either from a file or we'll use a sample
            print("This tool tests the Omegalock parser with sample HTML.")
            
            # Ask for HTML source
            print("\nSelect HTML source:")
            print("1. Use sample HTML from file")
            print("2. Use built-in sample HTML")
            print("3. Fetch live HTML from Omegalock site")
            
            source_choice = input("\nEnter choice (1-3): ").strip()
            
            html_content = ""
            
            if source_choice == "1":
                # Get HTML from file
                file_path = input("\nEnter path to HTML file: ").strip()
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    print(f"\nLoaded {len(html_content)} bytes from {file_path}")
                except Exception as e:
                    print(f"\nError loading file: {str(e)}")
                    input("\nPress Enter to return to the test menu...")
                    return
            
            elif source_choice == "2":
                # Use built-in sample
                html_content = """
                <html>
                    <head>
                        <title>0mega | Blog</title>
                    </head>
                    <body>
                        <div class="center block">
                            <h4 class="theading">Leaked Data</h4>
                            <p class="tstat">(5 cases total)</p>
                            <table class="datatable center">
                            <tr>
                                <td><b>company name</b></td>
                                <td><b>leaked</b></td>
                                <td><b>tags</b></td>
                                <td><b>total data size</b></td>
                                <td><b>last updated</b></td>
                                <td class="tab"><b>downloads</b></td>
                            </tr>
                            <tr class='trow'>
                                <td>Rotorcraft Leasing Company</td>
                                <td>100%</td>
                                <td>Helicopter support, pilot training, fueling service, maintenance</td>
                                <td>1.54 TB</td>
                                <td>2024-01-17</td>
                                <td><a href="/post/5.html" target="_blank">open</a></td>
                            </tr>
                            <tr class='trow'>
                                <td>US Liner Company & American Made LLC</td>
                                <td>100%</td>
                                <td>Industrial engineering, manufacturing, advanced materials, thermoplastic composite solutions</td>
                                <td>712 GB</td>
                                <td>2024-01-17</td>
                                <td><a href="/post/4.html" target="_blank">open</a></td>
                            </tr>
                            </table>
                        </div>
                    </body>
                </html>
                """
                print("\nUsing built-in sample HTML.")
            
            elif source_choice == "3":
                # Fetch from Omegalock site using onion_curl utility
                print("\nFetching HTML from Omegalock site...")
                from utils.onion_curl import fetch_onion_content
                
                config = Config()
                html, metadata = fetch_onion_content(
                    url="http://omegalock5zxwbhswbisc42o2q2i54vdulyvtqqbudqousisjgc7j7yd.onion/",
                    config=config,
                    save_to_file=False
                )
                
                if html:
                    html_content = html
                    print(f"\nFetched {len(html_content)} bytes from Omegalock site.")
                else:
                    print(f"\nError fetching HTML: {metadata.get('error', 'Unknown error')}")
                    input("\nPress Enter to return to the test menu...")
                    return
            
            else:
                print("\nInvalid choice.")
                input("\nPress Enter to return to the test menu...")
                return
            
            # Now that we have HTML, define the parser function that matches the real implementation
            def parse_omegalock_test(html_content, url=None):
                """Exact replica of the actual parser for testing"""
                title = "Omega Lock"
                victims = []
                
                try:
                    # Extract title
                    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()
                    
                    # Find data table
                    table_match = re.search(r'<table class="datatable center">(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
                    
                    if table_match:
                        table_content = table_match.group(1)
                        
                        # Extract rows
                        victim_rows = re.findall(r'<tr class=[\'"]trow[\'"]>(.*?)</tr>', table_content, re.DOTALL | re.IGNORECASE)
                        
                        print(f"\nFound {len(victim_rows)} victim rows in the table")
                        
                        # Process each row
                        for row in victim_rows:
                            # Extract cells
                            cells = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                            
                            if len(cells) >= 5:
                                # Extract fields from cells
                                company_name = re.sub(r'<.*?>', '', cells[0]).strip()
                                leak_percentage = re.sub(r'<.*?>', '', cells[1]).strip()
                                tags = re.sub(r'<.*?>', '', cells[2]).strip()
                                data_size = re.sub(r'<.*?>', '', cells[3]).strip()
                                last_updated = re.sub(r'<.*?>', '', cells[4]).strip()
                                
                                # Extract link
                                link_match = re.search(r'href="([^"]+)"', cells[5] if len(cells) > 5 else "", re.IGNORECASE)
                                link = link_match.group(1) if link_match else ""
                                
                                company_name = re.sub(r'<[^>]*>', '', company_name).strip()
                                
                                if company_name:  # Only add if we have a company name
                                    victims.append({
                                        "name": company_name,
                                        "date": last_updated,
                                        "group": "omegalock",
                                        "sector": tags,
                                        "leak_percentage": leak_percentage,
                                        "data_size": data_size,
                                        "link": link,
                                        "source_url": url
                                    })
                    else:
                        print("\nData table not found in HTML!")
                        
                        # Try fallback extraction
                        company_patterns = re.findall(
                            r'<td>([\w\s\.\,\&\;\-]+(?:Company|LLC|Inc|Ltd|GmbH|Corp|SA|AG|BV)?)</td>',
                            html_content,
                            re.IGNORECASE
                        )
                        
                        if company_patterns:
                            print(f"\nFallback extraction found {len(company_patterns)} potential company names")
                            for company in company_patterns:
                                company_name = company.strip()
                                if company_name and len(company_name) > 5:
                                    victims.append({
                                        "name": company_name,
                                        "date": datetime.now().strftime("%Y-%m-%d"),
                                        "group": "omegalock"
                                    })
                
                except Exception as e:
                    print(f"\nError parsing HTML: {str(e)}")
                
                return {
                    "title": title,
                    "victims": victims,
                    "url": url,
                    "is_using_tor": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Run the parser test
            print("\nRunning parser test...")
            result = parse_omegalock_test(html_content, "http://omegalock5zxwbhswbisc42o2q2i54vdulyvtqqbudqousisjgc7j7yd.onion/")
            
            # Display results
            print("\n" + "=" * 70)
            print(f"Title: {result['title']}")
            print(f"Found {len(result['victims'])} victims")
            print("=" * 70)
            
            # Show victims
            for i, victim in enumerate(result['victims']):
                print(f"\nVictim #{i+1}:")
                print(f"  Name: {victim.get('name', 'Unknown')}")
                print(f"  Date: {victim.get('date', 'Unknown')}")
                
                # Show sector if available
                if 'sector' in victim:
                    # Truncate sector if too long
                    sector = victim['sector']
                    if len(sector) > 60:
                        sector = sector[:57] + "..."
                    print(f"  Sector: {sector}")
                
                # Show leak percentage if available
                if 'leak_percentage' in victim:
                    print(f"  Leak: {victim['leak_percentage']}")
                
                # Show data size if available
                if 'data_size' in victim:
                    print(f"  Data Size: {victim['data_size']}")
                
                # Show link if available
                if 'link' in victim and victim['link']:
                    print(f"  Link: {victim['link']}")
            
            print("\n" + "=" * 70)
            print("Parser test completed")
            
            # Test how this would be processed by the collector
            print("\nTesting collector processing...")
            
            try:
                # Import the collector
                from collectors.omegalock import OmegalockCollector
                
                # Create a collector instance
                collector = OmegalockCollector()
                
                # Process the victims
                processed = collector._process_victims(result['victims'])
                
                # Display results
                print(f"\nProcessed {len(processed)} victims into claim format")
                
                if processed:
                    print("\nSample processed claim:")
                    print(f"  Collector: {processed[0]['collector']}")
                    print(f"  Threat actor: {processed[0]['threat_actor']}")
                    print(f"  Name: {processed[0]['name_network_identifier']}")
                    
                    if processed[0]['sector']:
                        sector = processed[0]['sector']
                        if len(sector) > 60:
                            sector = sector[:57] + "..."
                        print(f"  Sector: {sector}")
                    else:
                        print("  Sector: None")
                        
                    print(f"  Comment: {processed[0]['comment']}")
                    print(f"  Claim URL: {processed[0]['claim_url']}")
                    print(f"  Timestamp: {processed[0]['timestamp']}")
                    
                    # Test how this would look in database schema
                    print("\nThis maps to database schema as:")
                    print("  Threat Actor: omegalock")
                    print(f"  IP Network Identifier: {processed[0]['ip_network_identifier'] or 'None'}")
                    print(f"  Domain Network Identifier: {processed[0]['domain_network_identifier'] or 'None'}")
                    print(f"  Name Network Identifier: {processed[0]['name_network_identifier']}")
                    print(f"  Sector: {processed[0]['sector'] or 'None'}")
                    print(f"  Comment: {processed[0]['comment'] or 'None'}")
                    print(f"  Claim URL: {processed[0]['claim_url']}")
                    print(f"  Timestamp: {processed[0]['timestamp']}")
                
            except Exception as e:
                print(f"\nError testing collector: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error in test_omegalock_parser: {str(e)}", exc_info=True)
            print(f"\nError: {str(e)}")
        
        input("\nPress Enter to return to the test menu...")
    
    def test_collector_processing(self):
        """Test the OmegalockCollector processes parser output correctly"""
        from collectors.omegalock import OmegalockCollector
        
        # Create a collector instance
        collector = OmegalockCollector()
        
        # Sample parser output (victims)
        victims = [
            {
                "name": "Test Company Inc",
                "date": "2024-03-15",
                "group": "omegalock",
                "sector": "Software, Technology",
                "leak_percentage": "100%",
                "data_size": "500 GB",
                "link": "/post/6.html"
            }
        ]
        
        # Process the victims
        processed = collector._process_victims(victims)
        
        # Verify the processed data
        self.assertEqual(len(processed), 1)
        self.assertEqual(processed[0]["name_network_identifier"], "Test Company Inc")
        self.assertEqual(processed[0]["sector"], "Software, Technology")
        self.assertEqual(processed[0]["threat_actor"], "omegalock")
        
        # Verify the comment formatting
        self.assertIn("Leak: 100%", processed[0]["comment"])
        self.assertIn("Size: 500 GB", processed[0]["comment"])