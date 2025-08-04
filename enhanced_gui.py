# enhanced_gui.py
import FreeSimpleGUI as sg
from datetime import datetime
from decimal import Decimal, InvalidOperation
import os
import csv
from database_manager import DatabaseManager
from enhanced_stamp import Stamp, StampCollection

class EnhancedStampGUI:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.collection = self.db_manager.load_collection()
        self.current_stamp_id = None
        self.search_results = []
        
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
    
    def _create_layouts(self):
        """Create all GUI layouts"""
        # Menu bar
        menu_def = [
            ['&File', ['&New Collection', '&Import CSV', '&Export CSV', '&Backup Database', 'E&xit']],
            ['&Edit', ['&Add Stamp', '&Edit Stamp', '&Delete Stamp']],
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
        
        # Stamp list
        headings = ['ID', 'Scott #', 'Description', 'Country', 'Year', 'Condition', 'Value']
        stamp_list_frame = [
            [sg.Table(
                values=[],
                headings=headings,
                key="stamp_table",
                select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                enable_events=True,
                enable_click_events=True,  # Enable click events for double-click detection
                auto_size_columns=False,
                col_widths=[5, 12, 30, 15, 8, 12, 10],
                num_rows=15,
                expand_x=True,
                expand_y=True
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
        
        # Main layout with tabs - IMPORTANT: enable_events=True for tab selection detection
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
            ], expand_x=True, expand_y=True, key='tab_group', enable_events=True)]  # Enable events for tab selection
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
                    # The selected tab key will be in the tab_group's value
                    # Note: Different versions of FreeSimpleGUI might handle this differently
                    print("Browse Collection tab selected - refreshing stamp list")
                    self._refresh_all_stamps_from_database()
            
            # Alternative method: Check if the tab was specifically clicked
            # This handles cases where the event might be different
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
            if tab_group is not None:
                tab_group.update(value='tab_edit')  # Use the key we defined for the edit tab
        except Exception as e:
            print(f"Error switching to edit tab: {e}")

    def run(self):
        """Main event loop for the GUI"""
        while True:
            try:
                read_result = self.window.read()
                if read_result is None:
                    break
                    
                event, values = read_result
                
                if event in (None, 'Exit'):
                    break
                
                # Handle tab selection events - IMPORTANT: This must come early in the event handling
                if event == 'tab_group':
                    self._handle_tab_selection(event)
                    continue
                
                # Handle table double-click events
                if isinstance(event, tuple) and len(event) == 3:
                    element, event_type, data = event
                    if element == 'stamp_table' and event_type == '+DOUBLE CLICK+':
                        self._handle_table_double_click(data)
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
                elif event == 'stamp_table':
                    self._handle_table_select(values)
                
            except Exception as e:
                print(f"Error in event loop: {e}")
                sg.popup_error(f"An error occurred: {e}")
        
        self.window.close()

    def _handle_table_double_click(self, data):
        """Handle double-click on stamp table"""
        try:
            row = data[0]  # Get the row that was double-clicked
            if 0 <= row < len(self.search_results):
                stamp_id, stamp = self.search_results[row]
                self.current_stamp_id = stamp_id
                self._load_stamp_to_form(stamp)
                self._switch_to_edit_tab()
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
            self._refresh_all_stamps_from_database()  # Use the new method that reloads from DB
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
            self._refresh_all_stamps_from_database()  # Use the new method that reloads from DB
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
                self._refresh_all_stamps_from_database()  # Use the new method that reloads from DB
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
        self._refresh_all_stamps_from_database()  # Use the new method that reloads from DB
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
                    self._load_stamp_to_form(stamp)
        except Exception as e:
            print(f"Error handling table selection: {e}")

    def _create_stamp_from_values(self, values):
        """Create a Stamp object from form values"""
        return Stamp(
            scott_number=values['scott_number'],
            description=values['description'],
            country=values['country'],
            year=int(values['year']) if values['year'].strip() else None,
            denomination=values['denomination'],
            color=values['color'],
            condition_grade=values['condition_grade'],
            gum_condition=values['gum_condition'],
            perforation=values['perforation'],
            used=values['used'],
            plate_block=values['plate_block'],
            first_day_cover=values['first_day_cover'],
            location=values['location'],
            notes=values['notes'],
            qty_mint=int(values['qty_mint']),
            qty_used=int(values['qty_used']),
            catalog_value_mint=Decimal(values['catalog_value_mint']),
            catalog_value_used=Decimal(values['catalog_value_used']),
            purchase_price=Decimal(values['purchase_price']),
            current_market_value=Decimal(values['current_market_value']),
            want_list=values['want_list'],
            for_sale=values['for_sale'],
            date_acquired=values['date_acquired'] if values['date_acquired'] else None,
            source=values['source'],
            image_path=values['image_path']
        )