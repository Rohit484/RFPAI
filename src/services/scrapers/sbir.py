import os
import logging
from typing import List, Dict, Optional
import bs4

from datetime import datetime

from src.services.llm.llm import generate_rating
from src.services.rag.retriever import Retriever
from src.config.config import COMPANY_DATA_QUERY
from src.services.scrapers.scraper import Scraper

from src.utils.utlils import semantic_similarity

import requests
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SbirScraper(Scraper):
    
    def __init__(self, user_id: str):
        self.retierver = Retriever(user_id=user_id)
        self.docs = self.retierver.get_query_docs(COMPANY_DATA_QUERY, k=1)
        
        
    def scrape(self, user_id: str, keywords:str = None, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, rate: bool = False) -> List[Dict]:
        """
        Scrape SBIR website for proposals matching the given keywords and date range.

        Args:
            date_from (Optional[datetime]): Start date for the proposal closing date range.
            date_to (Optional[datetime]): End date for the proposal closing date range.
            rate (bool): Whether to generate relevance ratings for the proposals.
        Returns:
            List[Dict]: List of dictionaries containing the scraped proposal details.
        """
        try:
            # Create a lock to synchronize access to the global list
            lock = threading.Lock()

            # Define a function to be executed by each thread
            def process_link(link):
                # Perform the HTTP request
                response = requests.get(link)
                
                # Call the parse function and get the results
                parsed_results = self.parse(response.text, user_id, date_from, date_to, rate=rate)
                
                # Acquire the lock to safely update the global list
                with lock:
                    # Append the results to the global list
                    results.extend(parsed_results)
                    
            # Create a list to store the thread objects
            threads = []
            
            if not keywords:
                keywords = self.retriever.get_keywords(max_length=3)
                keywords = keywords.replace('"', "")
            
            print(keywords)
            
            url_extension = keywords.replace(" ", "%2520")
            url = f"https://www.sbir.gov/sbirsearch/topic/current/{url_extension}"
            
            html = requests.get(url).text
            
            # Parse and process the results
            results = []
            page_num = 1
            logging.info(f"Scraping page {page_num}")
            results.extend(self.parse(html, user_id, date_from, date_to, rate=rate))

            soup = bs4.BeautifulSoup(html, 'html.parser')
            next_button = soup.find(class_="next")
            if next_button:
                ul_element = soup.find("ul", class_="pagination")
                pages_urls = []
                for li_element in ul_element.find_all("li")[:-2]:
                    a_element = li_element.find("a")
                    if a_element is not None:
                        pages_urls.append("https://www.sbir.gov"+a_element["href"])
                # Create and start a thread for each link in pages_urls
                for link in pages_urls:
                    thread = threading.Thread(target=process_link, args=(link,))
                    thread.start()
                    threads.append(thread)
                # Wait for all threads to complete
                for thread in threads:
                    thread.join()
                    
            if rate:
                results.sort(key=lambda x: x['rating'], reverse=True)
            return results

        except Exception as e:
            logging.error(f"Error scraping SBIR website: {e}")
            return []

    def parse(self, html: str, user_id:str, date_from: Optional[datetime], date_to: Optional[datetime], rate:bool=False) -> List[Dict]:
        """
        Parse the HTML content from the SBIR website and extract proposal details.

        Args:
            html (str): HTML content to parse.
            date_from (Optional[datetime]): Start date for the proposal closing date range.
            date_to (Optional[datetime]): End date for the proposal closing date range.
            rate (bool): Whether to generate relevance ratings for the proposals.

        Returns:
            List[Dict]: List of dictionaries containing the parsed proposal details.
        """
        soup = bs4.BeautifulSoup(html, 'html.parser')


        li_elements = soup.find_all('li', class_='search-result')
        results = []
        for li in li_elements:
            close_date_tag = li.find('span', class_='solr-search-close-date').text
            close_date = datetime.strptime(close_date_tag.split(' ')[-1], '%m-%d-%Y')

            if date_from and date_to:
                if close_date < date_from or close_date > date_to:
                    continue

            title = li.find('h3', class_='title').text
            link = 'https://www.sbir.gov' + li.find('a')['href']
            open_date = li.find('span', class_='solr-search-open-date').text.split(' ')[-1]
            release_date = li.find('span', class_='solr-search-release-date').text.split(' ')[-1]
            due_date = li.find('span', class_='solr-search-due-date')
            if due_date.find('span'):
                due_date = "Multiple"
            else:
                due_date = due_date.text.split(' ')[-1]
            description = li.find('p', class_='search-snippet').text

            if rate:
                # rating, _ = generate_rating(title, description, company_description=docs)
                rating = semantic_similarity(self.docs, title + " " + description)
            else:
                rating = None

            entry = {
                'title': title,
                'link': link,
                'open_date': open_date,
                'release_date': release_date,
                'due_date': due_date,
                'close_date': close_date.date().__format__('%m-%d-%Y'),
                'description': description,
                'rating': rating
            }
            results.append(entry)

        return results

    def rate(proposals: List[Dict], company_data: str) -> List[Dict]:
        """
        Generate relevance ratings for a list of SBIR proposals based on the provided company data.

        Args:
            proposals (List[Dict]): List of dictionaries containing proposal details.
            company_data (str): Company data used to generate relevance ratings.

        Returns:
            List[Dict]: List of dictionaries containing the proposals with relevance ratings.
        """
        for proposal in proposals:
            proposal['rating'], _ = generate_rating(proposal['title'], proposal['description'], company_description=company_data)

        proposals.sort(key=lambda x: x['rating'], reverse=True)
        return proposals

# Example usage
# if __name__ == "__main__":
    # keywords = "Technology"
    # date_from = datetime(2024, 3, 15)
    # date_to = datetime(2024, 5, 31)

    # scraper = SbirScraper()
    # proposals = scraper.scrape(keywords, "temp", None, None)
    

    # # proposals = scrape_sbir(keywords, date_from, date_to)
    # # # if proposals:
    # # #     rated_proposals = rate_sbir(proposals, "\n".join(company_docs))
    # # #     for proposal in rated_proposals:
    # # #         print(f"Title: {proposal['title']}")
    # # #         print(f"Rating: {proposal['rating']}")
    # # #         print("---")
    # # # else:
    # # #     print("No proposals found.")
    
    # for proposal in proposals:
    #     print(proposal)
