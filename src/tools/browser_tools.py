# src/tools/browser_tools.py

import requests
import webbrowser
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Enhanced Search Tools ---

@tool
def tavily_web_search(query: str, max_results: int = 5) -> str:
    """
    Performs a comprehensive web search using Tavily API.
    Returns detailed search results with summaries and sources.
    
    Args:
        query: The search query
        max_results: Number of results to return (1-10)
    """
    try:
        if max_results < 1 or max_results > 10:
            max_results = 5
        
        tavily = TavilySearchResults(max_results=max_results)
        results = tavily.run(query)
        
        if not results:
            return f"No search results found for: {query}"
        
        # Format results nicely
        formatted_results = f"🔍 Search Results for: '{query}'\n\n"
        
        if isinstance(results, list):
            for i, result in enumerate(results, 1):
                if isinstance(result, dict):
                    title = result.get('title', 'No title')
                    url = result.get('url', 'No URL')
                    content = result.get('content', 'No content available')
                    
                    formatted_results += f"{i}. **{title}**\n"
                    formatted_results += f"   URL: {url}\n"
                    formatted_results += f"   Summary: {content[:200]}...\n\n"
                else:
                    formatted_results += f"{i}. {str(result)}\n\n"
        else:
            formatted_results += str(results)
        
        return formatted_results
        
    except Exception as e:
        return f"Error performing web search: {e}"


@tool
def scrape_webpage(url: str) -> str:
    """
    Scrapes and extracts text content from a webpage.
    Returns the main text content, title, and metadata.
    
    Args:
        url: The URL of the webpage to scrape
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return "Invalid URL provided. Please include http:// or https://"
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request with timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract main content
        main_content = ""
        
        # Try to find main content areas
        content_selectors = [
            'article', 'main', '.content', '#content', 
            '.post', '.entry-content', '.article-body'
        ]
        
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                main_content = content_area.get_text(separator='\n', strip=True)
                break
        
        # If no specific content area found, get body text
        if not main_content:
            body = soup.find('body')
            if body:
                main_content = body.get_text(separator='\n', strip=True)
        
        # Clean up the text
        lines = [line.strip() for line in main_content.split('\n') if line.strip()]
        cleaned_content = '\n'.join(lines)
        
        # Truncate if too long
        if len(cleaned_content) > 2000:
            cleaned_content = cleaned_content[:2000] + "... [Content truncated]"
        
        result = f"📄 **{title_text}**\n"
        result += f"🔗 URL: {url}\n\n"
        result += f"📝 **Content:**\n{cleaned_content}"
        
        return result
        
    except requests.exceptions.Timeout:
        return f"Timeout error: The webpage took too long to respond - {url}"
    except requests.exceptions.RequestException as e:
        return f"Error accessing webpage: {e}"
    except Exception as e:
        return f"Error scraping webpage: {e}"


@tool
def open_webpage_in_browser(url: str) -> str:
    """
    Opens a webpage in the default system browser.
    
    Args:
        url: The URL to open in the browser
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            # Add https if no scheme provided
            url = f"https://{url}"
        
        webbrowser.open(url)
        return f"✅ Opened {url} in your default browser."
        
    except Exception as e:
        return f"Error opening webpage in browser: {e}"


@tool
def search_and_open(query: str, open_first: bool = False) -> str:
    """
    Searches the web and optionally opens the first result in browser.
    
    Args:
        query: The search query
        open_first: Whether to open the first result in browser
    """
    try:
        # Perform search
        search_results = tavily_web_search(query, max_results=3)
        
        if open_first and "URL:" in search_results:
            # Extract first URL from results
            lines = search_results.split('\n')
            first_url = None
            
            for line in lines:
                if "URL:" in line:
                    first_url = line.replace("URL:", "").strip()
                    break
            
            if first_url:
                webbrowser.open(first_url)
                return f"{search_results}\n\n✅ Opened first result ({first_url}) in your browser."
        
        return search_results
        
    except Exception as e:
        return f"Error in search and open: {e}"


@tool
def get_page_links(url: str, limit: int = 10) -> str:
    """
    Extracts all links from a webpage.
    
    Args:
        url: The URL of the webpage
        limit: Maximum number of links to return
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        result = f"🔗 **Links found on {url}:**\n\n"
        count = 0
        
        for link in links:
            if count >= limit:
                break
                
            href = link['href']
            text = link.get_text(strip=True)
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(url, href)
            elif not href.startswith('http'):
                continue
            
            if text:
                result += f"{count + 1}. [{text}]({href})\n"
            else:
                result += f"{count + 1}. {href}\n"
            
            count += 1
        
        if count == 0:
            return f"No links found on {url}"
        
        return result
        
    except Exception as e:
        return f"Error extracting links: {e}"


@tool
def download_file(url: str, filename: str = None) -> str:
    """
    Downloads a file from a URL to the local system.
    
    Args:
        url: The URL of the file to download
        filename: Optional custom filename (will use URL filename if not provided)
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Determine filename
        if not filename:
            filename = url.split('/')[-1]
            if not filename or '.' not in filename:
                filename = "downloaded_file"
        
        # Create downloads directory if it doesn't exist
        downloads_dir = "downloads"
        os.makedirs(downloads_dir, exist_ok=True)
        
        filepath = os.path.join(downloads_dir, filename)
        
        # Download file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)
        
        return f"✅ Downloaded {filename} ({file_size_mb:.2f} MB) to {filepath}"
        
    except Exception as e:
        return f"Error downloading file: {e}"


# Enhanced browser tools list
browser_tools = [
    tavily_web_search,
    scrape_webpage,
    open_webpage_in_browser,
    search_and_open,
    get_page_links,
    download_file
]