# enhanced_gui.py
import FreeSimpleGUI as sg
from datetime import datetime
from decimal import Decimal, InvalidOperation
import os
import csv
import time
import platform
from typing import Optional, Tuple
from database_manager import DatabaseManager
from enhanced_stamp import Stamp, StampCollection

class MacOSDoubleClickHandler:
    def __init__(self, double_click_threshold=None):
        """
        Initialize double-click handler with platform-optimized settings
        
        Args:
            double_click_threshold: Maximum time between clicks to register as double-click (seconds)
        """
        # Platform-specific timing
        if double_click_threshold is None:
            self.double_click_threshold = 0.3 if self._is_macos() else 0.5
        else:
            self.double_click_threshold = double_click_threshold
            
        self.last_click_time = 0
        self.last_clicked_row = None
        
    def _is_macos(self) -> bool:
        """Check if running on macOS"""
        return platform.system() == 'Darwin'
        
    def handle_table_event(self, event, values, table_key='stamp_table') -> Tuple[bool, Optional[int]]:
        """
        Handle table click events and detect double-clicks
        
        Returns:
            Tuple of (is_double_click, selected_row)
        """
        current_time = time.time()
        is_double_click = False
        selected_row = None
        
        # Check if this is a table event
        if event == table_key and table_key in values:
            if len(values[table_key]) > 0:
                selected_row = values[table_key][0]
                
                # Check for double-click
                time_diff = current_time - self.last_click_time
                if (time_diff <= self.double_click_threshold and 
                    selected_row == self.last_clicked_row and
                    time_diff > 0.05):  # Prevent immediate re-triggers
                    is_double_click = True
                
                self.last_click_time = current_time
                self.last_clicked_row = selected_row
        
        # Also handle the tuple-based event format that FreeSimpleGUI sometimes uses
        elif isinstance(event, tuple) and len(event) >= 2:
            element_key = event[0]
            event_type = str(event[1])
            
            if element_key == table_key:
                if any(keyword in event_type.upper() for keyword in ['DOUBLE', 'DBL', '+2+']):
                    # Direct double-click detection
                    if table_key in values and len(values[table_key]) > 0:
                        selected_row = values[table_key][0]
                        is_double_click = True
        
        return is_double_click, selected_row
    
    def reset_click_state(self):
        """Reset click state to prevent triple-click issues"""
        self.last_click_time = 0
        self.last_clicked_row = None

