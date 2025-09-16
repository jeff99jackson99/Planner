#!/usr/bin/env python3
"""
FastAPI web application for Ascent Planner Calendar
Provides REST API access to Excel data
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import os
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Ascent Planner Calendar API",
    description="API for tracking events, status, and actions from Excel spreadsheet",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class TaskResponse(BaseModel):
    source: str
    date: str
    date_type: str
    task_name: str
    accountable: str
    status: str
    requirement_unclear: bool = False
    details: Optional[List[str]] = None

class DepartmentAlert(BaseModel):
    department: str
    alerts: List[str]
    priority: str = "medium"

class OverviewResponse(BaseModel):
    current_date: str
    total_tasks: int
    open_decisions: int
    high_priority_issues: int
    unclear_requirements: int
    department_alerts: List[DepartmentAlert]

# Global data storage
planner_data: Dict[str, pd.DataFrame] = {}
EXCEL_PATH = "/Users/jeffjackson/Desktop/Planner/Ascent Planner Sep, 16 2025.xlsx"

def load_excel_data() -> bool:
    """Load data from Excel file"""
    global planner_data
    try:
        if not os.path.exists(EXCEL_PATH):
            return False
        
        excel_file = pd.ExcelFile(EXCEL_PATH)
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
            planner_data[sheet_name] = df
        
        return True
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return False

def get_planner_tasks() -> pd.DataFrame:
    """Get tasks from the main Planner sheet"""
    if 'Planner' not in planner_data:
        return pd.DataFrame()
    
    df = planner_data['Planner'].copy()
    df = df.dropna(how='all')  # Remove completely empty rows
    return df

def get_open_decisions() -> pd.DataFrame:
    """Get open decisions that need attention"""
    sheet_name = 'Open Decision & Next Steps '
    if sheet_name not in planner_data:
        return pd.DataFrame()
    
    df = planner_data[sheet_name].copy()
    df = df.dropna(how='all')
    return df

def get_hotfixes_status() -> pd.DataFrame:
    """Get current hotfixes and their status"""
    if 'List of CR_HotFixes_ENHCE' not in planner_data:
        return pd.DataFrame()
    
    df = planner_data['List of CR_HotFixes_ENHCE'].copy()
    df = df.dropna(how='all')
    return df

def get_tasks_for_date(target_date: date) -> List[Dict[str, Any]]:
    """Get all tasks and events for a specific date"""
    tasks = []
    
    # Check main planner sheet
    planner_df = get_planner_tasks()
    if not planner_df.empty:
        date_columns = ['Start Date', 'Beta Realease', 'PROD Release']
        
        for _, row in planner_df.iterrows():
            for date_col in date_columns:
                if date_col in row and pd.notna(row[date_col]):
                    try:
                        event_date = pd.to_datetime(row[date_col], errors='coerce')
                        if pd.notna(event_date) and event_date.date() == target_date:
                            task = {
                                'source': 'Planner',
                                'date': event_date.date().isoformat(),
                                'date_type': date_col,
                                'task_name': str(row.get('Task Name', 'Unknown Task')),
                                'accountable': str(row.get('Accountable', 'N/A')),
                                'status': str(row.get('Status1', 'N/A')),
                                'requirement_unclear': bool(row.get('Requirement Unclear', False))
                            }
                            tasks.append(task)
                    except:
                        continue
    
    # Check for data migration updates on this date
    if 'Data Migration Updates' in planner_data:
        migration_df = planner_data['Data Migration Updates'].copy()
        for col in migration_df.columns:
            if isinstance(col, pd.Timestamp):
                if col.date() == target_date:
                    date_data = migration_df[col].dropna()
                    if not date_data.empty:
                        task = {
                            'source': 'Data Migration',
                            'date': target_date.isoformat(),
                            'date_type': 'Migration Update',
                            'task_name': f"Data Migration Activities",
                            'accountable': 'Migration Team',
                            'status': 'In Progress',
                            'requirement_unclear': False,
                            'details': [str(item) for item in date_data.tolist()]
                        }
                        tasks.append(task)
    
    return tasks

def get_department_alerts() -> List[DepartmentAlert]:
    """Get departments that need attention"""
    alerts = []
    
    # Check open decisions
    decisions_df = get_open_decisions()
    if not decisions_df.empty:
        for _, row in decisions_df.iterrows():
            if 'Open' in str(row.get('Unnamed: 3', '')):  # Status column
                decision_text = str(row.get('Unnamed: 2', 'Unknown Decision'))
                who = str(row.get('Gayatri Raol ', 'Unknown'))
                
                # Find existing alert for this department or create new one
                existing_alert = next((alert for alert in alerts if alert.department == who), None)
                if existing_alert:
                    existing_alert.alerts.append(f"Open Decision: {decision_text}")
                else:
                    alerts.append(DepartmentAlert(
                        department=who,
                        alerts=[f"Open Decision: {decision_text}"],
                        priority="high"
                    ))
    
    # Check high priority hotfixes
    hotfixes_df = get_hotfixes_status()
    if not hotfixes_df.empty:
        for _, row in hotfixes_df.iterrows():
            priority = str(row.get('Unnamed: 3', '')).lower()  # Priority column
            status = str(row.get('Unnamed: 5', '')).lower()     # Status column
            
            if 'highest' in priority or ('high' in priority and 'done' not in status):
                summary = str(row.get('Claim Related Feedback/Change Request/ Hot Fixes', 'Unknown Issue'))
                dept = 'Development Team'
                
                existing_alert = next((alert for alert in alerts if alert.department == dept), None)
                if existing_alert:
                    existing_alert.alerts.append(f"High Priority Issue: {summary}")
                else:
                    alerts.append(DepartmentAlert(
                        department=dept,
                        alerts=[f"High Priority Issue: {summary}"],
                        priority="highest" if 'highest' in priority else "high"
                    ))
    
    # Check planner tasks with unclear requirements
    planner_df = get_planner_tasks()
    if not planner_df.empty:
        unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
        if not unclear_tasks.empty:
            for _, row in unclear_tasks.iterrows():
                task_name = str(row.get('Task Name', 'Unknown Task'))
                accountable = str(row.get('Accountable', 'Unknown'))
                
                if pd.notna(accountable) and accountable != 'nan' and accountable != 'N/A':
                    existing_alert = next((alert for alert in alerts if alert.department == accountable), None)
                    if existing_alert:
                        existing_alert.alerts.append(f"Unclear Requirements: {task_name}")
                    else:
                        alerts.append(DepartmentAlert(
                            department=accountable,
                            alerts=[f"Unclear Requirements: {task_name}"],
                            priority="medium"
                        ))
    
    return alerts

@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    if not load_excel_data():
        print("Warning: Could not load Excel data on startup")

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Ascent Planner Calendar API",
        "version": "1.0.0",
        "sheets_loaded": len(planner_data),
        "current_date": date.today().isoformat(),
        "endpoints": {
            "health": "/healthz",
            "overview": "/api/overview",
            "today": "/api/events/today",
            "date": "/api/events/{date}",
            "upcoming": "/api/events/upcoming/{days}",
            "alerts": "/api/departments/alerts",
            "sheets": "/api/sheets"
        }
    }

@app.get("/api/sheets")
async def get_sheets():
    """Get list of available sheets with metadata"""
    if not planner_data:
        raise HTTPException(status_code=503, detail="No data loaded")
    
    sheets_info = {}
    for sheet_name, df in planner_data.items():
        sheets_info[sheet_name] = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": [str(col) for col in df.columns],
            "has_data": not df.empty
        }
    
    return sheets_info

@app.get("/api/overview", response_model=OverviewResponse)
async def get_overview():
    """Get today's overview with key metrics"""
    current_date = date.today()
    
    # Count total tasks
    planner_df = get_planner_tasks()
    total_tasks = len(planner_df) if not planner_df.empty else 0
    
    # Count open decisions
    decisions_df = get_open_decisions()
    open_decisions = len(decisions_df) if not decisions_df.empty else 0
    
    # Count high priority issues
    hotfixes_df = get_hotfixes_status()
    high_priority = 0
    if not hotfixes_df.empty:
        for _, row in hotfixes_df.iterrows():
            if 'high' in str(row.get('Unnamed: 3', '')).lower():
                high_priority += 1
    
    # Count unclear requirements
    unclear_reqs = 0
    if not planner_df.empty:
        unclear_reqs = len(planner_df[planner_df['Requirement Unclear'] == True])
    
    # Get department alerts
    alerts = get_department_alerts()
    
    return OverviewResponse(
        current_date=current_date.isoformat(),
        total_tasks=total_tasks,
        open_decisions=open_decisions,
        high_priority_issues=high_priority,
        unclear_requirements=unclear_reqs,
        department_alerts=alerts
    )

