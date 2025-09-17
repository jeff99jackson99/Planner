#!/usr/bin/env python3
"""
SharePoint Live Data Connector for Ascent Planner Calendar
"""
import pandas as pd
import requests
import streamlit as st
from typing import Dict, Optional
import io
import os
from datetime import datetime

class SharePointConnector:
    def __init__(self):
        self.sharepoint_url = None
        self.last_update = None
        self.cache_duration = 300  # 5 minutes cache
        
    def set_sharepoint_url(self, url: str) -> bool:
        """Set the SharePoint URL for live data feed"""
        try:
            # Extract the file ID from SharePoint URL
            if "sourcedoc=" in url:
                # This is a SharePoint share URL
                self.sharepoint_url = url
                return True
            else:
                st.error("Invalid SharePoint URL format")
                return False
        except Exception as e:
            st.error(f"Error setting SharePoint URL: {e}")
            return False
    
    def get_live_data(self) -> Optional[Dict[str, pd.DataFrame]]:
        """Get live data from SharePoint Excel file"""
        try:
            # For now, we'll use a simulated approach since SharePoint requires complex auth
            st.info("Live SharePoint connection requires authentication setup")
            
            # Alternative approaches for live data:
            return self._get_alternative_live_data()
            
        except Exception as e:
            st.error(f"Error connecting to SharePoint: {e}")
            return None
    
    def _get_alternative_live_data(self) -> Optional[Dict[str, pd.DataFrame]]:
        """Alternative methods for live data access"""
        
        # Method 1: Check if local file is updated
        local_file = "/Users/jeffjackson/Desktop/Planner/Ascent Planner Sep, 16 2025.xlsx"
        
        if os.path.exists(local_file):
            # Check if file has been modified recently
            file_mod_time = os.path.getmtime(local_file)
            current_time = datetime.now().timestamp()
            
            # If file was modified in last 5 minutes, consider it "live"
            if current_time - file_mod_time < 300:  # 5 minutes
                st.success("Using recently updated local file (Live data)")
            else:
                st.info("Using local file (Last updated: " + 
                       datetime.fromtimestamp(file_mod_time).strftime("%Y-%m-%d %H:%M:%S") + ")")
            
            # Load the Excel file
            try:
                excel_file = pd.ExcelFile(local_file)
                data = {}
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(local_file, sheet_name=sheet_name)
                    data[sheet_name] = df
                
                self.last_update = datetime.now()
                return data
                
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
                return None
        
        return None
    
    def setup_live_feed_instructions(self):
        """Show instructions for setting up live SharePoint feed"""
        st.markdown("""
        <div class="data-card">
            <h4>SharePoint Live Feed Setup</h4>
            <p><strong>Current URL:</strong> https://shivohm.sharepoint.com/.../Ascent Planner</p>
            
            <h5>Setup Options:</h5>
            <ol>
                <li><strong>SharePoint Sync:</strong> Sync the SharePoint file to local folder for auto-updates</li>
                <li><strong>Power Automate:</strong> Set up automatic export from SharePoint to accessible location</li>
                <li><strong>OneDrive Sync:</strong> Sync SharePoint to OneDrive, then access locally</li>
                <li><strong>API Access:</strong> Configure SharePoint API with proper authentication</li>
            </ol>
            
            <h5>Current Status:</h5>
            <p>✅ Application monitors local file for changes</p>
            <p>✅ Shows last update timestamp</p>
            <p>✅ Detects recent modifications as "live" data</p>
            <p>⚠️ SharePoint direct access requires authentication setup</p>
        </div>
        """, unsafe_allow_html=True)

# Global connector instance
sharepoint_connector = SharePointConnector()
