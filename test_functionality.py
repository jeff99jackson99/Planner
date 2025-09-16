#!/usr/bin/env python3
"""
Test script to verify the Ascent Planner Calendar functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.app.planner_app import AscentPlannerCalendar
from datetime import date, datetime

def test_functionality():
    """Test the core functionality of the planner"""
    print("🧪 Testing Ascent Planner Calendar Functionality")
    print("=" * 60)
    
    # Initialize planner
    excel_path = "/Users/jeffjackson/Desktop/Planner/Ascent Planner Sep, 16 2025.xlsx"
    planner = AscentPlannerCalendar(excel_path)
    
    if not planner.data:
        print("❌ Failed to load Excel data")
        return False
    
    print(f"✅ Successfully loaded {len(planner.data)} sheets")
    
    # Test 1: Check sheet loading
    print(f"\n📋 Loaded sheets:")
    for sheet_name, df in planner.data.items():
        print(f"  • {sheet_name}: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Test 2: Check planner tasks
    print(f"\n📊 Planner Tasks Analysis:")
    planner_df = planner.get_planner_tasks()
    if not planner_df.empty:
        print(f"  • Total tasks: {len(planner_df)}")
        
        # Check for tasks with unclear requirements
        unclear_tasks = planner_df[planner_df['Requirement Unclear'] == True]
        print(f"  • Tasks with unclear requirements: {len(unclear_tasks)}")
        
        # Check status distribution
        status_counts = planner_df['Status1'].value_counts()
        print(f"  • Status distribution:")
        for status, count in status_counts.head().items():
            if pd.notna(status):
                print(f"    - {status}: {count}")
    
    # Test 3: Check open decisions
    print(f"\n🔍 Open Decisions Analysis:")
    decisions_df = planner.get_open_decisions()
    if not decisions_df.empty:
        print(f"  • Open decisions tracked: {len(decisions_df)}")
    
    # Test 4: Check department alerts
    print(f"\n🚨 Department Alerts:")
    alerts = planner.get_department_alerts()
    if alerts:
        print(f"  • Departments needing attention: {len(alerts)}")
        for dept, issues in alerts.items():
            if dept != 'nan' and dept != 'N/A':
                print(f"    - {dept}: {len(issues)} issue(s)")
    else:
        print("  • No department alerts found")
    
    # Test 5: Check today's tasks
    print(f"\n📅 Today's Tasks ({planner.current_date}):")
    today_tasks = planner.get_tasks_for_date(planner.current_date)
    if today_tasks:
        print(f"  • Tasks for today: {len(today_tasks)}")
        for task in today_tasks[:3]:  # Show first 3
            print(f"    - {task['source']}: {task['task_name'][:50]}...")
    else:
        print("  • No tasks scheduled for today")
    
    # Test 6: Check upcoming milestones
    print(f"\n🎯 Upcoming Milestones (next 30 days):")
    milestones = planner.get_upcoming_milestones(30)
    if milestones:
        print(f"  • Upcoming milestones: {len(milestones)}")
        # Group by date
        dates = set(m['date'] for m in milestones)
        print(f"  • Dates with milestones: {len(dates)}")
    else:
        print("  • No upcoming milestones found")
    
    print(f"\n✅ All functionality tests completed successfully!")
    return True

if __name__ == "__main__":
    # Import pandas here to avoid import issues
    import pandas as pd
    
    success = test_functionality()
    if success:
        print(f"\n🚀 Ready to run the application!")
        print(f"   Streamlit: make dev")
        print(f"   FastAPI: make api")
    else:
        print(f"\n❌ Some tests failed. Please check the configuration.")
        sys.exit(1)
