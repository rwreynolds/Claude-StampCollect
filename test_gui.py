# test_gui.py
import unittest
from unittest.mock import patch, MagicMock, call
import tempfile
import os
from decimal import Decimal

# Mock FreeSimpleGUI before importing the GUI module
import sys
from unittest.mock import MagicMock

# Create a comprehensive mock for FreeSimpleGUI
mock_sg = MagicMock()
mock_sg.theme = MagicMock()
mock_sg.Window = MagicMock()
mock_sg.Text = MagicMock()
mock_sg.Input = MagicMock()
mock_sg.Button = MagicMock()
mock_sg.Table = MagicMock()
mock_sg.Combo = MagicMock()
mock_sg.Checkbox = MagicMock()
mock_sg.Multiline = MagicMock()
mock_sg.FileBrowse = MagicMock()
mock_sg.Frame = MagicMock()
mock_sg.Column = MagicMock()
mock_sg.VSeparator = MagicMock()
mock_sg.TabGroup = MagicMock()
mock_sg.Tab = MagicMock()
mock_sg.Menu = MagicMock()
mock_sg.popup = MagicMock()
mock_sg.popup_error = MagicMock()
mock_sg.popup_yes_no = MagicMock(return_value='Yes')
mock_sg.TABLE_SELECT_MODE_BROWSE = 'browse'

# Add the mock to sys.modules
sys.modules['FreeSimpleGUI'] = mock_sg

# Now we can import the GUI module
from enhanced_gui import EnhancedStampGUI
from enhanced_stamp import Stamp
from database_manager import DatabaseManager


