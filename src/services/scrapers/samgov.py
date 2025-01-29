import os
import logging
from typing import List, Dict

from src.services.llm.llm import generate_rating, extract_keywords
from src.services.rag.retriever import Retriever
from src.config.config import COMPANY_DATA_QUERY
from src.services.scrapers.scraper import Scraper
from src.utils.utlils import semantic_similarity
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

                            
class SamScraper(Scraper):   
    
    def __init__(self, user_id: str):
        self.retriever = Retriever(user_id=user_id)
        self.docs = self.retriever.get_query_docs(COMPANY_DATA_QUERY, k=1)
        
    def scrape(self,user_id: str, keywords:str = None, rate: bool = False) -> List[Dict]:
        """
        Scrape the SAM website for opportunities matching the given keywords.

        Args:
            keywords (str): Keywords to search for in the opportunities.
            rate (bool): Whether to generate relevance ratings for the opportunities.
            
        Returns:
            List[Dict]: List of dictionaries containing the scraped opportunity details.
        """
        results = []
        

        if not keywords:
            keywords = self.retriever.get_keywords(max_length=5)
        # keywords = keywords.replace('"', "")
        # keywords = keywords.replace(" ", "%20")
        
        print(keywords)

        # keywords = "technology or construction"        
        # keywords = keywords.replace(" ", "%20")

        
        for result in requests.get(f"https://sam.gov/api/prod/sgs/v1/search/?random=1712817914503&index=_all&page=0&mode=search&sort=-modifiedDate&size=10000&mfe=true&q={keywords}%0A&qMode=SEARCH_EDITOR&is_active=true").json()['_embedded']['results']:
            title = result['title']
            link = f"https://sam.gov/opp/{result['_id']}/view"
            try:
                if result['descriptions'] != []:
                    description = result['descriptions'][0]["content"]
                else:
                    description = "No description available."
            except KeyError:
                if 'description' in result:
                    description = result['description']
                elif 'objectives' in result:
                    description = result['objective']["content"]
            if rate:
                rating = semantic_similarity(self.docs, title + " " + description)
            else:
                rating = None
            entry = {
                'title': title,
                'link': link,
                'description': description,
                'rating': rating
            }
            results.append(entry)
        
        return results
       
    def parse(self, html: str, user_id: str, rate: bool = False) -> List[Dict]:
        """
        Parse the HTML content from the SAM website and extract opportunity details.

        Args:
            html (str): HTML content to parse.
            rate (bool): Whether to generate relevance ratings for the opportunities.
            
        Returns:
            List[Dict]: List of dictionaries containing the parsed opportunity details.
        """
        pass
    
    def rate(self, proposals: List[Dict], company_data: str) -> List[Dict]:
        """
        Generate relevance ratings for a list of proposals based on the provided company data.

        Args:
            proposals (List[Dict]): List of dictionaries containing proposal details.
            company_data (str): Company data used to generate relevance ratings.

        Returns:
            List[Dict]: List of dictionaries containing the proposals with relevance ratings
        """
        for proposal in proposals:
            proposal['rating'], _ = generate_rating(proposal['title'], proposal['description'], company_description=company_data)

        proposals.sort(key=lambda x: x['rating'], reverse=True)
        return proposals
    
    
# Example usage
if __name__ == "__main__":
    keywords = "technology"
    
    sam = SamScraper()
    
    opportunities = sam.scrape(keywords, user_id="123")
    if opportunities:
        for opportunity in opportunities:
            print(opportunity)

    else:
        print("No opportunities found.")