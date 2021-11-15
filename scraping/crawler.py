
import os
import requests
import random
import pandas as pd

from lxml import html
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

class OKRCrawler:
    """
    """
    def __init__(self,
                 handles_df_path,
                 base_url = 'https://openknowledge.worldbank.org/handle/',
                 stats_request =  "https://openknowledge.worldbank.org//rest/statlets?dsotype=2&dsoid={dsoid}&ids%5B%5D=abstract-views&ids%5B%5D=abstract-views-past-year&ids%5B%5D=file-downloads&ids%5B%5D=file-downloads-past-year"):
        
        self.base_url = base_url
        self.stats_request = stats_request
        self.handles_df_path = handles_df_path
        
        # Load handles df
        self.df = pd.read_csv(self.handles_df_path)
        
    def get_static_html(self, handle, export_html = False):
        """
        Loads html for static page
        """
        
        self.url =  self.base_url + handle
        
        # Send request for static page
        # print("Sending GET request for static page HTML...")
        
        self.page = requests.get(self.url)
        
        # Continue only if a 200 response
        try:
            self.page .raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Whoops it wasn't a 200
            error = "Error: " + str(e)
            print(error)
            return e
            # return None
        # else:
            # print(" Successfully loaded static page HTML...")
        finally:
            # Format html
            self.tree = html.fromstring(self.page.content)
            
            # Soupify
            self.soup = BeautifulSoup(self.page.content, 'html.parser')
            
            #save html for reference 
            if export_html:
                html_file_name = 'okr-{}'.format(handle.replace('/', '-')) + '.html'
                with open(html_file_name, "w", encoding='utf-8') as file:
                    file.write(str(self.soup))
        
    def get_stats_json(self, dsoid):
        """
        Uses dsoid from static html to send API request for download and view stats
        """
        # print('Sending API request for stats JSON...')
        stats_request = self.stats_request.format(dsoid = dsoid)
        stats_response = requests.get(stats_request)
        # print('Got respose with stats JSON...')
        return stats_response
        
    def process_json(self, json_source, list_index):
        """ 
        API response is a list of ordered JSONs, first contains information on 
        abstract views and third on file downloads
        
        This function process  the JSON to get matrices with stats """
        
        # Turn into dict and get the nth element
        json = json_source.json()[list_index]
        
        # Find matrix element
        matrix = json['dataset']['matrix']
        
        # Sum all elements in matrix
        return sum(matrix[0])
        
    def crawl(self, handle):
        """
        Loops over handles df and sends requests for each entry
        """
        self.get_static_html(handle)
        
        # Only process request if successfull response
        if self.page.status_code == 200:
            # Get static info --------------------------------
            
            # citation
            citation =  self.soup.find_all("div", {"class": "citation"})[0].text
            # remove special characters
            citation = citation.replace('\n', "").replace('“', '')
            
            # Get dsoid param from static html -> class="embed-cua-widget" data-dso-id = (...)
            embed_html_elem = self.soup.find_all("div", {"class": "embed-cua-widget"})
            dsoid = embed_html_elem[0]["data-dso-id"]
            
            # Get JSON with stats info -----------------------
            self.json = self.get_stats_json(dsoid)
            
            # Process JSON -----------------------------------
            
            # First item on json has info on abstract views
            abstract_views = self.process_json(self.json, 0)
            
            # Third item on json has info on n of downloads
            downloads = self.process_json(self.json, 2)
            
            # Download timestamp
            timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            
            return handle, citation, dsoid, abstract_views, downloads, timestamp
    
    def crawl_loop(self, 
                   handles_list = None,
                   export_df = True,
                   export_path = None,
                   columns = ['handle', 'citation', 'dsoid', 'abstract_views', 'downloads', 'scraping_date']):
        # Export variables df
        time = datetime.now().strftime("%m-%d-%Y-%H-%M")
        filename = 'okr_results-' + time + '.csv'
        path = os.getcwd()
        if export_path is not None:
            path = export_path
        file_path = os.path.join(path + filename)
        
        # Loop through all handles in df
        if handles_list is None:
            handles_list = self.df.Handle
        row_list = []
        idx = 1
        for handle in handles_list:
            print('Downloading {idx} of {total}'.format(idx = idx, total = len(handles_list)))
                    
            print('Scraping {}:'.format(handle))
            row = self.crawl(handle)
            print(row)
            
            # If error export as it is
            if row is None:
                self.results_df = pd.DataFrame(row_list, columns=columns)
                
                if export_df:
                    print('Interrupting loop')
                    print('Saving results df in {}'.format(file_path))
                    self.results_df.to_csv(file_path, index= False)
                    
                break
            # Otherwise contiue with loop
            else:
                row_list.append(row)
                idx += 1
                # Wait between .5 and 2s before sending another request
                sleep(round(random.uniform(.5, 2),3))
        
        # Create a results df
        df = pd.DataFrame(row_list, columns=columns)
        
        if export_df:
            print('Saving results df in {}'.format(file_path))
            self.results_df.to_csv(file_path, index= False)

if __name__ == "__main__":
    crawler = OKRCrawler('C:/Users/wb519128/Downloads/OKR-Data-2014-21.csv')
    crawler.crawl_loop(handles_list = crawler.df.Handle)

handle = crawler.df.Handle[5]
crawler.crawl(handle)

crawler.get_static_html(handle)

# RE-write crawl to handle HTML only if 200

# RE-write loop to handle exception


try:
    crawler.crawl(handle)
except:
    print("Error: do something")
else:
    print("Foo")