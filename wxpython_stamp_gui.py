# wxpython_stamp_gui_fixed.py
"""
Fixed wxPython Stamp Collection Manager GUI
This version eliminates all sizer parent-child relationship errors
"""

import wx
import wx.grid
import wx.adv
from decimal import Decimal, InvalidOperation
from datetime import datetime
import os

# Import existing backend modules
from database_manager import DatabaseManager
from enhanced_stamp import Stamp


class StampGrid(wx.grid.Grid):
    """Custom grid for displaying stamps"""
    
    def __init__(self, parent, main_frame=None):
        super().__init__(parent)
        self.main_frame = main_frame
        
        # Grid setup
        self.CreateGrid(0, 7)
        self.SetColLabelValue(0, "ID")
        self.SetColLabelValue(1, "Scott #")
        self.SetColLabelValue(2, "Description")
        self.SetColLabelValue(3, "Country")
        self.SetColLabelValue(4, "Year")
        self.SetColLabelValue(5, "Condition")
        self.SetColLabelValue(6, "Value")
        
        # Column widths
        self.SetColSize(0, 50)
        self.SetColSize(1, 100)
        self.SetColSize(2, 250)
        self.SetColSize(3, 100)
        self.SetColSize(4, 70)
        self.SetColSize(5, 100)
        self.SetColSize(6, 80)
        
        # Make grid read-only
        self.EnableEditing(False)
        
        # Bind events
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnDoubleClick)
    
    def OnDoubleClick(self, event):
        """Handle double-click to edit stamp"""
        row = event.GetRow()
        if row >= 0 and self.main_frame and hasattr(self.main_frame, 'EditSelectedStamp'):
            self.main_frame.EditSelectedStamp(row)
        event.Skip()

    def UpdateData(self, stamps_data):
        """Update grid with new stamp data"""
        # Clear existing data
        if self.GetNumberRows() > 0:
            self.DeleteRows(0, self.GetNumberRows())
        
        # Add new data
        for i, (stamp_id, stamp) in enumerate(stamps_data):
            self.AppendRows(1)
            self.SetCellValue(i, 0, str(stamp_id or "New"))
            self.SetCellValue(i, 1, stamp.scott_number)
            description = stamp.description
            if len(description) > 40:
                description = description[:37] + "..."
            self.SetCellValue(i, 2, description)
            self.SetCellValue(i, 3, stamp.country or "")
            self.SetCellValue(i, 4, str(stamp.year) if stamp.year else "")
            self.SetCellValue(i, 5, stamp.condition_grade)
            self.SetCellValue(i, 6, f"${stamp.calculate_total_value():.2f}")


