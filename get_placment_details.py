import requests
from bs4 import BeautifulSoup
import os
import csv
import time

# Folder to save all CSVs
output_dir = "data_23_10_25/placements"
os.makedirs(output_dir, exist_ok=True)

years = range(2011, 2025)  # 2011 to 2024
base_url = "https://sdit.ac.in/category/{year}/page/{page}/"

for year in years:
    page = 1
    csv_file = os.path.join(output_dir, f"students_{year}.csv")
    
    with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Page", "Student Name", "Department", "Company Logo URL"])
        
        while True:
            url = base_url.format(year=year, page=page)
            response = requests.get(url)
            
            if response.status_code == 404 or "404" in response.text:
                print(f"Year {year}: stopped at page {page}")
                break
            
            soup = BeautifulSoup(response.text, "html.parser")
            student_divs = soup.find_all("div", class_="cm-place")
            
            if not student_divs:
                print(f"Year {year}: no students found at page {page}, stopping.")
                break
            
            for div in student_divs:
                cols = div.find_all("div", class_="col-md-3")
                if len(cols) < 4:
                    continue  # skip malformed entries
                
                name = cols[0].get_text(strip=True)
                department = cols[2].get_text(strip=True)
                company_logo = cols[3].find("img")["src"] if cols[3].find("img") else ""
                
                print(year, page, name, department, company_logo)
                writer.writerow([page, name, department, company_logo])
            
            page += 1
            time.sleep(1)  # polite delay to avoid overloading the server

print("Scraping completed for all years.")
