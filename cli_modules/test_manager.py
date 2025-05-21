# cli_modules/test_manager.py
"""
Test management for the ransomware intelligence system.
"""

import logging
import sys
import importlib
from .ui import clear_screen, print_header, menu

class TestManager:
    """Manages testing functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger("test_manager")
    
    def run_tests(self):
        """Run all tests"""
        clear_screen()
        print_header("RUNNING TESTS")
        
        print("Initializing test framework...")
        print("Starting test execution...\n")
        
        try:
            # Import the test framework dynamically to avoid issues
            test_framework = importlib.import_module('test_framework')
            run_tests = getattr(test_framework, 'run_tests')
            
            # Run all registered tests
            success = run_tests()
            
            if success:
                print("\n" + "-" * 70)
                print("TEST STATUS: PASSED - All tests completed successfully!")
                print("-" * 70)
            else:
                print("\n" + "-" * 70)
                print("TEST STATUS: FAILED - Some tests did not pass. See details above.")
                print("-" * 70 + "\n")
                print("Check test_results.log for complete information.")
        except Exception as e:
            self.logger.error(f"Error running tests: {str(e)}", exc_info=True)
            print("\n" + "-" * 70)
            print(f"TEST FRAMEWORK ERROR: {str(e)}")
            print("Check logs for detailed stack trace.")
            print("-" * 70)
        
        input("\nPress Enter to return to the test menu...")
    
    def run_specific_tests(self):
        """Run specific test classes"""
        clear_screen()
        print_header("RUN SPECIFIC TESTS")
        
        try:
            # Import required modules dynamically
            test_framework = importlib.import_module('test_framework')
            TestRunner = getattr(test_framework, 'TestRunner')
            test_registry = importlib.import_module('tests.test_registry')
            
            # Get all test cases
            test_cases = test_registry.get_all_test_cases()
            
            if not test_cases:
                print("No test cases found. Make sure test modules are properly set up.")
                input("\nPress Enter to continue...")
                return
                
            # Create menu options from test cases
            options = []
            for i, tc in enumerate(test_cases):
                # Create a more user-friendly description from the class name
                name = tc.__name__.replace('TestCase', '')
                # If available, get the docstring for better description
                desc = tc.__doc__.split('\n')[0] if tc.__doc__ else f"Tests for {name}"
                options.append((str(i+1), f"{name}: {desc}"))
            
            print(f"Found {len(test_cases)} test suites.")
            
            while True:
                choice = menu("Select test suite to run:", options + [("b", "Back to test menu")])
                
                if choice == "b" or choice is None:
                    break
                    
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(test_cases):
                        clear_screen()
                        test_class = test_cases[index]
                        # Extract test methods for info
                        test_methods = [m for m in dir(test_class) if m.startswith('test_')]
                        
                        print_header(f"RUNNING TEST SUITE: {test_class.__name__}")
                        print(f"Description: {test_class.__doc__.strip() if test_class.__doc__ else 'No description available'}")
                        print(f"Test methods to run: {len(test_methods)}")
                        print("-" * 70 + "\n")
                        
                        runner = TestRunner()
                        results = runner.run_test_case(test_class)
                        
                        # Print summary of results
                        passed = sum(1 for r in results if r.success)
                        total = len(results)
                        
                        print("\n" + "-" * 70)
                        if passed == total:
                            print(f"SUCCESS: All {total} tests in this suite passed!")
                        else:
                            print(f"RESULTS: {passed}/{total} tests passed, {total - passed} failed")
                        print("-" * 70)
                        
                        input("\nPress Enter to continue...")
                    else:
                        print("Invalid choice.")
                        input("Press Enter to continue...")
                except ValueError:
                    print("Invalid input.")
                    input("Press Enter to continue...")
        except Exception as e:
            self.logger.error(f"Error in run_specific_tests: {str(e)}", exc_info=True)
            print(f"Error: {str(e)}")
            input("\nPress Enter to continue...")
    
    def test_tor_collector(self):
        """Run tests specifically for the Tor collector"""
        clear_screen()
        print_header("TESTING TOR COLLECTOR")
        
        try:
            # Import required modules dynamically
            test_framework = importlib.import_module('test_framework')
            TestRunner = getattr(test_framework, 'TestRunner')
            test_registry = importlib.import_module('tests.test_registry')
            
            # Get the TorCollectorTestCase class
            test_cases = []
            for case in test_registry.get_all_test_cases():
                if case.__name__ == "TorCollectorTestCase":
                    test_cases.append(case)
                    break
            
            if not test_cases:
                print("TorCollectorTestCase not found. Make sure tests/test_tor_collector.py is properly set up.")
                input("\nPress Enter to continue...")
                return
            
            print("Tor Collector Test Suite")
            print("-" * 70)
            print("This suite tests connectivity and functionality of the Tor proxy system.")
            print("Tests will verify:\n")
            print("  • Health endpoint availability")
            print("  • Tor proxy connection")
            print("  • Data collection through Tor")
            print("  • Security of the Tor configuration")
            print("-" * 70 + "\n")
                
            # Run the tests
            print("Starting Tor collector tests...\n")
            runner = TestRunner()
            results = runner.run_test_cases(test_cases)
            
            # Wait for user to acknowledge results
            input("\nPress Enter to continue...")
        except Exception as e:
            self.logger.error(f"Error in test_tor_collector: {str(e)}", exc_info=True)
            print(f"Error: {str(e)}")
            input("\nPress Enter to continue...")
            
    def manage_tests(self):
        """Interactive CLI for test management"""
        while True:
            choice = menu("TEST MANAGEMENT", [
                ("1", "Run all tests"),
                ("2", "Run specific tests"),
                ("3", "Test Tor collector"),
                ("4", "Onion Curl - Fetch HTML content"),
                ("5", "Test Onion Parser"),
                ("6", "Back to main menu")
            ])
            
            if choice == "1":
                self.run_tests()
            elif choice == "2":
                self.run_specific_tests()
            elif choice == "3":
                self.test_tor_collector()
            elif choice == "4":
                self.onion_curl()
            elif choice == "5":
                # Ask which parser to test
                clear_screen()
                print_header("TEST ONION PARSER")
                print("\nSelect parser to test:")
                print("1. Omegalock")
                # Add more parser options here as they become available
                print("2. Back to test menu")
                
                parser_choice = input("\nEnter choice: ").strip()
                
                if parser_choice == "1":
                    self.test_onion_parser("omegalock")
                # Add more parser choices here
                elif parser_choice == "2":
                    continue
                else:
                    print("\nInvalid choice.")
                    input("\nPress Enter to continue...")
            elif choice == "6" or choice is None:
                break

    def onion_curl(self):
        """
        Fetch and display HTML content from an onion site.
        
        This tool allows examining the HTML structure of onion sites
        to help with parser development.
        """
        clear_screen()
        print_header("ONION CURL - FETCH HTML CONTENT")
        
        print("This tool fetches HTML content from .onion sites to help you build parsers.")
        print("It requires the Tor proxy to be running.\n")
        
        # Check if Tor is running
        print("Checking Tor proxy status...")
        try:
            # Import the Config class and onion_curl utility
            from config import Config
            from utils.onion_curl import fetch_onion_content
            
            config = Config()
            
            # Make a quick health check request to the collection agent
            import requests
            health_url = f"{config.get_droplet_endpoint()}/health"
            try:
                response = requests.get(health_url, timeout=5)
                status = response.json()
                tor_working = status.get("tor_working", False)
                
                if tor_working:
                    print("\n✓ Tor proxy is running and configured correctly.")
                else:
                    print("\n⚠ Tor proxy is running but may not be configured correctly.")
                    print("  You can still try to fetch content, but it might not work.")
            except requests.RequestException:
                print("\n⚠ Cannot connect to collection agent. Is it running?")
                print("  Make sure the collection agent is running with 'docker-compose up -d'")
                print("  in the 'droplet' directory.")
                input("\nPress Enter to return to the test menu...")
                return
            
            # Get the onion URL
            print("\nEnter the onion URL to fetch (or a sample URL to test):")
            print("Example: http://omegalock5zxwbhswbisc42o2q2i54vdulyvtqqbudqousisjgc7j7yd.onion/")
            
            url = input("\nURL: ").strip()
            if not url:
                print("URL cannot be empty.")
                input("\nPress Enter to return to the test menu...")
                return
            
            # Additional options
            save_to_file = input("\nSave HTML to file? (y/n): ").lower() == 'y'
            show_full_content = input("Display full HTML content in console? (y/n): ").lower() == 'y'
            
            print("\nFetching content...")
            html, metadata = fetch_onion_content(
                url=url,
                config=config,
                save_to_file=save_to_file,
                output_dir="debug_html"
            )
            
            if html:
                # Show summary
                print("\n" + "=" * 70)
                print(f"URL: {url}")
                if "metadata" in metadata:
                    print(f"Content Length: {metadata.get('metadata', {}).get('content_length', 'Unknown')} bytes")
                    
                    if save_to_file:
                        saved_to = metadata.get('metadata', {}).get('saved_to')
                        if saved_to:
                            print(f"Saved to: {saved_to}")
                
                # Show victims if any were parsed
                if "victims" in metadata and metadata["victims"]:
                    print("\nFound Victims:")
                    for i, victim in enumerate(metadata["victims"][:5], 1):  # Show up to 5
                        print(f"  {i}. {victim.get('name', 'Unknown')}")
                    
                    if len(metadata["victims"]) > 5:
                        print(f"  ... and {len(metadata['victims']) - 5} more")
                
                # Display the HTML content preview
                if show_full_content:
                    print("\n" + "=" * 70)
                    print("HTML CONTENT:")
                    print("=" * 70)
                    print(html)
                else:
                    print("\n" + "=" * 70)
                    print("HTML PREVIEW (first 500 chars):")
                    print("-" * 70)
                    preview = html[:500] + ("..." if len(html) > 500 else "")
                    print(preview)
                    
                    if save_to_file:
                        print("\nFull content has been saved to file.")
                    else:
                        print("\nUse 'Save to file' option to examine the full HTML content.")
            else:
                print("\n" + "=" * 70)
                print(f"ERROR: {metadata.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.logger.error(f"Error in onion_curl: {str(e)}", exc_info=True)
            print(f"\nError: {str(e)}")
        
        input("\nPress Enter to return to the test menu...")

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
            
            # Now that we have HTML, define the test parser
            def parse_omegalock_test(html_content, url=None):
                """Simplified test version of the parser"""
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
                                # Extract only essential data
                                company_name = re.sub(r'<.*?>', '', cells[0]).strip()
                                tags = re.sub(r'<.*?>', '', cells[2]).strip()
                                data_size = re.sub(r'<.*?>', '', cells[3]).strip()
                                last_updated = re.sub(r'<.*?>', '', cells[4]).strip()
                                
                                # Extract link
                                link_match = re.search(r'href="([^"]+)"', cells[5] if len(cells) > 5 else "", re.IGNORECASE)
                                link = link_match.group(1) if link_match else ""
                                
                                victims.append({
                                    "name": company_name,
                                    "date": last_updated,
                                    "sector": tags,
                                    "data_size": data_size,
                                    "link": link
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
                                        "date": datetime.now().strftime("%Y-%m-%d")
                                    })
                
                except Exception as e:
                    print(f"\nError parsing HTML: {str(e)}")
                
                return {
                    "title": title,
                    "victims": victims
                }
            
            # Run the parser test
            print("\nRunning parser test...")
            result = parse_omegalock_test(html_content)
            
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
                    print(f"  Sector: {processed[0]['sector']}")
                    print(f"  Comment: {processed[0]['comment']}")
                    print(f"  Claim URL: {processed[0]['claim_url']}")
                    print(f"  Timestamp: {processed[0]['timestamp']}")
                
            except Exception as e:
                print(f"\nError testing collector: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error in test_omegalock_parser: {str(e)}", exc_info=True)
            print(f"\nError: {str(e)}")
        
        input("\nPress Enter to return to the test menu...")

    def test_onion_parser(self, parser_type="omegalock"):
        """
        Generic test function for onion site parsers.
        
        This tool allows testing various onion site parsers against sample HTML
        to ensure they correctly extract victim data and map to our schema.
        
        Args:
            parser_type: The type of parser to test (default: "omegalock")
        """
        clear_screen()
        print_header(f"TEST {parser_type.upper()} PARSER")
        
        try:
            # Import necessary modules
            from config import Config
            import re
            from datetime import datetime
            
            # First check if we have sample HTML
            print(f"This tool tests the {parser_type} parser with sample HTML.")
            
            # Set up parser URLs based on type
            parser_urls = {
                "omegalock": "http://omegalock5zxwbhswbisc42o2q2i54vdulyvtqqbudqousisjgc7j7yd.onion/",
                # Add more parser types and their URLs here as needed
            }
            
            # Get URL for the selected parser type
            target_url = parser_urls.get(parser_type, f"http://{parser_type}.onion/")
            
            # Ask for HTML source
            print("\nSelect HTML source:")
            print("1. Use sample HTML from file")
            print("2. Use built-in sample HTML")
            print("3. Fetch live HTML from onion site")
            
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
                # Use built-in samples based on parser type
                if parser_type == "omegalock":
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
                # Add more parser types and their sample HTML here
                else:
                    print(f"\nNo built-in sample available for {parser_type}.")
                    print("Please use file input or live fetching.")
                    input("\nPress Enter to return to the test menu...")
                    return
                    
                print(f"\nUsing built-in sample HTML for {parser_type}.")
            
            elif source_choice == "3":
                # Fetch from onion site using onion_curl utility
                print(f"\nFetching HTML from {parser_type} site...")
                from utils.onion_curl import fetch_onion_content
                
                config = Config()
                html, metadata = fetch_onion_content(
                    url=target_url,
                    config=config,
                    save_to_file=False
                )
                
                if html:
                    html_content = html
                    print(f"\nFetched {len(html_content)} bytes from {parser_type} site.")
                else:
                    print(f"\nError fetching HTML: {metadata.get('error', 'Unknown error')}")
                    input("\nPress Enter to return to the test menu...")
                    return
            
            else:
                print("\nInvalid choice.")
                input("\nPress Enter to return to the test menu...")
                return
            
            # Get the appropriate parser function based on type
            if parser_type == "omegalock":
                # Import the parser function - for testing we'll define a local version 
                # that matches the real implementation
                def parser_func(html_content, url=None):
                    """Test implementation of Omegalock parser"""
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
            
            # Add more parser functions for other types here
            else:
                print(f"\nNo parser implementation available for {parser_type}.")
                input("\nPress Enter to return to the test menu...")
                return
            
            # Run the parser test
            print("\nRunning parser test...")
            result = parser_func(html_content, target_url)
            
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
                # Import the collector based on parser type
                if parser_type == "omegalock":
                    from collectors.omegalock import OmegalockCollector
                    collector = OmegalockCollector()
                # Add more collector imports for other parser types here
                else:
                    print(f"\nNo collector implementation for {parser_type}.")
                    input("\nPress Enter to return to the test menu...")
                    return
                
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
                    print("  Threat Actor: " + processed[0]['threat_actor'])
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
            self.logger.error(f"Error in test_onion_parser: {str(e)}", exc_info=True)
            print(f"\nError: {str(e)}")
        
        input("\nPress Enter to return to the test menu...")