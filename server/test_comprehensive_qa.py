"""
Comprehensive QA Testing Script for College AI
Tests all major question categories and generates unanswered questions report
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict
import uuid

# Test categories with questions
TEST_QUESTIONS = {
    "🧭 College Information": [
        "What is SDIT?",
        "Tell me about Shree Devi Institute of Technology.",
        "What's the vision and mission of SDIT?",
        "Who is the principal of SDIT?",
        "Show me the principal's message.",
        "Who are the administrators?",
        "Is SDIT accredited by NAAC?",
        "What makes SDIT unique?",
        "What's SDIT's institutional distinctiveness?"
    ],
    "💻 Departments & Courses": [
        "List all departments in SDIT.",
        "Tell me about Computer Science Engineering.",
        "Does SDIT offer Artificial Intelligence or Data Science courses?",
        "What's the difference between AI & ML and AI & DS departments?",
        "Show faculty list for Mechanical Engineering.",
        "Who are the professors in Civil Engineering?",
        "Is there an MBA or MCA program?",
        "Does SDIT offer PhD programs?"
    ],
    "🧑‍🏫 Admissions & Academics": [
        "How can I apply for admission at SDIT?",
        "What's the eligibility criteria for B.E / M.Tech / MBA?",
        "When does admission open?",
        "Where can I find the application form?",
        "What is the fee structure for each program?",
        "What is the academic calendar?",
        "Where can I find the timetable for exams?",
        "How can I download the institutional calendar of events?"
    ],
    "💼 Placements": [
        "What is the placement record of SDIT?",
        "Which companies visit SDIT for placements?",
        "How many students got placed in Infosys / TCS / Oracle?",
        "What is the average package?",
        "What is the placement percentage?",
        "Tell me about placement training at SDIT.",
        "How can I contact the placement cell?",
        "Show me the list of recruiters."
    ],
    "🎉 Events & Activities": [
        "What is Sambhram festival?",
        "When is the next tech fest?",
        "Show me past events.",
        "What sports activities are conducted?",
        "Are there IEEE or technical workshops?",
        "List the annual events at SDIT.",
        "How can I participate in events?"
    ],
    "🏫 Infrastructure & Facilities": [
        "What facilities does SDIT offer?",
        "Does SDIT have a hostel / cafeteria / library?",
        "Is there transportation provided by SDIT?",
        "Tell me about the campus.",
        "Where is SDIT located?",
        "Can I see the SSR report or infrastructure details?"
    ],
    "🗂️ Administrative / Structured Data": [
        "Where can I find the bus routes?",
        "Show me the academic timetable.",
        "What is the daily schedule?",
        "Where is SDIT located?",
        "How to reach SDIT by bus/train?"
    ],
    "🌐 External / Comparative": [
        "What do students say about SDIT?",
        "How does SDIT rank compared to other colleges?",
        "Is SDIT good for placements?",
        "What is the cut-off for SDIT on Shiksha?",
        "Show me SDIT details on Shiksha or Careers360."
    ],
    "⚡ General / Catch-all": [
        "Give me a summary of SDIT.",
        "Where can I find all courses?",
        "Does SDIT have NAAC accreditation?",
        "Who is the contact person for admissions?",
        "Show all events, facilities, and placement info."
    ]
}

API_BASE_URL = "http://localhost:8000"
SESSION_ID = f"test-session-{uuid.uuid4().hex[:8]}"

class QATestRunner:
    def __init__(self):
        self.results = []
        self.session_id = SESSION_ID
        self.message_counter = 0
        
    def test_question(self, category: str, question: str) -> Dict:
        """Test a single question and return result"""
        print(f"  Testing: {question[:60]}...")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/query",
                json={
                    "query": question,
                    "top_k": 3,
                    "include_sources": False,
                    "session_id": self.session_id,
                    "message_index": self.message_counter,
                    "message_id": f"test-{self.message_counter}"
                },
                timeout=30
            )
            
            self.message_counter += 1
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                confidence = data.get("confidence_score", 0.0)
                
                # Detect if answer shows uncertainty
                uncertainty_phrases = [
                    "i don't have",
                    "i don't know",
                    "i'm not sure",
                    "i cannot answer",
                    "insufficient information",
                    "not enough information",
                    "couldn't find"
                ]
                
                has_uncertainty = any(phrase in answer.lower() for phrase in uncertainty_phrases)
                
                result = {
                    "category": category,
                    "question": question,
                    "answer": answer,
                    "confidence": confidence,
                    "has_uncertainty": has_uncertainty,
                    "is_low_confidence": confidence < 0.6,
                    "status": "✅ Answered" if (not has_uncertainty and confidence >= 0.6) else "⚠️ Uncertain"
                }
                
                # Brief status
                status_icon = "✅" if result["status"] == "✅ Answered" else "⚠️"
                print(f"    {status_icon} Confidence: {confidence:.2f}")
                
                return result
            else:
                return {
                    "category": category,
                    "question": question,
                    "answer": f"API Error: {response.status_code}",
                    "confidence": 0.0,
                    "has_uncertainty": True,
                    "is_low_confidence": True,
                    "status": "❌ Error"
                }
                
        except Exception as e:
            return {
                "category": category,
                "question": question,
                "answer": f"Exception: {str(e)}",
                "confidence": 0.0,
                "has_uncertainty": True,
                "is_low_confidence": True,
                "status": "❌ Error"
            }
    
    def run_all_tests(self):
        """Run all test questions"""
        print("=" * 80)
        print("🧪 COMPREHENSIVE QA TESTING - COLLEGE AI")
        print("=" * 80)
        print(f"Session ID: {self.session_id}")
        print(f"API URL: {API_BASE_URL}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        total_questions = sum(len(questions) for questions in TEST_QUESTIONS.values())
        current = 0
        
        for category, questions in TEST_QUESTIONS.items():
            print(f"\n{category}")
            print("-" * 80)
            
            for question in questions:
                current += 1
                print(f"[{current}/{total_questions}]", end=" ")
                result = self.test_question(category, question)
                self.results.append(result)
                time.sleep(0.5)  # Rate limiting
        
        print("\n" + "=" * 80)
        print("✅ Testing Complete!")
        print("=" * 80)
    
    def generate_report(self):
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_results_{timestamp}.md"
        
        # Calculate statistics
        total = len(self.results)
        answered = len([r for r in self.results if r["status"] == "✅ Answered"])
        uncertain = len([r for r in self.results if r["status"] == "⚠️ Uncertain"])
        errors = len([r for r in self.results if r["status"] == "❌ Error"])
        
        # Group unanswered by category
        unanswered_by_category = {}
        for result in self.results:
            if result["status"] != "✅ Answered":
                category = result["category"]
                if category not in unanswered_by_category:
                    unanswered_by_category[category] = []
                unanswered_by_category[category].append(result)
        
        # Generate markdown report
        report = f"""# College AI - Comprehensive QA Test Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Session ID:** {self.session_id}  
