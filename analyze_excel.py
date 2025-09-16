#!/usr/bin/env python3
"""
Excel spreadsheet analysis for Planner Calendar Application
"""
import os
import sys
import subprocess
from typing import Dict, List, Any

def install_package(package: str) -> bool:
    """Install a package if not available"""
    try:
        __import__(package)
        print(f"✓ {package} is available")
        return True
    except ImportError:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ Installed {package}")
            return True
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            return False

def analyze_excel_structure(excel_path: str) -> Dict[str, Any]:
    """Analyze Excel file structure and return detailed information"""
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        return {}
    
    # Ensure required packages are installed
    required_packages = ['pandas', 'openpyxl']
    for package in required_packages:
        if not install_package(package):
            return {}
    
    try:
        import pandas as pd
        from datetime import datetime
        
        print(f"\n📊 Analyzing Excel File: {excel_path}")
        print(f"📁 File size: {os.path.getsize(excel_path):,} bytes")
        print("=" * 80)
        
        excel_file = pd.ExcelFile(excel_path)
        analysis_results = {
            'file_path': excel_path,
            'sheets': {},
            'total_sheets': len(excel_file.sheet_names),
            'sheet_names': excel_file.sheet_names
        }
        
        print(f"📋 Found {len(excel_file.sheet_names)} sheet(s): {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- 📄 SHEET: {sheet_name} ---")
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # Basic sheet info
            sheet_info = {
                'name': sheet_name,
                'shape': df.shape,
                'columns': list(df.columns),
                'data_types': dict(df.dtypes.astype(str)),
                'date_columns': [],
                'status_columns': [],
                'action_columns': [],
                'department_columns': [],
                'sample_data': {}
            }
            
            print(f"📐 Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"📝 Columns: {list(df.columns)}")
            
            # Identify special columns
            for col in df.columns:
                # Handle cases where column names might be datetime objects or other types
                try:
                    col_str = str(col)
                    col_lower = col_str.lower()
                except:
                    col_str = str(col)
                    col_lower = col_str.lower()
                
                # Date columns - check both column name and data type
                if (df[col].dtype == 'datetime64[ns]' or 
                    isinstance(col, pd.Timestamp) or
                    any(keyword in col_lower for keyword in ['date', 'due', 'start', 'end', 'deadline', 'time'])):
                    sheet_info['date_columns'].append(col)
                
                # Status columns
                if any(keyword in col_lower for keyword in ['status', 'state', 'progress', 'phase', 'condition']):
                    sheet_info['status_columns'].append(col)
                
                # Action columns
                if any(keyword in col_lower for keyword in ['action', 'next', 'step', 'todo', 'task', 'decision']):
                    sheet_info['action_columns'].append(col)
                
                # Department columns
                if any(keyword in col_lower for keyword in ['department', 'dept', 'team', 'owner', 'responsible', 'assigned', 'accountable']):
                    sheet_info['department_columns'].append(col)
            
            # Print identified columns
            if sheet_info['date_columns']:
                print(f"📅 Date columns: {sheet_info['date_columns']}")
            if sheet_info['status_columns']:
                print(f"📊 Status columns: {sheet_info['status_columns']}")
            if sheet_info['action_columns']:
                print(f"✅ Action columns: {sheet_info['action_columns']}")
            if sheet_info['department_columns']:
                print(f"🏢 Department columns: {sheet_info['department_columns']}")
            
            # Sample data for non-empty sheets
            if not df.empty:
                print(f"\n📋 Sample Data (first 3 rows):")
                sample_df = df.head(3)
                for col in df.columns[:6]:  # Show first 6 columns max
                    if col in sample_df.columns:
                        values = sample_df[col].tolist()
                        sheet_info['sample_data'][col] = values
                        print(f"  {col}: {values}")
                
                if len(df.columns) > 6:
                    print(f"  ... and {len(df.columns) - 6} more columns")
            
            analysis_results['sheets'][sheet_name] = sheet_info
            print("-" * 50)
        
        print(f"\n✅ Analysis Complete!")
        print(f"📊 Summary:")
        print(f"  • Total sheets: {analysis_results['total_sheets']}")
        print(f"  • Total rows: {sum(info['shape'][0] for info in analysis_results['sheets'].values())}")
        print(f"  • Total columns: {sum(info['shape'][1] for info in analysis_results['sheets'].values())}")
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ Error analyzing Excel file: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    """Main analysis function"""
    print("🚀 Planner Calendar Application - Excel Analysis")
    print("=" * 60)
    
    excel_path = "/Users/jeffjackson/Desktop/Planner/Ascent Planner Sep, 16 2025.xlsx"
    results = analyze_excel_structure(excel_path)
    
    if results:
        print(f"\n🎯 Ready to build calendar application with this data structure!")
        return results
    else:
        print(f"\n❌ Could not analyze Excel file. Please check the file path and format.")
        return None

if __name__ == "__main__":
    main()
