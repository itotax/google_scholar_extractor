import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import urllib.parse
import sys

def fetch_page(url):
    """
    Fetch content of a page handling errors and rate limiting.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Request exception: {err}")
    return None

def parse_papers(page_content):
    """
    Parse the fetched page content for paper details.
    """
    soup = BeautifulSoup(page_content, "html.parser")

    
    papers_list = []

    for row in soup.find_all("tr", class_="gsc_a_tr"):
        #        print(row)
        try:
            title = row.find("a", class_="gsc_a_at").text
            authors = row.find("div", class_="gs_gray").text
            publication_info = row.find_all("div", class_="gs_gray")[1].text
            year = row.find("td", class_="gsc_a_y").find("span").text
            citations = row.find("td", class_="gsc_a_c").find("a").text if row.find("td", class_="gsc_a_c").find("a") else '0'

            # 論文のURLを取得
            url = row.find("a", class_="gsc_a_at").attrs['href']  # Get the URL of the paper
            # 論文IDを取得
            query = urllib.parse.urlparse(url).query
            # クエリを辞書に変換
            qs_d = urllib.parse.parse_qs(query)
            # 著者と論文IDを取得
            author_paper_id = qs_d['citation_for_view'][0]
            # 論文IDを取得
            paper_id = author_paper_id.split(":")[1]

            papers_list.append({
                "Paper ID": paper_id,
                "Title": title,
                "Authors": authors,
                "Publication Info": publication_info,
                "Year": year,
                "Citations": citations,
            })
        except AttributeError:  # Skip the row if parsing fails
            continue

    return papers_list

def fetch_papers(scholar_id):
    base_url = "https://scholar.google.com"
    papers_list = []
    start_index = 0
    page_size = 100  # Adjust based on how many items per page you want to process

    # get the author name
    url = f"{base_url}/citations?user={scholar_id}"
    page_content = fetch_page(url)
    if page_content:
        soup = BeautifulSoup(page_content, "html.parser")
        author_name = soup.find("meta",property="og:title")['content']
        print("Target Author: ", author_name)
    else:
        print("Failed to fetch author name.")
        return pd.DataFrame()

    while True:
        url = f"{base_url}/citations?user={scholar_id}&hl=en&cstart={start_index}&pagesize={page_size}"
        page_content = fetch_page(url)
        if page_content:
            new_papers = parse_papers(page_content)
            if not new_papers:
                break  # Break the loop if no papers are found
            papers_list.extend(new_papers)
            start_index += page_size
        else:
            break  # Break the loop if fetching fails

        time.sleep(5)  # Sleep to avoid hitting rate limits

    papers_df = pd.DataFrame(papers_list)

    return (author_name,papers_df)

# Example usage
scholar_id = sys.argv[1]
# Usage:
#   python google_scholar_extractor.py 'YOUR SCHOLAR ID'
# NOTE:
#   To get your scholar id, go to your google scholar profile and copy the id from the url 
#
# or you can just assign your name below
#scholar_id = 'INPUT YOURNAME'
(author_name,papers_df) = fetch_papers(scholar_id)

if not papers_df.empty:
    excel_file_path = 'google_scholar_papers_list('+author_name+').xlsx'
    papers_df.to_excel(excel_file_path, index=False, engine='openpyxl')  # Ensure you have 'openpyxl' installed
    print(f"Papers list saved to {excel_file_path}")
else:
    print("Failed to fetch papers.")
