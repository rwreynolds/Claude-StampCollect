# database_manager.py
import sqlite3
import os
from datetime import datetime
from decimal import Decimal
from enhanced_stamp import Stamp, StampCollection
from typing import List, Tuple, Dict, Optional, Any

class DatabaseManager:
    def __init__(self, db_path: str = "stamps.db"):
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stamps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scott_number TEXT NOT NULL,
                description TEXT NOT NULL,
                country TEXT,
                year INTEGER,
                denomination TEXT,
                color TEXT,
                condition_grade TEXT,
                gum_condition TEXT,
                perforation TEXT,
                used BOOLEAN,
                plate_block BOOLEAN,
                first_day_cover BOOLEAN,
                location TEXT,
                notes TEXT,
                qty_mint INTEGER,
                qty_used INTEGER,
                catalog_value_mint DECIMAL(10,2),
                catalog_value_used DECIMAL(10,2),
                purchase_price DECIMAL(10,2),
                current_market_value DECIMAL(10,2),
                want_list BOOLEAN,
                for_sale BOOLEAN,
                date_acquired DATE,
                source TEXT,
                image_path TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_collection(self) -> StampCollection:
        """Load all stamps from database"""
        collection = StampCollection()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM stamps')
        rows = cursor.fetchall()
        
        for row in rows:
            stamp = self._create_stamp_from_row(row)
            collection.add_stamp(stamp)
        
        conn.close()
        return collection
    
    def add_stamp(self, stamp: Stamp) -> int:
        """Add a stamp to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO stamps (
                scott_number, description, country, year, denomination,
                color, condition_grade, gum_condition, perforation,
                used, plate_block, first_day_cover, location, notes,
                qty_mint, qty_used, catalog_value_mint, catalog_value_used,
                purchase_price, current_market_value, want_list, for_sale,
                date_acquired, source, image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', self._stamp_to_tuple(stamp))
        
        stamp_id = cursor.lastrowid
        if stamp_id is None:
            raise ValueError("Failed to get ID of inserted stamp")
            
        conn.commit()
        conn.close()
        return stamp_id
    
    def update_stamp(self, stamp_id: int, stamp: Stamp):
        """Update existing stamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        values = self._stamp_to_tuple(stamp) + (stamp_id,)
        cursor.execute('''
            UPDATE stamps SET
                scott_number=?, description=?, country=?, year=?, denomination=?,
                color=?, condition_grade=?, gum_condition=?, perforation=?,
                used=?, plate_block=?, first_day_cover=?, location=?, notes=?,
                qty_mint=?, qty_used=?, catalog_value_mint=?, catalog_value_used=?,
                purchase_price=?, current_market_value=?, want_list=?, for_sale=?,
                date_acquired=?, source=?, image_path=?
            WHERE id=?
        ''', values)
        
        conn.commit()
        conn.close()
    
    def delete_stamp(self, stamp_id: int):
        """Delete stamp from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM stamps WHERE id=?', (stamp_id,))
        conn.commit()
        conn.close()
    
    def search_stamps(self, criteria: Dict) -> List[Tuple[int, Stamp]]:
        """Search stamps based on criteria"""
        conditions = []
        params = []
        
        if criteria['description']:
            conditions.append('description LIKE ?')
            params.append(f"%{criteria['description']}%")
        if criteria['scott_number']:
            conditions.append('scott_number LIKE ?')
            params.append(f"%{criteria['scott_number']}%")
        if criteria['country']:
            conditions.append('country LIKE ?')
            params.append(f"%{criteria['country']}%")
        if criteria['year_from']:
            conditions.append('year >= ?')
            params.append(int(criteria['year_from']))
        if criteria['year_to']:
            conditions.append('year <= ?')
            params.append(int(criteria['year_to']))
        if criteria['used_only']:
            conditions.append('used = 1')
        if criteria['want_list']:
            conditions.append('want_list = 1')
        
        query = 'SELECT * FROM stamps'
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            stamp_id = row[0]
            stamp = self._create_stamp_from_row(row)
            results.append((stamp_id, stamp))
        
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        """Get collection statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_stamps': 0,
            'used_stamps': 0,
            'mint_stamps': 0,
            'countries': 0,
            'total_catalog_value': Decimal('0.00'),
            'average_value': Decimal('0.00'),
            'want_list_items': 0,
            'for_sale_items': 0
        }
        
        # Get basic counts
        cursor.execute('SELECT COUNT(*) FROM stamps')
        stats['total_stamps'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM stamps WHERE used=1')
        stats['used_stamps'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT country) FROM stamps')
        stats['countries'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM stamps WHERE want_list=1')
        stats['want_list_items'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM stamps WHERE for_sale=1')
        stats['for_sale_items'] = cursor.fetchone()[0]
        
        # Calculate mint stamps
        stats['mint_stamps'] = stats['total_stamps'] - stats['used_stamps']
        
        # Calculate total value - fixed calculation
        cursor.execute('''
            SELECT 
                SUM(CASE 
                    WHEN used=1 THEN catalog_value_used * qty_used
                    ELSE catalog_value_mint * qty_mint
                END)
            FROM stamps
        ''')
        total_value = cursor.fetchone()[0] or 0
        stats['total_catalog_value'] = Decimal(str(total_value))
        
        # Calculate average value
        if stats['total_stamps'] > 0:
            stats['average_value'] = stats['total_catalog_value'] / stats['total_stamps']
        
        conn.close()
        return stats

    def _stamp_to_tuple(self, stamp: Stamp) -> tuple:
        """Convert Stamp object to tuple for database operations"""
        return (
            stamp.scott_number, stamp.description, stamp.country, stamp.year,
            stamp.denomination, stamp.color, stamp.condition_grade,
            stamp.gum_condition, stamp.perforation, stamp.used,
            stamp.plate_block, stamp.first_day_cover, stamp.location,
            stamp.notes, stamp.qty_mint, stamp.qty_used,
            float(stamp.catalog_value_mint), float(stamp.catalog_value_used),
            float(stamp.purchase_price), float(stamp.current_market_value),
            stamp.want_list, stamp.for_sale, stamp.date_acquired,
            stamp.source, stamp.image_path
        )
    
    def _create_stamp_from_row(self, row: tuple) -> Stamp:
        """Create Stamp object from database row"""
        try:
            return Stamp(
                scott_number=str(row[1] or ''),
                description=str(row[2] or ''),
                country=row[3] if row[3] is not None else None,  # Fixed: don't convert None to string
                year=int(row[4]) if row[4] else None,
                denomination=row[5] if row[5] is not None else None,  # Fixed: don't convert None to string
                color=row[6] if row[6] is not None else None,  # Fixed: don't convert None to string
                condition_grade=str(row[7] or 'Unknown'),
                gum_condition=str(row[8] or 'Unknown'),
                perforation=row[9] if row[9] is not None else None,  # Fixed: don't convert None to string
                used=bool(row[10]),
                plate_block=bool(row[11]),
                first_day_cover=bool(row[12]),
                location=row[13] if row[13] is not None else None,  # Fixed: don't convert None to string
                notes=row[14] if row[14] is not None else None,  # Fixed: don't convert None to string
                qty_mint=int(row[15] or 0),
                qty_used=int(row[16] or 0),
                catalog_value_mint=Decimal(str(row[17] or '0.00')),
                catalog_value_used=Decimal(str(row[18] or '0.00')),
                purchase_price=Decimal(str(row[19] or '0.00')),
                current_market_value=Decimal(str(row[20] or '0.00')),
                want_list=bool(row[21]),
                for_sale=bool(row[22]),
                date_acquired=row[23] if row[23] is not None else None,  # Fixed: don't convert None to string
                source=row[24] if row[24] is not None else None,  # Fixed: don't convert None to string
                image_path=row[25] if row[25] is not None else None  # Fixed: don't convert None to string
            )
        except Exception as e:
            print(f"Error creating stamp from row: {e}")
            raise