# test_stamp_collection.py
import unittest
import sqlite3
import tempfile
import os
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the modules to test
from enhanced_stamp import Stamp, StampCollection
from database_manager import DatabaseManager


class TestStamp(unittest.TestCase):
    """Test cases for the Stamp class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.basic_stamp = Stamp(
            scott_number="US001",
            description="Test Stamp"
        )
        
        self.detailed_stamp = Stamp(
            scott_number="US002",
            description="Detailed Test Stamp",
            country="USA",
            year=1990,
            denomination="25c",
            color="Red",
            condition_grade="Very Fine",
            gum_condition="Mint NH",
            perforation="11.5",
            used=False,
            plate_block=True,
            first_day_cover=False,
            location="Album 1",
            notes="Beautiful specimen",
            qty_mint=2,
            qty_used=0,
            catalog_value_mint=Decimal('15.50'),
            catalog_value_used=Decimal('8.25'),
            purchase_price=Decimal('12.00'),
            current_market_value=Decimal('16.00'),
            want_list=False,
            for_sale=True,
            date_acquired="2023-01-15",
            source="Local dealer",
            image_path="/images/stamp002.jpg"
        )
    
    def test_stamp_creation_minimal(self):
        """Test creating a stamp with minimal required fields"""
        self.assertEqual(self.basic_stamp.scott_number, "US001")
        self.assertEqual(self.basic_stamp.description, "Test Stamp")
        self.assertIsNone(self.basic_stamp.country)
        self.assertEqual(self.basic_stamp.condition_grade, "Unknown")
        self.assertEqual(self.basic_stamp.qty_mint, 0)
        self.assertEqual(self.basic_stamp.catalog_value_mint, Decimal('0.00'))
        self.assertFalse(self.basic_stamp.used)
    
    def test_stamp_creation_detailed(self):
        """Test creating a stamp with all fields populated"""
        self.assertEqual(self.detailed_stamp.scott_number, "US002")
        self.assertEqual(self.detailed_stamp.country, "USA")
        self.assertEqual(self.detailed_stamp.year, 1990)
        self.assertEqual(self.detailed_stamp.condition_grade, "Very Fine")
        self.assertTrue(self.detailed_stamp.plate_block)
        self.assertEqual(self.detailed_stamp.qty_mint, 2)
        self.assertEqual(self.detailed_stamp.catalog_value_mint, Decimal('15.50'))
    
    def test_calculate_total_value_mint(self):
        """Test total value calculation for mint stamps"""
        self.detailed_stamp.used = False
        self.detailed_stamp.qty_mint = 3
        self.detailed_stamp.catalog_value_mint = Decimal('10.00')
        
        expected_value = Decimal('30.00')
        self.assertEqual(self.detailed_stamp.calculate_total_value(), expected_value)
    
    def test_calculate_total_value_used(self):
        """Test total value calculation for used stamps"""
        self.detailed_stamp.used = True
        self.detailed_stamp.qty_used = 2
        self.detailed_stamp.catalog_value_used = Decimal('5.50')
        
        expected_value = Decimal('11.00')
        self.assertEqual(self.detailed_stamp.calculate_total_value(), expected_value)
    
    def test_calculate_total_value_zero_quantity(self):
        """Test total value calculation with zero quantities"""
        self.detailed_stamp.qty_mint = 0
        self.detailed_stamp.qty_used = 0
        
        self.assertEqual(self.detailed_stamp.calculate_total_value(), Decimal('0.00'))
    
    def test_calculate_total_value_none_quantity(self):
        """Test total value calculation with None quantities"""
        stamp = Stamp(
            scott_number="TEST",
            description="Test",
            qty_mint=None,
            qty_used=None
        )
        
        # Should handle None values gracefully
        self.assertEqual(stamp.calculate_total_value(), Decimal('0.00'))


class TestStampCollection(unittest.TestCase):
    """Test cases for the StampCollection class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.collection = StampCollection()
        self.stamp1 = Stamp(scott_number="US001", description="First Stamp")
        self.stamp2 = Stamp(scott_number="US002", description="Second Stamp")
    
    def test_empty_collection(self):
        """Test empty collection initialization"""
        self.assertEqual(len(self.collection.stamps), 0)
        self.assertEqual(len(self.collection.list_stamps()), 0)
    
    def test_add_single_stamp(self):
        """Test adding a single stamp to collection"""
        self.collection.add_stamp(self.stamp1)
        
        self.assertEqual(len(self.collection.stamps), 1)
        self.assertEqual(self.collection.stamps[0], self.stamp1)
    
    def test_add_multiple_stamps(self):
        """Test adding multiple stamps to collection"""
        self.collection.add_stamp(self.stamp1)
        self.collection.add_stamp(self.stamp2)
        
        self.assertEqual(len(self.collection.stamps), 2)
        self.assertIn(self.stamp1, self.collection.stamps)
        self.assertIn(self.stamp2, self.collection.stamps)
    
    def test_list_stamps(self):
        """Test listing stamps from collection"""
        self.collection.add_stamp(self.stamp1)
        self.collection.add_stamp(self.stamp2)
        
        stamp_list = self.collection.list_stamps()
        self.assertEqual(len(stamp_list), 2)
        self.assertEqual(stamp_list, [self.stamp1, self.stamp2])


