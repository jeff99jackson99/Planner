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
import os
from typing import Dict, List, Any, Optional
import calendar
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Ascent Planner Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AscentPlannerCalendar:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.data: Dict[str, pd.DataFrame] = {}
        self.current_date = datetime.now().date()
        self.load_data()
    
    def load_data(self) -> None:
        """Load data from Excel file"""
        try:
            if not os.path.exists(self.excel_path):
                st.error(f"📂 Excel file not found: {self.excel_path}")
                return
            
            excel_file = pd.ExcelFile(self.excel_path)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                self.data[sheet_name] = df
                
            st.success(f"✅ Loaded {len(self.data)} sheets from Excel file")
            
        except Exception as e:
            st.error(f"❌ Error loading Excel file: {e}")
    
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
                                task = {
                                    'source': 'Planner',
                                    'date': event_date.date(),
                                    'date_type': date_col,
                                    'task_name': str(row.get('Task Name', 'Unknown Task')),
                                    'accountable': str(row.get('Accountable', 'N/A')),
                                    'status': str(row.get('Status1', 'N/A')),
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
        """Get departments that need attention based on current status"""
        alerts = {}
        
        # Check open decisions
        decisions_df = self.get_open_decisions()
        if not decisions_df.empty:
            for _, row in decisions_df.iterrows():
                if 'Open' in str(row.get('Unnamed: 3', '')):  # Status column
                    decision_text = str(row.get('Unnamed: 2', 'Unknown Decision'))
                    who = str(row.get('Gayatri Raol ', 'Unknown'))
                    
                    if who not in alerts:
                        alerts[who] = []
                    alerts[who].append(f"Open Decision: {decision_text}")
        
        # Check high priority hotfixes
        hotfixes_df = self.get_hotfixes_status()
        if not hotfixes_df.empty:
            for _, row in hotfixes_df.iterrows():
                priority = str(row.get('Unnamed: 3', '')).lower()  # Priority column
                status = str(row.get('Unnamed: 5', '')).lower()     # Status column
                
                if 'highest' in priority or ('high' in priority and 'done' not in status):
                    summary = str(row.get('Claim Related Feedback/Change Request/ Hot Fixes', 'Unknown Issue'))
                    dept = 'Development Team'
                    
                    if dept not in alerts:
                        alerts[dept] = []
                    alerts[dept].append(f"High Priority Issue: {summary}")
        
        # Check planner tasks with unclear requirements
        planner_df = self.get_planner_tasks()
        if not planner_df.empty:
            unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
            if not unclear_tasks.empty:
                for _, row in unclear_tasks.iterrows():
                    task_name = str(row.get('Task Name', 'Unknown Task'))
                    accountable = str(row.get('Accountable', 'Unknown'))
                    
                    if pd.notna(accountable) and accountable != 'nan':
                        if accountable not in alerts:
                            alerts[accountable] = []
                        alerts[accountable].append(f"Unclear Requirements: {task_name}")
        
        return alerts
    
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

def show_todays_overview(planner: AscentPlannerCalendar):
    """Show today's overview with all relevant information"""
    st.header(f"📋 Today's Overview - {planner.current_date.strftime('%A, %B %d, %Y')}")
    
    # Today's tasks
    today_tasks = planner.get_tasks_for_date(planner.current_date)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader("📅 Today's Tasks")
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
                if dept != 'nan' and dept != 'N/A':
                    st.warning(f"**{dept}**")
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
        
        # Count high priority items
        hotfixes_df = planner.get_hotfixes_status()
        high_priority = 0
        if not hotfixes_df.empty:
            for _, row in hotfixes_df.iterrows():
                if 'high' in str(row.get('Unnamed: 3', '')).lower():
                    high_priority += 1
        st.metric("High Priority Issues", high_priority)
        
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
            st.plotly_chart(fig, use_container_width=True)

def show_data_insights(planner: AscentPlannerCalendar):
    """Show data insights and analytics"""
    st.header("📊 Data Insights & Analytics")
    
    # Sheet overview
    st.subheader("📋 Sheet Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        planner_df = planner.get_planner_tasks()
        st.metric("Total Tasks", len(planner_df) if not planner_df.empty else 0)
    
    with col2:
        decisions_df = planner.get_open_decisions()
        st.metric("Open Decisions", len(decisions_df) if not decisions_df.empty else 0)
    
    with col3:
        hotfixes_df = planner.get_hotfixes_status()
        st.metric("Issues Tracked", len(hotfixes_df) if not hotfixes_df.empty else 0)
    
    # Status distribution
    st.subheader("📈 Status Distribution")
    if not planner_df.empty:
        status_counts = planner_df['Status1'].value_counts()
        status_counts = status_counts[status_counts.index.notna()]
        
        if not status_counts.empty:
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Task Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Raw data access
    st.subheader("🔍 Raw Data Explorer")
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

def main():
    """Main application function"""
    st.title("📅 Ascent Planner Calendar")
    st.markdown("*Comprehensive project tracking and calendar management*")
    
    # Initialize the planner
    excel_path = "/Users/jeffjackson/Desktop/Planner/Ascent Planner Sep, 16 2025.xlsx"
    planner = AscentPlannerCalendar(excel_path)
    
    if not planner.data:
        st.error("❌ No data loaded. Please check the Excel file.")
        st.stop()
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    
    # Current date display
    st.sidebar.markdown(f"**📅 Today:** {planner.current_date.strftime('%B %d, %Y')}")
    st.sidebar.markdown(f"**📊 Sheets Loaded:** {len(planner.data)}")
    
    # Quick alerts in sidebar
    alerts = planner.get_department_alerts()
    if alerts:
        st.sidebar.warning(f"⚠️ {len(alerts)} department(s) need attention!")
    
    view_mode = st.sidebar.selectbox(
        "Select View",
        [
            "📋 Today's Overview",
            "📅 Calendar View", 
            "🎯 Upcoming Milestones",
            "🏢 Department Dashboard",
            "📊 Data Insights"
        ]
    )
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        planner.load_data()
        st.rerun()
    
    # Main content area
    if view_mode == "📋 Today's Overview":
        show_todays_overview(planner)
    elif view_mode == "📅 Calendar View":
        show_calendar_view(planner)
    elif view_mode == "🎯 Upcoming Milestones":
        show_upcoming_milestones(planner)
    elif view_mode == "🏢 Department Dashboard":
        show_department_dashboard(planner)
    elif view_mode == "📊 Data Insights":
        show_data_insights(planner)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📁 Data Source:** Ascent Planner Sep, 16 2025.xlsx")
    st.sidebar.markdown("**🔄 Last Updated:** " + datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    main()
