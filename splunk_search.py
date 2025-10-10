import splunklib.client as client
import splunklib.results as results
import csv
import sys
from datetime import datetime, timedelta
from tqdm import tqdm

class SplunkSearcher:
    def __init__(self, host, port, username, password):
        self.service = client.connect(host=host, port=port, username=username, password=password)

    def run_query_in_chunks(self, query, output_filename, earliest_time, latest_time, chunk_size_days=30):
        total_days = (latest_time - earliest_time).days
        
        # Initialize the progress bar with the total estimated number of chunks and total_days
        # I'm using total_days for now as a rough estimate for the number of iterations
        # but it can be refined later if needed
        with tqdm(total=total_days, unit="day", desc="Querying Splunk") as pbar:
            current_earliest = earliest_time
            query_results = []
            
            # Open CSV file in write mode, ensuring it's available throughout the chunk processing
            # It will create a new file, or overwrite if it already exists
            with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
                csv_writer = None # Initialize csv_writer to be set after the first chunk

                while current_earliest < latest_time:
                    current_latest = min(current_earliest + timedelta(days=chunk_size_days), latest_time)

                    # Construct the chunked query
                    chunk_query = f"{query} earliest={current_earliest.strftime('%Y-%m-%dT%H:%M:%S')} latest={current_latest.strftime('%Y-%m-%dT%H:%M:%S')}"
                    print(f"Running chunk query: {chunk_query}")

                    job = self.service.jobs.create(chunk_query, **{"exec_mode": "blocking"})

                    reader = results.ResultsReader(job.results())
                    
                    
                    
                    # If csv_writer is not yet initialized (first chunk), extract fieldnames to write header
                    if csv_writer is None:
                        # Fetch the first result to get the fieldnames
                        first_result = next(reader, None)
                        if first_result:
                            fieldnames = list(first_result.keys())
                            csv_writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                            csv_writer.writeheader()
                            query_results.append(first_result) # Add the first result to the list
                            
                            # Re-initialize reader to include first_result in subsequent iteration
                            reader = results.ResultsReader(job.results())

                    for result in reader:
                        if csv_writer is not None:
                            csv_writer.writerow(result)
                        else:
                            print("No results found in the first chunk to determine CSV headers.")
                    
                    
                    # Update progress bar
                    pbar.update((current_latest - current_earliest).days)

                    current_earliest = current_latest
                
                print(f"Results written to {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) != 9:
        print("Usage: python splunk_search.py <host> <port> <username> <password> <query> <output_file> <earliest_time_str> <latest_time_str>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]
    password = sys.argv[4]
    query = sys.argv[5]
    output_file = sys.argv[6]
    
    try:
        earliest_time_str = sys.argv[7]
        latest_time_str = sys.argv[8]
        
        # This will convert the string to datetime object
        earliest_time = datetime.strptime(earliest_time_str, '%Y-%m-%d %H:%M:%S')
        latest_time = datetime.strptime(latest_time_str, '%Y-%m-%d %H:%M:%S')
        
    except ValueError:
        print("Error: Please provide earliest and latest times in 'YYYY-MM-DD HH:MM:SS' format.")
        sys.exit(1)

    searcher = SplunkSearcher(host, port, username, password)
    searcher.run_query_in_chunks(query, output_file, earliest_time, latest_time)