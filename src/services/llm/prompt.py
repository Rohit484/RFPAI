from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.services.llm.models import Domains



rating_prompt = PromptTemplate(
    input_variables=['title', 'proposal_description', 'company_description'],
    template="""
        You are a bot designed to rate proposal relevance according to company overview description.
        Proposal Title: {title}
        Proposal Description: {proposal_description}
        Company Description: {company_description}
        NOTE: Rating is between 0 and 100, answer with a single digit between 0 and 100 no need to write the word "rating" or "rate".
        Rating:
        """
)


keywords_extraction_prompt = PromptTemplate(
    input_variables=['company_description', 'max_keywords'],
    template="""
        You are a bot desgined to design search query to find relevant RFPs for a given company.
        
        Design a search query based on the company description to find relevant RFPs.
        
        The search query is in the following logical format: KEYWORD1 OR/AND KEYWORD2 OR/AND KEYWORD3...
        NOTE: Choose keywords as general fields of interest for the company (example : Technology, Construction, etc.)
        NOTE: You can ONLY use AND/OR to combine keywords.
        NOTE: maximum number of keywords is {max_keywords}.
        
        Company Description: {company_description}
        
        Keywords:
    """
)


parser = JsonOutputParser(pydantic_object=Domains)

domains_prompt = PromptTemplate(
    template="""
    Extract main, sub and adjacent domains of a company based on the given data about the company data
    
    NOTE: domain are just one word, e.g., "Manufacturing", "Electronics", "AI", etc.
    
    {format_instructions}
    
    {company_data}
    """,
    input_variables=["company_data"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)