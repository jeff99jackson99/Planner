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
import hashlib

# Page configuration
st.set_page_config(
    page_title="Ascent Planner Calendar",
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
                
            st.success(f"Loaded {len(self.data)} sheets from Excel file")
            
        except Exception as e:
            st.error(f"Error loading Excel file: {e}")
    
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
        st.metric("Total Tasks", total_tasks, help="Total tasks across all project sheets")
    with col2:
        st.metric("Open Decisions", open_decisions, help="Decisions requiring immediate attention")
    with col3:
        st.metric("Critical Issues", critical_issues, help="High priority issues requiring Ascent action")
    with col4:
        st.metric("Unclear Requirements", unclear_reqs, help="Tasks needing requirement clarification")
    
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
    
    # Recent Activity Summary
    st.markdown('<div class="section-header"><h3>System Information</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="data-card">
            <h4>Data Sources</h4>
            <p><strong>{len(planner.data)} Excel sheets</strong> loaded successfully</p>
            <ul>
        """, unsafe_allow_html=True)
        
        for sheet_name, df in planner.data.items():
            st.markdown(f"<li>{sheet_name}: {len(df)} rows</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="data-card">
            <h4>System Status</h4>
            <p><strong>Last Updated:</strong> {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
            <p><strong>Current Date:</strong> {planner.current_date.strftime('%A, %B %d, %Y')}</p>
            <p><strong>Data File:</strong> Ascent Planner Sep, 16 2025.xlsx</p>
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
            st.metric("Total Tasks", len(planner_df) if not planner_df.empty else 0)
        with col2:
            st.metric("Open Decisions", len(decisions_df) if not decisions_df.empty else 0)
        with col3:
            st.metric("Issues Tracked", len(hotfixes_df) if not hotfixes_df.empty else 0)
        with col4:
            st.metric("Data Sources", len(planner.data))
        
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
        st.metric("Clear Requirements", len(clear_tasks))
    with col2:
        st.metric("Unclear Requirements", len(unclear_tasks))
    with col3:
        clarity_rate = (len(clear_tasks) / len(planner_df)) * 100
        st.metric("Clarity Rate", f"{clarity_rate:.1f}%")
    
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
    
    # Detailed unclear requirements list
    st.subheader("Tasks Needing Requirement Clarification")
    if not unclear_tasks.empty:
        for _, task in unclear_tasks.iterrows():
            task_name = str(task.get('Task Name', 'Unknown'))
            accountable = str(task.get('Accountable', 'Unassigned'))
            status = str(task.get('Status1', 'Not Set'))
            
            if pd.notna(accountable) and accountable != 'nan':
                st.write(f"**{task_name}** - Assigned to: {accountable} - Status: {status}")
            else:
                st.write(f"**{task_name}** - UNASSIGNED - Status: {status}")

def show_release_planning(planner: AscentPlannerCalendar):
    """Manage release planning for Beta and Production"""
    st.header("Release Planning")
    
    planner_df = planner.get_planner_tasks()
    if planner_df.empty:
        st.error("No planner data available")
        return
    
    # Release metrics
    beta_tasks = planner_df['Beta Realease'].notna().sum()
    prod_tasks = planner_df['PROD Release'].notna().sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Beta Release Tasks", beta_tasks)
    with col2:
        st.metric("Production Tasks", prod_tasks)
    with col3:
        total_release_tasks = beta_tasks + prod_tasks
        st.metric("Total Release Tasks", total_release_tasks)
    
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
    
    # Release timeline
    st.subheader("Release Timeline")
    
    # Show beta tasks with dates
    if not beta_df.empty:
        st.write("**Beta Release Tasks:**")
        for _, task in beta_df.iterrows():
            task_name = str(task.get('Task Name', 'Unknown'))
            beta_date = task.get('Beta Realease')
            status = str(task.get('Status1', 'Not Set'))
            accountable = str(task.get('Accountable', 'Unassigned'))
            
            if pd.notna(beta_date):
                st.write(f"• **{task_name}** - {beta_date} - {status} - {accountable}")

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
    
    # Professional header
    st.markdown("""
    <div class="header-container">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 300;">Ascent Planner Calendar</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Project Tracking & Milestone Management System</p>
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
        
        planner = AscentPlannerCalendar(excel_path)
        
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
            "Requirements Management",
            "Release Planning",
            "Decision Tracking", 
            "Issue Management",
            "Data Migration Progress",
            "Calendar View",
            "Data Analytics"
        ]
    )
    
    # Refresh button
    if st.sidebar.button("Refresh Data"):
        planner.load_data()
        st.rerun()
    
    # Main content area - task management focused views
    if view_mode == "Executive Dashboard":
        show_executive_dashboard(planner)
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
    elif view_mode == "Calendar View":
        show_calendar_view(planner)
    elif view_mode == "Data Analytics":
        show_data_insights(planner)
    else:
        show_executive_dashboard(planner)  # Default view
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Source:** Ascent Planner Sep, 16 2025.xlsx")
    st.sidebar.markdown("**Last Updated:** " + datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    main()
