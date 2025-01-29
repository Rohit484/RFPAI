import abc
from typing import List, Dict

class Scraper(abc.ABC):
    @abc.abstractmethod
    def scrape(self, keywords: str, user_id: str, rate: bool = False) -> List[Dict]:
        """
        Scrape the website for opportunities/proposals matching the given keywords.

        Args:
            keywords (str): Keywords to search for in the opportunities/proposals.
            user_id (str): User ID for retrieving company data.
            rate (bool): Whether to generate relevance ratings for the opportunities/proposals.

        Returns:
            List[Dict]: List of dictionaries containing the scraped opportunity/proposal details.
        """
        pass

    @abc.abstractmethod
    def parse(self, html: str, user_id: str, rate: bool = False) -> List[Dict]:
        """
        Parse the HTML content from the website and extract opportunity/proposal details.

        Args:
            html (str): HTML content to parse.
            user_id (str): User ID for retrieving company data.
            rate (bool): Whether to generate relevance ratings for the opportunities/proposals.

        Returns:
            List[Dict]: List of dictionaries containing the parsed opportunity/proposal details.
        """
        pass
    
    @abc.abstractmethod
    def rate(proposals: List[Dict], company_data: str) -> List[Dict]:
        """
        Generate relevance ratings for a list of proposals based on the provided company data.

        Args:
            proposals (List[Dict]): List of dictionaries containing proposal details.
            company_data (str): Company data used to generate relevance ratings.

        Returns:
            List[Dict]: List of dictionaries containing the proposals with relevance ratings
        """
        pass