class TestEnhancedStampGUICore(unittest.TestCase):
    """Test core functionality of the Enhanced Stamp GUI"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create all mock elements FIRST
        self.mock_elements = {}
        self._create_all_mock_elements()
        
        # Mock the window and its methods
        self.mock_window = MagicMock()
        self.mock_window.read = MagicMock(return_value=(None, {}))
        self.mock_window.close = MagicMock()
        
        # THIS IS CRITICAL: Make sure find_element returns our mock elements
        def mock_find_element(key):
            element = self.mock_elements.get(key)
            print(f"DEBUG: find_element('{key}') returning: {element}")  # Debug output
            return element
        
        self.mock_window.find_element = mock_find_element
        mock_sg.Window.return_value = self.mock_window
        
        # Patch DatabaseManager to use our temp database
        with patch('enhanced_gui.DatabaseManager') as mock_db_class:
            mock_db_instance = MagicMock()
            mock_db_class.return_value = mock_db_instance
            mock_db_instance.load_collection.return_value = MagicMock()
            mock_db_instance.load_collection.return_value.list_stamps.return_value = []
            mock_db_instance.get_statistics.return_value = {
                'total_stamps': 0, 'used_stamps': 0, 'mint_stamps': 0,
                'countries': 0, 'total_catalog_value': Decimal('0.00'),
                'average_value': Decimal('0.00'), 'want_list_items': 0,
                'for_sale_items': 0
            }
            
            self.gui = EnhancedStampGUI()
            self.gui.db_manager = mock_db_instance
            
            # IMPORTANT: Override the GUI's window with our mock AFTER initialization
            self.gui.window = self.mock_window
    
    def _create_all_mock_elements(self):
        """Create all possible mock elements that might be accessed"""
        all_fields = [
            # Basic form fields
            "scott_number", "description", "country", "year", "denomination",
            "color", "perforation", "location", "source", "notes", "image_path",
            # Numeric fields
            "qty_used", "qty_mint", 
            # Decimal fields
            "catalog_value_used", "catalog_value_mint", "purchase_price", "current_market_value",
            # Date fields
            "date_acquired",
            # Dropdown fields
            "condition_grade", "gum_condition",
            # Checkbox fields
            "used", "plate_block", "first_day_cover", "want_list", "for_sale",
            # Search fields
            "search_desc", "search_scott", "search_country", "search_year_from", "search_year_to",
            "search_used", "search_want",
            # Table
            "stamp_table",
            # Tab group
            "tab_group", "stats_display"
        ]
        
        for field in all_fields:
            mock_element = MagicMock()
            mock_element.get = MagicMock(return_value='')
            mock_element.update = MagicMock()
            self.mock_elements[field] = mock_element
            print(f"DEBUG: Created mock element for '{field}': {mock_element}")  # Debug output
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
    
    def test_mock_setup_verification(self):
        """Test that our mock setup is working correctly"""
        # This test verifies that find_element returns our mock elements
        element = self.gui.window.find_element('scott_number')
        self.assertIsNotNone(element)
        self.assertEqual(element, self.mock_elements['scott_number'])
        
        # Test that the element has the expected methods
        self.assertTrue(hasattr(element, 'get'))
        self.assertTrue(hasattr(element, 'update'))
    
    def test_gui_initialization(self):
        """Test GUI initialization"""
        self.assertIsNotNone(self.gui)
        self.assertIsNotNone(self.gui.db_manager)
        self.assertIsNotNone(self.gui.collection)
        self.assertIsNone(self.gui.current_stamp_id)
        self.assertEqual(self.gui.search_results, [])
    
    def test_clear_form_functionality(self):
        """Test clearing form fields"""
        print("DEBUG: Starting clear_form test")
        
        # Reset all mock calls before the test
        for element in self.mock_elements.values():
            element.update.reset_mock()
        
        # Call clear form
        self.gui._clear_form()
        
        # Define field groups as they are in the actual method
        basic_fields = [
            "scott_number", "description", "country", "year", "denomination",
            "color", "perforation", "location", "source", "notes", "image_path"
        ]
        numeric_fields = ["qty_used", "qty_mint"]
        decimal_fields = ["catalog_value_used", "catalog_value_mint", "purchase_price", "current_market_value"]
        date_fields = ["date_acquired"]
        dropdown_fields = ["condition_grade", "gum_condition"]
        checkbox_names = ["used", "plate_block", "first_day_cover", "want_list", "for_sale"]
        
        print(f"DEBUG: Checking basic fields: {basic_fields}")
        
        # Verify that update was called on basic text fields with empty strings
        for field in basic_fields:
            element = self.mock_elements[field]
            print(f"DEBUG: Checking {field}, update called: {element.update.called}, calls: {element.update.call_args_list}")
            self.mock_elements[field].update.assert_called_with(value='')
        
        # Verify numeric fields get '0'
        for field in numeric_fields:
            self.mock_elements[field].update.assert_called_with(value='0')
        
        # Verify decimal fields get '0.00'  
        for field in decimal_fields:
            self.mock_elements[field].update.assert_called_with(value='0.00')
        
        # Verify date field gets empty string
        for field in date_fields:
            self.mock_elements[field].update.assert_called_with(value='')
        
        # Verify dropdowns were reset to 'Unknown'
        for field in dropdown_fields:
            self.mock_elements[field].update.assert_called_with(value='Unknown')
        
        # Verify checkboxes were cleared (set to False)
        for checkbox in checkbox_names:
            self.mock_elements[checkbox].update.assert_called_with(value=False)
        
        # Verify current_stamp_id was cleared
        self.assertIsNone(self.gui.current_stamp_id)
    
    def test_validate_required_fields_success(self):
        """Test successful validation of required fields"""
        # Set up mock elements with valid values
        self.mock_elements["scott_number"].get.return_value = "US001"
        self.mock_elements["description"].get.return_value = "Test Stamp"
        
        print("DEBUG: Testing required fields validation with valid data")
        result = self.gui._validate_required_fields()
        print(f"DEBUG: Validation result: {result}")
        self.assertTrue(result)
    
    def test_validate_required_fields_failure(self):
        """Test validation failure with empty required fields"""
        # Set up mock elements with invalid values (empty scott_number)
        self.mock_elements["scott_number"].get.return_value = ""
        self.mock_elements["description"].get.return_value = "Test Stamp"
        
        with patch('enhanced_gui.sg.popup_error') as mock_popup:
            print("DEBUG: Testing required fields validation with invalid data")
            result = self.gui._validate_required_fields()
            print(f"DEBUG: Validation result: {result}")
            self.assertFalse(result)
            mock_popup.assert_called_once()

    def test_validate_numeric_fields_success(self):
        """Test successful validation of numeric fields"""
        numeric_fields = ["qty_used", "qty_mint", "catalog_value_used", 
                         "catalog_value_mint", "purchase_price", "current_market_value"]
        
        # Set all numeric fields to valid values
        for field in numeric_fields:
            self.mock_elements[field].get.return_value = "10.50"
        
        result = self.gui._validate_numeric_fields()
        self.assertTrue(result)
    
    def test_validate_numeric_fields_failure(self):
        """Test validation failure with invalid numeric values"""
        numeric_fields = ["qty_used", "qty_mint", "catalog_value_used", 
                         "catalog_value_mint", "purchase_price", "current_market_value"]
        
        # Set first field to invalid value, others to valid
        self.mock_elements[numeric_fields[0]].get.return_value = "invalid_number"
        for field in numeric_fields[1:]:
            self.mock_elements[field].get.return_value = "10.50"
        
        with patch('enhanced_gui.sg.popup_error') as mock_popup:
            result = self.gui._validate_numeric_fields()
            self.assertFalse(result)
            mock_popup.assert_called_once()
    
    def test_validate_date_success(self):
        """Test successful date validation"""
        self.mock_elements["date_acquired"].get.return_value = "2023-01-15"
        
        result = self.gui._validate_date()
        self.assertTrue(result)
    
    def test_validate_date_failure(self):
        """Test date validation failure"""
        self.mock_elements["date_acquired"].get.return_value = "invalid-date"
        
        with patch('enhanced_gui.sg.popup_error') as mock_popup:
            result = self.gui._validate_date()
            self.assertFalse(result)
            mock_popup.assert_called_once()
    
    def test_create_stamp_from_values(self):
        """Test creating stamp from form values"""
        values = {
            'scott_number': 'US001',
            'description': 'Test Stamp',
            'country': 'USA',
            'year': '1990',
            'denomination': '25c',
            'color': 'Red',
            'condition_grade': 'Fine',
            'gum_condition': 'Mint NH',
            'perforation': '11.5',
            'used': False,
            'plate_block': True,
            'first_day_cover': False,
            'location': 'Album 1',
            'notes': 'Test notes',
            'qty_mint': '1',
            'qty_used': '0',
            'catalog_value_mint': '10.00',
            'catalog_value_used': '5.00',
            'purchase_price': '8.00',
            'current_market_value': '12.00',
            'want_list': False,
            'for_sale': True,
            'date_acquired': '2023-01-15',
            'source': 'Test source',
            'image_path': '/path/to/image.jpg'
        }
        
        stamp = self.gui._create_stamp_from_values(values)
        
        self.assertEqual(stamp.scott_number, 'US001')
        self.assertEqual(stamp.description, 'Test Stamp')
        self.assertEqual(stamp.country, 'USA')
        self.assertEqual(stamp.year, 1990)
        self.assertTrue(stamp.plate_block)
        self.assertEqual(stamp.catalog_value_mint, Decimal('10.00'))
    
    def test_load_stamp_to_form(self):
        """Test loading stamp data into form"""
        # Create test stamp
        test_stamp = Stamp(
            scott_number="US001",
            description="Test Stamp",
            country="USA",
            year=1990,
            used=False,
            catalog_value_mint=Decimal('10.00'),
            qty_mint=1
        )
        
        # Reset all mock calls before the test
        for element in self.mock_elements.values():
            element.update.reset_mock()
        
        print("DEBUG: Starting load_stamp_to_form test")
        
        # Load stamp to form
        self.gui._load_stamp_to_form(test_stamp)
        
        print("DEBUG: Checking update calls after load_stamp_to_form")
        
        # Verify that update was called with correct values
        self.mock_elements["scott_number"].update.assert_called_with(value="US001")
        self.mock_elements["description"].update.assert_called_with(value="Test Stamp")
        self.mock_elements["country"].update.assert_called_with(value="USA")
        self.mock_elements["year"].update.assert_called_with(value="1990")
        self.mock_elements["used"].update.assert_called_with(value=False)


class TestStampGUISearch(unittest.TestCase):
    """Test search functionality in the GUI"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create all mock elements FIRST
        self.mock_elements = {}
        self._create_all_mock_elements()
        
        # Create and store mock window
        self.mock_window = MagicMock()
        self.mock_window.read = MagicMock(return_value=(None, {}))
        self.mock_window.close = MagicMock()
        
        def mock_find_element(key):
            return self.mock_elements.get(key)
        
        self.mock_window.find_element = mock_find_element
        mock_sg.Window.return_value = self.mock_window
        
        with patch('enhanced_gui.DatabaseManager') as mock_db_class:
            mock_db_instance = MagicMock()
            mock_db_class.return_value = mock_db_instance
            mock_db_instance.load_collection.return_value = MagicMock()
            mock_db_instance.load_collection.return_value.list_stamps.return_value = []
            mock_db_instance.get_statistics.return_value = {
                'total_stamps': 0, 'used_stamps': 0, 'mint_stamps': 0,
                'countries': 0, 'total_catalog_value': Decimal('0.00'),
                'average_value': Decimal('0.00'), 'want_list_items': 0,
                'for_sale_items': 0
            }
            
            self.gui = EnhancedStampGUI()
            self.gui.db_manager = mock_db_instance
            
            # IMPORTANT: Override the GUI's window with our mock AFTER initialization
            self.gui.window = self.mock_window
    
    def _create_all_mock_elements(self):
        """Create all possible mock elements that might be accessed"""
        all_fields = [
            # Basic form fields
            "scott_number", "description", "country", "year", "denomination",
            "color", "perforation", "location", "source", "notes", "image_path",
            # Numeric fields
            "qty_used", "qty_mint", 
            # Decimal fields
            "catalog_value_used", "catalog_value_mint", "purchase_price", "current_market_value",
            # Date fields
            "date_acquired",
            # Dropdown fields
            "condition_grade", "gum_condition",
            # Checkbox fields
            "used", "plate_block", "first_day_cover", "want_list", "for_sale",
            # Search fields
            "search_desc", "search_scott", "search_country", "search_year_from", "search_year_to",
            "search_used", "search_want",
            # Table
            "stamp_table",
            # Tab group
            "tab_group", "stats_display"
        ]
        
        for field in all_fields:
            mock_element = MagicMock()
            mock_element.get = MagicMock(return_value='')
            mock_element.update = MagicMock()
            self.mock_elements[field] = mock_element
    
    def test_perform_search(self):
        """Test performing a search operation"""
        # Mock search results
        test_stamp = Stamp(scott_number="US001", description="Test Stamp")
        search_results = [(1, test_stamp)]
        
        # Create new mock for search_stamps method
        mock_search = MagicMock(return_value=search_results)
        self.gui.db_manager.search_stamps = mock_search
        
        # Mock form values
        values = {
            'search_desc': 'Test',
            'search_scott': 'US001',
            'search_country': 'USA',
            'search_year_from': '1990',
            'search_year_to': '2000',
            'search_used': False,
            'search_want': False
        }
        
        # Perform search
        self.gui._perform_search(values)
        
        # Verify search was called with correct criteria
        expected_criteria = {
            'description': 'Test',
            'scott_number': 'US001',
            'country': 'USA',
            'year_from': '1990',
            'year_to': '2000',
            'used_only': False,
            'want_list': False
        }
        
        self.gui.db_manager.search_stamps.assert_called_once_with(expected_criteria)
        
        # Verify search results were set
        self.assertEqual(self.gui.search_results, search_results)
    
    def test_clear_search(self):
        """Test clearing search results"""
        search_fields = ['search_desc', 'search_scott', 'search_country', 
                        'search_year_from', 'search_year_to']
        search_checks = ['search_used', 'search_want']
        
        # Reset all mock calls before the test
        for element in self.mock_elements.values():
            element.update.reset_mock()
        
        # Set up the _refresh_stamp_list method to avoid errors
        with patch.object(self.gui, '_refresh_stamp_list') as mock_refresh:
            print("DEBUG: Starting clear_search test")
            
            # Clear search
            self.gui._clear_search()
            
            print("DEBUG: Checking search field updates")
            
            # Verify search fields were cleared
            for field in search_fields:
                print(f"DEBUG: Checking {field}, update called: {self.mock_elements[field].update.called}")
                self.mock_elements[field].update.assert_called_with(value='')
            
            for check in search_checks:
                self.mock_elements[check].update.assert_called_with(value=False)
            
            # Verify refresh was called
            mock_refresh.assert_called_once()


