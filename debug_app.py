#!/usr/bin/env python3
"""
Debug version of the Planner Calendar Application
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

st.set_page_config(
    page_title="Ascent Planner Debug",
    page_icon="📅",
    layout="wide"
)

def main():
    st.title("📅 Ascent Planner Calendar - Debug Mode")
    st.write("Testing basic functionality...")
    
    # Test 1: Check if we can load basic Streamlit components
    st.success("✅ Streamlit is working!")
    
    # Test 2: Check Excel file
    excel_path = "Ascent Planner Sep, 16 2025.xlsx"
    if os.path.exists(excel_path):
        st.success(f"✅ Excel file found: {excel_path}")
        
        try:
            # Test 3: Try to load Excel data
            excel_file = pd.ExcelFile(excel_path)
            st.success(f"✅ Excel file loaded with {len(excel_file.sheet_names)} sheets")
            
            # Show sheet names
            st.write("**Sheet names:**")
            for i, sheet_name in enumerate(excel_file.sheet_names, 1):
                st.write(f"{i}. {sheet_name}")
            
            # Test 4: Try to load first sheet
            first_sheet = excel_file.sheet_names[0]
            df = pd.read_excel(excel_path, sheet_name=first_sheet)
            st.success(f"✅ Successfully loaded '{first_sheet}' with {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Show sample data
            st.write(f"**Sample data from {first_sheet}:**")
            st.dataframe(df.head(3))
            
        except Exception as e:
            st.error(f"❌ Error loading Excel data: {e}")
            st.write("**Full error:**")
            st.code(str(e))
    else:
        st.error(f"❌ Excel file not found: {excel_path}")
        st.write("**Current directory:**", os.getcwd())
        st.write("**Files in current directory:**")
        try:
            files = os.listdir(".")
            for file in sorted(files):
                st.write(f"- {file}")
        except Exception as e:
            st.error(f"Error listing files: {e}")
    
    # Test 5: Check imports
    st.write("**Testing imports:**")
    try:
        import plotly.express as px
        st.success("✅ Plotly imported successfully")
    except Exception as e:
        st.error(f"❌ Plotly import failed: {e}")
    
    try:
        from datetime import datetime, timedelta
        st.success("✅ Datetime imported successfully")
        st.write(f"Current date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        st.error(f"❌ Datetime import failed: {e}")
    
    # Test 6: Basic Streamlit widgets
    st.write("**Testing Streamlit widgets:**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Test Metric", "42", "↑ 5%")
    with col2:
        st.button("Test Button")
    with col3:
        st.selectbox("Test Select", ["Option 1", "Option 2"])
    
    # Show system info
    st.write("**System Information:**")
    st.write(f"- Python version: {pd.__version__}")
    st.write(f"- Pandas version: {pd.__version__}")
    st.write(f"- Current working directory: {os.getcwd()}")
    st.write(f"- Streamlit version: {st.__version__}")

if __name__ == "__main__":
    main()
