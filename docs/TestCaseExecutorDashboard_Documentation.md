# TestCaseExecutor Dashboard — Full Documentation

---

## Table of Contents
1. Login Page
2. Sidebar Navigation
3. Test Runs Page
4. Test Run Details Page
5. New Test Run Page
6. Continue Test Run Page
7. Dev Config Page
8. Analysis Page

---

## 1. Login Page
- **Path:** `/`
- **Purpose:** Redirects to centralized authentication.
- **UI Elements:**
  - Message: "Redirecting to centralized login..."
  - Info: "Please sign in using the shared authentication portal."
- **Behavior:**
  - On load, redirects to login URL.
- **Screenshot:** ![Login Page](screenshots/login_page.png)

---

## 2. Sidebar Navigation
- **Component:** `Sidebar`
- **UI Elements:**
  - **Logo:** Top left, CERAI logo.
  - **Navigation Items:**
    - Home (icon: Home)
    - Test Runs (icon: Home)
    - Users (icon: Users)
    - Logout (icon: LogOut)
  - **User Info:** Username, email, role (Admin, etc.)
- **Behavior:**
  - Clicking navigation items routes to respective pages.
  - Logout clears session and redirects to login.
- **Screenshot:** ![Sidebar](screenshots/sidebar.png)

---

## 3. Test Runs Page
- **Path:** `/`
- **Purpose:** List and filter all test runs.
- **UI Elements:**
  - **Header:**
    - Logo (Test-run.png)
    - Title: "Test Runs"
  - **Filters:**
    - Target, Status, Domain, Plan, Metric, Language (dropdowns)
    - Each filter uses a select box populated from API.
  - **Table:**
    - Columns: Run ID, Run Name, Target, Status, Start Time, End Time, Domain, Duration, Average Score, Evaluation Time
    - Each row clickable to view details
    - Pagination controls (10 per page)
    - Sorting by Start/End Time
  - **Buttons:**
    - Filter clear/reset (if implemented)
- **Behavior:**
  - Changing filters updates table.
  - Clicking a row navigates to details.
- **Screenshot:** ![Test Runs Page](screenshots/test_runs_page.png)

---

## 4. Test Run Details Page
- **Path:** `/test-runs/:runName`
- **Purpose:** Show details for a specific test run.
- **UI Elements:**
  - **Summary Card:**
    - Run ID, Name, Target, Domain, Status, Start/End Time
    - Status color: Completed (green), Running (blue), Failed (red)
  - **Timeline:**
    - Visual timeline of events (RunTimeline)
    - Hovering highlights metrics/plans
  - **Test Case Table:**
    - Columns: Detail ID, Testcase Name, Metric, Plan, Conversation ID, Status, Score
    - Row click: Opens Modal with full conversation details
  - **Filters:**
    - Metric, Status (dropdowns)
  - **Modal:**
    - Shows: User Prompt, System Prompt, Agent Response, Testcase Name, Score, Reason, Target
    - Score indicator (circle, percentage)
  - **Scroll Hint:**
    - Shows if table is scrollable
- **Behavior:**
  - Filtering updates table.
  - Clicking a row opens modal.
  - Timeline updates on hover.
- **Screenshot:** ![Test Run Details](screenshots/test_run_details_page.png)

---

## 5. New Test Run Page
- **Path:** `/create-test-run`
- **Purpose:** Configure and start a new test run.
- **UI Elements:**
  - **Form Fields:**
    - Run Name (input)
    - Target (dropdown)
    - Test Plan (dropdown)
    - Test Case ID (input)
    - Metric (dropdown)
    - Max Test Cases (dropdown)
    - Domain (dropdown)
    - Language (dropdown)
  - **Custom Selects:** For dropdowns
  - **Loop Component:**
    - Shows progress of test case execution
    - Steps: Setup, Validation, Execution, Cleanup
  - **Buttons:**
    - Start/Run (AppButton)
    - Reset/Clear (if implemented)
- **Behavior:**
  - Selecting options updates form state.
  - Start triggers test run and shows progress.
- **Screenshot:** ![New Test Run](screenshots/new_test_run_page.png)

---

## 6. Continue Test Run Page
- **Path:** `/continue-run/:runName`
- **Purpose:** Resume an existing test run.
- **UI Elements:**
  - **Form Fields:**
    - Test Plan, Test Case ID, Metric, Max Test Cases, Domain, Language
  - **Accordion:** For grouping test case details
  - **Loop Component:** Progress for each test case
  - **Existing Run Details:**
    - Shows grouped details by plan/metric
  - **Buttons:**
    - Resume/Continue (AppButton)
- **Behavior:**
  - Selecting options updates form state.
  - Resume continues test run and updates progress.
- **Screenshot:** ![Continue Test Run](screenshots/continue_test_run_page.png)

---

## 7. Dev Config Page
- **Path:** `/__dev/config`
- **Purpose:** View and edit developer configuration.
- **UI Elements:**
  - **Fields:**
    - Database Engine (input)
    - Database File (input)
    - Backend Port (input)
    - Interface Manager Port (input)
  - **Buttons:**
    - Save/Update (AppButton)
- **Behavior:**
  - Editing fields updates config state.
  - Save sends update to backend.
- **Screenshot:** ![Dev Config](screenshots/dev_config_page.png)

---

## 8. Analysis Page
- **Path:** `/analyse/:runName`
- **Purpose:** Analyze results of a test run.
- **UI Elements:**
  - **Summary:** Run Name, Status, Start/End Time
  - **Details Table:**
    - Testcase Name, Metric, Strategy, Status, Score, Error
  - **Accordion:** Expand for more details
  - **Progress Bar/Indicator:** Shows analysis progress
- **Behavior:**
  - Shows real-time analysis progress
  - Expanding rows shows more details
- **Screenshot:** ![Analysis Page](screenshots/analysis_page.png)

---

> **Note:** Replace screenshot placeholders with actual images. Every button, filter, and table column is described above. For further detail, see the codebase for prop types and CSS classes.