@app.get("/api/events/today", response_model=List[TaskResponse])
async def get_todays_events():
    """Get events for today"""
    tasks = get_tasks_for_date(date.today())
    return [TaskResponse(**task) for task in tasks]

@app.get("/api/events/{target_date}", response_model=List[TaskResponse])
async def get_events_for_date_endpoint(target_date: str):
    """Get events for a specific date (YYYY-MM-DD format)"""
    if not planner_data:
        raise HTTPException(status_code=503, detail="No data loaded")
    
    try:
        target_date_obj = datetime.fromisoformat(target_date).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    tasks = get_tasks_for_date(target_date_obj)
    return [TaskResponse(**task) for task in tasks]

@app.get("/api/events/upcoming/{days}", response_model=List[TaskResponse])
async def get_upcoming_events(days: int = 30):
    """Get upcoming events for the next N days"""
    if not planner_data:
        raise HTTPException(status_code=503, detail="No data loaded")
    
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    current_date = date.today()
    upcoming_tasks = []
    
    for i in range(days):
        check_date = current_date + timedelta(days=i)
        tasks = get_tasks_for_date(check_date)
        upcoming_tasks.extend(tasks)
    
    # Sort by date
    upcoming_tasks.sort(key=lambda x: x['date'])
    return [TaskResponse(**task) for task in upcoming_tasks]

