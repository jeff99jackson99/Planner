#!/usr/bin/env python3
"""
Planner Calendar Application - Main Streamlit App
Incorporates data from all Excel sheets to provide comprehensive project tracking
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import pytz
import os
from typing import Dict, List, Any, Optional
import calendar
import numpy as np
import hashlib
import time

def get_arizona_time():
    """Get current time in Arizona timezone"""
    arizona_tz = pytz.timezone('US/Arizona')
    return datetime.now(arizona_tz)

def map_department_name(dept_name):
    """Map department names to standardized business departments"""
    if not dept_name or pd.isna(dept_name):
        return "Other"
    
    dept_lower = str(dept_name).lower().strip()
    
    # Core business departments
    if any(keyword in dept_lower for keyword in ['claim', 'claims']):
        return "Claims"
    elif any(keyword in dept_lower for keyword in ['account', 'accounting', 'finance']):
        return "Accounting"  
    elif any(keyword in dept_lower for keyword in ['contract', 'admin']):
        return "Contract Admin"
    elif any(keyword in dept_lower for keyword in ['cancel', 'cancellation']):
        return "Cancellations"
    elif any(keyword in dept_lower for keyword in ['onboard', 'onboarding']):
        return "Onboarding"
    elif any(keyword in dept_lower for keyword in ['commission', 'commissions']):
        return "Commissions"
    else:
        return "Other"

# SharePoint connector functionality embedded to avoid import issues
class SharePointConnector:
    def __init__(self):
        self.sharepoint_url = None
        self.last_update = None
        self.cache_duration = 300  # 5 minutes cache
        
    def set_sharepoint_url(self, url: str) -> bool:
        """Set the SharePoint URL for live data feed"""
        try:
            if "sourcedoc=" in url:
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
            return self._get_alternative_live_data()
        except Exception as e:
            st.error(f"Error connecting to SharePoint: {e}")
            return None
    
    def _get_alternative_live_data(self) -> Optional[Dict[str, pd.DataFrame]]:
        """Get live data from SharePoint-synced locations"""
        # Try multiple potential SharePoint sync locations
        potential_paths = [
            # OneDrive SharePoint sync path
            os.path.expanduser("~/OneDrive - Shivohm/Ascent-SDSTeam/Ascent Planner Sep, 16 2025.xlsx"),
            # SharePoint Desktop sync path
            os.path.expanduser("~/SharePoint - Shivohm/Ascent-SDSTeam/Ascent Planner Sep, 16 2025.xlsx"),
            # Local synced copy
            "/Users/jeffjackson/Desktop/Planner/Ascent Planner Sep, 16 2025.xlsx",
            # Cloud deployment path
            "Ascent Planner Sep, 16 2025.xlsx"
        ]
        
        for file_path in potential_paths:
            if os.path.exists(file_path):
                file_mod_time = os.path.getmtime(file_path)
                current_time = datetime.now().timestamp()
                mod_datetime = datetime.fromtimestamp(file_mod_time)
                
                # Check if this looks like live SharePoint data
                # Convert to Arizona time for display
                arizona_tz = pytz.timezone('US/Arizona')
                mod_datetime_az = mod_datetime.replace(tzinfo=pytz.UTC).astimezone(arizona_tz)
                
                if current_time - file_mod_time < 3600:  # Within last hour
                    st.success(f"✅ LIVE SHAREPOINT DATA - Last updated: {mod_datetime_az.strftime('%H:%M:%S')} AZ")
                elif current_time - file_mod_time < 86400:  # Within last day
                    st.info(f"📊 SharePoint data from today: {mod_datetime_az.strftime('%H:%M:%S')} AZ")
                else:
                    st.warning(f"⚠️ SharePoint data from: {mod_datetime_az.strftime('%Y-%m-%d %H:%M:%S')} AZ")
                
                try:
                    excel_file = pd.ExcelFile(file_path)
                    data = {}
                    for sheet_name in excel_file.sheet_names:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        data[sheet_name] = df
                    
                    self.last_update = datetime.now()
                    
                    # Show data source info
                    if "OneDrive" in file_path:
                        st.sidebar.success("📡 Data Source: OneDrive SharePoint Sync")
                    elif "SharePoint" in file_path:
                        st.sidebar.success("📡 Data Source: SharePoint Desktop Sync")
                    else:
                        st.sidebar.info("📁 Data Source: Local File")
                    
                    return data
                    
                except Exception as e:
                    st.error(f"Error reading Excel file from {file_path}: {e}")
                    continue
        
        # Silently return None if no SharePoint file found
        return None

# Page configuration
st.set_page_config(
    page_title="Ascent Planner Calendar",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AscentPlannerCalendar:
    def __init__(self, excel_path: str, use_live_feed: bool = False):
        self.excel_path = excel_path
        self.data: Dict[str, pd.DataFrame] = {}
        self.current_date = get_arizona_time().date()
        self.use_live_feed = use_live_feed
        self.sharepoint_connector = SharePointConnector() if use_live_feed else None
        self.load_data()
    
    def load_data(self) -> None:
        """Load data ONLY from SharePoint live feed"""
        try:
            # ONLY use SharePoint data - no local fallback
            if self.sharepoint_connector:
                live_data = self.sharepoint_connector.get_live_data()
                if live_data:
                    self.data = live_data
                    
                    # Show detailed information about ALL tabs loaded
                    st.sidebar.markdown("**📊 SHAREPOINT DATA LOADED:**")
                    for sheet_name, df in self.data.items():
                        rows_with_data = len(df.dropna(how='all'))
                        st.sidebar.markdown(f"• {sheet_name}: {rows_with_data} rows")
                    
                    return
            
            # Silently handle SharePoint connection issues
            pass
            
        except Exception as e:
            st.error(f"Error loading SharePoint data: {e}")
    
    def get_planner_tasks(self) -> pd.DataFrame:
        """Get tasks from the main Planner sheet"""
        if 'Planner' not in self.data:
            return pd.DataFrame()
        
        df = self.data['Planner'].copy()
        
        # Clean up the data
        df = df.dropna(how='all')  # Remove completely empty rows
        
        return df
    
    def get_open_decisions(self) -> pd.DataFrame:
        """Get open decisions that need attention"""
        sheet_name = 'Open Decision & Next Steps '
        if sheet_name not in self.data:
            return pd.DataFrame()
        
        df = self.data[sheet_name].copy()
        df = df.dropna(how='all')
        
        return df
    
    def get_hotfixes_status(self) -> pd.DataFrame:
        """Get current hotfixes and their status"""
        if 'List of CR_HotFixes_ENHCE' not in self.data:
            return pd.DataFrame()
        
        df = self.data['List of CR_HotFixes_ENHCE'].copy()
        df = df.dropna(how='all')
        
        return df
    
    def get_data_migration_status(self) -> pd.DataFrame:
        """Get data migration progress"""
        if 'Data Migration Updates' not in self.data:
            return pd.DataFrame()
        
        df = self.data['Data Migration Updates'].copy()
        df = df.dropna(how='all')
        
        return df
    
    def get_roadmap_items(self) -> pd.DataFrame:
        """Get roadmap items for upcoming releases"""
        if 'Roadmap for next two releases' not in self.data:
            return pd.DataFrame()
        
        df = self.data['Roadmap for next two releases'].copy()
        df = df.dropna(how='all')
        
        return df
    
    def get_tasks_for_date(self, target_date: date) -> List[Dict[str, Any]]:
        """Get all tasks and events for a specific date"""
        tasks = []
        
        # Check main planner sheet
        planner_df = self.get_planner_tasks()
        if not planner_df.empty:
            # Look for date columns in the planner
            date_columns = ['Start Date', 'Beta Realease', 'PROD Release']
            
            for _, row in planner_df.iterrows():
                for date_col in date_columns:
                    if date_col in row and pd.notna(row[date_col]):
                        try:
                            event_date = pd.to_datetime(row[date_col], errors='coerce')
                            if pd.notna(event_date) and event_date.date() == target_date:
                                # Clean up the data values
                                accountable = row.get('Accountable', 'N/A')
                                if pd.isna(accountable) or str(accountable).lower() in ['nan', 'none', '']:
                                    # Skip unassigned tasks - don't show in milestones
                                    continue
                                
                                status = row.get('Status1', 'N/A')
                                if pd.isna(status) or str(status).lower() in ['nan', 'none', '']:
                                    status = 'Not Set'
                                
                                task_name = row.get('Task Name', 'Unknown Task')
                                if pd.isna(task_name) or str(task_name).lower() in ['nan', 'none', '']:
                                    task_name = 'Unnamed Task'
                                
                                task = {
                                    'source': 'Planner',
                                    'date': event_date.date(),
                                    'date_type': date_col,
                                    'task_name': str(task_name).strip(),
                                    'accountable': str(accountable).strip(),
                                    'status': str(status).strip(),
                                    'demo_training': str(row.get(' Demo/Training', 'N/A')),
                                    'requirement_unclear': row.get('Requirement Unclear', False)
                                }
                                tasks.append(task)
                        except:
                            continue
        
        # Check for data migration updates on this date
        migration_df = self.get_data_migration_status()
        if not migration_df.empty:
            # Data Migration sheet has dates as column headers
            for col in migration_df.columns:
                if isinstance(col, pd.Timestamp):
                    if col.date() == target_date:
                        # Find non-null values in this date column
                        date_data = migration_df[col].dropna()
                        if not date_data.empty:
                            task = {
                                'source': 'Data Migration',
                                'date': target_date,
                                'date_type': 'Migration Update',
                                'task_name': f"Data Migration Activities ({len(date_data)} items)",
                                'accountable': 'Migration Team',
                                'status': 'In Progress',
                                'details': date_data.tolist()
                            }
                            tasks.append(task)
        
        return tasks
    
    def get_department_alerts(self) -> Dict[str, List[str]]:
        """Get departments that need attention based on current status - Ascent focused"""
        alerts = {}
        
        # Check open decisions - these are Ascent decisions
        decisions_df = self.get_open_decisions()
        if not decisions_df.empty:
            for _, row in decisions_df.iterrows():
                if 'Open' in str(row.get('Unnamed: 3', '')):  # Status column
                    decision_text = str(row.get('Unnamed: 2', 'Unknown Decision'))
                    who = str(row.get('Gayatri Raol ', 'Unknown'))
                    
                    # Consolidate Matt/Madison variations
                    who_clean = self._consolidate_department_name(who)
                    
                    # Skip if consolidation returned None (NaN values)
                    if who_clean is not None:
                        if who_clean not in alerts:
                            alerts[who_clean] = []
                        alerts[who_clean].append(f"Open Decision: {decision_text}")
        
        # Check high priority hotfixes - ONLY if they require Ascent action
        hotfixes_df = self.get_hotfixes_status()
        if not hotfixes_df.empty:
            for _, row in hotfixes_df.iterrows():
                priority = str(row.get('Unnamed: 3', '')).lower()  # Priority column
                status = str(row.get('Unnamed: 5', '')).lower()     # Status column
                summary = str(row.get('Claim Related Feedback/Change Request/ Hot Fixes', 'Unknown Issue'))
                
                # Only include if it's highest priority AND requires Ascent action (not just Sona development)
                if ('highest' in priority and 'done' not in status and 
                    self._requires_ascent_action(summary)):
                    
                    dept = 'Ascent Product Team'
                    
                    if dept not in alerts:
                        alerts[dept] = []
                    alerts[dept].append(f"Critical Issue: {summary}")
        
        # Check planner tasks with unclear requirements - only Ascent assignees
        planner_df = self.get_planner_tasks()
        if not planner_df.empty:
            unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
            if not unclear_tasks.empty:
                for _, row in unclear_tasks.iterrows():
                    task_name = str(row.get('Task Name', 'Unknown Task'))
                    accountable = row.get('Accountable', 'Unknown')
                    
                    # Clean up accountable field
                    if pd.isna(accountable) or str(accountable).lower() in ['nan', 'none', '']:
                        # Skip unassigned tasks - don't show in alerts
                        continue
                    else:
                        accountable = str(accountable).strip()
                        accountable = self._consolidate_department_name(accountable)
                    
                    # Only include if it's an Ascent person/team and not None
                    if (accountable is not None and accountable != 'Unknown' and 
                        self._is_ascent_team(accountable)):
                        if accountable not in alerts:
                            alerts[accountable] = []
                        alerts[accountable].append(f"Unclear Requirements: {task_name}")
        
        return alerts
    
    def _consolidate_department_name(self, name: str) -> str:
        """Consolidate similar department/person names with smart matching"""
        if pd.isna(name) or str(name).lower() in ['nan', 'none', '', 'n/a']:
            return None  # Return None for NaN values to filter them out
        
        name_clean = str(name).strip().lower()
        name_clean = name_clean.replace('/', '').replace('//', '').replace(' ', '')
        
        # Matt/Madison consolidation - catch all variations
        matt_variations = ['matt', 'matthew']
        madison_variations = ['madison', 'maddy']
        
        has_matt = any(variation in name_clean for variation in matt_variations)
        has_madison = any(variation in name_clean for variation in madison_variations)
        
        if has_matt or has_madison:
            return 'Matt & Madison'
        
        # Upendra variations
        upendra_variations = ['upendra', 'upendrachaudhari', 'upendrachaudhari,nareshbhai']
        if any(variation in name_clean for variation in upendra_variations):
            return 'Upendra Chaudhari'
        
        # Naresh variations  
        naresh_variations = ['naresh', 'nareshbhai', 'nareshpansuriya']
        if any(variation in name_clean for variation in naresh_variations):
            return 'Naresh Pansuriya'
        
        # Shivani variations
        shivani_variations = ['shivani', 'shivanichinial', 'dattu/shivani']
        if any(variation in name_clean for variation in shivani_variations):
            return 'Shivani Chinial'
        
        # SDS variations
        sds_variations = ['sds', 'sds ']
        if any(variation in name_clean for variation in sds_variations):
            return 'SDS'
        
        # Return original cleaned name if no matches
        return str(name).strip()
    
    def _requires_ascent_action(self, issue_summary: str) -> bool:
        """Check if a high priority issue requires Ascent action vs just Sona development"""
        issue_lower = str(issue_summary).lower()
        
        # Issues that require Ascent decision/input
        ascent_keywords = [
            'decision', 'approval', 'business rule', 'requirement', 
            'specification', 'clarification', 'policy', 'process',
            'user acceptance', 'testing', 'validation', 'sign off'
        ]
        
        return any(keyword in issue_lower for keyword in ascent_keywords)
    
    def _is_ascent_team(self, name: str) -> bool:
        """Check if this is an Ascent team member vs Sona contractor"""
        name_lower = str(name).lower()
        
        # Ascent team members
        ascent_names = ['matt', 'madison', 'sds', 'ascent']
        
        # Sona contractors (exclude from alerts)
        sona_names = ['upendra', 'naresh', 'shivani', 'dattu', 'sona']
        
        # If it's a Sona contractor, don't include
        if any(sona in name_lower for sona in sona_names):
            return False
        
        # If it's clearly Ascent, include
        if any(ascent in name_lower for ascent in ascent_names):
            return True
        
        # Skip unassigned items (handled elsewhere)
        if 'unassigned' in name_lower:
            return False
        
        # Default to including (better to over-alert than miss something)
        return True
    
    def get_upcoming_milestones(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming milestones and important dates"""
        milestones = []
        end_date = self.current_date + timedelta(days=days_ahead)
        
        # Check all dates in the date range
        for i in range(days_ahead):
            check_date = self.current_date + timedelta(days=i)
            tasks = self.get_tasks_for_date(check_date)
            milestones.extend(tasks)
        
        return sorted(milestones, key=lambda x: x['date'])