class TestDatabaseManager(unittest.TestCase):
    """Test cases for the DatabaseManager class"""
    
    def setUp(self):
        """Set up test fixtures with temporary database"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize database manager with temp database
        self.db_manager = DatabaseManager(self.db_path)
        
        # Create test stamps
        self.test_stamp1 = Stamp(
            scott_number="TEST001",
            description="Test Stamp 1",
            country="USA",
            year=1990,
            catalog_value_mint=Decimal('10.00'),
            qty_mint=1
        )
        
        self.test_stamp2 = Stamp(
            scott_number="TEST002",
            description="Test Stamp 2",
            country="Canada",
            year=1995,
            used=True,
            catalog_value_used=Decimal('5.00'),
            qty_used=2,
            want_list=True
        )
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
    
    def test_database_creation(self):
        """Test that database and tables are created properly"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check that stamps table exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stamps'")
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "stamps")
    
    def test_add_stamp(self):
        """Test adding a stamp to the database"""
        stamp_id = self.db_manager.add_stamp(self.test_stamp1)
        
        self.assertIsInstance(stamp_id, int)
        self.assertGreater(stamp_id, 0)
        
        # Verify stamp was added
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stamps WHERE id=?", (stamp_id,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "TEST001")  # scott_number
        self.assertEqual(result[2], "Test Stamp 1")  # description
    
    def test_load_collection(self):
        """Test loading stamps from database into collection"""
        # Add stamps to database
        self.db_manager.add_stamp(self.test_stamp1)
        self.db_manager.add_stamp(self.test_stamp2)
        
        # Load collection
        collection = self.db_manager.load_collection()
        
        self.assertEqual(len(collection.stamps), 2)
        
        # Check that stamps were loaded correctly
        loaded_stamps = collection.list_stamps()
        scott_numbers = [stamp.scott_number for stamp in loaded_stamps]
        self.assertIn("TEST001", scott_numbers)
        self.assertIn("TEST002", scott_numbers)
    
    def test_update_stamp(self):
        """Test updating an existing stamp"""
        # Add stamp first
        stamp_id = self.db_manager.add_stamp(self.test_stamp1)
        
        # Modify stamp
        updated_stamp = Stamp(
            scott_number="TEST001_UPDATED",
            description="Updated Test Stamp",
            country="Mexico",
            year=2000,
            catalog_value_mint=Decimal('15.00'),
            qty_mint=2
        )
        
        # Update in database
        self.db_manager.update_stamp(stamp_id, updated_stamp)
        
        # Verify update
        collection = self.db_manager.load_collection()
        updated_stamp_from_db = collection.stamps[0]
        
        self.assertEqual(updated_stamp_from_db.scott_number, "TEST001_UPDATED")
        self.assertEqual(updated_stamp_from_db.description, "Updated Test Stamp")
        self.assertEqual(updated_stamp_from_db.country, "Mexico")
        self.assertEqual(updated_stamp_from_db.year, 2000)
    
    def test_delete_stamp(self):
        """Test deleting a stamp from database"""
        # Add stamp first
        stamp_id = self.db_manager.add_stamp(self.test_stamp1)
        
        # Verify it exists
        collection = self.db_manager.load_collection()
        self.assertEqual(len(collection.stamps), 1)
        
        # Delete stamp
        self.db_manager.delete_stamp(stamp_id)
        
        # Verify deletion
        collection = self.db_manager.load_collection()
        self.assertEqual(len(collection.stamps), 0)
    
    def test_search_stamps_by_description(self):
        """Test searching stamps by description"""
        self.db_manager.add_stamp(self.test_stamp1)
        self.db_manager.add_stamp(self.test_stamp2)
        
        criteria = {
            'description': 'Test Stamp 1',
            'scott_number': '',
            'country': '',
            'year_from': '',
            'year_to': '',
            'used_only': False,
            'want_list': False
        }
        
        results = self.db_manager.search_stamps(criteria)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1].scott_number, "TEST001")
    
    def test_search_stamps_by_scott_number(self):
        """Test searching stamps by Scott number"""
        self.db_manager.add_stamp(self.test_stamp1)
        self.db_manager.add_stamp(self.test_stamp2)
        
        criteria = {
            'description': '',
            'scott_number': 'TEST002',
            'country': '',
            'year_from': '',
            'year_to': '',
            'used_only': False,
            'want_list': False
        }
        
        results = self.db_manager.search_stamps(criteria)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1].scott_number, "TEST002")
    
    def test_search_stamps_by_year_range(self):
        """Test searching stamps by year range"""
        self.db_manager.add_stamp(self.test_stamp1)  # 1990
        self.db_manager.add_stamp(self.test_stamp2)  # 1995
        
        criteria = {
            'description': '',
            'scott_number': '',
            'country': '',
            'year_from': '1992',
            'year_to': '1998',
            'used_only': False,
            'want_list': False
        }
        
        results = self.db_manager.search_stamps(criteria)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1].scott_number, "TEST002")
    
    def test_search_stamps_used_only(self):
        """Test searching for used stamps only"""
        self.db_manager.add_stamp(self.test_stamp1)  # mint
        self.db_manager.add_stamp(self.test_stamp2)  # used
        
        criteria = {
            'description': '',
            'scott_number': '',
            'country': '',
            'year_from': '',
            'year_to': '',
            'used_only': True,
            'want_list': False
        }
        
        results = self.db_manager.search_stamps(criteria)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1].scott_number, "TEST002")
        self.assertTrue(results[0][1].used)
    
    def test_search_stamps_want_list(self):
        """Test searching for want list items"""
        self.db_manager.add_stamp(self.test_stamp1)  # not on want list
        self.db_manager.add_stamp(self.test_stamp2)  # on want list
        
        criteria = {
            'description': '',
            'scott_number': '',
            'country': '',
            'year_from': '',
            'year_to': '',
            'used_only': False,
            'want_list': True
        }
        
        results = self.db_manager.search_stamps(criteria)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1].scott_number, "TEST002")
        self.assertTrue(results[0][1].want_list)
    
    def test_get_statistics_empty_db(self):
        """Test statistics with empty database"""
        stats = self.db_manager.get_statistics()
        
        self.assertEqual(stats['total_stamps'], 0)
        self.assertEqual(stats['used_stamps'], 0)
        self.assertEqual(stats['mint_stamps'], 0)
        self.assertEqual(stats['countries'], 0)
        self.assertEqual(stats['total_catalog_value'], Decimal('0.00'))
        self.assertEqual(stats['average_value'], Decimal('0.00'))
        self.assertEqual(stats['want_list_items'], 0)
        self.assertEqual(stats['for_sale_items'], 0)
    
    def test_get_statistics_with_stamps(self):
        """Test statistics with stamps in database"""
        self.db_manager.add_stamp(self.test_stamp1)  # mint, $10.00
        self.db_manager.add_stamp(self.test_stamp2)  # used, $5.00 * 2 = $10.00
        
        stats = self.db_manager.get_statistics()
        
        self.assertEqual(stats['total_stamps'], 2)
        self.assertEqual(stats['used_stamps'], 1)
        self.assertEqual(stats['mint_stamps'], 1)
        self.assertEqual(stats['countries'], 2)  # USA and Canada
        self.assertEqual(stats['total_catalog_value'], Decimal('20.00'))
        self.assertEqual(stats['average_value'], Decimal('10.00'))
        self.assertEqual(stats['want_list_items'], 1)
        self.assertEqual(stats['for_sale_items'], 0)
    
    def test_create_stamp_from_row_valid_data(self):
        """Test creating stamp from database row with valid data"""
        # Simulate a database row (id is at index 0)
        row = (
            1,  # id
            "TEST001",  # scott_number
            "Test Description",  # description
            "USA",  # country
            1990,  # year
            "25c",  # denomination
            "Red",  # color
            "Very Fine",  # condition_grade
            "Mint NH",  # gum_condition
            "11.5",  # perforation
            False,  # used
            True,  # plate_block
            False,  # first_day_cover
            "Album 1",  # location
            "Test notes",  # notes
            1,  # qty_mint
            0,  # qty_used
            10.50,  # catalog_value_mint
            5.25,  # catalog_value_used
            8.00,  # purchase_price
            12.00,  # current_market_value
            False,  # want_list
            True,  # for_sale
            "2023-01-15",  # date_acquired
            "Local dealer",  # source
            "/path/to/image.jpg"  # image_path
        )
        
        stamp = self.db_manager._create_stamp_from_row(row)
        
        self.assertEqual(stamp.scott_number, "TEST001")
        self.assertEqual(stamp.description, "Test Description")
        self.assertEqual(stamp.country, "USA")
        self.assertEqual(stamp.year, 1990)
        self.assertEqual(stamp.catalog_value_mint, Decimal('10.50'))
        self.assertTrue(stamp.plate_block)
        self.assertFalse(stamp.used)
    
    def test_create_stamp_from_row_null_values(self):
        """Test creating stamp from database row with null values"""
        # Simulate a database row with null values
        row = (
            1,  # id
            "TEST001",  # scott_number
            "Test Description",  # description
            None,  # country
            None,  # year
            None,  # denomination
            None,  # color
            "Unknown",  # condition_grade
            "Unknown",  # gum_condition
            None,  # perforation
            False,  # used
            False,  # plate_block
            False,  # first_day_cover
            None,  # location
            None,  # notes
            0,  # qty_mint
            0,  # qty_used
            0.00,  # catalog_value_mint
            0.00,  # catalog_value_used
            0.00,  # purchase_price
            0.00,  # current_market_value
            False,  # want_list
            False,  # for_sale
            None,  # date_acquired
            None,  # source
            None  # image_path
        )
        
        stamp = self.db_manager._create_stamp_from_row(row)
        
        self.assertEqual(stamp.scott_number, "TEST001")
        self.assertEqual(stamp.description, "Test Description")
        self.assertIsNone(stamp.country)
        self.assertIsNone(stamp.year)
        self.assertEqual(stamp.catalog_value_mint, Decimal('0.00'))
    
    def test_stamp_to_tuple_conversion(self):
        """Test converting stamp object to tuple for database operations"""
        tuple_data = self.db_manager._stamp_to_tuple(self.test_stamp1)
        
        # Check that it returns a tuple with the correct number of elements
        self.assertIsInstance(tuple_data, tuple)
        self.assertEqual(len(tuple_data), 25)  # Should match number of database columns
        
        # Check specific values
        self.assertEqual(tuple_data[0], "TEST001")  # scott_number
        self.assertEqual(tuple_data[1], "Test Stamp 1")  # description
        self.assertEqual(tuple_data[2], "USA")  # country
        self.assertEqual(tuple_data[3], 1990)  # year


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for database operations"""
    
    def setUp(self):
        """Set up test fixtures with temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
    
    def test_full_crud_operations(self):
        """Test complete CRUD (Create, Read, Update, Delete) operations"""
        # Create
        original_stamp = Stamp(
            scott_number="CRUD001",
            description="CRUD Test Stamp",
            country="TestLand",
            year=2000,
            catalog_value_mint=Decimal('25.00'),
            qty_mint=1
        )
        
        stamp_id = self.db_manager.add_stamp(original_stamp)
        self.assertIsNotNone(stamp_id)
        
        # Read
        collection = self.db_manager.load_collection()
        self.assertEqual(len(collection.stamps), 1)
        loaded_stamp = collection.stamps[0]
        self.assertEqual(loaded_stamp.scott_number, "CRUD001")
        
        # Update
        updated_stamp = Stamp(
            scott_number="CRUD001_UPDATED",
            description="Updated CRUD Test Stamp",
            country="UpdatedLand",
            year=2001,
            catalog_value_mint=Decimal('30.00'),
            qty_mint=2
        )
        
        self.db_manager.update_stamp(stamp_id, updated_stamp)
        
        # Verify update
        collection = self.db_manager.load_collection()
        self.assertEqual(len(collection.stamps), 1)
        updated_loaded_stamp = collection.stamps[0]
        self.assertEqual(updated_loaded_stamp.scott_number, "CRUD001_UPDATED")
        self.assertEqual(updated_loaded_stamp.country, "UpdatedLand")
        self.assertEqual(updated_loaded_stamp.year, 2001)
        
        # Delete
        self.db_manager.delete_stamp(stamp_id)
        
        # Verify deletion
        collection = self.db_manager.load_collection()
        self.assertEqual(len(collection.stamps), 0)
    
    def test_complex_search_scenarios(self):
        """Test complex search scenarios with multiple criteria"""
        # Add test data
        stamps = [
            Stamp("US001", "Lincoln", "USA", 1909, catalog_value_mint=Decimal('100.00'), qty_mint=1),
            Stamp("US002", "Washington", "USA", 1932, used=True, catalog_value_used=Decimal('5.00'), qty_used=1),
            Stamp("CA001", "Maple Leaf", "Canada", 1935, catalog_value_mint=Decimal('15.00'), qty_mint=1, want_list=True),
            Stamp("UK001", "Queen Victoria", "UK", 1840, catalog_value_mint=Decimal('500.00'), qty_mint=1),
        ]
        
        for stamp in stamps:
            self.db_manager.add_stamp(stamp)
        
        # Test search by country and year range
        criteria = {
            'description': '',
            'scott_number': '',
            'country': 'USA',
            'year_from': '1900',
            'year_to': '1940',
            'used_only': False,
            'want_list': False
        }
        
        results = self.db_manager.search_stamps(criteria)
        self.assertEqual(len(results), 2)
        
        # Test search combining multiple criteria
        criteria = {
            'description': '',
            'scott_number': '',
            'country': '',
            'year_from': '1930',
            'year_to': '1940',
            'used_only': False,
            'want_list': True
        }
        
        results = self.db_manager.search_stamps(criteria)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1].scott_number, "CA001")


