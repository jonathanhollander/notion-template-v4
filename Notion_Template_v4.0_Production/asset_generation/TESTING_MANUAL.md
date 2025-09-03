# Estate Planning Concierge v4.0 - Manual Testing Guide

## Testing Overview

This guide provides step-by-step instructions to manually test all the fixes implemented in the Estate Planning Concierge v4.0 Review Dashboard.

## Pre-Test Setup

### 1. Environment Setup
```bash
cd "/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation"

# Ensure environment variables are set
export REVIEW_API_TOKEN="estate-planning-review-2024"
export OPENROUTER_API_KEY="your-api-key-here"  # Optional, for full functionality
```

### 2. Dependencies Check
```bash
# Verify Python dependencies
python3 -c "import flask, aiosqlite, asyncio; print('✅ All dependencies available')"
```

## Test Plan Execution

### Test 1: CRITICAL - Database Connection Fix
**Purpose**: Verify that the fatal `_get_connection()` method calls are fixed.

**Steps**:
1. Start the dashboard:
   ```bash
   python3 review_dashboard.py
   ```

2. **Expected Result**: 
   - ✅ Dashboard starts without `AttributeError: 'AssetDatabase' object has no attribute '_get_connection'`
   - ✅ See message: "Starting Review Dashboard on http://localhost:5000"
   - ✅ No immediate crashes in the terminal

3. **If it fails**: Check for any remaining `_get_connection()` calls in the error traceback.

---

### Test 2: CRITICAL - Async/Sync Pattern Fix  
**Purpose**: Verify that asyncio.run() is used instead of event loop anti-patterns.

**Steps**:
1. Open browser to `http://localhost:5000`
2. Enter your name and click "Start Review Session"
3. Click "Load Evaluations" 

**Expected Result**:
- ✅ No warnings about "event loop is already running"
- ✅ No memory leaks or hanging processes
- ✅ Clean asyncio execution

**If it fails**: Look for warnings in terminal about event loops or hanging processes.

---

### Test 3: CRITICAL - Authentication System
**Purpose**: Verify token-based authentication is working.

**Steps**:
1. Test without token:
   ```bash
   curl -X POST http://localhost:5000/api/start-session \
        -H "Content-Type: application/json" \
        -d '{"reviewer_name": "Test User"}'
   ```
   
   **Expected**: HTTP 401 with authentication error message

2. Test with correct token:
   ```bash
   curl -X POST http://localhost:5000/api/start-session \
        -H "Content-Type: application/json" \
        -H "X-API-TOKEN: estate-planning-review-2024" \
        -d '{"reviewer_name": "Test User"}'
   ```
   
   **Expected**: HTTP 200 with success response

3. Test with wrong token:
   ```bash
   curl -X POST http://localhost:5000/api/start-session \
        -H "Content-Type: application/json" \
        -H "X-API-TOKEN: wrong-token" \
        -d '{"reviewer_name": "Test User"}'
   ```
   
   **Expected**: HTTP 401 with authentication error

---

### Test 4: CRITICAL - API Endpoint Consistency
**Purpose**: Verify frontend JavaScript matches backend API routes.

**Steps**:
1. Open browser developer tools (F12)
2. Navigate to `http://localhost:5000`
3. Fill in API token field: `estate-planning-review-2024`
4. Enter a reviewer name and click "Start Review Session"
5. Click "Load Evaluations"

**Expected Result**:
- ✅ No 404 errors in browser developer console
- ✅ API calls match exactly between frontend JS and backend routes
- ✅ Successful responses from all API endpoints

**Check Network Tab** for these endpoints:
- `/api/start-session` → 200 OK
- `/api/load-evaluations` → 200 OK  
- `/api/get-progress` → 200 OK

---

### Test 5: HIGH - Database State Management
**Purpose**: Verify in-memory state is removed and database is the single source of truth.

**Steps**:
1. Start dashboard and create a session
2. Make a decision on any competition (if available)
3. Stop the dashboard (Ctrl+C)
4. Restart the dashboard
5. Check if decisions are preserved

**Expected Result**:
- ✅ No references to `self.competitive_evaluations` or `self.human_decisions` in error logs
- ✅ All data persists across restarts
- ✅ Dashboard uses database queries for all state

---

### Test 6: HIGH - External Template File  
**Purpose**: Verify HTML template is loaded from external file instead of embedded string.

