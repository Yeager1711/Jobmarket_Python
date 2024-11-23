from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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

        # Extract district/address
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
    return jobs_data


def format_job_text(job_text):
    """Replace newline characters with a clean format for better readability"""
    if job_text:
        return job_text.replace("\n", "<br>")
    return job_text


def fetch_job_details(jobs_data):
    # Path to ChromeDriver
    chrome_service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    for job in jobs_data:
        ref_link = job.get("ref_link")
        if ref_link and ref_link != "Unknown Link":
            driver.get(ref_link)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "job-description"))
                )
                # Parse the job detail page using BeautifulSoup
                page_soup = BeautifulSoup(driver.page_source, "html.parser")

                # Extract all job-description__item sections inside job-description
                job_description_section = page_soup.find("div", class_="job-description")
                expire_on_tag = page_soup.find("div", class_="job-detail__information-detail--actions-label")
                job["expire_on"] = expire_on_tag.text.strip() if expire_on_tag else "Unknown Expiry Date"
                
                if job_description_section:
                    job_details = job_description_section.find_all("div", class_="job-description__item")

                    # Extracting the first section as description
                    if len(job_details) > 0:
                        description_tag = job_details[0].find("div", class_="job-description__item--content")
                        job["description"] = format_job_text(description_tag.text.strip() if description_tag else "Unknown Description")

                    # Extracting the second section as requirement
                    if len(job_details) > 1:
                        requirement_tag = job_details[1].find("div", class_="job-description__item--content")
                        job["requirement"] = format_job_text(requirement_tag.text.strip() if requirement_tag else "Unknown Requirement")

                    # Extracting the third section as benefits
                    if len(job_details) > 2:
                        benefits_tag = job_details[2].find("div", class_="job-description__item--content")
                        job["benefits"] = format_job_text(benefits_tag.text.strip() if benefits_tag else "Unknown Benefits")

                    # Extracting the fourth section as work time
                    if len(job_details) > 3:
                        work_time_tag = job_details[3].find("div", class_="job-description__item--content")
                        job["work_time"] = format_job_text(work_time_tag.text.strip() if work_time_tag else "Unknown Work Time")

                    # Extracting the fifth section as application (if present)
                    if len(job_details) > 4:
                        application_tag = job_details[4].find("div", class_="job-description__item--content")
                        job["application"] = format_job_text(application_tag.text.strip() if application_tag else "Unknown Application")

                # Extracting additional details outside of job-description
                # 1. Extracting all job-detail__info--section-content-value elements
                info_value_divs = page_soup.find_all("div", class_="job-detail__info--section-content-value")
                for info_value in info_value_divs:
                    section_title = info_value.find_previous("div").text.strip() if info_value.find_previous("div") else "Unknown Section"
                    if section_title == "Địa điểm":
                        job["additional_location"] = format_job_text(info_value.text.strip())
                    elif section_title == "Kinh nghiệm":
                        job["additional_experience"] = format_job_text(info_value.text.strip())
                    # Add more translations as needed for other sections

                # 2. Extracting all box-general-group-info-value inside box-general-content
                box_general_content = page_soup.find("div", class_="box-general-content")
                if box_general_content:
                    box_general_info_values = box_general_content.find_all("div", class_="box-general-group-info-value")
                    for box_info in box_general_info_values:
                        group_title = box_info.find_previous("div").text.strip() if box_info.find_previous("div") else "Unknown Group"
                        if group_title == "Cấp bậc":
                            job["group_rank"] = format_job_text(box_info.text.strip())
                        elif group_title == "Kinh nghiệm":
                            job["group_experience"] = format_job_text(box_info.text.strip())
                        elif group_title == "Số lượng tuyển":
                            job["group_recruitment_number"] = format_job_text(box_info.text.strip())
                        elif group_title == "Hình thức làm việc":
                            job["group_work_type"] = format_job_text(box_info.text.strip())
                        elif group_title == "Giới tính":
                            job["group_gender"] = format_job_text(box_info.text.strip())

            except Exception as e:
                print(f"Error loading job details from {ref_link}:", e)
            
            # Add a delay to avoid overloading the server
            time.sleep(5)  # Wait for 2 seconds before processing the next job

            

    driver.quit()  # Close the browser

    # Display the job details
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


# Execute the functions
jobs_data = extract_feature_job_details()
fetch_job_details(jobs_data)
