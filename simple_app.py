#!/usr/bin/env python3
"""
Simple version of the Planner Calendar Application for testing
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

st.set_page_config(
    page_title="Ascent Planner - Simple",
    page_icon="📅",
    layout="wide"
)

def main():
    st.title("📅 Ascent Planner Calendar - Simple Version")
    st.write("Testing basic functionality...")
    
    # Show current status
    st.success("✅ Streamlit is working!")
    st.write(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"Current directory: {os.getcwd()}")
    
    # Look for Excel file
    excel_files = [f for f in os.listdir(".") if f.endswith(('.xlsx', '.xls'))]
    
    if excel_files:
        st.success(f"✅ Found {len(excel_files)} Excel file(s):")
        for f in excel_files:
            st.write(f"- {f}")
        
        # Try to load the first Excel file
        excel_path = excel_files[0]
        try:
            st.info(f"Loading: {excel_path}")
            excel_file = pd.ExcelFile(excel_path)
            st.success(f"✅ Successfully loaded Excel file with {len(excel_file.sheet_names)} sheets")
            
            # Show sheets
            st.write("**Available sheets:**")
            for i, sheet_name in enumerate(excel_file.sheet_names, 1):
                st.write(f"{i}. {sheet_name}")
            
            # Load first sheet as sample
            first_sheet = excel_file.sheet_names[0]
            df = pd.read_excel(excel_path, sheet_name=first_sheet)
            
            st.write(f"**Sample from '{first_sheet}':**")
            st.write(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Show basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sheets", len(excel_file.sheet_names))
            with col2:
                st.metric("Rows in Main Sheet", df.shape[0])
            with col3:
                st.metric("Columns in Main Sheet", df.shape[1])
            
            # Show sample data
            if not df.empty:
                st.dataframe(df.head(5), use_container_width=True)
            
            # Basic analysis
            st.subheader("📊 Quick Analysis")
            
            # Look for date columns
            date_columns = []
            for col in df.columns:
                if 'date' in str(col).lower() or 'start' in str(col).lower():
                    date_columns.append(col)
            
            if date_columns:
                st.write("**Date columns found:**")
                for col in date_columns:
                    st.write(f"- {col}")
            
            # Look for status columns
            status_columns = []
            for col in df.columns:
                if 'status' in str(col).lower():
                    status_columns.append(col)
            
            if status_columns:
                st.write("**Status columns found:**")
                for col in status_columns:
                    st.write(f"- {col}")
                    if col in df.columns:
                        status_counts = df[col].value_counts()
                        st.write(f"  Status distribution:")
                        for status, count in status_counts.head().items():
                            if pd.notna(status):
                                st.write(f"    - {status}: {count}")
            
        except Exception as e:
            st.error(f"❌ Error loading Excel file: {e}")
            st.code(str(e))
    else:
        st.error("❌ No Excel files found in current directory")
        st.write("**All files in directory:**")
        try:
            all_files = os.listdir(".")
            for f in sorted(all_files):
                st.write(f"- {f}")
        except Exception as e:
            st.error(f"Error listing files: {e}")

if __name__ == "__main__":
    main()