**Steps**:
1. Verify template file exists:
   ```bash
   ls -la templates/dashboard.html
   ```

2. Check the dashboard loads correctly:
   ```bash
   curl -s http://localhost:5000 | grep "Estate Planning Concierge v4.0"
   ```

**Expected Result**:
- ✅ `templates/dashboard.html` exists and is not empty
- ✅ Homepage loads correctly using external template
- ✅ No embedded HTML strings in `review_dashboard.py` (search for `dashboard_html = """`)

---

### Test 7: MEDIUM - Input Validation
**Purpose**: Verify API endpoints validate input properly.

**Steps**:
1. Test invalid JSON:
   ```bash
   curl -X POST http://localhost:5000/api/make-decision \
        -H "X-API-TOKEN: estate-planning-review-2024" \
        -H "Content-Type: application/json" \
        -d 'invalid json'
   ```
   **Expected**: HTTP 400 with JSON parsing error

2. Test missing required fields:
   ```bash
   curl -X POST http://localhost:5000/api/make-decision \
        -H "X-API-TOKEN: estate-planning-review-2024" \
        -H "Content-Type: application/json" \
        -d '{}'
   ```
   **Expected**: HTTP 400 with missing fields error

3. Test field length limits:
   ```bash
   curl -X POST http://localhost:5000/api/make-decision \
        -H "X-API-TOKEN: estate-planning-review-2024" \
        -H "Content-Type: application/json" \
        -d '{"competition_id": 1, "selected_prompt_text": "'"$(python3 -c "print('x' * 11000)")"'", "selected_model": "test", "reasoning": "test"}'
   ```
   **Expected**: HTTP 400 with field too long error

4. Test invalid data types:
   ```bash
   curl -X POST http://localhost:5000/api/get-competition/-1
   ```
   **Expected**: HTTP 400 with invalid competition_id error

---

### Test 8: MEDIUM - Production Configuration
**Purpose**: Verify deployment files are properly configured.

**Steps**:
1. Check WSGI configuration:
   ```bash
   python3 wsgi.py
   ```
   **Expected**: WSGI server starts on port 8000

2. Verify deployment documentation:
   ```bash
   ls -la DEPLOYMENT.md wsgi.py estate-planning-dev.service
   ```
   **Expected**: All deployment files exist and are readable

3. Test WSGI application creation:
   ```bash
   python3 -c "from wsgi import create_app; app = create_app(); print('✅ WSGI app created successfully')"
   ```
   **Expected**: No errors, successful app creation

---

## Final Integration Test

### Complete User Workflow
**Purpose**: Test the entire user workflow end-to-end.

**Steps**:
1. Start the dashboard
2. Open `http://localhost:5000` in browser
3. Enter your name: `Manual Tester`
4. Enter API token: `estate-planning-review-2024`
5. Click "Start Review Session" 
6. Click "Load Evaluations"
7. If competitions are available, make a decision and record it
8. Click "Export Decisions"
9. Check that progress is tracked correctly

**Expected Result**:
- ✅ Complete workflow executes without errors
- ✅ All UI interactions work properly
- ✅ Database operations complete successfully
- ✅ Authentication is enforced throughout
- ✅ Input validation catches invalid data
- ✅ Error messages are informative

## Troubleshooting

### Common Issues

1. **Dashboard won't start**
   - Check for remaining `_get_connection()` calls
   - Verify all Python dependencies are installed
   - Check for syntax errors in modified files

2. **Authentication errors**
   - Verify `REVIEW_API_TOKEN` environment variable
   - Check token is correctly passed in headers or form data
   - Ensure token matches exactly (case-sensitive)

3. **Database errors**  
   - Check database file permissions
   - Verify database file path is correct
   - Ensure database directory exists and is writable

4. **Template not found errors**
   - Verify `templates/dashboard.html` exists
   - Check Flask template directory configuration
   - Ensure file permissions allow reading

### Success Criteria

All tests should show:
- ✅ No fatal crashes or exceptions
- ✅ Authentication required and working
- ✅ Input validation preventing bad data
- ✅ Database persistence working
- ✅ External template loading
- ✅ API endpoints responding correctly
- ✅ Production deployment ready

### Test Completion

When all tests pass, the Estate Planning Concierge v4.0 Review Dashboard is ready for production deployment with all critical and high-priority fixes implemented.

**Manual Test Status**: ⏳ Ready for execution
**Next Steps**: Run each test in sequence and verify expected results