class TestStampGUICRUD(unittest.TestCase):
    """Test CRUD operations in the GUI"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create all mock elements FIRST
        self.mock_elements = {}
        self._create_all_mock_elements()
        
        # Create and store mock window
        self.mock_window = MagicMock()
        self.mock_window.read = MagicMock(return_value=(None, {}))
        self.mock_window.close = MagicMock()
        
        def mock_find_element(key):
            return self.mock_elements.get(key)
        
        self.mock_window.find_element = mock_find_element
        mock_sg.Window.return_value = self.mock_window
        
        with patch('enhanced_gui.DatabaseManager') as mock_db_class:
            mock_db_instance = MagicMock()
            mock_db_class.return_value = mock_db_instance
            mock_db_instance.load_collection.return_value = MagicMock()
            mock_db_instance.load_collection.return_value.list_stamps.return_value = []
            mock_db_instance.get_statistics.return_value = {
                'total_stamps': 0, 'used_stamps': 0, 'mint_stamps': 0,
                'countries': 0, 'total_catalog_value': Decimal('0.00'),
                'average_value': Decimal('0.00'), 'want_list_items': 0,
                'for_sale_items': 0
            }
            
            self.gui = EnhancedStampGUI()
            self.gui.db_manager = mock_db_instance
            
            # IMPORTANT: Override the GUI's window with our mock AFTER initialization
            self.gui.window = self.mock_window
    
    def _create_all_mock_elements(self):
        """Create all possible mock elements that might be accessed"""
        all_fields = [
            # Basic form fields
            "scott_number", "description", "country", "year", "denomination",
            "color", "perforation", "location", "source", "notes", "image_path",
            # Numeric fields
            "qty_used", "qty_mint", 
            # Decimal fields
            "catalog_value_used", "catalog_value_mint", "purchase_price", "current_market_value",
            # Date fields
            "date_acquired",
            # Dropdown fields
            "condition_grade", "gum_condition",
            # Checkbox fields
            "used", "plate_block", "first_day_cover", "want_list", "for_sale",
            # Search fields
            "search_desc", "search_scott", "search_country", "search_year_from", "search_year_to",
            "search_used", "search_want",
            # Table
            "stamp_table",
            # Tab group
            "tab_group", "stats_display"
        ]
        
        for field in all_fields:
            mock_element = MagicMock()
            mock_element.get = MagicMock(return_value='')
            mock_element.update = MagicMock()
            self.mock_elements[field] = mock_element
    
    def test_add_stamp_success(self):
        """Test successful stamp addition"""
        # Mock form values
        values = {
            'scott_number': 'US001',
            'description': 'Test Stamp',
            'country': 'USA',
            'year': '1990',
            'denomination': '25c',
            'color': 'Red',
            'condition_grade': 'Fine',
            'gum_condition': 'Mint NH',
            'perforation': '11.5',
            'used': False,
            'plate_block': False,
            'first_day_cover': False,
            'location': 'Album 1',
            'notes': 'Test notes',
            'qty_mint': '1',
            'qty_used': '0',
            'catalog_value_mint': '10.00',
            'catalog_value_used': '5.00',
            'purchase_price': '8.00',
            'current_market_value': '12.00',
            'want_list': False,
            'for_sale': False,
            'date_acquired': '2023-01-15',
            'source': 'Test source',
            'image_path': ''
        }
        
        # Create new mock for add_stamp method
        mock_add = MagicMock(return_value=1)
        self.gui.db_manager.add_stamp = mock_add
        
        # Mock the helper methods
        with patch.object(self.gui, '_clear_form') as mock_clear, \
             patch.object(self.gui, '_refresh_stamp_list') as mock_refresh, \
             patch.object(self.gui, '_update_statistics') as mock_stats, \
             patch('enhanced_gui.sg.popup') as mock_popup:
            
            self.gui._add_stamp(values)
            
            # Verify database method was called
            self.gui.db_manager.add_stamp.assert_called_once()
            
            # Verify helper methods were called
            mock_clear.assert_called_once()
            mock_refresh.assert_called_once()
            mock_stats.assert_called_once()
            
            # Verify success popup was shown
            mock_popup.assert_called_once_with("Stamp added successfully!")
    
    def test_update_stamp_success(self):
        """Test successful stamp update"""
        # Set current stamp ID
        self.gui.current_stamp_id = 1
        
        # Mock form values
        values = {
            'scott_number': 'US001_UPDATED',
            'description': 'Updated Test Stamp',
            'country': 'USA',
            'year': '1991',
            'denomination': '30c',
            'color': 'Blue',
            'condition_grade': 'Very Fine',
            'gum_condition': 'Hinged',
            'perforation': '12',
            'used': True,
            'plate_block': False,
            'first_day_cover': False,
            'location': 'Album 2',
            'notes': 'Updated notes',
            'qty_mint': '0',
            'qty_used': '1',
            'catalog_value_mint': '12.00',
            'catalog_value_used': '6.00',
            'purchase_price': '9.00',
            'current_market_value': '14.00',
            'want_list': True,
            'for_sale': False,
            'date_acquired': '2023-02-15',
            'source': 'Updated source',
            'image_path': ''
        }
        
        # Create mock for update_stamp method
        mock_update = MagicMock()
        self.gui.db_manager.update_stamp = mock_update
        
        with patch.object(self.gui, '_clear_form') as mock_clear, \
             patch.object(self.gui, '_refresh_stamp_list') as mock_refresh, \
             patch.object(self.gui, '_update_statistics') as mock_stats, \
             patch('enhanced_gui.sg.popup') as mock_popup:
            
            self.gui._update_stamp(values)
            
            # Verify database method was called with correct ID
            mock_update.assert_called_once()
            self.assertEqual(mock_update.call_args[0][0], 1)  # stamp_id
            
            # Verify helper methods were called
            mock_clear.assert_called_once()
            mock_refresh.assert_called_once() 
            mock_stats.assert_called_once()
            
            # Verify success popup was shown
            mock_popup.assert_called_once_with("Stamp updated successfully!")
    
    def test_update_stamp_no_selection(self):
        """Test update stamp with no stamp selected"""
        # Create mock for update_stamp method
        mock_update = MagicMock()
        self.gui.db_manager.update_stamp = mock_update
        
        # No current stamp ID
        self.gui.current_stamp_id = None
        
        with patch('enhanced_gui.sg.popup_error') as mock_popup:
            self.gui._update_stamp({})
            
            # Verify error popup was shown
            mock_popup.assert_called_once_with("No stamp selected!")
            
            # Verify database method was not called
            mock_update.assert_not_called()
    
    def test_delete_stamp_success(self):
        """Test successful stamp deletion"""
        # Set current stamp ID
        self.gui.current_stamp_id = 1
        
        # Create mock for delete_stamp method
        mock_delete = MagicMock()
        self.gui.db_manager.delete_stamp = mock_delete
        
        with patch('enhanced_gui.sg.popup_yes_no', return_value='Yes') as mock_confirm, \
             patch.object(self.gui, '_clear_form') as mock_clear, \
             patch.object(self.gui, '_refresh_stamp_list') as mock_refresh, \
             patch.object(self.gui, '_update_statistics') as mock_stats, \
             patch('enhanced_gui.sg.popup') as mock_popup:
            
            self.gui._delete_stamp()
            
            # Verify confirmation was asked
            mock_confirm.assert_called_once_with("Are you sure you want to delete this stamp?")
            
            # Verify database method was called with correct ID
            mock_delete.assert_called_once_with(1)
            
            # Verify helper methods were called
            mock_clear.assert_called_once()
            mock_refresh.assert_called_once()
            mock_stats.assert_called_once()
            
            # Verify success popup was shown
            mock_popup.assert_called_once_with("Stamp deleted successfully!")
    
    def test_delete_stamp_cancelled(self):
        """Test stamp deletion cancellation"""
        # Create mock for delete_stamp method
        mock_delete = MagicMock()
        self.gui.db_manager.delete_stamp = mock_delete
        
        # Set current stamp ID
        self.gui.current_stamp_id = 1
        
        with patch('enhanced_gui.sg.popup_yes_no', return_value='No') as mock_confirm:
            self.gui._delete_stamp()
            
            # Verify confirmation was asked
            mock_confirm.assert_called_once()
            
            # Verify database method was not called
            mock_delete.assert_not_called()


# Test configuration and runner
class TestConfiguration:
    """Test configuration and setup utilities"""
    
    @staticmethod
    def create_test_database():
        """Create a test database with sample data"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        db_manager = DatabaseManager(temp_db.name)
        
        # Add sample stamps
        sample_stamps = [
            Stamp("US001", "Washington 1c", "USA", 1932, 
                  catalog_value_mint=Decimal('5.00'), qty_mint=1),
            Stamp("US002", "Lincoln 3c", "USA", 1909, used=True,
                  catalog_value_used=Decimal('2.50'), qty_used=1),
            Stamp("CA001", "Maple Leaf", "Canada", 1935,
                  catalog_value_mint=Decimal('15.00'), qty_mint=1, want_list=True),
        ]
        
        for stamp in sample_stamps:
            db_manager.add_stamp(stamp)
        
        return temp_db.name, db_manager
    
    @staticmethod
    def cleanup_test_database(db_path):
        """Clean up test database"""
        try:
            os.unlink(db_path)
        except OSError:
            pass


if __name__ == '__main__':
    # Create test suite for GUI tests
    gui_test_classes = [
        TestEnhancedStampGUICore,
        TestStampGUISearch,
        TestStampGUICRUD
    ]
    
    loader = unittest.TestLoader()
    suites = [loader.loadTestsFromTestCase(test_class) for test_class in gui_test_classes]
    combined_suite = unittest.TestSuite(suites)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"GUI TESTS RUN: {result.testsRun}")
    print(f"FAILURES: {len(result.failures)}")
    print(f"ERRORS: {len(result.errors)}")
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"SUCCESS RATE: {success_rate:.1f}%")
    print(f"{'='*50}")