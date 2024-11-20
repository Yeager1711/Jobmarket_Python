from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests
import json
import re
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get ApiUrl from environment
api_url = os.getenv('ApiUrl')

def extract_feature_job_details():
    chrome_service = Service(ChromeDriverManager().install())
    chrome_options = Options()

    # Initialize the driver
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    # URL of the webpage
    url = 'https://www.topcv.vn'  # Replace with the actual URL
    driver.get(url)

    # Use WebDriverWait to ensure elements are loaded
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "col-md-4"))
        )
    except Exception as e:
        print("Error waiting for elements:", e)
        driver.quit()
        return

    # Scroll down the page to load all content (if necessary)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Find all job elements
    job_divs = driver.find_elements(By.CLASS_NAME, "col-md-4")

    jobs_data = []  # List to store job details

    # Iterate through each job element to extract basic info and ref_link
    for div in job_divs:
        html_content = div.get_attribute("outerHTML")
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract the data-job-id attribute
        data_job_id = div.get_attribute("data-job-id")

        # Extract job title
        job_title_tag = soup.find("strong", class_="job_title")
        job_title = job_title_tag.text.strip() if job_title_tag else "Unknown Title"

        # Extract company name
        company_name_tag = soup.find("span", class_="company-name")
        company_name = company_name_tag.text.strip() if company_name_tag else "Unknown Company"

        # Extract salary
        salary_tag = soup.find("div", class_="salary")
        salary = salary_tag.text.strip() if salary_tag else "Unknown Salary"

        # Extract address
        address_tag = soup.find("div", class_="address")
        if address_tag:
            # Use BeautifulSoup to remove HTML tags and get the text
            district_html = address_tag.get("data-original-title", "")
            district_soup = BeautifulSoup(district_html, "html.parser")
            district = district_soup.get_text(strip=True)
        else:
            district = "Unknown District"


        # Extract images
        images = soup.find_all("img", class_="img-responsive")
        image_urls = [img['src'] for img in images if 'src' in img.attrs]

        # Extract salary range using regex
        salary_from = 0
        salary_to = 0
        if salary != "Unknown Salary":
            salary_match = re.findall(r'\d+', salary)
            if len(salary_match) >= 2:
                salary_from = int(salary_match[0])
                salary_to = int(salary_match[1])

        # Define a reference link
        ref_link_tag = soup.find("a", href=True)
        ref_link = ref_link_tag['href'] if ref_link_tag else "Unknown Link"

        # Prepare the job data
        job_data = {
            "job_Id": data_job_id,
            "title": job_title,
            "company_name": company_name,
            "salary": salary,
            "district_name": district,
            "image": image_urls[0] if image_urls else "",
            "description": "Pending",  # Placeholder
            "requirement": "Pending",   # Placeholder
            "salary_from": salary_from,
            "salary_to": salary_to,
            "companyId": data_job_id,
            "expire_on": "",
            "ref_job_Id": data_job_id,
            "ref_link": ref_link
        }
        jobs_data.append(job_data)

    driver.quit()  # Close the browser
    headers = {'Content-Type': 'application/json'}
    for job_data in jobs_data:
        try:
            response = requests.post(f"{api_url}/jobs", json=job_data, headers=headers)
            response_json = response.json()

            # Log response in a formatted manner
            print(f"Status Code: {response.status_code}")
            print("Response JSON:")
            print(json.dumps(response_json, indent=4, ensure_ascii=False))
        except Exception as e:
            print("Error sending data to the server:", e)
# Call the function to execute
extract_feature_job_details()
