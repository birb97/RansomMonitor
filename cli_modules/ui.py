# cli_modules/ui.py
"""
UI utility functions for the CLI interface.
"""

import os

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title, char='='):
    """Print a formatted header with title"""
    print(f"\n{char * 3} {title} {char * 3}\n")

def menu(title, options):
    """
    Display a menu and get user choice
    
    Args:
        title: Menu title
        options: List of (option_number, option_text) tuples
        
    Returns:
        Selected option number as string, or None if invalid
    """
    clear_screen()
    print_header(title)
    
    for option_num, option_text in options:
        print(f"{option_num}. {option_text}")
    
    choice = input("\nEnter your choice: ")
    return choice if any(choice == opt_num for opt_num, _ in options) else None