"""
VULNERABILITY ALERT MANAGEMENT DASHBOARD
DEVELOPER INTEGRATION CONTRACT

Use this file when another developer already has a Streamlit application
and needs to incorporate the vulnerability-management requirements.

SOURCE DATA:
The CSV is expected from VVMS. Preserve the source column names.

BUSINESS DEFINITIONS:
- RRD: final remediation date.
- 2-Week Mark: operational due date used by the team.
  Expected value = RRD minus 14 calendar days.
- Days Left: supplied by VVMS, but the dashboard should ALSO calculate
  days remaining from today's date to the 2-Week Mark for validation.
- ATC: Application Technical Contact (person/contact), not an exception status.

REQUIRED SOURCE COLUMNS:
1. 2-Week Mark
2. Days Left
3. RRD
4. Score
5. Application
6. Environment
7. App ID
8. Host
9. Server Type
10. Scheduling
11. Scanner Location
12. Title
13. Tracking ID
14. QID
15. ATC
16. Primary?
17. Intrusive?
18. Patch Available?
19. Cluster Group

REQUIRED INTERACTIVITY:
- Global search
- Multi-select filters
- Score range filter
- Dashboard KPIs update with filters
- Charts update with filters
- Spreadsheet-style findings workspace
- Column sorting
- Row selection / finding-detail view
- Download/export of the filtered dataset

REQUIRED KPI CARDS:
- Total findings
- Overdue operational deadline
- Due within 7 days
- Due within 14 days
- High score findings
- Patch available
- Intrusive
- Unique applications
- Unique ATCs

REQUIRED DERIVED FIELDS:
- Calculated Days Left
- Overdue
- Due Bucket
- High Score
- Intrusive Flag
- Patch Available Flag
- Operational Priority
- Expected 2-Week Mark
- Deadline Date Difference
- Days Left Difference

SUGGESTED OPERATIONAL PRIORITY:
1. Immediate Attention
2. Coordination Required
3. Patch / Remediate
4. Due Soon
5. Plan Remediation
6. Review Date
7. On Track

SPREADSHEET / WORKSPACE:
The findings table is a primary feature of the application, not a secondary
table under charts. It should use the same filtered DataFrame as the dashboard.

DATA SAFETY:
Do not place real production vulnerability data in a public repository.
Use sanitized or synthetic CSV files for development and demos.
"""
