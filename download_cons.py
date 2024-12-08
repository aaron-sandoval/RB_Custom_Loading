import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def download_con_files(urls, download_dir='downloads'):
    """
    Download binary files between 2MB and 30MB from a list of webpages.
    
    Args:
        urls (list): List of webpage URLs to search for binary files
        download_dir (str, optional): Directory to save downloaded files. 
                                    Defaults to 'downloads'.
    """
    MIN_SIZE = 2 * 1024 * 1024  # 2 MB in bytes
    MAX_SIZE = 30 * 1024 * 1024  # 30 MB in bytes
    
    os.makedirs(download_dir, exist_ok=True)
    
    download_results = {
        'successful': [],
        'failed': [],
        'skipped': []
    }
    
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links
            candidate_files = []
            for link in soup.find_all('a', href=True):
                try:
                    file_url = urljoin(url, link.get('href'))
                    
                    # Get file size from headers
                    head_response = requests.head(file_url, allow_redirects=True)
                    content_length = int(head_response.headers.get('content-length', 0))
                    content_type = head_response.headers.get('content-type', '').lower()
                    
                    # Check if it's a binary file of the right size
                    if (MIN_SIZE <= content_length <= MAX_SIZE and 
                        'text/html' not in content_type):
                        candidate_files.append(file_url)
                
                except Exception as e:
                    continue  # Skip problematic links
            
            # If exactly one file matches criteria, download it
            if len(candidate_files) == 1:
                file_url = candidate_files[0]
                try:
                    filename = os.path.basename(urlparse(file_url).path)
                    filepath = os.path.join(download_dir, filename)
                    
                    # Check if file already exists
                    if os.path.exists(filepath):
                        print(f"Skipping existing file: {filename}")
                        download_results['skipped'].append({
                            'url': file_url,
                            'filepath': filepath
                        })
                        continue
                    
                    # Download the file
                    file_response = requests.get(file_url)
                    file_response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        f.write(file_response.content)
                    
                    download_results['successful'].append({
                        'url': file_url,
                        'filepath': filepath
                    })
                    print(f"Successfully downloaded: {filename}")
                
                except Exception as e:
                    download_results['failed'].append({
                        'url': file_url,
                        'error': str(e)
                    })
                    print(f"Failed to download {file_url}: {e}")
            
            else:
                error_msg = (f"Found {len(candidate_files)} files matching criteria "
                           f"(expected exactly 1)")
                download_results['failed'].append({
                    'url': url,
                    'error': error_msg
                })
                print(f"Failed to process {url}: {error_msg}")
        
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