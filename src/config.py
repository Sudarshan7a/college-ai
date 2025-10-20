"""
Configuration file for data fetching operations.

Customize sitemaps, filters, and output settings here.
"""

# Sitemap Index URL (automatically extracts all sitemaps)
SITEMAP_INDEX = "https://sdit.ac.in/sitemap_index.xml"

# Individual Sitemap URLs to crawl
SITEMAPS = [
    "https://sdit.ac.in/post-sitemap.xml",
    "https://sdit.ac.in/post-sitemap2.xml",
    "https://sdit.ac.in/post-sitemap3.xml",
    "https://sdit.ac.in/post-sitemap4.xml",
    "https://sdit.ac.in/page-sitemap.xml",
    "https://sdit.ac.in/category-sitemap.xml",
    "https://sdit.ac.in/author-sitemap.xml"
]

# Empty template page URL for filtering similar pages
# Pages with content structure/text similar to this page will be skipped
TEMPLATE_URL = "https://sdit.ac.in/rakshitha-b-k-3/"

# Content filtering thresholds
CONTENT_FILTER = {
    'min_text_length': 500,      # Minimum characters
    'min_paragraphs': 3,         # Minimum <p> tags
    'min_sentences': 5           # Minimum sentences
}

# Template similarity threshold (0.0-1.0)
# 0.7 means if 70% of words are common with empty template, skip the page
TEMPLATE_SIMILARITY_THRESHOLD = 0.7

# Output settings
OUTPUT_DIR = "data/raw_pages"

# Request settings
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Logging level
LOG_LEVEL = "WARNING"  # DEBUG, INFO, WARNING, ERROR (Changed from INFO to reduce verbosity)

# Category Classification Schema
CATEGORIES = {
    "college_info": {
        "tag": "college_info",
        "description": "About, Vision, Mission, Administration, Principal's Message",
        "keywords": [
            "about", "vision", "mission", "administration", "principal", 
            "message", "history", "overview", "governance", "leadership",
            "chancellor", "director", "management", "institution"
        ]
    },
    "departments": {
        "tag": "departments",
        "description": "CSE, ECE, Mechanical, Civil, MBA, MCA departments",
        "keywords": [
            "department", "cse", "ece", "mechanical", "civil", "mba", "mca",
            "computer science", "electronics", "engineering", "faculty",
            "program", "curriculum", "syllabus", "branch", "stream"
        ]
    },
    "admissions": {
        "tag": "admissions",
        "description": "Eligibility, Application Form, Academic Calendar, Fees",
        "keywords": [
            "admission", "eligibility", "application", "form", "calendar",
            "fees", "intake", "enroll", "registration", "apply", "academic",
            "semester", "entrance", "exam", "criteria", "documents"
        ]
    },
    "placements": {
        "tag": "placements",
        "description": "Recruiters, Placement Stats, Training, Career",
        "keywords": [
            "placement", "recruiter", "career", "training", "job", "company",
            "statistics", "stats", "package", "salary", "interview", "tpo",
            "campus", "drive", "offer", "opportunity"
        ]
    },
    "events": {
        "tag": "events",
        "description": "Fests, Workshops, NSS, IEEE, Clubs, Activities",
        "keywords": [
            "event", "fest", "workshop", "seminar", "conference", "nss",
            "ieee", "club", "activity", "cultural", "technical", "sports",
            "competition", "hackathon", "symposium", "celebration"
        ]
    },
    "facilities": {
        "tag": "facilities",
        "description": "Campus, Library, Hostel, Transport, Infrastructure",
        "keywords": [
            "facility", "facilities", "campus", "library", "hostel", "transport",
            "infrastructure", "lab", "laboratory", "canteen", "cafeteria",
            "sports", "gym", "wifi", "building", "classroom", "auditorium"
        ]
    },
    "assistance": {
        "tag": "assistance",
        "description": "FAQs, Contact Info, Grievance, Student Helpdesk",
        "keywords": [
            "faq", "contact", "helpdesk", "grievance", "support", "query",
            "assistance", "help", "email", "phone", "address", "enquiry",
            "complaint", "redressal", "student services"
        ]
    },
    "admin_data": {
        "tag": "admin_data",
        "description": "Timetables, Reports, NAAC, SSR, Policies",
        "keywords": [
            "timetable", "schedule", "naac", "ssr", "report", "policy",
            "regulation", "rule", "guideline", "accreditation", "audit",
            "compliance", "governance", "document", "committee"
        ]
    }
}

# Data directories
DATA_DIR = "data/MyDrive/collegeAi/data"
EXTRACTED_DATA_DIR = "data/MyDrive/collegeAi/data/extracted"
CSV_LOG_FILE = "data/MyDrive/collegeAi/data/data_inventory.csv"

# Similarity thresholds
TEMPLATE_DUPLICATE_THRESHOLD = 0.85  # 85% similarity means duplicate
SEMANTIC_SIMILARITY_THRESHOLD = 0.5  # Minimum semantic similarity for classification
