# Comprehensive QA Testing Guide

This guide helps you test all major question categories and identify unanswered questions.

## 🚀 Quick Start

### Step 1: Start the Server

```powershell
cd server
python server.py
```

Wait for the message: `✅ SERVER READY FOR REQUESTS!`

### Step 2: Run the Test Script

Open a new terminal:

```powershell
cd server
python test_comprehensive_qa.py
```

### Step 3: Check Results

The script will:

1. Test **all 62 questions** across 9 categories
2. Generate a detailed markdown report: `test_results_YYYYMMDD_HHMMSS.md`
3. Show summary in console

## 📊 What Gets Tested

### Categories (62 Total Questions):

- 🧭 **College Information** (9 questions)
- 💻 **Departments & Courses** (8 questions)
- 🧑‍🏫 **Admissions & Academics** (8 questions)
- 💼 **Placements** (8 questions)
- 🎉 **Events & Activities** (7 questions)
- 🏫 **Infrastructure & Facilities** (6 questions)
- 🗂️ **Administrative / Structured Data** (5 questions)
- 🌐 **External / Comparative** (5 questions)
- ⚡ **General / Catch-all** (5 questions)

## 📝 Understanding Results

### Status Types:

- ✅ **Answered** - High confidence, no uncertainty phrases
- ⚠️ **Uncertain** - Low confidence or LLM shows uncertainty
- ❌ **Error** - API error or exception

### Confidence Scoring:

- `> 0.6` = Good confidence
- `0.0 to 0.6` = Low confidence (needs attention)
- `< 0.0` = Very low confidence (definitely needs data)

## 📄 Report Contents

The generated report includes:

1. **Summary Statistics** - Overall pass/fail rates
2. **Unanswered Questions** - Grouped by category with reasons
3. **Successfully Answered** - Questions that worked well
4. **Full Results** - Complete test output with all answers

## 🔍 Finding Unanswered Questions

After running the test, check:

1. **Console Output** - Quick summary of issues
2. **Markdown Report** - Detailed breakdown of all uncertain/failed questions
3. **Log File** - `data/logs/unanswered_questions.jsonl` - Persistent log

## 💡 Tips

- Run tests **after major data updates**
- Compare results **before and after** changes
- Focus on **high-priority categories** first (Admissions, Placements)
- Test **weekly** to track improvements
- Share reports with **content team** to identify gaps

---

_Happy Testing! 🧪_
