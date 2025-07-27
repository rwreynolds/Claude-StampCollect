# main.py
from enhanced_gui import EnhancedStampGUI

def main():
    """Main entry point for the Enhanced Stamp Collection Manager"""
    try:
        app = EnhancedStampGUI()
        app.run()
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Make sure you have FreeSimpleGUI installed: pip install FreeSimpleGUI")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check your installation and try again.")

if __name__ == "__main__":
    main()