class BrowsePanel(wx.Panel):
    """Browse and search panel"""
    
    def __init__(self, parent, main_frame=None):
        super().__init__(parent)
        self.main_frame = main_frame
        self.CreateControls()
        self.DoLayout()
    
    def CreateControls(self):
        """Create all controls for browse panel"""
        # Search controls - ALL use self as parent
        self.search_desc = wx.TextCtrl(self)
        self.search_scott = wx.TextCtrl(self)
        self.search_country = wx.TextCtrl(self)
        self.search_used = wx.CheckBox(self, label="Used Only")
        self.search_want = wx.CheckBox(self, label="Want List")
        self.search_btn = wx.Button(self, label="Search")
        self.clear_btn = wx.Button(self, label="Clear")
        
        # Grid - pass main_frame reference
        self.stamp_grid = StampGrid(self, main_frame=self.main_frame)
        
        # Bind events
        self.search_btn.Bind(wx.EVT_BUTTON, self.OnSearch)
        self.clear_btn.Bind(wx.EVT_BUTTON, self.OnClear)
    
    def DoLayout(self):
        """Layout controls"""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Search section
        search_box = wx.StaticBox(self, label="Search")
        search_sizer = wx.StaticBoxSizer(search_box, wx.VERTICAL)
        
        # Search fields grid
        search_grid = wx.FlexGridSizer(3, 2, 5, 10)
        search_grid.AddGrowableCol(1)
        
        # Add controls in correct order
        fields = [
            ("Description:", self.search_desc),
            ("Scott #:", self.search_scott),
            ("Country:", self.search_country),
        ]
        
        for label_text, control in fields:
            search_grid.Add(wx.StaticText(self, label=label_text), 0, wx.ALIGN_CENTER_VERTICAL)
            search_grid.Add(control, 1, wx.EXPAND)
        
        search_sizer.Add(search_grid, 0, wx.EXPAND | wx.ALL, 5)
        
        # Search options
        options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        options_sizer.Add(self.search_used, 0, wx.ALL, 5)
        options_sizer.Add(self.search_want, 0, wx.ALL, 5)
        options_sizer.AddStretchSpacer()
        options_sizer.Add(self.search_btn, 0, wx.ALL, 5)
        options_sizer.Add(self.clear_btn, 0, wx.ALL, 5)
        
        search_sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Grid
        main_sizer.Add(self.stamp_grid, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
    
    def OnSearch(self, event):
        """Handle search"""
        if self.main_frame and hasattr(self.main_frame, 'OnSearch'):
            self.main_frame.OnSearch(event)
    
    def OnClear(self, event):
        """Handle clear search"""
        if self.main_frame and hasattr(self.main_frame, 'OnClearSearch'):
            self.main_frame.OnClearSearch(event)


class EditPanel(wx.Panel):
    """Edit/Add stamp panel"""
    
    def __init__(self, parent, main_frame=None):
        super().__init__(parent)
        self.main_frame = main_frame
        self.current_stamp_id = None
        self.CreateControls()
        self.DoLayout()
    
    def CreateControls(self):
        """Create all form controls"""
        # Create the scrolled window first
        self.scroll = wx.ScrolledWindow(self)
        self.scroll.SetScrollRate(0, 20)
        
        # ALL CONTROLS NOW USE self.scroll AS PARENT
        # Basic info controls
        self.scott_number = wx.TextCtrl(self.scroll)
        self.description = wx.TextCtrl(self.scroll)
        self.country = wx.TextCtrl(self.scroll)
        self.year = wx.SpinCtrl(self.scroll, min=1800, max=2030, initial=2023)
        self.denomination = wx.TextCtrl(self.scroll)
        self.color = wx.TextCtrl(self.scroll)
        self.location = wx.TextCtrl(self.scroll)
        self.perforation = wx.TextCtrl(self.scroll)
        
        # Condition controls
        condition_choices = ['Unknown', 'Poor', 'Fair', 'Fine', 'Very Fine', 'Extremely Fine', 'Superb']
        self.condition_grade = wx.Choice(self.scroll, choices=condition_choices)
        self.condition_grade.SetSelection(0)
        
        gum_choices = ['Unknown', 'Mint NH', 'Hinged', 'Heavily Hinged', 'No Gum']
        self.gum_condition = wx.Choice(self.scroll, choices=gum_choices)
        self.gum_condition.SetSelection(0)
        
        # Quantity controls
        self.qty_mint = wx.SpinCtrl(self.scroll, min=0, max=999, initial=0)
        self.qty_used = wx.SpinCtrl(self.scroll, min=0, max=999, initial=0)
        
        # Value controls
        self.catalog_value_mint = wx.TextCtrl(self.scroll, value="0.00")
        self.catalog_value_used = wx.TextCtrl(self.scroll, value="0.00")
        self.purchase_price = wx.TextCtrl(self.scroll, value="0.00")
        self.current_market_value = wx.TextCtrl(self.scroll, value="0.00")
        
        # Checkbox controls
        self.used = wx.CheckBox(self.scroll, label="Used")
        self.plate_block = wx.CheckBox(self.scroll, label="Plate Block")
        self.first_day_cover = wx.CheckBox(self.scroll, label="First Day Cover")
        self.want_list = wx.CheckBox(self.scroll, label="Want List")
        self.for_sale = wx.CheckBox(self.scroll, label="For Sale")
        
        # Other field controls
        self.source = wx.TextCtrl(self.scroll)
        self.date_acquired = wx.TextCtrl(self.scroll)
        self.notes = wx.TextCtrl(self.scroll, style=wx.TE_MULTILINE, size=wx.Size(-1, 100))
        self.image_path = wx.TextCtrl(self.scroll)
        self.browse_btn = wx.Button(self.scroll, label="Browse...")
        
        # Action button controls
        self.add_btn = wx.Button(self.scroll, label="Add Stamp")
        self.update_btn = wx.Button(self.scroll, label="Update Stamp")
        self.delete_btn = wx.Button(self.scroll, label="Delete Stamp")
        self.clear_btn = wx.Button(self.scroll, label="Clear Form")
        
        # Bind events
        self.add_btn.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.update_btn.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.delete_btn.Bind(wx.EVT_BUTTON, self.OnDelete)
        self.clear_btn.Bind(wx.EVT_BUTTON, self.OnClear)
        self.browse_btn.Bind(wx.EVT_BUTTON, self.OnBrowse)
    
    def DoLayout(self):
        """Layout all controls"""
        # Main sizer for the panel itself
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Sizer for the scrolled window content
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Basic info section
        basic_box = wx.StaticBox(self.scroll, label="Basic Information")
        basic_sizer = wx.StaticBoxSizer(basic_box, wx.VERTICAL)
        basic_grid = wx.FlexGridSizer(8, 2, 5, 10)
        basic_grid.AddGrowableCol(1)
        
        # Add basic fields
        basic_fields = [
            ("Scott Number*:", self.scott_number),
            ("Description*:", self.description),
            ("Country:", self.country),
            ("Year:", self.year),
            ("Denomination:", self.denomination),
            ("Color:", self.color),
            ("Location:", self.location),
            ("Perforation:", self.perforation),
        ]
        
        for label_text, control in basic_fields:
            basic_grid.Add(wx.StaticText(self.scroll, label=label_text), 0, wx.ALIGN_CENTER_VERTICAL)
            basic_grid.Add(control, 1, wx.EXPAND)
        
        basic_sizer.Add(basic_grid, 0, wx.EXPAND | wx.ALL, 5)
        scroll_sizer.Add(basic_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Condition section
        condition_box = wx.StaticBox(self.scroll, label="Condition & Quantities")
        condition_sizer = wx.StaticBoxSizer(condition_box, wx.VERTICAL)
        condition_grid = wx.FlexGridSizer(6, 2, 5, 10)
        condition_grid.AddGrowableCol(1)
        
        condition_fields = [
            ("Condition:", self.condition_grade),
            ("Gum:", self.gum_condition),
            ("Qty Mint:", self.qty_mint),
            ("Qty Used:", self.qty_used),
            ("Cat Val Mint:", self.catalog_value_mint),
            ("Cat Val Used:", self.catalog_value_used),
        ]
        
        for label_text, control in condition_fields:
            condition_grid.Add(wx.StaticText(self.scroll, label=label_text), 0, wx.ALIGN_CENTER_VERTICAL)
            condition_grid.Add(control, 1, wx.EXPAND)
        
        condition_sizer.Add(condition_grid, 0, wx.EXPAND | wx.ALL, 5)
        
        # Checkboxes
        checkbox_sizer = wx.BoxSizer(wx.HORIZONTAL)
        checkboxes = [self.used, self.plate_block, self.first_day_cover, self.want_list, self.for_sale]
        for cb in checkboxes:
            checkbox_sizer.Add(cb, 0, wx.ALL, 5)
        
        condition_sizer.Add(wx.StaticText(self.scroll, label="Options:"), 0, wx.ALL, 5)
        condition_sizer.Add(checkbox_sizer, 0, wx.ALL, 5)
        scroll_sizer.Add(condition_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Financial section
        financial_box = wx.StaticBox(self.scroll, label="Financial Information")
        financial_sizer = wx.StaticBoxSizer(financial_box, wx.VERTICAL)
        financial_grid = wx.FlexGridSizer(4, 2, 5, 10)
        financial_grid.AddGrowableCol(1)
        
        financial_fields = [
            ("Purchase Price:", self.purchase_price),
            ("Market Value:", self.current_market_value),
            ("Source:", self.source),
            ("Date Acquired:", self.date_acquired),
        ]
        
        for label_text, control in financial_fields:
            financial_grid.Add(wx.StaticText(self.scroll, label=label_text), 0, wx.ALIGN_CENTER_VERTICAL)
            financial_grid.Add(control, 1, wx.EXPAND)
        
        financial_sizer.Add(financial_grid, 0, wx.EXPAND | wx.ALL, 5)
        scroll_sizer.Add(financial_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Notes section
        notes_box = wx.StaticBox(self.scroll, label="Notes")
        notes_sizer = wx.StaticBoxSizer(notes_box, wx.VERTICAL)
        notes_sizer.Add(self.notes, 1, wx.EXPAND | wx.ALL, 5)
        scroll_sizer.Add(notes_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Image section
        image_box = wx.StaticBox(self.scroll, label="Image")
        image_sizer = wx.StaticBoxSizer(image_box, wx.HORIZONTAL)
        image_sizer.Add(wx.StaticText(self.scroll, label="Path:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        image_sizer.Add(self.image_path, 1, wx.EXPAND | wx.RIGHT, 5)
        image_sizer.Add(self.browse_btn, 0)
        scroll_sizer.Add(image_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Buttons section
        btn_box = wx.StaticBox(self.scroll, label="Actions")
        btn_sizer = wx.StaticBoxSizer(btn_box, wx.HORIZONTAL)
        btn_sizer.Add(self.add_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.update_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.delete_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.clear_btn, 0, wx.ALL, 5)
        scroll_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Set the sizer for the scrolled window
        self.scroll.SetSizer(scroll_sizer)
        
        # Add scrolled window to main panel
        main_sizer.Add(self.scroll, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
    
    def OnAdd(self, event):
        """Add stamp"""
        if self.main_frame and hasattr(self.main_frame, 'OnAddStamp'):
            self.main_frame.OnAddStamp(event)
    
    def OnUpdate(self, event):
        """Update stamp"""
        if self.main_frame and hasattr(self.main_frame, 'OnUpdateStamp'):
            self.main_frame.OnUpdateStamp(event)
    
    def OnDelete(self, event):
        """Delete stamp"""
        if self.main_frame and hasattr(self.main_frame, 'OnDeleteStamp'):
            self.main_frame.OnDeleteStamp(event)
    
    def OnClear(self, event):
        """Clear form"""
        if self.main_frame and hasattr(self.main_frame, 'OnClearForm'):
            self.main_frame.OnClearForm(event)
    
    def OnBrowse(self, event):
        """Browse for image"""
        if self.main_frame and hasattr(self.main_frame, 'OnBrowseImage'):
            self.main_frame.OnBrowseImage(event)


class StatsPanel(wx.Panel):
    """Statistics panel"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.CreateControls()
        self.DoLayout()
    
    def CreateControls(self):
        """Create statistics controls"""
        self.stats_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.stats_text.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    
    def DoLayout(self):
        """Layout statistics controls"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label="Collection Statistics:"), 0, wx.ALL, 5)
        sizer.Add(self.stats_text, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)


class StampFrame(wx.Frame):
    """Main application frame"""
    
    def __init__(self):
        super().__init__(None, title="Professional Stamp Collection Manager", 
                        size=wx.Size(1200, 800))
        
        # Initialize database
        self.db_manager = DatabaseManager()
        self.search_results = []
        
        self.CreateMenuBar()
        self.CreateStatusBar()
        self.CreateControls()
        self.CreateLayout()
        
        # Load initial data
        self.RefreshStampList()
        
        # Center window
        self.Center()
    
    def CreateMenuBar(self):
        """Create menu bar"""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q")
        
        # Edit menu
        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_ADD, "&Add Stamp\tCtrl+N")
        edit_menu.Append(wx.ID_EDIT, "&Edit Stamp\tCtrl+E")
        edit_menu.Append(wx.ID_DELETE, "&Delete Stamp\tDel")
        
        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "&About")
        
        menubar.Append(file_menu, "&File")
        menubar.Append(edit_menu, "&Edit")
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnMenuAdd, id=wx.ID_ADD)
        self.Bind(wx.EVT_MENU, self.OnMenuEdit, id=wx.ID_EDIT)
        self.Bind(wx.EVT_MENU, self.OnMenuDelete, id=wx.ID_DELETE)
    
    def CreateStatusBar(self):
        """Create status bar"""
        statusbar = super().CreateStatusBar()
        statusbar.SetStatusText("Ready")
        self.statusbar = statusbar
    
    def CreateControls(self):
        """Create main controls"""
        # Create notebook
        self.notebook = wx.Notebook(self)
        
        # Create panels - pass reference to self (main frame)
        self.browse_panel = BrowsePanel(self.notebook, main_frame=self)
        self.edit_panel = EditPanel(self.notebook, main_frame=self)
        self.stats_panel = StatsPanel(self.notebook)
        
        # Add panels to notebook
        self.notebook.AddPage(self.browse_panel, "Browse Collection")
        self.notebook.AddPage(self.edit_panel, "Add/Edit Stamps")
        self.notebook.AddPage(self.stats_panel, "Statistics")
        
        # Bind notebook events
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
    
    def CreateLayout(self):
        """Create main layout"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    # Event handlers
    def OnPageChanged(self, event):
        """Handle notebook page changes"""
        page = event.GetSelection()
        if page == 2:  # Statistics tab
            self.UpdateStatistics()
        elif page == 0:  # Browse tab
            self.RefreshStampList()
    
    def OnSearch(self, event):
        """Perform search"""
        criteria = {
            'description': self.browse_panel.search_desc.GetValue(),
            'scott_number': self.browse_panel.search_scott.GetValue(),
            'country': self.browse_panel.search_country.GetValue(),
            'year_from': '',
            'year_to': '',
            'used_only': self.browse_panel.search_used.GetValue(),
            'want_list': self.browse_panel.search_want.GetValue()
        }
        
        try:
            results = self.db_manager.search_stamps(criteria)
            self.search_results = results
            self.browse_panel.stamp_grid.UpdateData(results)
            self.statusbar.SetStatusText(f"Found {len(results)} stamps")
        except Exception as e:
            wx.MessageBox(f"Search error: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def OnClearSearch(self, event):
        """Clear search and show all stamps"""
        self.browse_panel.search_desc.SetValue("")
        self.browse_panel.search_scott.SetValue("")
        self.browse_panel.search_country.SetValue("")
        self.browse_panel.search_used.SetValue(False)
        self.browse_panel.search_want.SetValue(False)
        self.RefreshStampList()
    
    def RefreshStampList(self):
        """Refresh the stamp list from database"""
        try:
            criteria = {
                'description': '',
                'scott_number': '',
                'country': '',
                'year_from': '',
                'year_to': '',
                'used_only': False,
                'want_list': False
            }
            
            results = self.db_manager.search_stamps(criteria)
            self.search_results = results
            self.browse_panel.stamp_grid.UpdateData(results)
            self.statusbar.SetStatusText(f"Loaded {len(results)} stamps")
            
        except Exception as e:
            wx.MessageBox(f"Error loading stamps: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def UpdateStatistics(self):
        """Update statistics display"""
        try:
            stats = self.db_manager.get_statistics()
            
            stats_text = f"""Collection Statistics:

Total Stamps: {stats['total_stamps']:,}
Used Stamps: {stats['used_stamps']:,}
Mint Stamps: {stats['mint_stamps']:,}
Countries Represented: {stats['countries']}

Financial Summary:
Total Catalog Value: ${stats['total_catalog_value']:,.2f}
Average Value per Stamp: ${stats['average_value']:.2f}

Special Categories:
Want List Items: {stats['want_list_items']}
For Sale Items: {stats['for_sale_items']}
"""
            
            self.stats_panel.stats_text.SetValue(stats_text)
            
        except Exception as e:
            wx.MessageBox(f"Error updating statistics: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def EditSelectedStamp(self, row):
        """Edit selected stamp (switch to edit tab)"""
        if 0 <= row < len(self.search_results):
            stamp_id, stamp = self.search_results[row]
            self.LoadStampToForm(stamp, stamp_id)
            self.notebook.SetSelection(1)  # Switch to edit tab
    
    def LoadStampToForm(self, stamp, stamp_id=None):
        """Load stamp data into form"""
        self.edit_panel.current_stamp_id = stamp_id
        
        self.edit_panel.scott_number.SetValue(stamp.scott_number)
        self.edit_panel.description.SetValue(stamp.description)
        self.edit_panel.country.SetValue(stamp.country or "")
        self.edit_panel.year.SetValue(stamp.year or 2023)
        self.edit_panel.denomination.SetValue(stamp.denomination or "")
        self.edit_panel.color.SetValue(stamp.color or "")
        self.edit_panel.location.SetValue(stamp.location or "")
        self.edit_panel.perforation.SetValue(stamp.perforation or "")
        
        self.edit_panel.condition_grade.SetStringSelection(stamp.condition_grade)
        self.edit_panel.gum_condition.SetStringSelection(stamp.gum_condition)
        
        self.edit_panel.qty_mint.SetValue(stamp.qty_mint or 0)
        self.edit_panel.qty_used.SetValue(stamp.qty_used or 0)
        self.edit_panel.catalog_value_mint.SetValue(f"{stamp.catalog_value_mint:.2f}")
        self.edit_panel.catalog_value_used.SetValue(f"{stamp.catalog_value_used:.2f}")
        
        self.edit_panel.used.SetValue(stamp.used)
        self.edit_panel.plate_block.SetValue(stamp.plate_block)
        self.edit_panel.first_day_cover.SetValue(stamp.first_day_cover)
        self.edit_panel.want_list.SetValue(stamp.want_list)
        self.edit_panel.for_sale.SetValue(stamp.for_sale)
        
        self.edit_panel.purchase_price.SetValue(f"{stamp.purchase_price:.2f}")
        self.edit_panel.current_market_value.SetValue(f"{stamp.current_market_value:.2f}")
        self.edit_panel.source.SetValue(stamp.source or "")
        self.edit_panel.date_acquired.SetValue(stamp.date_acquired or "")
        self.edit_panel.notes.SetValue(stamp.notes or "")
        self.edit_panel.image_path.SetValue(stamp.image_path or "")
    
    def ClearForm(self):
        """Clear all form fields"""
        self.edit_panel.current_stamp_id = None
        
        self.edit_panel.scott_number.SetValue("")
        self.edit_panel.description.SetValue("")
        self.edit_panel.country.SetValue("")
        self.edit_panel.year.SetValue(2023)
        self.edit_panel.denomination.SetValue("")
        self.edit_panel.color.SetValue("")
        self.edit_panel.location.SetValue("")
        self.edit_panel.perforation.SetValue("")
        
        self.edit_panel.condition_grade.SetSelection(0)
        self.edit_panel.gum_condition.SetSelection(0)
        
        self.edit_panel.qty_mint.SetValue(0)
        self.edit_panel.qty_used.SetValue(0)
        self.edit_panel.catalog_value_mint.SetValue("0.00")
        self.edit_panel.catalog_value_used.SetValue("0.00")
        
        self.edit_panel.used.SetValue(False)
        self.edit_panel.plate_block.SetValue(False)
        self.edit_panel.first_day_cover.SetValue(False)
        self.edit_panel.want_list.SetValue(False)
        self.edit_panel.for_sale.SetValue(False)
        
        self.edit_panel.purchase_price.SetValue("0.00")
        self.edit_panel.current_market_value.SetValue("0.00")
        self.edit_panel.source.SetValue("")
        self.edit_panel.date_acquired.SetValue("")
        self.edit_panel.notes.SetValue("")
        self.edit_panel.image_path.SetValue("")
    
    def ValidateForm(self):
        """Validate form fields"""
        if not self.edit_panel.scott_number.GetValue().strip():
            wx.MessageBox("Scott Number is required!", "Validation Error", wx.OK | wx.ICON_ERROR)
            return False
        
        if not self.edit_panel.description.GetValue().strip():
            wx.MessageBox("Description is required!", "Validation Error", wx.OK | wx.ICON_ERROR)
            return False
        
        # Validate numeric fields
        try:
            Decimal(self.edit_panel.catalog_value_used.GetValue())
            Decimal(self.edit_panel.catalog_value_mint.GetValue())
            Decimal(self.edit_panel.purchase_price.GetValue())
            Decimal(self.edit_panel.current_market_value.GetValue())
        except InvalidOperation:
            wx.MessageBox("Invalid numeric value in price fields!", "Validation Error", wx.OK | wx.ICON_ERROR)
            return False
        
        return True
    
    def CreateStampFromForm(self):
        """Create Stamp object from form data"""
        return Stamp(
            scott_number=self.edit_panel.scott_number.GetValue(),
            description=self.edit_panel.description.GetValue(),
            country=self.edit_panel.country.GetValue() or None,
            year=self.edit_panel.year.GetValue() if self.edit_panel.year.GetValue() != 2023 else None,
            denomination=self.edit_panel.denomination.GetValue() or None,
            color=self.edit_panel.color.GetValue() or None,
            condition_grade=self.edit_panel.condition_grade.GetStringSelection(),
            gum_condition=self.edit_panel.gum_condition.GetStringSelection(),
            perforation=self.edit_panel.perforation.GetValue() or None,
            used=self.edit_panel.used.GetValue(),
            plate_block=self.edit_panel.plate_block.GetValue(),
            first_day_cover=self.edit_panel.first_day_cover.GetValue(),
            location=self.edit_panel.location.GetValue() or None,
            notes=self.edit_panel.notes.GetValue() or None,
            qty_mint=self.edit_panel.qty_mint.GetValue(),
            qty_used=self.edit_panel.qty_used.GetValue(),
            catalog_value_mint=Decimal(self.edit_panel.catalog_value_mint.GetValue()),
            catalog_value_used=Decimal(self.edit_panel.catalog_value_used.GetValue()),
            purchase_price=Decimal(self.edit_panel.purchase_price.GetValue()),
            current_market_value=Decimal(self.edit_panel.current_market_value.GetValue()),
            want_list=self.edit_panel.want_list.GetValue(),
            for_sale=self.edit_panel.for_sale.GetValue(),
            date_acquired=self.edit_panel.date_acquired.GetValue() or None,
            source=self.edit_panel.source.GetValue() or None,
            image_path=self.edit_panel.image_path.GetValue() or None
        )
    
    # Button event handlers
    def OnAddStamp(self, event):
        """Add new stamp"""
        if self.ValidateForm():
            try:
                stamp = self.CreateStampFromForm()
                self.db_manager.add_stamp(stamp)
                self.ClearForm()
                self.RefreshStampList()
                wx.MessageBox("Stamp added successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                self.statusbar.SetStatusText("Stamp added successfully")
            except Exception as e:
                wx.MessageBox(f"Error adding stamp: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def OnUpdateStamp(self, event):
        """Update existing stamp"""
        if not self.edit_panel.current_stamp_id:
            wx.MessageBox("No stamp selected!", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        if self.ValidateForm():
            try:
                stamp = self.CreateStampFromForm()
                self.db_manager.update_stamp(self.edit_panel.current_stamp_id, stamp)
                self.ClearForm()
                self.RefreshStampList()
                wx.MessageBox("Stamp updated successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                self.statusbar.SetStatusText("Stamp updated successfully")
            except Exception as e:
                wx.MessageBox(f"Error updating stamp: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def OnDeleteStamp(self, event):
        """Delete selected stamp"""
        if not self.edit_panel.current_stamp_id:
            wx.MessageBox("No stamp selected!", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        dlg = wx.MessageDialog(self, "Are you sure you want to delete this stamp?", 
                              "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION)
        
        if dlg.ShowModal() == wx.ID_YES:
            try:
                self.db_manager.delete_stamp(self.edit_panel.current_stamp_id)
                self.ClearForm()
                self.RefreshStampList()
                wx.MessageBox("Stamp deleted successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                self.statusbar.SetStatusText("Stamp deleted successfully")
            except Exception as e:
                wx.MessageBox(f"Error deleting stamp: {e}", "Error", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
    
    def OnClearForm(self, event):
        """Clear form fields"""
        self.ClearForm()
    
    def OnBrowseImage(self, event):
        """Browse for image file"""
        wildcard = "Image files (*.jpg;*.jpeg;*.png;*.gif)|*.jpg;*.jpeg;*.png;*.gif"
        dlg = wx.FileDialog(self, "Choose image file", wildcard=wildcard, style=wx.FD_OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.edit_panel.image_path.SetValue(dlg.GetPath())
        
        dlg.Destroy()
    
    # Menu event handlers
    def OnMenuAdd(self, event):
        """Handle Add menu item"""
        self.notebook.SetSelection(1)  # Switch to edit tab
        self.ClearForm()
    
    def OnMenuEdit(self, event):
        """Handle Edit menu item"""
        selected_row = self.browse_panel.stamp_grid.GetGridCursorRow()
        if selected_row >= 0:
            self.EditSelectedStamp(selected_row)
        else:
            wx.MessageBox("Please select a stamp to edit", "No Selection", wx.OK | wx.ICON_INFORMATION)
    
    def OnMenuDelete(self, event):
        """Handle Delete menu item"""
        selected_row = self.browse_panel.stamp_grid.GetGridCursorRow()
        if selected_row >= 0:
            self.EditSelectedStamp(selected_row)
            self.OnDeleteStamp(event)
        else:
            wx.MessageBox("Please select a stamp to delete", "No Selection", wx.OK | wx.ICON_INFORMATION)
    
    def OnExit(self, event):
        """Handle exit menu"""
        self.Close()
    
    def OnAbout(self, event):
        """Show about dialog"""
        info = wx.adv.AboutDialogInfo()
        info.SetName("Professional Stamp Collection Manager")
        info.SetVersion("2.0")
        info.SetDescription("A comprehensive stamp collection management application built with wxPython.\n\n" +
                           "Features:\n" +
                           "• Complete stamp catalog management\n" +
                           "• Advanced search and filtering\n" +
                           "• Collection statistics\n" +
                           "• SQLite database backend\n" +
                           "• Import/Export capabilities")
        info.SetCopyright("(C) 2024")
        info.AddDeveloper("Stamp Collection Manager Team")
        info.SetWebSite("https://github.com/your-repo/stamp-manager")
        
        wx.adv.AboutBox(info)


class StampApp(wx.App):
    """Main application class"""
    
    def OnInit(self):
        """Initialize application"""
        try:
            frame = StampFrame()
            frame.Show()
            return True
        except Exception as e:
            wx.MessageBox(f"Error starting application: {e}", "Startup Error", wx.OK | wx.ICON_ERROR)
            return False


# For compatibility with the main.py import
def main():
    """Main entry point"""
    app = StampApp()
    app.MainLoop()


if __name__ == "__main__":
    main()