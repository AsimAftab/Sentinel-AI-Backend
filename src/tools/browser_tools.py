# src/tools/browser_tools.py

from langchain_community.tools.tavily_search import TavilySearchResults

# You can add more tools like web scraping here
# from langchain_community.tools import DuckDuckGoSearchRun

# Ensure TAVILY_API_KEY is in your .env file
browser_tools = [TavilySearchResults(max_results=3)]

# Example of a different toolset
# search_tool = DuckDuckGoSearchRun()