@app.get("/api/departments/alerts", response_model=List[DepartmentAlert])
async def get_department_alerts_endpoint():
    """Get departments that need attention"""
    if not planner_data:
        raise HTTPException(status_code=503, detail="No data loaded")
    
    return get_department_alerts()

@app.post("/api/reload")
async def reload_data():
    """Reload data from Excel file"""
    if load_excel_data():
        return {
            "message": "Data reloaded successfully", 
            "sheets": len(planner_data),
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to reload data")

@app.get("/api/stats")
async def get_statistics():
    """Get detailed statistics about the data"""
    if not planner_data:
        raise HTTPException(status_code=503, detail="No data loaded")
    
    stats = {
        "sheets": {},
        "summary": {
            "total_sheets": len(planner_data),
            "total_rows": 0,
            "total_columns": 0
        }
    }
    
    for sheet_name, df in planner_data.items():
        sheet_stats = {
            "rows": len(df),
            "columns": len(df.columns),
            "empty_rows": df.isnull().all(axis=1).sum(),
            "column_types": dict(df.dtypes.astype(str))
        }
        
        # Add specific insights for each sheet
        if sheet_name == 'Planner':
            sheet_stats["tasks_with_unclear_requirements"] = len(df[df.get('Requirement Unclear', False) == True])
            sheet_stats["tasks_with_status"] = len(df[df['Status1'].notna()]) if 'Status1' in df.columns else 0
        
        stats["sheets"][sheet_name] = sheet_stats
        stats["summary"]["total_rows"] += sheet_stats["rows"]
        stats["summary"]["total_columns"] += sheet_stats["columns"]
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
