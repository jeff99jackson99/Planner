# 📅 Ascent Planner Calendar

A comprehensive calendar application that tracks events, status, and actions from your Excel spreadsheet data. Built with Python, Streamlit, and FastAPI for complete project management and tracking.

![Planner Dashboard](https://img.shields.io/badge/Status-Active-green) ![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal)

## 🎯 Key Features

- **📋 Today's Overview**: View today's tasks with status and required actions
- **📅 Calendar View**: Navigate to any date to see scheduled events  
- **🎯 Upcoming Milestones**: Preview events for the next N days
- **🚨 Department Alerts**: Real-time notifications when departments need attention
- **📊 Data Insights**: Analytics and statistics from your project data
- **🔄 Live Updates**: Reload Excel data without restarting the application
- **🌐 REST API**: Programmatic access via FastAPI endpoints

## 📊 Your Data Analysis

Based on your Excel spreadsheet analysis:

- **📋 Total Tasks**: 193 tasks across 6 project sheets
- **⚠️ Unclear Requirements**: 82 tasks need requirement clarification  
- **🚨 Department Alerts**: 13 departments currently need attention
- **📈 Status Distribution**: 80 Not Started, 48 In Review, 16 In Progress
- **📅 Upcoming Milestones**: 11 milestones across 2 dates in next 30 days

### Data Sources Integrated

1. **Planner Sheet**: 194 tasks with dates, status, and accountability
2. **Open Decisions & Next Steps**: 20 critical decisions requiring attention
3. **Roadmap**: Upcoming releases and requirements tracking
4. **CR/HotFixes**: 89 bug reports and enhancement requests
5. **Data Migration**: Daily progress tracking with 200+ date columns
6. **Important Links**: Reference documentation and URLs

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Your Excel file: `Ascent Planner Sep, 16 2025.xlsx`

### Installation & Setup

```bash
# Clone the repository
git clone https://github.com/jeff99jackson99/Planner.git
cd Planner

# Install dependencies
make setup

# Analyze your Excel data structure
make analyze
```

### Running the Applications

#### Option 1: Streamlit Web Interface
```bash
make dev
```
Then open: http://localhost:8501

#### Option 2: FastAPI Server
```bash
make api
```
Then open: http://localhost:8000

## 📱 Application Views

### 1. Today's Overview
- Current date tasks and milestones
- Department alerts requiring immediate attention
- Quick statistics dashboard
- Status indicators for urgent items

### 2. Calendar View
- Interactive date picker
- Task details for any selected date
- Source tracking (Planner, Migration, etc.)
- Status and accountability information

### 3. Upcoming Milestones
- Configurable look-ahead period (1-90 days)
- Grouped by date with countdown
- Priority indicators and status tracking
- Comprehensive milestone details

### 4. Department Dashboard
- Real-time alerts by department/person
- Open decisions requiring attention
- High-priority issues tracking
- Workload distribution analytics

### 5. Data Insights
- Interactive analytics and visualizations
- Sheet-by-sheet data exploration
- Search functionality across all data
- Export capabilities for further analysis

## 🔗 API Endpoints

The FastAPI server provides RESTful access to your data:

### Core Endpoints
- `GET /` - Application info and available endpoints
- `GET /healthz` - Health check
- `GET /api/overview` - Today's overview with key metrics

### Event Endpoints  
- `GET /api/events/today` - Today's tasks and events
- `GET /api/events/{date}` - Events for specific date (YYYY-MM-DD)
- `GET /api/events/upcoming/{days}` - Upcoming events (1-365 days)

### Management Endpoints
- `GET /api/departments/alerts` - Department attention alerts
- `GET /api/sheets` - Available Excel sheets metadata
- `GET /api/stats` - Detailed data statistics
- `POST /api/reload` - Reload Excel data

### API Documentation
Interactive API docs available at: http://localhost:8000/docs

## 🛠️ Development Commands

```bash
# Setup and installation
make setup          # Install dependencies
make install        # Install in development mode

# Running applications  
make dev            # Run Streamlit web interface
make api            # Run FastAPI server
make analyze        # Analyze Excel file structure

# Maintenance
make clean          # Clean temporary files
make help           # Show all available commands
```

## 📋 Current Status & Alerts

### 🚨 Immediate Attention Required

**Development Team**: 45 high-priority issues
- Multiple critical bugs and enhancement requests
- Several items marked as "Highest" priority

**Requirements Clarification**: 82 tasks
- Significant portion of tasks have unclear requirements
- Impacts project timeline and delivery

**Open Decisions**: 20 pending decisions
- Cross-team decisions requiring stakeholder input
- Blocking progress on dependent tasks

## 🎯 Key Insights from Your Data

### Task Distribution
- **Not Started**: 80 tasks (41%)
- **In Review**: 48 tasks (25%) 
- **In Progress**: 16 tasks (8%)
- **Phase 2**: 7 tasks (4%)
- **Rework**: 7 tasks (4%)

### Department Workload
Multiple departments are actively engaged with varying workloads:
- Heavy involvement from Upendra, Naresh, and Shivani
- Cross-functional coordination between Matt/Madison teams
- Development team handling majority of technical issues

### Timeline Tracking
- **Data Migration**: Daily progress updates with detailed tracking
- **Release Planning**: Two major releases in roadmap
- **Issue Resolution**: Active bug fixing and enhancement pipeline

## 🔄 Data Refresh

The application automatically loads your Excel data on startup. To refresh data:

1. **Via Web Interface**: Click "🔄 Refresh Data" in sidebar
2. **Via API**: `POST /api/reload`  
3. **Via Restart**: Restart the application

## 📁 File Structure

```
Planner/
├── src/app/
│   ├── planner_app.py          # Streamlit application
│   ├── web.py                  # FastAPI application  
│   └── __main__.py             # FastAPI entry point
├── analyze_excel.py            # Excel analysis script
├── test_functionality.py      # Functionality test script
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project configuration
├── Makefile                   # Development commands
└── README.md                  # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions or issues:
- Create an issue in this repository
- Check the API documentation at `/docs`
- Review the Excel analysis output

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🎯 Ready to track your project milestones and keep departments on task!**

*Built with ❤️ using Python, Streamlit, FastAPI, and your comprehensive project data.*
