# AI & Automation Learning Tracker (linked)

This pack links **Phase → Curriculum → Project → Weekly plan** with shared IDs so nothing is orphaned learning.

## Files (import each as a Google Sheets tab)

| File | Sheet name to use | Role |
|------|-------------------|------|
| `01_Phases_Projects.csv` | Phases | Master spine: each phase has one primary project |
| `02_Curriculum_Resources.csv` | Curriculum | Free resources; `LinkedProjectID` points at what you ship |
| `03_Projects_Ship.csv` | Projects | Hands-on builds + leave-localhost checklist |
| `04_Weekly_Plan.csv` | Weekly | 12-week calendar tied to PhaseID + ProjectID |
| `05_Daily_Log.csv` | DailyLog | Habit tracker; copy a row per study day |

## How the links work

```
PhaseID (P1…P10)
   ├── Curriculum rows (LinkedProjectID → PRJ-xx)
   ├── Weekly rows (ProjectID)
   └── Projects rows (ProjectID, DependsOn)
```

- Finish curriculum items for a phase → ship the linked `PRJ-xx`
- A phase is **Done** only when `Projects.Status = Done` and `LiveURL` is filled
- Optional extras: `PRJ-11` (approve queue), `PRJ-12` (observability)

## Import into Google Sheets (2 minutes)

1. Open [Google Sheets](https://sheets.google.com) → **Blank spreadsheet**
2. Name it: `AI Automation Learning Tracker 2026`
3. **File → Import → Upload** → choose `01_Phases_Projects.csv`
4. Import location: **Replace current sheet**
5. Repeat for the other CSVs with **Insert new sheet(s)**
6. Rename tabs: Phases / Curriculum / Projects / Weekly / DailyLog

### Optional Sheets formulas (after import)

On **Phases** in a helper column:

```text
=IFERROR(VLOOKUP(F2, Projects!A:K, 10, FALSE), "")
```

(Assumes `ProjectID` is column F on Phases and Status is column J on Projects — adjust if needed.)

Data validation for Status columns: `Not Started, In Progress, Done, Blocked, Skipped`

## Cadence reminder

- **10–14 hrs/week** for **12 weeks** core (~120–170 hrs)
- Then optional P9/P10 voice + growth projects
- Every week ends with something **deployed or CI-visible**, not only local

## When Zapier tasks are available

Ask me to push this pack into your Google Drive/Sheets automatically and keep `DailyLog` updated from chat.