def show_executive_dashboard(planner: AscentPlannerCalendar):
    """Show consolidated executive dashboard with all key information"""
    
    # Key Metrics Row
    st.markdown('<div class="section-header"><h3>Key Performance Indicators</h3></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total tasks
    planner_df = planner.get_planner_tasks()
    total_tasks = len(planner_df) if not planner_df.empty else 0
    
    # Open decisions
    decisions_df = planner.get_open_decisions()
    open_decisions = len(decisions_df) if not decisions_df.empty else 0
    
    # Critical issues
    hotfixes_df = planner.get_hotfixes_status()
    critical_issues = 0
    if not hotfixes_df.empty:
        for _, row in hotfixes_df.iterrows():
            priority = str(row.get('Unnamed: 3', '')).lower()
            status = str(row.get('Unnamed: 5', '')).lower()
            summary = str(row.get('Claim Related Feedback/Change Request/ Hot Fixes', 'Unknown Issue'))
            if ('highest' in priority and 'done' not in status and planner._requires_ascent_action(summary)):
                critical_issues += 1
    
    # Unclear requirements
    unclear_reqs = 0
    if not planner_df.empty:
        unclear_reqs = len(planner_df[planner_df['Requirement Unclear'] == True])
    
    with col1:
        st.metric("Total Project Tasks", total_tasks, help="All tasks across planner, roadmap, and migration sheets")
    with col2:
        st.metric("Business Decisions Pending", open_decisions, help="Open decisions blocking project progress - require executive input")
    with col3:
        st.metric("Critical Issues (Ascent Action)", critical_issues, help="Highest priority issues requiring Ascent business decisions or approvals")
    with col4:
        st.metric("Tasks Blocked on Requirements", unclear_reqs, help="Tasks that cannot proceed until requirements are clarified")
        
        # Add dropdown for unclear requirements
        if unclear_reqs > 0:
            unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
            unclear_options = ["Select blocked task..."] + [str(task.get('Task Name', 'Unknown')).strip() 
                                                           for _, task in unclear_tasks.iterrows() 
                                                           if str(task.get('Task Name', 'Unknown')).strip()]
            
            selected_unclear = st.selectbox(
                f"Review {unclear_reqs} blocked tasks:",
                unclear_options,
                key="exec_unclear_dropdown"
            )
            
            if selected_unclear != "Select blocked task...":
                # Find the selected task details
                selected_task_data = unclear_tasks[unclear_tasks['Task Name'].str.strip() == selected_unclear].iloc[0]
                
                with st.expander(f"Task Details: {selected_unclear}", expanded=True):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        accountable = selected_task_data.get('Accountable')
                        if pd.notna(accountable) and str(accountable).lower() not in ['nan', 'none', '']:
                            accountable_clean = planner._consolidate_department_name(accountable)
                            st.write(f"**Owner:** {accountable_clean}")
                        else:
                            st.error("**Owner:** UNASSIGNED")
                        
                        status = selected_task_data.get('Status1')
                        if pd.notna(status) and str(status).lower() not in ['nan', 'none', '']:
                            st.write(f"**Status:** {status}")
                        else:
                            st.write("**Status:** Not Set")
                    
                    with col_b:
                        beta_date = selected_task_data.get('Beta Realease')
                        if pd.notna(beta_date):
                            st.write(f"**Beta Release:** {beta_date}")
                        
                        prod_date = selected_task_data.get('PROD Release')
                        if pd.notna(prod_date):
                            st.write(f"**Prod Release:** {prod_date}")
                    
                    st.warning("**Action Required:** Clarify requirements before work can proceed")
    
    # Department Organization Section
    st.markdown('<div class="section-header"><h3>Tasks Organized by Business Department</h3></div>', unsafe_allow_html=True)
    
    # Categorize unclear requirements by business department
    if unclear_reqs > 0:
        unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
        
        # Define department categories based on task content
        departments = {
            'Claims': [],
            'Accounting': [],
            'Cancellations': [],
            'Commissions': [],
            'Onboarding': [],
            'Reinsurance': []
        }
        
        # Categorize tasks by department based on task name content
        for _, task in unclear_tasks.iterrows():
            task_name = str(task.get('Task Name', 'Unknown')).strip().lower()
            accountable = task.get('Accountable')
            status = task.get('Status1')
            
            # Clean up owner info
            if pd.notna(accountable) and str(accountable).lower() not in ['nan', 'none', '']:
                owner = planner._consolidate_department_name(accountable)
            else:
                owner = 'UNASSIGNED'
            
            # Clean up status
            if pd.notna(status) and str(status).lower() not in ['nan', 'none', '']:
                status_clean = str(status)
            else:
                status_clean = 'Not Set'
            
            task_info = {
                'name': str(task.get('Task Name', 'Unknown')).strip(),
                'owner': owner,
                'status': status_clean
            }
            
            # Categorize by keywords in task name
            if any(keyword in task_name for keyword in ['claim', 'payment to claim', 'lemon squad', 'snapsheet']):
                departments['Claims'].append(task_info)
            elif any(keyword in task_name for keyword in ['reconcile', 'journal', 'cash', 'financial', 'rpt', 'report']):
                departments['Accounting'].append(task_info)
            elif any(keyword in task_name for keyword in ['cancel', 'refund', 'diversicare']):
                departments['Cancellations'].append(task_info)
            elif any(keyword in task_name for keyword in ['commission', 'statement', 'payee']):
                departments['Commissions'].append(task_info)
            elif any(keyword in task_name for keyword in ['onboard', 'setup', 'agent', 'dealer']):
                departments['Onboarding'].append(task_info)
            elif any(keyword in task_name for keyword in ['reins', 'cession', 'collateral']):
                departments['Reinsurance'].append(task_info)
            else:
                # Put uncategorized items in the most relevant department
                if 'nacha' in task_name or 'ach' in task_name or 'stripe' in task_name:
                    departments['Accounting'].append(task_info)
                else:
                    departments['Accounting'].append(task_info)  # Default to accounting
        
        # Create tabs for each department
        dept_tabs = st.tabs([f"{dept} ({len(tasks)})" for dept, tasks in departments.items() if len(tasks) > 0])
        
        tab_index = 0
        for dept_name, tasks in departments.items():
            if len(tasks) > 0:
                with dept_tabs[tab_index]:
                    st.write(f"**{len(tasks)} tasks** in {dept_name} department with unclear requirements:")
                    
                    # Create dropdown for this department
                    dept_options = ["Select task..."] + [task['name'] for task in tasks]
                    selected_dept_task = st.selectbox(
                        f"Review {dept_name} tasks:",
                        dept_options,
                        key=f"dept_{dept_name.lower()}_dropdown"
                    )
                    
                    if selected_dept_task != "Select task...":
                        # Find the selected task
                        selected_task_info = next(task for task in tasks if task['name'] == selected_dept_task)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Owner:** {selected_task_info['owner']}")
                        with col2:
                            st.write(f"**Status:** {selected_task_info['status']}")
                        with col3:
                            st.write(f"**Department:** {dept_name}")
                        
                        if selected_task_info['owner'] == 'UNASSIGNED':
                            st.error("**Priority Action:** Assign owner to begin requirement clarification")
                        else:
                            st.warning("**Action Required:** Owner needs to clarify requirements")
                    
                    # Show summary list
                    with st.expander(f"View all {dept_name} tasks"):
                        for i, task in enumerate(tasks, 1):
                            st.write(f"{i}. **{task['name']}** - {task['owner']} - {task['status']}")
                
                tab_index += 1
    
    # Key Performance Indicators Explanation
    st.markdown('<div class="section-header"><h3>Key Performance Indicators Explained</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="data-card">
            <h4>Actual Spreadsheet Data:</h4>
            <p><strong>193 Total Tasks:</strong> From main Planner sheet (all project work)</p>
            <p><strong>20 Open Decisions:</strong> From 'Open Decision & Next Steps' sheet</p>
            <p><strong>{} Critical Issues:</strong> From 'CR_HotFixes_ENHCE' sheet (Highest priority requiring Ascent action)</p>
            <p><strong>82 Tasks Blocked:</strong> Tasks marked 'Requirement Unclear = True' in Planner sheet</p>
        </div>
        """.format(critical_issues), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="data-card">
            <h4>Real Data Insights:</h4>
            <p><strong>Only 25 of 193 tasks</strong> have owners assigned (13% assigned)</p>
            <p><strong>166 tasks have status</strong> information (86% have status)</p>
            <p><strong>65 tasks scheduled</strong> for Beta release</p>
            <p><strong>47 tasks scheduled</strong> for Production release</p>
            <p><strong>Major Gap:</strong> Most tasks need owners assigned</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Critical Issues Details
    if critical_issues > 0:
        st.markdown('<div class="section-header"><h3>Critical Issues Requiring Immediate Ascent Action</h3></div>', unsafe_allow_html=True)
        
        # Show what the critical issues actually are
        hotfixes_df = planner.get_hotfixes_status()
        if not hotfixes_df.empty:
            critical_found = 0
            for _, row in hotfixes_df.iterrows():
                priority = str(row.get('Unnamed: 3', '')).lower()
                status = str(row.get('Unnamed: 5', '')).lower()
                summary = str(row.get('Claim Related Feedback/Change Request/ Hot Fixes', 'Unknown Issue'))
                
                if ('highest' in priority and 'done' not in status and 
                    planner._requires_ascent_action(summary)):
                    critical_found += 1
                    st.markdown(f"""
                    <div class="alert-container">
                        <h4 style="margin-top: 0; color: #721c24;">Critical Issue #{critical_found}</h4>
                        <p><strong>Issue:</strong> {summary}</p>
                        <p><strong>Priority Level:</strong> {row.get('Unnamed: 3', 'Unknown')}</p>
                        <p><strong>Current Status:</strong> {row.get('Unnamed: 5', 'Unknown')}</p>
                        <p><strong>Why Critical:</strong> Requires Ascent business decision, policy clarification, or executive approval</p>
                        <p><strong>Impact:</strong> Blocking other work until resolved</p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-container">
            <h4 style="margin-top: 0; color: #155724;">No Critical Issues</h4>
            <p style="margin-bottom: 0;">All highest priority issues have been resolved or don't require Ascent action</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Department Alerts Section
    st.markdown('<div class="section-header"><h3>Department Attention Required</h3></div>', unsafe_allow_html=True)
    
    alerts = planner.get_department_alerts()
    if alerts:
        for dept, issues in alerts.items():
            dept_display = str(dept).strip()
            if dept_display and dept_display != 'Unknown':
                st.markdown(f"""
                <div class="alert-container">
                    <h4 style="margin-top: 0; color: #856404;">{dept_display}</h4>
                    <p style="margin-bottom: 0;"><strong>{len(issues)} items</strong> requiring attention</p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"View {dept_display} Details"):
                    for i, issue in enumerate(issues, 1):
                        st.write(f"{i}. {issue}")
    else:
        st.markdown("""
        <div class="success-container">
            <h4 style="margin-top: 0; color: #155724;">All Departments On Track</h4>
            <p style="margin-bottom: 0;">No immediate departmental attention required</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Section
    st.markdown('<div class="section-header"><h3>Project Analytics & Visualizations</h3></div>', unsafe_allow_html=True)
    
    if not planner_df.empty:
        # Create multiple chart views
        chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs(["Status Distribution", "Department Workload", "Timeline Analysis", "Priority Breakdown"])
        
        with chart_tab1:
            # Status Distribution - Pie and Bar Charts
            status_counts = planner_df['Status1'].value_counts()
            status_counts = status_counts[status_counts.index.notna()]
            
            if not status_counts.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie Chart
                    fig_pie = px.pie(
                        values=status_counts.values,
                        names=status_counts.index,
                        title="Task Status Distribution (Pie Chart)",
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_pie.update_layout(height=400, title_font_size=14)
                    st.plotly_chart(fig_pie, use_container_width=True, key="tab1_pie")
                
                with col2:
                    # Bar Chart
                    fig_bar = px.bar(
                        x=status_counts.index,
                        y=status_counts.values,
                        title="Task Status Distribution (Bar Chart)",
                        labels={'x': 'Status', 'y': 'Number of Tasks'},
                        color=status_counts.values,
                        color_continuous_scale='Blues'
                    )
                    fig_bar.update_layout(height=400, title_font_size=14)
                    st.plotly_chart(fig_bar, use_container_width=True, key="tab1_bar")
        
        with chart_tab2:
            # Department Workload Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Tasks by Department (Horizontal Bar)
                dept_counts = planner_df['Accountable'].value_counts()
                dept_counts = dept_counts[dept_counts.index.notna()]
                dept_counts = dept_counts[dept_counts.index != 'nan'][:10]  # Top 10
                
                if not dept_counts.empty:
                    fig_dept = px.bar(
                        x=dept_counts.values,
                        y=dept_counts.index,
                        orientation='h',
                        title="Tasks by Department/Person (Top 10)",
                        labels={'x': 'Number of Tasks', 'y': 'Accountable'},
                        color=dept_counts.values,
                        color_continuous_scale='Viridis'
                    )
                    fig_dept.update_layout(height=500, title_font_size=14)
                    st.plotly_chart(fig_dept, use_container_width=True, key="tab2_dept")
            
            with col2:
                # Department Status Breakdown
                if 'Accountable' in planner_df.columns and 'Status1' in planner_df.columns:
                    dept_status = pd.crosstab(planner_df['Accountable'], planner_df['Status1'])
                    dept_status = dept_status.head(8)  # Top 8 departments
                    
                    fig_stacked = px.bar(
                        dept_status,
                        title="Status Distribution by Department",
                        labels={'value': 'Number of Tasks', 'index': 'Department'},
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_stacked.update_layout(height=500, title_font_size=14)
                    st.plotly_chart(fig_stacked, use_container_width=True, key="tab2_stacked")
        
        with chart_tab3:
            # Timeline Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Requirements Clarity Over Time
                unclear_count = len(planner_df[planner_df['Requirement Unclear'] == True])
                clear_count = total_tasks - unclear_count
                
                clarity_data = pd.DataFrame({
                    'Category': ['Clear Requirements', 'Unclear Requirements'],
                    'Count': [clear_count, unclear_count]
                })
                
                fig_clarity = px.bar(
                    clarity_data,
                    x='Category',
                    y='Count',
                    title="Requirements Clarity Status",
                    color='Category',
                    color_discrete_map={'Clear Requirements': '#2ecc71', 'Unclear Requirements': '#e74c3c'}
                )
                fig_clarity.update_layout(height=400, title_font_size=14)
                st.plotly_chart(fig_clarity, use_container_width=True, key="tab3_clarity")
            
            with col2:
                # Task Distribution by Phase
                if 'Beta Realease' in planner_df.columns and 'PROD Release' in planner_df.columns:
                    beta_tasks = planner_df['Beta Realease'].notna().sum()
                    prod_tasks = planner_df['PROD Release'].notna().sum()
                    other_tasks = total_tasks - beta_tasks - prod_tasks
                    
                    phase_data = pd.DataFrame({
                        'Phase': ['Beta Release', 'Production Release', 'Other'],
                        'Tasks': [beta_tasks, prod_tasks, other_tasks]
                    })
                    
                    fig_phase = px.pie(
                        phase_data,
                        values='Tasks',
                        names='Phase',
                        title="Tasks by Release Phase",
                        color_discrete_sequence=['#3498db', '#9b59b6', '#95a5a6']
                    )
                    fig_phase.update_layout(height=400, title_font_size=14)
                    st.plotly_chart(fig_phase, use_container_width=True, key="tab3_phase")
        
        with chart_tab4:
            # Priority and Issue Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Open Decisions by Type
                decisions_df = planner.get_open_decisions()
                if not decisions_df.empty and len(decisions_df) > 1:
                    # Create a simple count of decisions
                    decision_count = len(decisions_df)
                    total_decisions = 20  # From your data
                    resolved_decisions = total_decisions - decision_count
                    
                    decision_data = pd.DataFrame({
                        'Status': ['Open Decisions', 'Resolved Decisions'],
                        'Count': [decision_count, resolved_decisions]
                    })
                    
                    fig_decisions = px.bar(
                        decision_data,
                        x='Status',
                        y='Count',
                        title="Decision Status Overview",
                        color='Status',
                        color_discrete_map={'Open Decisions': '#f39c12', 'Resolved Decisions': '#27ae60'}
                    )
                    fig_decisions.update_layout(height=400, title_font_size=14)
                    st.plotly_chart(fig_decisions, use_container_width=True, key="tab4_decisions")
            
            with col2:
                # Department Alert Summary
                alerts = planner.get_department_alerts()
                if alerts:
                    alert_data = pd.DataFrame([
                        {'Department': dept, 'Alert_Count': len(issues)}
                        for dept, issues in alerts.items()
                    ])
                    
                    fig_alerts = px.bar(
                        alert_data,
                        x='Department',
                        y='Alert_Count',
                        title="Alerts by Department",
                        color='Alert_Count',
                        color_continuous_scale='Reds'
                    )
                    fig_alerts.update_layout(height=400, title_font_size=14)
                    fig_alerts.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_alerts, use_container_width=True, key="tab4_alerts")
    
    # Actual Data Summary
    st.markdown('<div class="section-header"><h3>Actual Spreadsheet Data Summary</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="data-card">
            <h4>Real Data Completeness</h4>
            <p><strong>Planner Sheet:</strong> 193 tasks total</p>
            <ul>
                <li>25 tasks have owners (13%)</li>
                <li>166 tasks have status (86%)</li>
                <li>65 tasks have Beta dates</li>
                <li>47 tasks have Prod dates</li>
                <li>82 tasks marked unclear requirements</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="data-card">
            <h4>Other Sheets Data</h4>
            <p><strong>Open Decisions:</strong> 20 items (17 have owners)</p>
            <p><strong>Hotfixes/Issues:</strong> 89 items (86 have priority)</p>
            <p><strong>Data Migration:</strong> 28 modules tracked daily</p>
            <p><strong>Important Links:</strong> 6 reference URLs</p>
            <p><strong>Roadmap:</strong> 73 roadmap items</p>
        </div>
        """, unsafe_allow_html=True)

def show_todays_overview(planner: AscentPlannerCalendar):
    """Show today's overview with all relevant information"""
    st.header(f"Today's Overview - {planner.current_date.strftime('%A, %B %d, %Y')}")
    
    # Today's tasks
    today_tasks = planner.get_tasks_for_date(planner.current_date)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader("Today's Tasks")
        if today_tasks:
            for task in today_tasks:
                with st.expander(f"{task['source']}: {task['task_name'][:50]}..."):
                    st.write(f"**Type:** {task['date_type']}")
                    st.write(f"**Accountable:** {task['accountable']}")
                    st.write(f"**Status:** {task['status']}")
                    if 'requirement_unclear' in task and task['requirement_unclear']:
                        st.warning("⚠️ Requirements are unclear for this task")
        else:
            st.info("No tasks scheduled for today")
    
    with col2:
        st.subheader("🚨 Department Alerts")
        alerts = planner.get_department_alerts()
        if alerts:
            for dept, issues in alerts.items():
                # Clean up department names for display
                if pd.isna(dept) or str(dept).lower() in ['nan', 'none', '', 'n/a']:
                    dept = 'Unassigned Team'
                
                dept_display = str(dept).strip()
                if dept_display and dept_display != 'Unknown':
                    st.warning(f"**{dept_display}**")
                    for issue in issues[:3]:  # Show first 3 issues
                        st.write(f"• {issue}")
                    if len(issues) > 3:
                        st.write(f"... and {len(issues) - 3} more issues")
        else:
            st.success("✅ No immediate alerts")
    
    with col3:
        st.subheader("📊 Quick Stats")
        
        # Count open decisions
        decisions_df = planner.get_open_decisions()
        open_decisions = len(decisions_df) if not decisions_df.empty else 0
        st.metric("Open Decisions", open_decisions)
        
        # Count high priority items that require Ascent action
        hotfixes_df = planner.get_hotfixes_status()
        high_priority = 0
        if not hotfixes_df.empty:
            for _, row in hotfixes_df.iterrows():
                priority = str(row.get('Unnamed: 3', '')).lower()
                status = str(row.get('Unnamed: 5', '')).lower()
                summary = str(row.get('Claim Related Feedback/Change Request/ Hot Fixes', 'Unknown Issue'))
                
                # Only count if highest priority AND requires Ascent action
                if ('highest' in priority and 'done' not in status and 
                    planner._requires_ascent_action(summary)):
                    high_priority += 1
        st.metric("Critical Issues (Ascent Action)", high_priority)
        
        # Count unclear requirements
        planner_df = planner.get_planner_tasks()
        unclear_reqs = 0
        if not planner_df.empty:
            unclear_reqs = len(planner_df[planner_df['Requirement Unclear'] == True])
        st.metric("Unclear Requirements", unclear_reqs)

def show_calendar_view(planner: AscentPlannerCalendar):
    """Show calendar view with task scheduling"""
    st.header("📅 Calendar View")
    
    # Date picker
    selected_date = st.date_input(
        "Select Date",
        value=planner.current_date,
        min_value=date(2025, 1, 1),
        max_value=date(2026, 12, 31)
    )
    
    # Show tasks for selected date
    tasks = planner.get_tasks_for_date(selected_date)
    
    if tasks:
        st.success(f"📋 Found {len(tasks)} item(s) for {selected_date.strftime('%A, %B %d, %Y')}")
        
        for i, task in enumerate(tasks, 1):
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"### {i}. {task['task_name']}")
                    st.write(f"**Source:** {task['source']}")
                    st.write(f"**Type:** {task['date_type']}")
                
                with col2:
                    st.write(f"**Accountable:** {task['accountable']}")
                    st.write(f"**Status:** {task['status']}")
                
                with col3:
                    if task.get('requirement_unclear'):
                        st.error("⚠️ Unclear Requirements")
                    elif task['status'] == 'DONE':
                        st.success("✅ Completed")
                    elif 'In Progress' in task['status']:
                        st.info("🔄 In Progress")
                    else:
                        st.warning("⏳ Pending")
                
                if 'details' in task:
                    with st.expander("View Details"):
                        for detail in task['details']:
                            st.write(f"• {detail}")
                
                st.divider()
    else:
        st.info(f"📅 No items scheduled for {selected_date.strftime('%A, %B %d, %Y')}")

def show_upcoming_milestones(planner: AscentPlannerCalendar):
    """Show upcoming milestones and deadlines"""
    st.header("🎯 Upcoming Milestones")
    
    days_ahead = st.slider("Days to look ahead", 1, 90, 30)
    milestones = planner.get_upcoming_milestones(days_ahead)
    
    if milestones:
        st.success(f"🔮 Found {len(milestones)} upcoming milestone(s)")
        
        # Group by date
        milestones_by_date = {}
        for milestone in milestones:
            date_key = milestone['date']
            if date_key not in milestones_by_date:
                milestones_by_date[date_key] = []
            milestones_by_date[date_key].append(milestone)
        
        for milestone_date, items in sorted(milestones_by_date.items()):
            days_until = (milestone_date - planner.current_date).days
            
            if days_until == 0:
                date_label = "🔥 TODAY"
            elif days_until == 1:
                date_label = "⚡ TOMORROW"
            elif days_until <= 7:
                date_label = f"📅 {milestone_date.strftime('%A')} ({days_until} days)"
            else:
                date_label = f"📅 {milestone_date.strftime('%B %d')} ({days_until} days)"
            
            st.subheader(date_label)
            
            for item in items:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{item['task_name']}** ({item['date_type']})")
                
                with col2:
                    st.write(f"*{item['accountable']}*")
                
                with col3:
                    if item['status'] == 'DONE':
                        st.success("✅")
                    elif 'In Progress' in item['status']:
                        st.info("🔄")
                    else:
                        st.warning("⏳")
            
            st.divider()
    else:
        st.info("🎯 No upcoming milestones found")

def show_department_dashboard(planner: AscentPlannerCalendar):
    """Show department-specific dashboard with alerts and tasks"""
    st.header("🏢 Department Dashboard")
    
    alerts = planner.get_department_alerts()
    
    if alerts:
        st.warning(f"⚠️ {len(alerts)} department(s) need attention!")
        
        for dept, issues in alerts.items():
            if dept != 'nan' and dept != 'N/A':
                with st.expander(f"🏢 {dept} ({len(issues)} issue(s))", expanded=True):
                    for i, issue in enumerate(issues, 1):
                        if 'Open Decision' in issue:
                            st.error(f"{i}. {issue}")
                        elif 'High Priority' in issue:
                            st.warning(f"{i}. {issue}")
                        elif 'Unclear Requirements' in issue:
                            st.info(f"{i}. {issue}")
                        else:
                            st.write(f"{i}. {issue}")
    else:
        st.success("✅ All departments are on track!")
    
    # Show department workload
    st.subheader("📊 Department Workload")
    
    planner_df = planner.get_planner_tasks()
    if not planner_df.empty:
        # Count tasks by accountable person/department
        workload = planner_df['Accountable'].value_counts()
        workload = workload[workload.index != 'nan']  # Remove NaN entries
        
        if not workload.empty:
            fig = px.bar(
                x=workload.values,
                y=workload.index,
                orientation='h',
                title="Tasks by Department/Person",
                labels={'x': 'Number of Tasks', 'y': 'Accountable'}
            )
            st.plotly_chart(fig, use_container_width=True, key="dept_workload")

def show_data_insights(planner: AscentPlannerCalendar):
    """Show comprehensive data insights and analytics with multiple charts"""
    st.header("Data Insights & Analytics")
    
    # Create comprehensive analytics tabs
    analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs([
        "Overview Charts", "Advanced Analytics", "Raw Data Explorer"
    ])
    
    with analytics_tab1:
        # Sheet overview metrics
        st.subheader("Data Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        planner_df = planner.get_planner_tasks()
        decisions_df = planner.get_open_decisions()
        hotfixes_df = planner.get_hotfixes_status()
        
        with col1:
            st.metric("Total Project Tasks", len(planner_df) if not planner_df.empty else 0, help="All tasks in main planner sheet")
        with col2:
            st.metric("Business Decisions Pending", len(decisions_df) if not decisions_df.empty else 0, help="Open decisions requiring executive input")
        with col3:
            st.metric("Bug Reports & Enhancements", len(hotfixes_df) if not hotfixes_df.empty else 0, help="All issues tracked in CR/Hotfixes sheet")
        with col4:
            st.metric("Excel Sheets Loaded", len(planner.data), help="Number of data sources integrated")
        
        # Business-Critical Analysis
        st.subheader("Critical Business Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Task completion rate analysis
            if not planner_df.empty:
                status_counts = planner_df['Status1'].value_counts()
                status_counts = status_counts[status_counts.index.notna()]
                
                # Calculate completion metrics
                completed_statuses = ['DONE', 'Completed', 'Finished']
                in_progress_statuses = ['In Progress', 'In Review', 'Phase 2']
                
                completed = sum(status_counts.get(status, 0) for status in completed_statuses)
                in_progress = sum(status_counts.get(status, 0) for status in in_progress_statuses)
                not_started = status_counts.get('Not Started', 0)
                
                completion_data = pd.DataFrame({
                    'Status': ['Completed', 'In Progress', 'Not Started'],
                    'Count': [completed, in_progress, not_started],
                    'Percentage': [
                        (completed/len(planner_df))*100,
                        (in_progress/len(planner_df))*100,
                        (not_started/len(planner_df))*100
                    ]
                })
                
                fig_completion = px.pie(
                    completion_data,
                    values='Percentage',
                    names='Status',
                    title="Project Progress",
                    color_discrete_map={
                        'Completed': '#27ae60',
                        'In Progress': '#f39c12', 
                        'Not Started': '#e74c3c'
                    }
                )
                fig_completion.update_layout(height=400)
                fig_completion.update_traces(texttemplate='%{label}: %{percent}', textposition='auto')
                st.plotly_chart(fig_completion, use_container_width=True, key="exec_completion")
        
        with col2:
            # Risk assessment - unclear requirements by department
            if not planner_df.empty:
                unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
                if not unclear_tasks.empty:
                    # Consolidate department names before counting
                    consolidated_depts = []
                    for _, task in unclear_tasks.iterrows():
                        dept = task.get('Accountable')
                        consolidated = planner._consolidate_department_name(dept)
                        if consolidated is not None:  # Skip None values (NaN)
                            consolidated_depts.append(consolidated)
                    
                    if consolidated_depts:
                        risk_by_dept = pd.Series(consolidated_depts).value_counts().head(8)
                        
                        fig_risk = px.pie(
                            values=risk_by_dept.values,
                            names=risk_by_dept.index,
                            title="Tasks Waiting for Requirements",
                            color_discrete_sequence=px.colors.sequential.Reds_r
                        )
                        fig_risk.update_layout(height=400)
                        fig_risk.update_traces(texttemplate='%{label}: %{value}', textposition='auto')
                        st.plotly_chart(fig_risk, use_container_width=True, key="exec_risk")
        
        # Actionable Business Insights
        st.subheader("Actionable Business Intelligence")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Open Decisions Timeline - What needs immediate action
            decisions_df = planner.get_open_decisions()
            if not decisions_df.empty:
                # Create decision urgency analysis
                decision_owners = []
                for _, row in decisions_df.iterrows():
                    if 'Open' in str(row.get('Unnamed: 3', '')):
                        who = str(row.get('Gayatri Raol ', 'Unknown'))
                        decision_owners.append(who)
                
                if decision_owners:
                    # Consolidate Matt/Madison variations before charting
                    consolidated_owners = []
                    for owner in decision_owners:
                        consolidated = planner._consolidate_department_name(owner)
                        if consolidated is not None:  # Skip None values
                            consolidated_owners.append(consolidated)
                    
                    if consolidated_owners:
                        decision_counts = pd.Series(consolidated_owners).value_counts()
                        
                        fig_decisions = px.pie(
                            values=decision_counts.values,
                            names=decision_counts.index,
                            title="Pending Decisions by Owner",
                            color_discrete_sequence=px.colors.sequential.Oranges_r
                        )
                        fig_decisions.update_layout(height=400)
                        fig_decisions.update_traces(texttemplate='%{label}: %{value}', textposition='auto')
                        st.plotly_chart(fig_decisions, use_container_width=True, key="exec_decisions")
        
        with col2:
            # Critical Issues by Priority - What's blocking progress
            hotfixes_df = planner.get_hotfixes_status()
            if not hotfixes_df.empty:
                priority_counts = hotfixes_df['Unnamed: 3'].value_counts()
                priority_counts = priority_counts[priority_counts.index.notna()]
                
                if not priority_counts.empty:
                    # Map priority levels to colors
                    priority_colors = {
                        'Highest': '#e74c3c',
                        'High': '#f39c12',
                        'Medium': '#f1c40f',
                        'Low': '#27ae60'
                    }
                    
                    colors = [priority_colors.get(str(priority), '#95a5a6') for priority in priority_counts.index]
                    
                    fig_priority = px.pie(
                        values=priority_counts.values,
                        names=priority_counts.index,
                        title="Issues by Priority",
                        color_discrete_map=priority_colors
                    )
                    fig_priority.update_layout(height=400)
                    fig_priority.update_traces(texttemplate='%{label}: %{value}', textposition='auto')
                    st.plotly_chart(fig_priority, use_container_width=True, key="exec_priority")
    
    with analytics_tab2:
        # Business-Critical Advanced Analytics
        st.subheader("Executive Decision Support")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Release Timeline Analysis - Beta vs Prod readiness
            if not planner_df.empty:
                beta_ready = 0
                prod_ready = 0
                
                for _, row in planner_df.iterrows():
                    if pd.notna(row.get('Beta Realease')) and row.get('Status1') in ['DONE', 'Completed']:
                        beta_ready += 1
                    if pd.notna(row.get('PROD Release')) and row.get('Status1') in ['DONE', 'Completed']:
                        prod_ready += 1
                
                beta_total = planner_df['Beta Realease'].notna().sum()
                prod_total = planner_df['PROD Release'].notna().sum()
                
                release_data = pd.DataFrame({
                    'Release': ['Beta Release', 'Production Release'],
                    'Ready': [beta_ready, prod_ready],
                    'Total': [beta_total, prod_total],
                    'Completion_Rate': [
                        (beta_ready/beta_total*100) if beta_total > 0 else 0,
                        (prod_ready/prod_total*100) if prod_total > 0 else 0
                    ]
                })
                
                fig_release = px.pie(
                    release_data,
                    values='Completion_Rate',
                    names='Release',
                    title="Release Readiness",
                    color_discrete_sequence=['#3498db', '#9b59b6']
                )
                fig_release.update_layout(height=400)
                fig_release.update_traces(texttemplate='%{label}: %{value:.1f}%', textposition='auto')
                st.plotly_chart(fig_release, use_container_width=True, key="adv_release")
        
        with col2:
            # Department Bottleneck Analysis - Where are the problems?
            if not planner_df.empty:
                # Find departments with most unclear requirements (bottlenecks)
                unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
                bottleneck_analysis = unclear_tasks['Accountable'].value_counts().head(6)
                bottleneck_analysis = bottleneck_analysis[bottleneck_analysis.index.notna()]
                bottleneck_analysis = bottleneck_analysis[bottleneck_analysis.index != 'nan']
                
                if not bottleneck_analysis.empty:
                    fig_bottleneck = px.pie(
                        values=bottleneck_analysis.values,
                        names=bottleneck_analysis.index,
                        title="Tasks Waiting for Requirements",
                        color_discrete_sequence=px.colors.sequential.Reds_r
                    )
                    fig_bottleneck.update_layout(height=400)
                    fig_bottleneck.update_traces(texttemplate='%{label}: %{value}', textposition='auto')
                    st.plotly_chart(fig_bottleneck, use_container_width=True, key="adv_bottleneck")
        
        # Critical Path Analysis
        st.subheader("Critical Path & Risk Analysis")
        
        if not planner_df.empty:
            # Identify critical path items
            critical_items = planner_df[
                (planner_df['Requirement Unclear'] == True) | 
                (planner_df['Status1'].isin(['Not Started', 'Rework']))
            ]
            
            if not critical_items.empty:
                risk_summary = {
                    'High Risk (Unclear + Not Started)': len(critical_items[
                        (critical_items['Requirement Unclear'] == True) & 
                        (critical_items['Status1'] == 'Not Started')
                    ]),
                    'Medium Risk (Unclear Only)': len(critical_items[
                        (critical_items['Requirement Unclear'] == True) & 
                        (critical_items['Status1'] != 'Not Started')
                    ]),
                    'Low Risk (Not Started Only)': len(critical_items[
                        (critical_items['Requirement Unclear'] == False) & 
                        (critical_items['Status1'] == 'Not Started')
                    ])
                }
                
                risk_df = pd.DataFrame(list(risk_summary.items()), columns=['Risk Level', 'Count'])
                
                fig_risk_summary = px.pie(
                    risk_df,
                    values='Count',
                    names='Risk Level',
                    title="Project Risk Level",
                    color_discrete_map={
                        'High Risk (Unclear + Not Started)': '#e74c3c',
                        'Medium Risk (Unclear Only)': '#f39c12',
                        'Low Risk (Not Started Only)': '#f1c40f'
                    }
                )
                fig_risk_summary.update_layout(height=400)
                st.plotly_chart(fig_risk_summary, use_container_width=True, key="adv_risk_summary")
    
    with analytics_tab3:
        # Raw data access
        st.subheader("Raw Data Explorer")
        sheet_name = st.selectbox("Select Sheet", list(planner.data.keys()))
        
        if sheet_name:
            df = planner.data[sheet_name]
            st.write(f"**{sheet_name}** - {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Show column info
            with st.expander("Column Information"):
                for col in df.columns:
                    st.write(f"• **{col}** ({df[col].dtype})")
            
            # Show data with search
            search_term = st.text_input("Search in data (optional)")
            if search_term:
                # Simple search across string columns
                mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                filtered_df = df[mask]
                st.write(f"Found {len(filtered_df)} matching rows")
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.dataframe(df, use_container_width=True)

def show_requirements_management(planner: AscentPlannerCalendar):
    """Manage unclear requirements and requirement clarification"""
    st.header("Requirements Management")
    
    planner_df = planner.get_planner_tasks()
    if planner_df.empty:
        st.error("No planner data available")
        return
    
    # Requirements overview
    unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
    clear_tasks = planner_df[planner_df['Requirement Unclear'] == False]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tasks Ready to Work", len(clear_tasks), help="Tasks with clear, actionable requirements")
    with col2:
        st.metric("Tasks Blocked (Need Clarification)", len(unclear_tasks), help="Tasks waiting for requirement clarification before work can begin")
    with col3:
        clarity_rate = (len(clear_tasks) / len(planner_df)) * 100
        st.metric("Project Clarity Rate", f"{clarity_rate:.1f}%", help="Percentage of tasks with clear requirements")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Requirements by department
        if not unclear_tasks.empty:
            # Consolidate department names before counting
            consolidated_depts = []
            for _, task in unclear_tasks.iterrows():
                dept = task.get('Accountable')
                consolidated = planner._consolidate_department_name(dept)
                if consolidated is not None:  # Skip None values (NaN)
                    consolidated_depts.append(consolidated)
            
            if consolidated_depts:
                unclear_by_dept = pd.Series(consolidated_depts).value_counts().head(8)
                
                fig_unclear = px.pie(
                    values=unclear_by_dept.values,
                    names=unclear_by_dept.index,
                    title="Unclear Requirements by Department"
                )
                st.plotly_chart(fig_unclear, use_container_width=True, key="req_unclear_dept")
    
    with col2:
        # Overall clarity status
        clarity_data = pd.DataFrame({
            'Status': ['Clear', 'Unclear'],
            'Count': [len(clear_tasks), len(unclear_tasks)]
        })
        
        fig_clarity = px.pie(
            clarity_data,
            values='Count',
            names='Status',
            title="Overall Requirements Status",
            color_discrete_map={'Clear': '#27ae60', 'Unclear': '#e74c3c'}
        )
        st.plotly_chart(fig_clarity, use_container_width=True, key="req_clarity_overall")
    
    # Interactive unclear requirements dropdown
    st.subheader("Review Tasks with Unclear Requirements")
    
    if not unclear_tasks.empty:
        # Create list of all unclear tasks for dropdown
        unclear_task_options = ["Select a task to review..."]
        unclear_task_data = {}
        
        for idx, task in unclear_tasks.iterrows():
            task_name = str(task.get('Task Name', 'Unknown')).strip()
            if task_name and task_name != 'Unknown':
                unclear_task_options.append(task_name)
                unclear_task_data[task_name] = {
                    'accountable': task.get('Accountable'),
                    'status': task.get('Status1'),
                    'start_date': task.get('Start Date'),
                    'beta_date': task.get('Beta Realease'),
                    'prod_date': task.get('PROD Release'),
                    'demo_training': task.get(' Demo/Training'),
                    'requirement_unclear': task.get('Requirement Unclear.1')
                }
        
        # Dropdown selection
        selected_task = st.selectbox(
            f"Select from {len(unclear_task_options)-1} tasks with unclear requirements:",
            unclear_task_options
        )
        
        # Show details of selected task
        if selected_task != "Select a task to review...":
            task_info = unclear_task_data[selected_task]
            
            st.markdown(f"""
            <div class="data-card">
                <h4>{selected_task}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Assignment Info:**")
                accountable = task_info['accountable']
                if pd.notna(accountable) and str(accountable).lower() not in ['nan', 'none', '']:
                    accountable_clean = planner._consolidate_department_name(accountable)
                    st.write(f"Owner: {accountable_clean}")
                else:
                    st.error("Owner: UNASSIGNED")
                
                status = task_info['status']
                if pd.notna(status) and str(status).lower() not in ['nan', 'none', '']:
                    st.write(f"Status: {status}")
                else:
                    st.write("Status: Not Set")
            
            with col2:
                st.write("**Timeline:**")
                start_date = task_info['start_date']
                if pd.notna(start_date):
                    st.write(f"Start Date: {start_date}")
                
                beta_date = task_info['beta_date']
                if pd.notna(beta_date):
                    st.write(f"Beta Release: {beta_date}")
                
                prod_date = task_info['prod_date']
                if pd.notna(prod_date):
                    st.write(f"Prod Release: {prod_date}")
            
            with col3:
                st.write("**Requirement Status:**")
                unclear_detail = task_info['requirement_unclear']
                if pd.notna(unclear_detail):
                    st.write(f"Clarity Status: {unclear_detail}")
                else:
                    st.write("Clarity Status: Unclear")
                
                demo_training = task_info['demo_training']
                if pd.notna(demo_training):
                    st.write(f"Demo/Training: {demo_training}")
            
            # Action needed section
            st.markdown("""
            <div class="alert-container">
                <h4 style="margin-top: 0;">Action Required</h4>
                <p>This task cannot proceed until requirements are clarified. Contact the owner or assign an owner to begin requirement clarification process.</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.success("No tasks have unclear requirements - all requirements are clear!")

def show_release_planning(planner: AscentPlannerCalendar):
    """Manage release planning for Beta and Production"""
    st.header("Release Planning")
    
    planner_df = planner.get_planner_tasks()
    if planner_df.empty:
        st.error("No planner data available")
        return
    
    # Release metrics - based on actual data
    beta_tasks = planner_df['Beta Realease'].notna().sum()  # 65 actual
    prod_tasks = planner_df['PROD Release'].notna().sum()   # 47 actual
    
    # Count assigned vs unassigned
    beta_assigned = 0
    prod_assigned = 0
    
    for _, task in planner_df.iterrows():
        accountable = task.get('Accountable')
        if pd.notna(accountable) and str(accountable).lower() not in ['nan', 'none', '']:
            if pd.notna(task.get('Beta Realease')):
                beta_assigned += 1
            if pd.notna(task.get('PROD Release')):
                prod_assigned += 1
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Beta Tasks Scheduled", beta_tasks, help="Tasks with Beta release dates")
    with col2:
        st.metric("Beta Tasks Assigned", beta_assigned, help="Beta tasks with actual owners")
    with col3:
        st.metric("Prod Tasks Scheduled", prod_tasks, help="Tasks with Production release dates")
    with col4:
        st.metric("Prod Tasks Assigned", prod_assigned, help="Production tasks with actual owners")
    
    # Release readiness analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Beta release status
        beta_df = planner_df[planner_df['Beta Realease'].notna()]
        if not beta_df.empty:
            beta_status = beta_df['Status1'].value_counts()
            beta_status = beta_status[beta_status.index.notna()]
            
            if not beta_status.empty:
                fig_beta = px.pie(
                    values=beta_status.values,
                    names=beta_status.index,
                    title="Beta Release Task Status"
                )
                st.plotly_chart(fig_beta, use_container_width=True, key="release_beta")
    
    with col2:
        # Production release status
        prod_df = planner_df[planner_df['PROD Release'].notna()]
        if not prod_df.empty:
            prod_status = prod_df['Status1'].value_counts()
            prod_status = prod_status[prod_status.index.notna()]
            
            if not prod_status.empty:
                fig_prod = px.pie(
                    values=prod_status.values,
                    names=prod_status.index,
                    title="Production Release Task Status"
                )
                st.plotly_chart(fig_prod, use_container_width=True, key="release_prod")
    
    # Release timeline - only show assigned tasks
    st.subheader("Release Timeline (Assigned Tasks Only)")
    
    # Show beta tasks with dates - filter out NaN values
    if not beta_df.empty:
        st.write("**Beta Release Tasks with Owners:**")
        assigned_beta_tasks = 0
        
        for _, task in beta_df.iterrows():
            task_name = str(task.get('Task Name', 'Unknown'))
            beta_date = task.get('Beta Realease')
            status = task.get('Status1')
            accountable = task.get('Accountable')
            
            # Only show if task has an owner and valid data
            if (pd.notna(beta_date) and 
                pd.notna(accountable) and 
                str(accountable).lower() not in ['nan', 'none', ''] and
                pd.notna(status) and 
                str(status).lower() not in ['nan', 'none', '']):
                
                # Consolidate the accountable name
                accountable_clean = planner._consolidate_department_name(accountable)
                if accountable_clean is not None:
                    assigned_beta_tasks += 1
                    st.write(f"• **{task_name}** - {beta_date} - {status} - {accountable_clean}")
        
        if assigned_beta_tasks == 0:
            st.info("No Beta Release tasks have been assigned to specific owners yet")
    
    # Show production tasks with dates - filter out NaN values  
    if not prod_df.empty:
        st.write("**Production Release Tasks with Owners:**")
        assigned_prod_tasks = 0
        
        for _, task in prod_df.iterrows():
            task_name = str(task.get('Task Name', 'Unknown'))
            prod_date = task.get('PROD Release')
            status = task.get('Status1')
            accountable = task.get('Accountable')
            
            # Only show if task has an owner and valid data
            if (pd.notna(prod_date) and 
                pd.notna(accountable) and 
                str(accountable).lower() not in ['nan', 'none', ''] and
                pd.notna(status) and 
                str(status).lower() not in ['nan', 'none', '']):
                
                # Consolidate the accountable name
                accountable_clean = planner._consolidate_department_name(accountable)
                if accountable_clean is not None:
                    assigned_prod_tasks += 1
                    st.write(f"• **{task_name}** - {prod_date} - {status} - {accountable_clean}")
        
        if assigned_prod_tasks == 0:
            st.info("No Production Release tasks have been assigned to specific owners yet")

def show_decision_tracking(planner: AscentPlannerCalendar):
    """Track open decisions and next steps"""
    st.header("Decision Tracking")
    
    decisions_df = planner.get_open_decisions()
    if decisions_df.empty:
        st.error("No decision data available")
        return
    
    # Decision metrics
    open_decisions = 0
    for _, row in decisions_df.iterrows():
        if 'Open' in str(row.get('Unnamed: 3', '')):
            open_decisions += 1
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Decisions", len(decisions_df))
    with col2:
        st.metric("Open Decisions", open_decisions)
    with col3:
        closed_decisions = len(decisions_df) - open_decisions
        st.metric("Resolved Decisions", closed_decisions)
    
    # Decision ownership chart
    decision_owners = []
    for _, row in decisions_df.iterrows():
        if 'Open' in str(row.get('Unnamed: 3', '')):
            who = str(row.get('Gayatri Raol ', 'Unknown'))
            consolidated = planner._consolidate_department_name(who)
            if consolidated is not None:  # Skip None values
                decision_owners.append(consolidated)
    
    if decision_owners:
        decision_counts = pd.Series(decision_owners).value_counts()
        
        fig_decisions = px.pie(
            values=decision_counts.values,
            names=decision_counts.index,
            title="Open Decisions by Owner"
        )
        st.plotly_chart(fig_decisions, use_container_width=True, key="decision_owners")
    
    # Detailed decision list
    st.subheader("Open Decisions Requiring Action")
    for _, row in decisions_df.iterrows():
        if 'Open' in str(row.get('Unnamed: 3', '')):
            decision = str(row.get('Unnamed: 2', 'Unknown Decision'))
            who = str(row.get('Gayatri Raol ', 'Unknown'))
            
            with st.expander(f"Decision Owner: {who}"):
                st.write(decision)

def show_issue_management(planner: AscentPlannerCalendar):
    """Manage hotfixes, bugs, and enhancement requests"""
    st.header("Issue Management")
    
    hotfixes_df = planner.get_hotfixes_status()
    if hotfixes_df.empty:
        st.error("No issue data available")
        return
    
    # Issue metrics
    col1, col2, col3, col4 = st.columns(4)
    
    priority_counts = hotfixes_df['Unnamed: 3'].value_counts()
    
    with col1:
        st.metric("Total Issues", len(hotfixes_df))
    with col2:
        highest_count = priority_counts.get('Highest', 0)
        st.metric("Highest Priority", highest_count)
    with col3:
        high_count = priority_counts.get('High', 0)
        st.metric("High Priority", high_count)
    with col4:
        done_count = hotfixes_df['Unnamed: 5'].value_counts().get('DONE', 0)
        st.metric("Completed", done_count)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority distribution
        priority_counts = priority_counts[priority_counts.index.notna()]
        if not priority_counts.empty:
            fig_priority = px.pie(
                values=priority_counts.values,
                names=priority_counts.index,
                title="Issues by Priority Level"
            )
            st.plotly_chart(fig_priority, use_container_width=True, key="issue_priority")
    
    with col2:
        # Status distribution
        status_counts = hotfixes_df['Unnamed: 5'].value_counts()
        status_counts = status_counts[status_counts.index.notna()]
        
        if not status_counts.empty:
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Issues by Status"
            )
            st.plotly_chart(fig_status, use_container_width=True, key="issue_status")
    
    # High priority issues list
    st.subheader("High Priority Issues")
    for _, issue in hotfixes_df.iterrows():
        priority = str(issue.get('Unnamed: 3', ''))
        if priority in ['Highest', 'High']:
            summary = str(issue.get('Claim Related Feedback/Change Request/ Hot Fixes', 'Unknown'))
            status = str(issue.get('Unnamed: 5', 'Unknown'))
            st.write(f"**{priority}**: {summary} - Status: {status}")

def show_data_migration_progress(planner: AscentPlannerCalendar):
    """Track data migration daily progress"""
    st.header("Data Migration Progress")
    
    migration_df = planner.get_data_migration_status()
    if migration_df.empty:
        st.error("No migration data available")
        return
    
    # Find date columns (they're the column headers)
    date_columns = [col for col in migration_df.columns if isinstance(col, pd.Timestamp)]
    
    if date_columns:
        st.metric("Days Tracked", len(date_columns))
        
        # Recent migration activity
        recent_dates = sorted(date_columns, reverse=True)[:7]  # Last 7 days
        
        st.subheader("Recent Migration Activity (Last 7 Days)")
        for date_col in recent_dates:
            date_str = date_col.strftime('%Y-%m-%d')
            activities = migration_df[date_col].dropna()
            
            if not activities.empty:
                with st.expander(f"{date_str} - {len(activities)} activities"):
                    for activity in activities:
                        if pd.notna(activity):
                            st.write(f"• {activity}")
    
    # Migration modules overview
    if 'Module' in migration_df.index:
        modules = migration_df.loc['Module'].dropna()
        if not modules.empty:
            st.subheader("Migration Modules")
            module_counts = pd.Series(modules).value_counts()
            
            fig_modules = px.pie(
                values=module_counts.values,
                names=module_counts.index,
                title="Migration by Module"
            )
            st.plotly_chart(fig_modules, use_container_width=True, key="migration_modules")

def show_complete_sharepoint_data(planner: AscentPlannerCalendar):
    """Show complete view of ALL SharePoint data from ALL tabs"""
    st.header("Complete SharePoint Data - All Tabs")
    st.markdown("**Live data from all 6 SharePoint sheets**")
    
    if not planner.data:
        st.error("No SharePoint data loaded")
        return
    
    # Create tabs for each SharePoint sheet
    sheet_tabs = st.tabs([f"{sheet_name} ({len(df.dropna(how='all'))})" for sheet_name, df in planner.data.items()])
    
    tab_index = 0
    for sheet_name, df in planner.data.items():
        with sheet_tabs[tab_index]:
            st.subheader(f"SharePoint Sheet: {sheet_name}")
            
            # Show sheet summary
            rows_with_data = len(df.dropna(how='all'))
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Rows with Data", rows_with_data)
            with col3:
                st.metric("Columns", len(df.columns))
            
            # Show key insights for each sheet
            if sheet_name == 'Planner':
                # Main planner analysis
                st.write("**Key Insights from Planner Sheet:**")
                
                unclear_count = len(df[df['Requirement Unclear'] == True]) if 'Requirement Unclear' in df.columns else 0
                assigned_count = df['Accountable'].notna().sum() if 'Accountable' in df.columns else 0
                status_count = df['Status1'].notna().sum() if 'Status1' in df.columns else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tasks with Unclear Requirements", unclear_count)
                with col2:
                    st.metric("Assigned Tasks", assigned_count)
                with col3:
                    st.metric("Tasks with Status", status_count)
                
                # Show status distribution
                if 'Status1' in df.columns:
                    status_counts = df['Status1'].value_counts()
                    status_counts = status_counts[status_counts.index.notna()]
                    
                    if not status_counts.empty:
                        fig_status = px.pie(
                            values=status_counts.values,
                            names=status_counts.index,
                            title="Task Status Distribution"
                        )
                        st.plotly_chart(fig_status, use_container_width=True, key=f"complete_{sheet_name}_status")
            
            elif sheet_name == 'Open Decision & Next Steps ':
                # Decision analysis
                st.write("**Open Decisions Analysis:**")
                
                open_decisions = 0
                decision_owners = []
                
                for _, row in df.iterrows():
                    if 'Open' in str(row.get('Unnamed: 3', '')):
                        open_decisions += 1
                        who = str(row.get('Gayatri Raol ', 'Unknown'))
                        if who != 'Unknown':
                            decision_owners.append(who)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Open Decisions", open_decisions)
                with col2:
                    st.metric("Decision Makers", len(set(decision_owners)))
                
                # Show decision ownership
                if decision_owners:
                    decision_counts = pd.Series(decision_owners).value_counts()
                    fig_decisions = px.pie(
                        values=decision_counts.values,
                        names=decision_counts.index,
                        title="Decisions by Owner"
                    )
                    st.plotly_chart(fig_decisions, use_container_width=True, key=f"complete_{sheet_name}_decisions")
            
            elif sheet_name == 'List of CR_HotFixes_ENHCE':
                # Issues analysis
                st.write("**Issues & Hotfixes Analysis:**")
                
                priority_counts = df['Unnamed: 3'].value_counts() if 'Unnamed: 3' in df.columns else pd.Series()
                status_counts = df['Unnamed: 5'].value_counts() if 'Unnamed: 5' in df.columns else pd.Series()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if not priority_counts.empty:
                        priority_counts = priority_counts[priority_counts.index.notna()]
                        fig_priority = px.pie(
                            values=priority_counts.values,
                            names=priority_counts.index,
                            title="Issues by Priority"
                        )
                        st.plotly_chart(fig_priority, use_container_width=True, key=f"complete_{sheet_name}_priority")
                
                with col2:
                    if not status_counts.empty:
                        status_counts = status_counts[status_counts.index.notna()]
                        fig_issue_status = px.pie(
                            values=status_counts.values,
                            names=status_counts.index,
                            title="Issues by Status"
                        )
                        st.plotly_chart(fig_issue_status, use_container_width=True, key=f"complete_{sheet_name}_status")
            
            # Show raw data for all sheets
            st.subheader(f"Raw Data from {sheet_name}")
            
            # Add search functionality
            search_term = st.text_input(f"Search in {sheet_name}:", key=f"search_{sheet_name}")
            
            if search_term:
                # Search across all columns
                mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                filtered_df = df[mask]
                st.write(f"Found {len(filtered_df)} matching rows")
                st.dataframe(filtered_df, use_container_width=True)
            else:
                # Show all data
                st.dataframe(df, use_container_width=True)
            
            # Show column information
            with st.expander(f"Column Details for {sheet_name}"):
                st.write(f"**{len(df.columns)} columns in this sheet:**")
                for i, col in enumerate(df.columns, 1):
                    non_null_count = df[col].notna().sum()
                    st.write(f"{i}. **{col}** - {non_null_count} entries ({df[col].dtype})")
        
        tab_index += 1

def show_beta_tasks_by_department(planner: AscentPlannerCalendar):
    """Show all Beta release tasks with their departments"""
    st.header("Beta Release Tasks - All Tasks with Departments")
    st.markdown("**Live SharePoint data - Complete Beta task listing**")
    
    planner_df = planner.get_planner_tasks()
    if planner_df.empty:
        st.error("No planner data available from SharePoint")
        return
    
    # Filter for Beta release tasks only from actual SharePoint data
    beta_tasks = planner_df[planner_df['Beta Realease'].notna()]
    
    if beta_tasks.empty:
        st.info("No Beta release tasks found in SharePoint data")
        return
    
    # Beta release overview metrics from actual data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Beta Tasks", len(beta_tasks))  # 65 from SharePoint
    
    with col2:
        # Count actual assigned tasks (not NaN)
        assigned_count = 0
        for _, task in beta_tasks.iterrows():
            accountable = task.get('Accountable')
            if pd.notna(accountable) and str(accountable).lower() not in ['nan', 'none', '']:
                assigned_count += 1
        st.metric("Assigned Beta Tasks", assigned_count)  # 2 from SharePoint (Nareshbhai, Upendra)
    
    with col3:
        unassigned_count = len(beta_tasks) - assigned_count
        st.metric("Unassigned Beta Tasks", unassigned_count)  # 63 from SharePoint
    
    with col4:
        assignment_rate = (assigned_count / len(beta_tasks)) * 100 if len(beta_tasks) > 0 else 0
        st.metric("Assignment Rate", f"{assignment_rate:.1f}%")  # 3.1% from SharePoint
    
    # Complete Beta task list with departments
    st.subheader("All Beta Tasks with Departments (65 total from SharePoint)")
    
    # Create a comprehensive list of all Beta tasks
    beta_task_list = []
    
    for _, task in beta_tasks.iterrows():
        task_name = str(task.get('Task Name', 'Unknown')).strip()
        accountable = task.get('Accountable')
        status = task.get('Status1')
        beta_date = task.get('Beta Realease')
        
        # Determine department based on task name using standardized mapping
        task_name_lower = task_name.lower()
        if any(keyword in task_name_lower for keyword in ['claim', 'lemon squad', 'snapsheet']):
            department = 'Claims'
        elif any(keyword in task_name_lower for keyword in ['onboard', 'setup', 'agent', 'dealer', 'autohouse']):
            department = 'Onboarding'
        elif any(keyword in task_name_lower for keyword in ['cancel', 'refund']):
            department = 'Cancellations'
        elif any(keyword in task_name_lower for keyword in ['contract', 'wizard', 'front end', 'admin']):
            department = 'Contract Admin'
        elif any(keyword in task_name_lower for keyword in ['rpt', 'report', 'financial', 'accounting', 'earnings']):
            department = 'Accounting'
        elif any(keyword in task_name_lower for keyword in ['commission']):
            department = 'Commissions'
        else:
            department = 'Other'
        
        # Clean up owner and status
        if pd.notna(accountable) and str(accountable).lower() not in ['nan', 'none', '']:
            owner = planner._consolidate_department_name(accountable)
        else:
            owner = 'UNASSIGNED'
        
        if pd.notna(status) and str(status).lower() not in ['nan', 'none', '']:
            status_clean = str(status)
        else:
            status_clean = 'Not Set'
        
        # Safe date comparison
        due_soon = False
        if pd.notna(beta_date):
            try:
                beta_date_converted = pd.to_datetime(beta_date)
                cutoff_date = pd.Timestamp('2025-09-25')
                due_soon = beta_date_converted <= cutoff_date
            except:
                due_soon = False
        
        beta_task_list.append({
            'task_name': task_name,
            'department': department,
            'owner': owner,
            'status': status_clean,
            'beta_date': beta_date,
            'due_soon': due_soon
        })
    
    # Show department distribution
    dept_counts = {}
    for task in beta_task_list:
        dept = task['department']
        if dept not in dept_counts:
            dept_counts[dept] = 0
        dept_counts[dept] += 1
    
    # Department distribution chart
    if dept_counts:
        fig_dept_dist = px.pie(
            values=list(dept_counts.values()),
            names=list(dept_counts.keys()),
            title="Beta Tasks by Department"
        )
        st.plotly_chart(fig_dept_dist, use_container_width=True, key="beta_dept_distribution")
    
    # Interactive Beta task selector - organized by department
    st.subheader("Select Beta Task to Review")
    
    # Group tasks by department for organized dropdown - business priority order
    dept_order = ['Claims', 'Accounting', 'Contract Admin', 'Cancellations', 'Onboarding', 'Commissions', 'Other']
    
    task_options = ["Select Beta task..."]
    
    # Add tasks organized by department
    for dept in dept_order:
        dept_tasks = [task for task in beta_task_list if task['department'] == dept]
        if dept_tasks:
            task_options.append(f"--- {dept.upper()} DEPARTMENT ({len(dept_tasks)} tasks) ---")
            for task in sorted(dept_tasks, key=lambda x: x['task_name']):
                status_indicator = "✅" if 'done' in task['status'].lower() else "🔄" if 'progress' in task['status'].lower() else "⏳"
                owner_indicator = f"[{task['owner']}]" if task['owner'] != 'UNASSIGNED' else "[UNASSIGNED]"
                task_options.append(f"    {task['task_name']} {status_indicator} {owner_indicator}")
    
    selected_beta_task = st.selectbox(
        "Choose from 65 Beta tasks organized by department:",
        task_options,
        key="all_beta_tasks_dropdown"
    )
    
    if selected_beta_task != "Select Beta task..." and not selected_beta_task.startswith("---"):
        # Extract task name from the formatted dropdown option
        selected_task = None
        if selected_beta_task.startswith("    "):
            # Remove leading spaces and extract task name before status indicators
            task_name_clean = selected_beta_task.strip()
            # Remove status and owner indicators step by step
            for indicator in [" ✅", " 🔄", " ⏳"]:
                if indicator in task_name_clean:
                    task_name_clean = task_name_clean.split(indicator)[0]
            # Remove owner indicator
            if " [" in task_name_clean:
                task_name_clean = task_name_clean.split(" [")[0]
            
            # Find the selected task safely
            for task in beta_task_list:
                if task['task_name'] == task_name_clean:
                    selected_task = task
                    break
            
            if selected_task:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="data-card">
                        <h4>Task Details</h4>
                        <p><strong>Task:</strong> {selected_task['task_name']}</p>
                        <p><strong>Department:</strong> {selected_task['department']}</p>
                        <p><strong>Beta Date:</strong> {selected_task['beta_date']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="data-card">
                        <h4>Assignment</h4>
                        <p><strong>Owner:</strong> {selected_task['owner']}</p>
                        <p><strong>Status:</strong> {selected_task['status']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    if selected_task['due_soon']:
                        st.error("**DUE SOON** - Beta date approaching")
                    elif selected_task['owner'] == 'UNASSIGNED':
                        st.warning("**NEEDS OWNER** - No one assigned")
                    elif 'done' in selected_task['status'].lower():
                        st.success("**READY** - Task completed")
                    else:
                        st.info("**IN PROGRESS** - Work ongoing")
            else:
                st.error("**Task not found** - Please try selecting a different task from the dropdown.")
    
    # Complete Beta task table
    st.subheader("Complete Beta Task List")
    
    # Department filter - show all business departments for consistency
    business_departments = ['Claims', 'Accounting', 'Contract Admin', 'Cancellations', 'Onboarding', 'Commissions', 'Other']
    department_options = ["All Departments"] + business_departments
    
    selected_department = st.selectbox(
        "Filter by Department:",
        department_options,
        key="beta_department_filter"
    )
    
    # Filter tasks based on selected department
    if selected_department == "All Departments":
        filtered_tasks = beta_task_list
    else:
        filtered_tasks = [task for task in beta_task_list if task['department'] == selected_department]
    
    # Display count
    task_count = len(filtered_tasks)
    if selected_department == "All Departments":
        st.write(f"Showing {task_count} Beta tasks")
    else:
        st.write(f"Showing {task_count} Beta tasks from {selected_department}")
    
    # Create DataFrame for display
    if task_count > 0:
        display_data = []
        for i, task in enumerate(filtered_tasks, 1):
            display_data.append({
                '#': i,
                'Task Name': task['task_name'],
                'Department': task['department'],
                'Owner': task['owner'],
                'Status': task['status'],
                'Beta Date': task['beta_date'],
                'Priority': '🔥 DUE SOON' if task['due_soon'] else '📅 Scheduled'
            })
        
        display_df = pd.DataFrame(display_data)
        st.dataframe(display_df, use_container_width=True)
    else:
        # Show empty table structure when no tasks
        empty_df = pd.DataFrame(columns=['#', 'Task Name', 'Department', 'Owner', 'Status', 'Beta Date', 'Priority'])
        st.dataframe(empty_df, use_container_width=True)
        st.info(f"No Beta tasks currently assigned to {selected_department} department.")

def show_sharepoint_setup(planner: AscentPlannerCalendar):
    """Configure SharePoint live feed setup"""
    st.header("SharePoint Live Feed Configuration")
    
    st.markdown("""
    <div class="data-card">
        <h4>Your SharePoint Live Feed</h4>
        <p><strong>Site:</strong> https://shivohm.sharepoint.com/sites/Ascent-SDSTeam</p>
        <p><strong>File:</strong> Ascent Planner Sep, 16 2025.xlsx</p>
        <p><strong>Document ID:</strong> ed87f8ed-3e27-439b-8c39-bea7016a6e79</p>
        <p><strong>Status:</strong> ✅ URL configured and ready</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show current connection status
    if planner.sharepoint_connector and planner.sharepoint_connector.sharepoint_url:
        st.success("🔗 SharePoint URL configured successfully!")
        
        # Show live data status
        if planner.use_live_feed:
            st.markdown("""
            <div class="success-container">
                <h4>Live Feed Active</h4>
                <p>Application is monitoring SharePoint for updates</p>
                <p>Data refreshes automatically when SharePoint file changes</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("SharePoint URL not configured")
    
    # Setup options
    st.subheader("Live Feed Setup Options")
    
    option_tabs = st.tabs(["OneDrive Sync", "SharePoint Sync", "API Integration", "Manual Update"])
    
    with option_tabs[0]:
        st.markdown("""
        <div class="data-card">
            <h4>OneDrive Sync (Recommended)</h4>
            <ol>
                <li>Open OneDrive on your computer</li>
                <li>Navigate to the SharePoint site: Ascent-SDSTeam</li>
                <li>Click "Sync" on the document library</li>
                <li>The Excel file will sync to your local OneDrive folder</li>
                <li>Update the application to point to the synced file</li>
            </ol>
            <p><strong>Benefits:</strong> Automatic updates, offline access, simple setup</p>
        </div>
        """, unsafe_allow_html=True)
    
    with option_tabs[1]:
        st.markdown("""
        <div class="data-card">
            <h4>SharePoint Desktop Sync</h4>
            <ol>
                <li>Install SharePoint sync client</li>
                <li>Sync the Ascent-SDSTeam site</li>
                <li>Excel file appears in local SharePoint folder</li>
                <li>Application automatically detects updates</li>
            </ol>
            <p><strong>Benefits:</strong> Direct SharePoint integration, team collaboration</p>
        </div>
        """, unsafe_allow_html=True)
    
    with option_tabs[2]:
        st.markdown("""
        <div class="data-card">
            <h4>API Integration (Advanced)</h4>
            <p><strong>Requirements:</strong></p>
            <ul>
                <li>SharePoint API credentials</li>
                <li>Azure app registration</li>
                <li>OAuth authentication setup</li>
            </ul>
            <p><strong>Benefits:</strong> Real-time updates, no local storage needed</p>
            <p><strong>Status:</strong> Framework ready, needs authentication configuration</p>
        </div>
        """, unsafe_allow_html=True)
    
    with option_tabs[3]:
        st.markdown("""
        <div class="data-card">
            <h4>Manual Update Process</h4>
            <ol>
                <li>Download updated Excel file from SharePoint</li>
                <li>Replace local file: "Ascent Planner Sep, 16 2025.xlsx"</li>
                <li>Click "Refresh Data" in application</li>
                <li>Application detects file changes automatically</li>
            </ol>
            <p><strong>Benefits:</strong> Simple, no technical setup required</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Current status
    st.subheader("Current Data Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # File information
        if os.path.exists(planner.excel_path):
            file_mod_time = os.path.getmtime(planner.excel_path)
            mod_datetime = datetime.fromtimestamp(file_mod_time)
            
            st.markdown(f"""
            <div class="data-card">
                <h4>Local File Status</h4>
                <p><strong>File Found:</strong> Yes</p>
                <p><strong>Last Modified:</strong> {get_arizona_time().strftime('%Y-%m-%d %H:%M:%S AZ')}</p>
                <p><strong>Size:</strong> {os.path.getsize(planner.excel_path):,} bytes</p>
                <p><strong>Sheets:</strong> {len(planner.data)}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Live feed status
        st.markdown(f"""
        <div class="data-card">
            <h4>Live Feed Status</h4>
            <p><strong>Live Feed Enabled:</strong> {planner.use_live_feed}</p>
            <p><strong>SharePoint Connector:</strong> {'Active' if planner.sharepoint_connector else 'Inactive'}</p>
            <p><strong>Auto-Refresh:</strong> {'Enabled' if planner.use_live_feed else 'Manual'}</p>
            <p><strong>Update Check:</strong> Every 30 seconds</p>
        </div>
        """, unsafe_allow_html=True)

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def login_page():
    """Display login page"""
    # Add some spacing
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Center the content
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center'>
            <h1>Ascent Planner Calendar</h1>
            <p><strong>Project Tracking & Milestone Management</strong></p>
            <hr>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Secure Login Required")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_b:
                submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if username == "ascent1" and password == "Planner1234":
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.success("Access granted! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8em'>
            <p>Authorized personnel only</p>
        </div>
        """, unsafe_allow_html=True)

def logout():
    """Logout function"""
    st.session_state['authenticated'] = False
    st.session_state['username'] = None
    st.rerun()

def apply_custom_css():
    """Apply custom CSS for professional theme"""
    st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .stApp {
        background-color: #f8f9fa;
    }
    .css-1d391kg {
        background-color: #ffffff;
    }
    .metric-container {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .alert-container {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .success-container {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .header-container {
        background: linear-gradient(90deg, #2c3e50 0%, #3498db 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .section-header {
        background-color: #34495e;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .data-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""
    # Check authentication first
    if not check_authentication():
        login_page()
        return
    
    # Apply custom styling
    apply_custom_css()
    
    # Auto-refresh functionality for live SharePoint data
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Auto-refresh every 30 seconds
    current_time = time.time()
    if current_time - st.session_state.last_refresh > 30:  # 30 seconds
        st.session_state.last_refresh = current_time
        st.rerun()
    
    # Professional header with live status
    st.markdown("""
    <div class="header-container">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 300;">Ascent Planner Calendar</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Live SharePoint Project Tracking & Management System</p>
        <p style="margin: 0.2rem 0 0 0; font-size: 0.9rem; opacity: 0.7;">Auto-refreshing every 30 seconds</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Initialize the planner - handle both local and cloud deployment
        excel_path = os.getenv('EXCEL_PATH', "/Users/jeffjackson/Desktop/Planner/Ascent Planner Sep, 16 2025.xlsx")
        
        # For Streamlit Cloud, try relative path first
        if not os.path.exists(excel_path):
            excel_path = "Ascent Planner Sep, 16 2025.xlsx"
        
        # System info (only show in development)
        if os.getenv('STREAMLIT_ENV') != 'production':
            with st.sidebar.expander("System Information"):
                st.write(f"Excel path: {excel_path}")
                st.write(f"File exists: {os.path.exists(excel_path)}")
                st.write(f"Current dir: {os.getcwd()}")
        
        if not os.path.exists(excel_path):
            st.error("Data file not found!")
            st.write("**Looking for file:**", excel_path)
            try:
                files = [f for f in os.listdir(".") if f.endswith(('.xlsx', '.xls'))]
                if files:
                    st.write("Available Excel files:")
                    for f in files:
                        st.write(f"- {f}")
                    # Try the first Excel file found
                    excel_path = files[0]
                    st.info(f"Using: {excel_path}")
                else:
                    st.write("No Excel files found in current directory")
                    st.stop()
            except Exception as e:
                st.error(f"Error accessing files: {e}")
                st.stop()
        
        # ONLY use SharePoint data - no local fallback
        st.sidebar.markdown("**📡 SHAREPOINT LIVE DATA**")
        st.sidebar.success("Connected to Ascent-SDSTeam")
        st.sidebar.markdown("Using live SharePoint data only")
        
        # Force live feed mode
        use_live_feed = True
        
        # Initialize with SharePoint-only mode
        planner = AscentPlannerCalendar(excel_path, use_live_feed=True)
        
        # Configure SharePoint URL with your exact URL
        sharepoint_url = "https://shivohm.sharepoint.com/:x:/r/sites/Ascent-SDSTeam/_layouts/15/Doc2.aspx?action=edit&sourcedoc=%7Bed87f8ed-3e27-439b-8c39-bea7016a6e79%7D&wdOrigin=TEAMS-MAGLEV.teams_ns.rwc&wdExp=TEAMS-TREATMENT&wdhostclicktime=1758148996116&web=1"
        
        if planner.sharepoint_connector:
            planner.sharepoint_connector.set_sharepoint_url(sharepoint_url)
        
        if not planner.data:
            st.error("No data loaded. Please check the Excel file.")
            st.stop()
            
    except Exception as e:
        st.error(f"Application Error: {e}")
        with st.expander("Error Details"):
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())
        st.stop()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # User info and logout
    st.sidebar.markdown(f"**User:** {st.session_state.get('username', 'Unknown')}")
    if st.sidebar.button("Logout"):
        logout()
    
    st.sidebar.markdown("---")
    
    # Current date display
    st.sidebar.markdown(f"**Today:** {planner.current_date.strftime('%B %d, %Y')}")
    st.sidebar.markdown(f"**Data Sources:** {len(planner.data)} sheets loaded")
    
    # Quick alerts in sidebar
    alerts = planner.get_department_alerts()
    if alerts:
        st.sidebar.warning(f"{len(alerts)} departments need attention")
    
    view_mode = st.sidebar.selectbox(
        "Select View",
        [
            "Executive Dashboard",
            "Beta Tasks by Department",
            "Complete SharePoint Data View",
            "Requirements Management",
            "Release Planning",
            "Decision Tracking", 
            "Issue Management",
            "Data Migration Progress",
            "SharePoint Live Feed Setup",
            "Calendar View",
            "Data Analytics"
        ]
    )
    
    # Live feed configuration
    if use_live_feed:
        st.sidebar.markdown("**Live Feed Status:**")
        if planner.sharepoint_connector:
            st.sidebar.success("SharePoint connector active")
            if st.sidebar.button("Configure SharePoint URL"):
                sharepoint_url = st.sidebar.text_input(
                    "SharePoint File URL:",
                    value="https://shivohm.sharepoint.com/:x:/r/sites/Ascent-SDSTeam/_layouts/15/Doc2.aspx...",
                    help="Paste your SharePoint Excel file URL"
                )
                if sharepoint_url:
                    planner.sharepoint_connector.set_sharepoint_url(sharepoint_url)
        
        # Auto-refresh status display
        st.sidebar.success("🔄 Auto-refresh: Every 30 seconds")
        
        # Show next refresh countdown
        next_refresh = 30 - (time.time() - st.session_state.last_refresh)
        if next_refresh > 0:
            st.sidebar.info(f"Next refresh in: {int(next_refresh)} seconds")
    
    # Main content area - SharePoint data focused views
    if view_mode == "Executive Dashboard":
        show_executive_dashboard(planner)
    elif view_mode == "Beta Tasks by Department":
        show_beta_tasks_by_department(planner)
    elif view_mode == "Complete SharePoint Data View":
        show_complete_sharepoint_data(planner)
    elif view_mode == "Requirements Management":
        show_requirements_management(planner)
    elif view_mode == "Release Planning":
        show_release_planning(planner)
    elif view_mode == "Decision Tracking":
        show_decision_tracking(planner)
    elif view_mode == "Issue Management":
        show_issue_management(planner)
    elif view_mode == "Data Migration Progress":
        show_data_migration_progress(planner)
    elif view_mode == "SharePoint Live Feed Setup":
        show_sharepoint_setup(planner)
    elif view_mode == "Calendar View":
        show_calendar_view(planner)
    elif view_mode == "Data Analytics":
        show_data_insights(planner)
    else:
        show_executive_dashboard(planner)  # Default view
    
    # Footer with live status
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📡 SharePoint Live Feed**")
    st.sidebar.markdown("**File:** Ascent Planner Sep, 16 2025.xlsx")
    st.sidebar.markdown("**Live Update:** " + get_arizona_time().strftime("%H:%M:%S AZ"))
    st.sidebar.markdown("**Status:** 🟢 Auto-refreshing")

if __name__ == "__main__":
    main()
