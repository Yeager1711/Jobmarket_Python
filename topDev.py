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
import random
import string


load_dotenv()
api_url = os.getenv('ApiUrl')


# Function to generate a random job_id with numbers between 0 and 9

def extract_job(): 
    chrome_service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    
    # Initialize the driver
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    
    # URL của trang web
    url = 'https://topdev.vn/it-jobs?src=topdev.vn&medium=mainmenu'
    driver.get(url)
    
    try:
        time.sleep(30) 
    except Exception as e:
        print("Error waiting for elements:", e)
        driver.quit()
        return
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    job_list = []
    job_ids = set()
    jobs = soup.find_all('a', href=True)  # Tìm tất cả các thẻ <a> có thuộc tính href
    
    for job in jobs:
        job_url = job['href']
        if '/detail-jobs/' in job_url:
            job_data = {}
            
            job_Id_match = re.search(r'-(\d+)\??', job_url)
            job_Id = job_Id_match.group(1) if job_Id_match else None
            if not job_Id or job_Id in job_ids:
                continue
            job_ids.add(job_Id)

        
            
            # Lấy ref_link (toàn bộ href)
            ref_link_tag =  'https://topdev.vn' + job_url  
            ref_link = ref_link_tag
            
            # Lấy job title
            job_title_tag = job.find('a', class_='text-lg font-bold transition-all text-primary')
            if not job_title_tag:
                job_title_tag = job.find('a', class_='text-lg font-bold transition-all hover:text-primary')
            job_title = job_title_tag.text.strip() if job_title_tag else ""
            
           # Kiểm tra class 'text-gray-600 transition-all hover:text-primary' trước
            company_name_tag = job.find('a', class_='text-gray-600 transition-all hover:text-primary')
            if not company_name_tag:
                company_name_tag = job.find('a', class_='text-lg font-bold transition-all hover:text-primary')

            # Lấy tên công ty nếu tìm thấy thẻ
            company_name = company_name_tag.text.strip() if company_name_tag else ""
            
            # Lấy salary
            job_data['salary'] = ""
            job_data['salary_from'] = 0
            job_data['salary_to'] = 0
            
            # Lấy district name
            district_div = job.find('div', class_='flex flex-wrap items-end gap-2 text-gray-500')
            district_tag = district_div.find('p') if district_div else None
            district = district_tag.text.strip() if district_tag else ""

            salary_from = 0
            salary_to = 0
            salary_div = job.find('div', class_='mt-2 flex items-center justify-start gap-5')  # Tìm div chứa thông tin lương
            if salary_div:
                salary_p = salary_div.find('p', class_='text-primary')  # Tìm thẻ <p> chứa thông tin lương
                if salary_p:
                    salary_text = salary_p.text.strip()
                    match = re.match(r"([\d\.,]+) VND to ([\d\.,]+) VND", salary_text)
                    if match:
                        salary_from = int(match.group(1).replace('.', ''))
                        salary_to = int(match.group(2).replace('.', ''))
                        job_data['salary'] = f"{salary_from} VND to {salary_to} VND"
                    else:
                        job_data['salary'] = salary_text
                else:
                    job_data['salary'] = ""
            else:
                job_data['salary'] = ""
            
            # Lấy image
            images = job.find_all('img', class_='h-28 w-40 max-w-full rounded-xl bg-white object-contain p-2')
            image_urls = [img['src'] for img in images if 'src' in img.attrs]
            
            # Lấy position
            position_tag = job.find('a', class_='mr-2 inline-block')
            position = position_tag.text.strip() if position_tag else ""
        
            # Điều kiện lọc dữ liệu cần lưu
            job_data = {
                "job_Id": job_Id,
                "title": job_title,
                "company_name": company_name,
                "district_name": district,
                "image": image_urls[0] if images else "",
                "description": "Pending", 
                "salary_from":salary_from,
                "salary_to":salary_to,
                "requirement": "Pending",  
                "companyId": job_Id, 
                "expire_on": "31/12/2024", 
                "ref_job_Id": job_Id,
                "ref_link": ref_link,
                "position": position
            }
            job_list.append(job_data)
    
    driver.quit()

    # Gửi dữ liệu đã lọc tới API
    headers = {'Content-Type': 'application/json'}
    for job_data in job_list:
        try:
            response = requests.post(f"{api_url}/jobs", json=job_data, headers=headers)
            if response.status_code == 200:
                print(f"Job {job_data['job_id']} posted successfully.")
                print(f"Status code: {response.status_code}")
            else:
                print(f"Failed to post job {job_data['job_Id']}. Status: {response.status_code}")
        except Exception as e:
            print(f"Error sending job {job_data['job_Id']} to server:", e)

    # Extract and post jobs
    extract_job()
# Extract and post jobs

jobs_data = extract_job()


    
    