**Total Questions Tested:** {total}

---

## 📊 Summary Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| ✅ **Successfully Answered** | {answered} | {(answered/total*100):.1f}% |
| ⚠️ **Uncertain/Low Confidence** | {uncertain} | {(uncertain/total*100):.1f}% |
| ❌ **Errors** | {errors} | {(errors/total*100):.1f}% |
| **TOTAL** | {total} | 100% |

---

## ⚠️ UNANSWERED / UNCERTAIN QUESTIONS

These questions need attention - either missing data or low confidence responses.

"""
        
        if unanswered_by_category:
            for category, results in unanswered_by_category.items():
                report += f"\n### {category}\n\n"
                for i, result in enumerate(results, 1):
                    report += f"**{i}. {result['question']}**\n"
                    report += f"- Status: {result['status']}\n"
                    report += f"- Confidence: {result['confidence']:.2f}\n"
                    report += f"- Has Uncertainty: {'Yes' if result['has_uncertainty'] else 'No'}\n"
                    report += f"- Answer Preview: {result['answer'][:150]}...\n\n"
        else:
            report += "\n🎉 **All questions were answered successfully!**\n\n"
        
        report += "\n---\n\n## ✅ SUCCESSFULLY ANSWERED QUESTIONS\n\n"
        
        answered_results = [r for r in self.results if r["status"] == "✅ Answered"]
        if answered_results:
            by_category = {}
            for result in answered_results:
                category = result["category"]
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(result)
            
            for category, results in by_category.items():
                report += f"\n### {category} ({len(results)} questions)\n\n"
                for result in results:
                    report += f"- ✅ {result['question']} (Confidence: {result['confidence']:.2f})\n"
        
        report += f"\n---\n\n## 📝 Full Test Results\n\n"
        report += "<details>\n<summary>Click to expand full results</summary>\n\n"
        
        for i, result in enumerate(self.results, 1):
            report += f"\n### {i}. {result['question']}\n\n"
            report += f"- **Category:** {result['category']}\n"
            report += f"- **Status:** {result['status']}\n"
            report += f"- **Confidence:** {result['confidence']:.2f}\n"
            report += f"- **Answer:**\n\n```\n{result['answer']}\n```\n\n"
        
        report += "</details>\n\n"
        report += "---\n\n*End of Report*\n"
        
        # Save report
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        # Also print summary to console
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Successfully Answered: {answered}/{total} ({(answered/total*100):.1f}%)")
        print(f"⚠️ Uncertain/Low Confidence: {uncertain}/{total} ({(uncertain/total*100):.1f}%)")
        print(f"❌ Errors: {errors}/{total} ({(errors/total*100):.1f}%)")
        print("=" * 80)
        
        if unanswered_by_category:
            print("\n⚠️ QUESTIONS NEEDING ATTENTION:")
            print("-" * 80)
            for category, results in unanswered_by_category.items():
                print(f"\n{category}: {len(results)} questions")
                for result in results:
                    print(f"  • {result['question']}")
        
        return report_file

def main():
    """Main test runner"""
    print("\n🚀 Starting Comprehensive QA Testing...\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ ERROR: Server is not responding properly!")
            print(f"   Please start the server: python server.py")
            return
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to server at {API_BASE_URL}")
        print(f"   Error: {e}")
        print(f"   Please start the server: python server.py")
        return
    
    print("✅ Server is running!")
    print()
    
    # Run tests
    runner = QATestRunner()
    runner.run_all_tests()
    
    # Generate report
    report_file = runner.generate_report()
    
    print(f"\n✅ Testing complete! Check {report_file} for full results.\n")

if __name__ == "__main__":
    main()
