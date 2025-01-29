from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain


import logging
from typing import Tuple
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

from src.config.creds import OPENAI_API_KEY
from src.config.config import ENGINE
from src.services.llm.prompt import rating_prompt, keywords_extraction_prompt, domains_prompt, parser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def generate_rating(title: str, proposal_description: str, company_description: str) -> Tuple[int, str]:
    """
    Generate a rating for the relevance of a proposal based on the company description.

    Args:
        title (str): The title of the proposal.
        proposal_description (str): The description of the proposal.
        company_description (str): The description of the company.

    Returns:
        Tuple[int, str]: A tuple containing the rating (0-100) and the raw response from the language model.
    """
    try:
        # Input validation
        if not title or not proposal_description or not company_description:
            raise ValueError("All input parameters (title, proposal_description, company_description) are required.")

        llm = ChatOpenAI(model_name=ENGINE, temperature=0, openai_api_key=OPENAI_API_KEY)
        chain = LLMChain(llm=llm, prompt=rating_prompt)
        response = chain.invoke({
            "title": title,
            "proposal_description": proposal_description,
            "company_description": company_description
        })

        # Validate and convert the response to an integer rating
        rating = int(response["text"].strip())
        if rating < 0 or rating > 100:
            raise ValueError(f"Invalid rating: {rating}. Rating should be between 0 and 100.")

        return rating, response

    except Exception as e:
        logging.error(f"Error generating rating: {e}")
        return 0, str(e)
    
    
    
def extract_keywords(company_description: str, max_keywords: int) -> str:
    """
    Extract keywords from a company description using a language model.

    Args:
        company_description (str): The description of the company.

    Returns:
        str: The extracted keywords from the company description.
    """
    try:
        # Input validation
        if not company_description:
            raise ValueError("Company description is required.")

        llm = ChatOpenAI(model_name=ENGINE, temperature=0, openai_api_key=OPENAI_API_KEY)
        chain = LLMChain(llm=llm, prompt=keywords_extraction_prompt)
        response = chain.invoke({
            "company_description": company_description,
            "max_keywords": max_keywords
        })

        return response["text"].strip()

    except Exception as e:
        logging.error(f"Error extracting keywords: {e}")
        return str(e)
    
    
    
def get_domains(company_data: dict) -> dict:
    """
    Extract main, sub, and adjacent domains of a company based on the given data about the company.

    Args:
        company_data (dict): The data about the company.

    Returns:
        dict: The extracted main, sub, and adjacent domains of the company.
    """
    try:
        # Input validation
        if not company_data:
            raise ValueError("Company data is required.")

        llm = ChatOpenAI(model_name=ENGINE, temperature=0, openai_api_key=OPENAI_API_KEY)
        chain = chain = domains_prompt | llm | parser

        response = chain.invoke({
            "company_data": company_data
        })

        return response

    except Exception as e:
        logging.error(f"Error extracting domains: {e}")
        return None
    
    
# if __name__ == "__main__":
