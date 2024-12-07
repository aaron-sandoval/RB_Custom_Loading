import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def download_con_files(urls, download_dir='downloads'):
    """
    Download .con files from a list of webpages.
    
    Args:
        urls (list): List of webpage URLs to search for .con files
        download_dir (str, optional): Directory to save downloaded files. 
                                      Defaults to 'downloads'.
    
    Returns:
        dict: A dictionary with download results (success and failed downloads)
    """
    # Create download directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)
    
    # Dictionary to track download results
    download_results = {
        'successful': [],
        'failed': [],
        'skipped': []
    }
    
    # Process each webpage
    for url in urls:
        try:
            # Fetch the webpage
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links ending with .con
            con_links = [
                link.get('href') for link in soup.find_all('a', href=True) 
                if link.get('href', '').lower().endswith('con')
            ]
            
            # If no .con files found on this page
            if not con_links:
                print(f"No .con files found on {url}")
                download_results['failed'].append({
                    'url': url,
                    'error': 'No .con files found'
                })
                continue
            
            # Download each .con file
            for con_link in con_links:
                try:
                    # Convert relative URL to absolute URL
                    full_con_url = urljoin(url, con_link)
                    
                    # Generate filename
                    filename = os.path.basename(urlparse(full_con_url).path)
                    
                    # Full path for saving the file
                    filepath = os.path.join(download_dir, filename)
                    
                    # Check if file already exists
                    if os.path.exists(filepath):
                        print(f"Skipping existing file: {filename}")
                        download_results['skipped'].append({
                            'url': full_con_url,
                            'filepath': filepath
                        })
                        continue
                    
                    # Download the .con file
                    con_response = requests.get(full_con_url)
                    con_response.raise_for_status()
                    
                    # Check content type
                    content_type = con_response.headers.get('content-type', '').lower()
                    if 'text/html' in content_type or b'<!DOCTYPE html>' in con_response.content[:20]:
                        print(f"Skipping HTML file: {con_link}")
                        download_results['failed'].append({
                            'url': full_con_url,
                            'error': 'File appears to be HTML, not binary'
                        })
                        continue
                    
                    # Write file content
                    with open(filepath, 'wb') as file:
                        file.write(con_response.content)
                    
                    download_results['successful'].append({
                        'url': full_con_url,
                        'filepath': filepath
                    })
                    
                    print(f"Successfully downloaded: {filename}")
                
                except Exception as e:
                    download_results['failed'].append({
                        'url': full_con_url,
                        'error': str(e)
                    })
                    print(f"Failed to download {con_link}: {e}")
        
        except Exception as e:
            download_results['failed'].append({
                'url': url,
                'error': str(e)
            })
            print(f"Failed to process {url}: {e}")
    
    return download_results

def main():
    # Example usage
    with open('URLs.txt', 'r') as f:
        urls_to_download = [line.strip() for line in f if line.strip()]
    
    # Download files
    results = download_con_files(urls_to_download)
    
    # Print summary
    print("\nDownload Summary:")
    print(f"Successful downloads: {len(results['successful'])}")
    print(f"Failed downloads: {len(results['failed'])}")
    print(f"Skipped files: {len(results['skipped'])}")
    
    # Print and write failed download URLs
    if results['failed']:
        print("\nFailed Downloads:")
        # Write just the URLs to file
        with open('failedURLs.txt', 'w') as f:
            for failure in results['failed']:
                # Print detailed info to console
                print(f"URL: {failure['url']}")
                print(f"Error: {failure['error']}")
                print("-" * 40)
                
                # Write only URL to file
                f.write(f"{failure['url']}\n")
        
        print(f"\nFailed URLs have been written to failedURLs.txt")

if __name__ == '__main__':
    main()