class EnhancedStampGUI:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.collection = self.db_manager.load_collection()
        self.current_stamp_id = None
        self.search_results = []
        
        # Initialize double-click handler
        self.double_click_handler = MacOSDoubleClickHandler()
        
        # Set theme
        sg.theme('DarkTeal9')
        
        # Initialize layouts
        self._create_layouts()
        self.window = sg.Window(
            "Professional Stamp Collection Manager", 
            self.main_layout, 
            size=(1200, 800),
            resizable=True,
            finalize=True
        )
        
        self._refresh_stamp_list()
        self._update_statistics()
    
    def _is_macos(self) -> bool:
        """Check if running on macOS"""
        return platform.system() == 'Darwin'
    
    def _create_layouts(self):
        """Create all GUI layouts"""
        # Menu bar with macOS-style shortcuts
        menu_def = [
            ['&File', ['&New Collection::Cmd+N', '&Import CSV', '&Export CSV', '&Backup Database', 'E&xit::Cmd+Q']],
            ['&Edit', ['&Add Stamp::Cmd+A', '&Edit Stamp::Cmd+E', '&Delete Stamp::Cmd+D']],
            ['&View', ['&Statistics', '&Want List', '&For Sale List']],
            ['&Help', ['&About']]
        ]
        
        # Search frame
        search_frame = [
            [sg.Text("Search Stamps:")],
            [sg.Text("Description:"), sg.Input(key="search_desc", size=(20, 1)),
             sg.Text("Scott #:"), sg.Input(key="search_scott", size=(15, 1)),
             sg.Text("Country:"), sg.Input(key="search_country", size=(15, 1))],
            [sg.Text("Year From:"), sg.Input(key="search_year_from", size=(8, 1)),
             sg.Text("To:"), sg.Input(key="search_year_to", size=(8, 1)),
             sg.Checkbox("Used Only", key="search_used"),
             sg.Checkbox("Want List", key="search_want"),
             sg.Button("Search"), sg.Button("Clear Search")]
        ]
        
        # Stamp list with enhanced configuration for better click handling
        headings = ['ID', 'Scott #', 'Description', 'Country', 'Year', 'Condition', 'Value']
        
        # Platform-specific table configuration
        table_config = {
            'enable_events': True,
            'enable_click_events': True,
            'select_mode': sg.TABLE_SELECT_MODE_BROWSE,
            'auto_size_columns': False,
            'col_widths': [5, 12, 30, 15, 8, 12, 10],
            'num_rows': 15,
            'expand_x': True,
            'expand_y': True
        }
        
        # Add macOS-specific enhancements
        if self._is_macos():
            table_config['bind_return_key'] = True
            table_config['right_click_menu'] = ['Right', ['Edit Stamp', 'Delete Stamp', '---', 'View Details']]
        
        stamp_list_frame = [
            [sg.Text("Double-click a row to edit stamp" + (" (or Control+click for menu)" if self._is_macos() else ""))],
            [sg.Table(
                values=[],
                headings=headings,
                key="stamp_table",
                **table_config
            )]
        ]
        
        # Stamp details frame
        left_column = [
            [sg.Text("Scott Number*:"), sg.Input(key="scott_number", size=(20, 1))],
            [sg.Text("Description*:"), sg.Input(key="description", size=(40, 1))],
            [sg.Text("Country:"), sg.Input(key="country", size=(25, 1))],
            [sg.Text("Year:"), sg.Input(key="year", size=(10, 1))],
            [sg.Text("Denomination:"), sg.Input(key="denomination", size=(15, 1))],
            [sg.Text("Color:"), sg.Input(key="color", size=(20, 1))],
            [sg.Text("Perforation:"), sg.Input(key="perforation", size=(15, 1))],
            [sg.Text("Location:"), sg.Input(key="location", size=(25, 1))]
        ]
        
        right_column = [
            [sg.Text("Condition:"), sg.Combo(
                ['Unknown', 'Poor', 'Fair', 'Fine', 'Very Fine', 'Extremely Fine', 'Superb'],
                key="condition_grade", default_value='Unknown', readonly=True)],
            [sg.Text("Gum:"), sg.Combo(
                ['Unknown', 'Mint NH', 'Hinged', 'Heavily Hinged', 'No Gum'],
                key="gum_condition", default_value='Unknown', readonly=True)],
            [sg.Checkbox("Used", key="used")],
            [sg.Checkbox("Plate Block", key="plate_block")],
            [sg.Checkbox("First Day Cover", key="first_day_cover")],
            [sg.Checkbox("Want List Item", key="want_list")],
            [sg.Checkbox("For Sale", key="for_sale")],
            [sg.Text("Source:"), sg.Input(key="source", size=(20, 1))]
        ]
        
        quantities_column = [
            [sg.Text("Quantities & Values:")],
            [sg.Text("Qty Used:"), sg.Input(key="qty_used", size=(8, 1), default_text="0")],
            [sg.Text("Qty Mint:"), sg.Input(key="qty_mint", size=(8, 1), default_text="0")],
            [sg.Text("Cat Val Used:"), sg.Input(key="catalog_value_used", size=(10, 1), default_text="0.00")],
            [sg.Text("Cat Val Mint:"), sg.Input(key="catalog_value_mint", size=(10, 1), default_text="0.00")],
            [sg.Text("Purchase Price:"), sg.Input(key="purchase_price", size=(10, 1), default_text="0.00")],
            [sg.Text("Market Value:"), sg.Input(key="current_market_value", size=(10, 1), default_text="0.00")],
            [sg.Text("Date Acquired:"), sg.Input(key="date_acquired", size=(12, 1))]
        ]
        
        details_frame = [
            [sg.Column(left_column), sg.VSeparator(), sg.Column(right_column), sg.VSeparator(), sg.Column(quantities_column)],
            [sg.Text("Notes:")],
            [sg.Multiline(key="notes", size=(80, 4))],
            [sg.Text("Image Path:"), sg.Input(key="image_path", size=(50, 1)), sg.FileBrowse()],
            [sg.Button("Add Stamp"), sg.Button("Update Stamp"), sg.Button("Delete Stamp"), sg.Button("Clear Form")]
        ]
        
        # Statistics frame
        stats_frame = [
            [sg.Text("Collection Statistics:")],
            [sg.Text("", key="stats_display", size=(60, 6), font=('Courier', 10))]
        ]
        
        # Main layout with tabs
        tab1_layout = [
            [sg.Frame("Search", search_frame, expand_x=True)],
            [sg.Frame("Stamp Collection", stamp_list_frame, expand_x=True, expand_y=True)]
        ]
        
        tab2_layout = [
            [sg.Frame("Stamp Details", details_frame, expand_x=True)]
        ]
        
        tab3_layout = [
            [sg.Frame("Statistics", stats_frame, expand_x=True)]
        ]
        
        self.main_layout = [
            [sg.Menu(menu_def)],
            [sg.TabGroup([
                [sg.Tab('Browse Collection', tab1_layout, key='tab_browse')],
                [sg.Tab('Add/Edit Stamps', tab2_layout, key='tab_edit')],
                [sg.Tab('Statistics', tab3_layout, key='tab_stats')]
            ], expand_x=True, expand_y=True, key='tab_group', enable_events=True)]
        ]
    
    def _refresh_stamp_list(self, stamps=None):
        """Refresh the stamp list display"""
        if stamps is None:
            # Reload collection from database to get latest data
            self.collection = self.db_manager.load_collection()
            stamps = [(None, stamp) for stamp in self.collection.list_stamps()]
        
        table_data = []
        for db_id, stamp in stamps:
            value = stamp.calculate_total_value()
            table_data.append([
                db_id or "New",
                stamp.scott_number,
                stamp.description[:40],
                stamp.country,
                stamp.year or "",
                stamp.condition_grade,
                f"${value:.2f}"
            ])
        
        # Safely update the table
        table_element = self.window.find_element('stamp_table')
        if table_element is not None:
            try:
                table_element.update(values=table_data)
            except Exception as e:
                print(f"Error updating stamp table: {e}")
        
        self.search_results = stamps
    
    def _refresh_all_stamps_from_database(self):
        """Refresh the stamp list with all stamps from database (clears any search filters)"""
        try:
            # Load all stamps from database
            self.collection = self.db_manager.load_collection()
            all_stamps = []
            
            # Get stamps with their database IDs by searching for all stamps
            search_results = self.db_manager.search_stamps({
                'description': '',
                'scott_number': '',
                'country': '',
                'year_from': '',
                'year_to': '',
                'used_only': False,
                'want_list': False
            })
            
            self._refresh_stamp_list(search_results)
            print(f"Refreshed stamp list with {len(search_results)} stamps from database")
            
        except Exception as e:
            print(f"Error refreshing stamps from database: {e}")
            sg.popup_error(f"Error loading stamps: {e}")
    
    def _update_statistics(self):
        """Update statistics display"""
        stats = self.db_manager.get_statistics()
        
        stats_text = f"""
Total Stamps: {stats['total_stamps']:,}
Used Stamps: {stats['used_stamps']:,}
Mint Stamps: {stats['mint_stamps']:,}
Countries Represented: {stats['countries']}

Total Catalog Value: ${stats['total_catalog_value']:,.2f}
Average Value per Stamp: ${stats['average_value']:.2f}

Want List Items: {stats['want_list_items']}
For Sale Items: {stats['for_sale_items']}
        """.strip()
        
        # Safely update the stats display
        stats_element = self.window.find_element('stats_display')
        if stats_element is not None:
            try:
                stats_element.update(value=stats_text)
            except Exception as e:
                print(f"Error updating statistics display: {e}")

    def _handle_tab_selection(self, event):
        """Handle tab selection events"""
        try:
            if event == 'tab_group':
                # Get the currently selected tab
                tab_group = self.window.find_element('tab_group')
                if tab_group is not None:
                    print("Browse Collection tab selected - refreshing stamp list")
                    self._refresh_all_stamps_from_database()
            
            # Alternative method: Check if the tab was specifically clicked
            elif event in ['tab_browse', 'Browse Collection']:
                print("Browse Collection tab selected - refreshing stamp list")
                self._refresh_all_stamps_from_database()
                
        except Exception as e:
            print(f"Error handling tab selection: {e}")
    
    def _clear_form(self):
        """Clear all form fields"""
        fields = [
            "scott_number", "description", "country", "year", "denomination", 
            "color", "perforation", "location", "source", "notes", "image_path"
        ]
        
        for field in fields:
            element = self.window.find_element(field)
            if element is not None:
                element.update(value='')
        
        # Handle dropdown fields separately
        dropdown_fields = ["condition_grade", "gum_condition"]
        for field in dropdown_fields:
            element = self.window.find_element(field)
            if element is not None:
                element.update(value='Unknown')
        
        # Handle numeric fields
        numeric_fields = ["qty_used", "qty_mint"]
        for field in numeric_fields:
            element = self.window.find_element(field)
            if element is not None:
                element.update(value='0')
        
        # Handle decimal fields
        decimal_fields = ["catalog_value_used", "catalog_value_mint", "purchase_price", "current_market_value"]
        for field in decimal_fields:
            element = self.window.find_element(field)
            if element is not None:
                element.update(value='0.00')
        
        # Handle date field
        date_element = self.window.find_element('date_acquired')
        if date_element is not None:
            date_element.update(value='')
        
        # Clear checkboxes safely
        checkboxes = ["used", "plate_block", "first_day_cover", "want_list", "for_sale"]
        for checkbox in checkboxes:
            element = self.window.find_element(checkbox)
            if element is not None:
                element.update(value=False)
        
        self.current_stamp_id = None
    
    def _load_stamp_to_form(self, stamp):
        """Load stamp data into form fields"""
        if not stamp:
            return

        # Dictionary of field names and their corresponding values
        fields = {
            "scott_number": stamp.scott_number,
            "description": stamp.description,
            "country": stamp.country or "",
            "year": str(stamp.year) if stamp.year else "",
            "denomination": stamp.denomination or "",
            "color": stamp.color or "",
            "perforation": stamp.perforation or "",
            "location": stamp.location or "",
            "condition_grade": stamp.condition_grade,
            "gum_condition": stamp.gum_condition,
            "used": stamp.used,
            "plate_block": stamp.plate_block,
            "first_day_cover": stamp.first_day_cover,
            "want_list": stamp.want_list,
            "for_sale": stamp.for_sale,
            "qty_used": str(stamp.qty_used),
            "qty_mint": str(stamp.qty_mint),
            "catalog_value_used": f"{stamp.catalog_value_used:.2f}",
            "catalog_value_mint": f"{stamp.catalog_value_mint:.2f}",
            "purchase_price": f"{stamp.purchase_price:.2f}",
            "current_market_value": f"{stamp.current_market_value:.2f}",
            "date_acquired": stamp.date_acquired or "",
            "source": stamp.source or "",
            "notes": stamp.notes or "",
            "image_path": stamp.image_path or ""
        }

        # Safely update each field
        for key, value in fields.items():
            element = self.window.find_element(key)
            if element is not None:
                element.update(value=value)

    def _validate_required_fields(self):
        """Validate required fields"""
        required = ["scott_number", "description"]
        for field in required:
            element = self.window.find_element(field)
            if element is None:
                return False
            value = element.get()
            if value is None or not value.strip():
                sg.popup_error(f"{field.replace('_', ' ').title()} is required!")
                return False
        return True

    def _validate_numeric_fields(self):
        """Validate numeric fields"""
        numeric_fields = ["qty_used", "qty_mint", "catalog_value_used", 
                         "catalog_value_mint", "purchase_price", "current_market_value"]
        for field in numeric_fields:
            element = self.window.find_element(field)
            if element is None:
                return False
            value = element.get()
            if value is None:
                sg.popup_error(f"Invalid numeric value in {field.replace('_', ' ').title()}")
                return False
            if value.strip():  # Only validate if not empty
                try:
                    Decimal(value)
                except InvalidOperation:
                    sg.popup_error(f"Invalid numeric value in {field.replace('_', ' ').title()}")
                    return False
        return True

    def _validate_date(self):
        """Validate date_acquired field"""
        element = self.window.find_element('date_acquired')
        if element is None:
            return False
        date_str = element.get()
        if date_str is None:
            sg.popup_error("Invalid date format. Use YYYY-MM-DD")
            return False
        date_str = date_str.strip()
        if date_str:  # Only validate if not empty
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                sg.popup_error("Invalid date format. Use YYYY-MM-DD")
                return False
        return True

    def _switch_to_edit_tab(self):
        """Switch to the Add/Edit tab"""
        try:
            tab_group = self.window.find_element('tab_group')
            if tab_group is not None and tab_group.Widget is not None:
                try:
                    # Try the most direct approach
                    tab_group.Widget.select(1)  # Select second tab (Add/Edit)
                    return True
                except Exception as e:
                    print(f"Tab switching failed: {e}")
                    return False
            else:
                print("Tab group or widget not available")
                return False
        except Exception as e:
            print(f"Error switching to edit tab: {e}")
            return False

    def _handle_keyboard_shortcuts(self, event, values):
        """Handle keyboard shortcuts, including macOS Command key combinations"""
        try:
            event_str = str(event).lower()
            
            # Handle macOS Command key combinations
            if self._is_macos() and ('cmd' in event_str or 'command' in event_str):
                if 'n' in event_str:  # Cmd+N - New stamp
                    self._clear_form()
                    self._switch_to_edit_tab()
                elif 's' in event_str:  # Cmd+S - Save
                    if self._validate_all_fields():
                        if self.current_stamp_id:
                            self._update_stamp(values)
                        else:
                            self._add_stamp(values)
                elif 'd' in event_str:  # Cmd+D - Delete
                    self._delete_stamp()
                elif 'e' in event_str:  # Cmd+E - Edit
                    if self.current_stamp_id:
                        self._switch_to_edit_tab()
                elif 'q' in event_str:  # Cmd+Q - Quit
                    return 'Exit'
            
            # Handle Control key combinations for other platforms
            elif 'control' in event_str or 'ctrl' in event_str:
                if 'n' in event_str:
                    self._clear_form()
                    self._switch_to_edit_tab()
                elif 's' in event_str:
                    if self._validate_all_fields():
                        if self.current_stamp_id:
                            self._update_stamp(values)
                        else:
                            self._add_stamp(values)
                elif 'delete' in event_str or 'del' in event_str:
                    self._delete_stamp()
            
            # Handle Enter key on table
            elif event_str == 'return' or event_str == '\r':
                if 'stamp_table' in values and len(values['stamp_table']) > 0:
                    selected_row = values['stamp_table'][0]
                    self._handle_table_double_click(selected_row)
                    
        except Exception as e:
            print(f"Error handling keyboard shortcut: {e}")
        
        return None

    def run(self):
        """Main event loop with improved macOS double-click handling"""
        while True:
            try:
                # Use timeout for better responsiveness, especially on macOS
                read_result = self.window.read(timeout=100)
                
                if read_result is None:
                    break
                    
                event, values = read_result
                
                if event in (None, 'Exit'):
                    break
                
                # Handle keyboard shortcuts first
                shortcut_result = self._handle_keyboard_shortcuts(event, values)
                if shortcut_result == 'Exit':
                    break
                elif shortcut_result is not None:
                    continue
                
                # Handle double-click detection with improved algorithm
                is_double_click, selected_row = self.double_click_handler.handle_table_event(
                    event, values, 'stamp_table'
                )
                
                if is_double_click and selected_row is not None:
                    print(f"Double-click detected on row {selected_row}")
                    self._handle_table_double_click(selected_row)
                    self.double_click_handler.reset_click_state()  # Prevent triple-click issues
                    continue
                
                # Handle tab selection events
                if event == 'tab_group':
                    self._handle_tab_selection(event)
                    continue

                # Handle single table click (for selection)
                elif event == 'stamp_table':
                    self._handle_table_select(values)
                    continue
                
                # Handle right-click context menu items (macOS)
                elif event in ['Edit Stamp', 'Delete Stamp', 'View Details']:
                    if event == 'Edit Stamp':
                        if 'stamp_table' in values and len(values['stamp_table']) > 0:
                            selected_row = values['stamp_table'][0]
                            self._handle_table_double_click(selected_row)
                    elif event == 'Delete Stamp':
                        self._delete_stamp()
                    elif event == 'View Details':
                        if 'stamp_table' in values and len(values['stamp_table']) > 0:
                            selected_row = values['stamp_table'][0]
                            self._handle_table_select(values)
                            self._switch_to_edit_tab()
                    continue
                
                # Handle other events
                if event == 'Clear Form':
                    self._clear_form()
                elif event == 'Add Stamp':
                    if self._validate_all_fields():
                        self._add_stamp(values)
                elif event == 'Update Stamp':
                    if self._validate_all_fields():
                        self._update_stamp(values)
                elif event == 'Delete Stamp':
                    self._delete_stamp()
                elif event == 'Search':
                    self._perform_search(values)
                elif event == 'Clear Search':
                    self._clear_search()
                
            except Exception as e:
                print(f"Error in event loop: {e}")
                sg.popup_error(f"An error occurred: {e}")
        
        self.window.close()

    def _handle_table_double_click(self, row):
        """Handle double-click on stamp table"""
        try:
            print(f"Double-click detected on row: {row}")
            
            if 0 <= row < len(self.search_results):
                stamp_id, stamp = self.search_results[row]
                print(f"Loading stamp for editing: {stamp.scott_number} (ID: {stamp_id})")
                
                self.current_stamp_id = stamp_id
                self._load_stamp_to_form(stamp)
                
                # Try to switch to edit tab
                if self._switch_to_edit_tab():
                    sg.popup_quick_message(f"Editing: {stamp.scott_number}", auto_close_duration=1)
                else:
                    sg.popup_quick_message(f"Loaded: {stamp.scott_number}\nClick 'Add/Edit Stamps' tab to edit", auto_close_duration=2)
                    
        except Exception as e:
            print(f"Error handling table double-click: {e}")

    def _validate_all_fields(self):
        """Validate all form fields"""
        return all([
            self._validate_required_fields(),
            self._validate_numeric_fields(),
            self._validate_date()
        ])
    
    def _add_stamp(self, values):
        """Add a new stamp to the collection"""
        try:
            stamp = self._create_stamp_from_values(values)
            self.db_manager.add_stamp(stamp)
            self._clear_form()
            self._refresh_all_stamps_from_database()
            self._update_statistics()
            sg.popup("Stamp added successfully!")
        except Exception as e:
            sg.popup_error(f"Error adding stamp: {e}")

    def _update_stamp(self, values):
        """Update existing stamp"""
        if not self.current_stamp_id:
            sg.popup_error("No stamp selected!")
            return
        try:
            stamp = self._create_stamp_from_values(values)
            self.db_manager.update_stamp(self.current_stamp_id, stamp)
            self._clear_form()
            self._refresh_all_stamps_from_database()
            self._update_statistics()
            sg.popup("Stamp updated successfully!")
        except Exception as e:
            sg.popup_error(f"Error updating stamp: {e}")

    def _delete_stamp(self):
        """Delete selected stamp"""
        if not self.current_stamp_id:
            sg.popup_error("No stamp selected!")
            return
        try:
            if sg.popup_yes_no("Are you sure you want to delete this stamp?") == 'Yes':
                self.db_manager.delete_stamp(self.current_stamp_id)
                self._clear_form()
                self._refresh_all_stamps_from_database()
                self._update_statistics()
                sg.popup("Stamp deleted successfully!")
        except Exception as e:
            sg.popup_error(f"Error deleting stamp: {e}")

    def _perform_search(self, values):
        """Search stamps based on criteria"""
        try:
            criteria = {
                'description': values['search_desc'],
                'scott_number': values['search_scott'],
                'country': values['search_country'],
                'year_from': values['search_year_from'],
                'year_to': values['search_year_to'],
                'used_only': values['search_used'],
                'want_list': values['search_want']
            }
            results = self.db_manager.search_stamps(criteria)
            self._refresh_stamp_list(results)
        except Exception as e:
            sg.popup_error(f"Error performing search: {e}")

    def _clear_search(self):
        """Clear search results and show all stamps"""
        self._refresh_all_stamps_from_database()
        search_fields = ['search_desc', 'search_scott', 'search_country', 
                       'search_year_from', 'search_year_to']
        for field in search_fields:
            element = self.window.find_element(field)
            if element is not None:
                element.update(value='')
        search_checks = ['search_used', 'search_want']
        for check in search_checks:
            element = self.window.find_element(check)
            if element is not None:
                element.update(value=False)

    def _handle_table_select(self, values):
        """Handle stamp selection from table"""
        try:
            if len(values['stamp_table']) > 0:
                selected_row = values['stamp_table'][0]
                if 0 <= selected_row < len(self.search_results):
                    stamp_id, stamp = self.search_results[selected_row]
                    self.current_stamp_id = stamp_id
                    # Don't automatically load to form on single click - just store selection
                    print(f"Selected stamp: {stamp.scott_number} (ID: {stamp_id})")
        except Exception as e:
            print(f"Error handling table selection: {e}")

    def _create_stamp_from_values(self, values):
        """Create a Stamp object from form values"""
        return Stamp(
            scott_number=values['scott_number'],
            description=values['description'],
            country=values['country'] if values['country'].strip() else None,
            year=int(values['year']) if values['year'].strip() else None,
            denomination=values['denomination'] if values['denomination'].strip() else None,
            color=values['color'] if values['color'].strip() else None,
            condition_grade=values['condition_grade'],
            gum_condition=values['gum_condition'],
            perforation=values['perforation'] if values['perforation'].strip() else None,
            used=values['used'],
            plate_block=values['plate_block'],
            first_day_cover=values['first_day_cover'],
            location=values['location'] if values['location'].strip() else None,
            notes=values['notes'] if values['notes'].strip() else None,
            qty_mint=int(values['qty_mint']) if values['qty_mint'].strip() else 0,
            qty_used=int(values['qty_used']) if values['qty_used'].strip() else 0,
            catalog_value_mint=Decimal(values['catalog_value_mint']) if values['catalog_value_mint'].strip() else Decimal('0.00'),
            catalog_value_used=Decimal(values['catalog_value_used']) if values['catalog_value_used'].strip() else Decimal('0.00'),
            purchase_price=Decimal(values['purchase_price']) if values['purchase_price'].strip() else Decimal('0.00'),
            current_market_value=Decimal(values['current_market_value']) if values['current_market_value'].strip() else Decimal('0.00'),
            want_list=values['want_list'],
            for_sale=values['for_sale'],
            date_acquired=values['date_acquired'] if values['date_acquired'].strip() else None,
            source=values['source'] if values['source'].strip() else None,
            image_path=values['image_path'] if values['image_path'].strip() else None
        )