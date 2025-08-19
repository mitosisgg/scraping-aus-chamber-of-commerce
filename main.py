import requests
from bs4 import BeautifulSoup
import time
import csv

def filter_category_urls(category_urls):
    """
    Filter category URLs to:
    1. Remove URLs containing numeric characters
    2. Return only distinct URLs
    """
    # Use a set to automatically handle duplicates
    filtered_urls = set()
    
    for url in category_urls:
        # Skip URLs containing numeric characters
        if not any(char.isdigit() for char in url):
            filtered_urls.add(url)
    
    # Convert back to sorted list
    return sorted(list(filtered_urls))

def get_category_urls():
    url = "https://australia.chamberofcommerce.com/business-directory/queensland/albion/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links with the specific path pattern
        base_path = '/business-directory/queensland/albion/'
        category_urls = []
        
        # Find all anchor tags
        all_links = soup.find_all('a', href=True)
        
        # Filter links that match our path pattern
        for link in all_links:
            href = link['href']
            if href.startswith(base_path) and href != base_path:
                full_url = f"https://australia.chamberofcommerce.com{href}"
                category_urls.append(full_url)
            
        return category_urls
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return []

def get_business_urls_from_category(category_url):
    """
    Given a category URL, fetch all business URLs from that category page,
    including handling pagination.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    business_urls = []
    page_number = 1
    
    while True:
        # Construct the page URL
        if page_number > 1:
            page_url = f"{category_url}?page={page_number}"
        else:
            page_url = category_url
            
        try:
            response = requests.get(page_url, headers=headers)
            response.raise_for_status()
            
            # Save the HTML response for debugging
            # Get the last portion of the URL (after the last slash)
            # url_parts = category_url.split('/')
            # filename = url_parts[-1] if url_parts[-1] else url_parts[-2]
            # with open(f'response_{filename}_{page_number}.html', 'w', encoding='utf-8') as f:
            #     f.write(response.text)
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all anchor links with placeid attribute
            business_links = soup.find_all('a', {'placeid': True})
            
            # Extract business URLs from links with placeid
            for link in business_links:
                href = link.get('href')
                if href:
                    full_url = f"https://australia.chamberofcommerce.com{href}"
                    business_urls.append(full_url)
                    
            # Check pagination
            page_items = soup.find_all('li', class_='page-item')
            if not page_items:
                print('no pagination found')
                break
                
            # Find the highest page number available
            max_page = page_number
            for item in page_items:
                link = item.find('a', href=True)
                if link and '?page=' in link['href']:
                    try:
                        page_num = int(link['href'].split('?page=')[1])
                        max_page = max(max_page, page_num)
                    except (ValueError, IndexError):
                        continue
            
            if page_number >= max_page:
                print(f'No more pages to process (current page: {page_number}, max page: {max_page})')
                break
                
            page_number += 1
            
            # Add a small delay to be polite to the server
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page_number}: {e}")
            break
            
    return business_urls

def fetch_business_details(urls):
    """
    Fetch business details from URLs in business_urls.csv
    Returns a list of dictionaries containing business details
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    business_details = []
    
    # Use the provided URLs
    
    for url in urls:
        url = url.strip()
        print(f"\nFetching details for: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract business name from sup element with specific style
            name = soup.find('sup', style='top:-0.2em;')
            business_name = name.text.strip() if name else "N/A"
            print(f"Found business name: {business_name}")
            
            # Extract phone number from the link with selector-type="Phone"
            phone = soup.find('a', {'selector-type': 'Phone'})
            phone_number = phone.text.strip() if phone else "N/A"
            
            # Extract address components
            address_parts = []
            address1 = soup.find('span', {'selector-type': 'Address1'})
            address2 = soup.find('span', {'selector-type': 'Address2'})
            city = soup.find('span', {'selector-type': 'City'})
            state = soup.find('span', {'selector-type': 'State'})
            zip_code = soup.find('span', {'selector-type': 'Zip'})
            
            if address1:
                address_parts.append(address1.text.strip())
            if address2 and address2.text.strip():
                address_parts.append(address2.text.strip())
            if city:
                address_parts.append(city.text.strip())
            if state:
                address_parts.append(state.text.strip())
            if zip_code:
                address_parts.append(zip_code.text.strip())
            
            business_address = ' '.join(address_parts) if address_parts else "N/A"
            
            # Save the details
            business_details.append({
                'URL': url,
                'Name': business_name,
                'Phone': phone_number,
                'Address': business_address
            })
            
            # Add delay to be polite to the server
            time.sleep(2)
            
        except Exception as e:
            print(f"Error fetching details for {url}: {str(e)}")
            continue
    
    return business_details

def write_to_csv(business_urls): 
    with open('business_urls.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for url in business_urls:
            writer.writerow([url])
    
    print(f"\nTotal business URLs found: {len(business_urls)}")
    print("Business URLs have been saved to business_urls.csv")

if __name__ == "__main__":
    # print("Fetching category URLs...")
    # category_urls = get_category_urls()
    # print(f"\nFound {len(category_urls)} categories total")
    
    # # Filter and get distinct URLs
    # filtered_urls = filter_category_urls(category_urls)
    # print(f"\nAfter filtering: {len(filtered_urls)} distinct categories without numbers:")
    # for url in filtered_urls:
    #     print(url)
    
    # # # Process each category and get its business URLs
    # all_business_urls = []
    
    # for category_url in filtered_urls:
    #     print(f"\nProcessing category: {category_url}")
    #     business_urls = get_business_urls_from_category(category_url)
    #     print(f"Found {len(business_urls)} businesses in this category")
    #     all_business_urls.extend(business_urls)
    
    # # Save all business URLs to CSV
    # write_to_csv(all_business_urls)
    
    print("Reading business URLs from CSV...")
    all_business_urls = []
    with open('business_urls.csv', 'r', encoding='utf-8') as csvfile:
        all_business_urls.extend(url.strip() for url in csvfile.readlines())
    print(f"\nFound {len(all_business_urls)} business URLs in CSV")

    # Fetch business details for the first 5 URLs
    print("\nFetching business details for first 5 URLs...")
    first_5_urls = all_business_urls
    business_details = fetch_business_details(first_5_urls)
    
    # Save business details to CSV
    with open('business_details.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['URL', 'Name', 'Phone', 'Address']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(business_details)
    
    print(f"\nTotal business details saved: {len(business_details)}")
    print("Business details have been saved to business_details.csv")



        
    

    
    