# Test runner and utility functions
class TestDataValidation(unittest.TestCase):
    """Test data validation and edge cases"""
    
    def test_decimal_precision(self):
        """Test decimal precision in monetary values"""
        stamp = Stamp(
            scott_number="DECIMAL001",
            description="Decimal Test",
            catalog_value_mint=Decimal('123.456789'),  # More precision than needed
            purchase_price=Decimal('99.99')
        )
        
        # Values should maintain precision
        self.assertEqual(stamp.catalog_value_mint, Decimal('123.456789'))
        self.assertEqual(stamp.purchase_price, Decimal('99.99'))
    
    def test_boolean_field_defaults(self):
        """Test boolean field default values"""
        stamp = Stamp(scott_number="BOOL001", description="Boolean Test")
        
        self.assertFalse(stamp.used)
        self.assertFalse(stamp.plate_block)
        self.assertFalse(stamp.first_day_cover)
        self.assertFalse(stamp.want_list)
        self.assertFalse(stamp.for_sale)
    
    def test_string_field_defaults(self):
        """Test string field default values"""
        stamp = Stamp(scott_number="STR001", description="String Test")
        
        self.assertIsNone(stamp.country)
        self.assertIsNone(stamp.denomination)
        self.assertIsNone(stamp.color)
        self.assertEqual(stamp.condition_grade, "Unknown")
        self.assertEqual(stamp.gum_condition, "Unknown")


if __name__ == '__main__':
    # Create a test suite combining all test cases
    test_classes = [
        TestStamp,
        TestStampCollection,
        TestDatabaseManager,
        TestDatabaseIntegration,
        TestDataValidation
    ]
    
    loader = unittest.TestLoader()
    suites = [loader.loadTestsFromTestCase(test_class) for test_class in test_classes]
    combined_suite = unittest.TestSuite(suites)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"TESTS RUN: {result.testsRun}")
    print(f"FAILURES: {len(result.failures)}")
    print(f"ERRORS: {len(result.errors)}")
    print(f"SUCCESS RATE: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")