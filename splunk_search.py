import splunklib.client as client
import splunklib.results as results
import csv
import sys
import argparse
import shlex
from datetime import datetime, timedelta
from tqdm import tqdm

class SplunkSearcher:
    def __init__(self, host, port, username, password):
        self.service = client.connect(host=host, port=port, username=username, password=password)

    def run_query_in_chunks(self, query, output_filename, earliest_time, latest_time, chunk_size_days=7):
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
                    query_parts = query.split("|")
                    if len(query_parts) == 1:
                        chunk_query = f"{query} earliest={current_earliest.strftime('%m/%d/%Y:%H:%M:%S')} latest={current_latest.strftime('%m/%d/%Y:%H:%M:%S')}"
                        # Construct the chunked query
                        chunk_query = f"{query} earliest={current_earliest.strftime('%m/%d/%Y:%H:%M:%S')} latest={current_latest.strftime('%m/%d/%Y:%H:%M:%S')}"
                    else:
                        for i, j in enumerate(query_parts[1:]):
                            query_parts[i+1] = j.replace("search", f"search earliest={current_earliest.strftime('%m/%d/%Y:%H:%M:%S')} latest={current_latest.strftime('%m/%d/%Y:%H:%M:%S')}")
                        chunk_query = f"{query_parts[0]} earliest={current_earliest.strftime('%m/%d/%Y:%H:%M:%S')} latest={current_latest.strftime('%m/%d/%Y:%H:%M:%S')} {"|" + query_parts[1] if len(query_parts) == 2 else "| " + "|".join(query_parts[1:])}"
                        # Construct the chunked query
                        chunk_query = f"{query_parts[0]} earliest={current_earliest.strftime('%m/%d/%Y:%H:%M:%S')} latest={current_latest.strftime('%m/%d/%Y:%H:%M:%S')} {"|" + query_parts[1] if len(query_parts) == 2 else "| " + "|".join(query_parts[1:])}"
                    #print(f"Running chunk query: {chunk_query}")

                    job = self.service.jobs.create(chunk_query, **{"exec_mode": "blocking", "count":0})
                    while not job.is_done():
                        sys.sleep(2)
                    reader = results.ResultsReader(job.results(count=0))
                    
                    # If csv_writer is not yet initialized (first chunk), extract fieldnames to write header
                    if csv_writer is None:
                        # Fetch the first result to get the fieldnames
                        first_result = next(reader, None)
                        if first_result:
                            fieldnames = list(first_result.keys())
                            csv_writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                            csv_writer.writeheader()
                            csv_writer.writerow(first_result) # Add the first result to the list
                            
                            # Re-initialize reader to include first_result in subsequent iteration
                            #reader = results.ResultsReader(job.results(count=0))

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
    parser = argparse.ArgumentParser(description="Run Splunk queries in chunks.")
    parser.add_argument("--host", required=True, help="Splunk host")
    parser.add_argument("--port", type=int, required=True, help="Splunk port")
    parser.add_argument("--username", required=True, help="Splunk username")
    parser.add_argument("--password", required=True, help="Splunk password")
    parser.add_argument("--query", nargs='+', required=True, help="Splunk query string. Wrap arguments with spaces in quotes, e.g., 'index=main user=\"test user\"'.")
    parser.add_argument("--output_file", required=True, help="Output CSV filename")
    parser.add_argument("--earliest_time_str", required=True, help="Earliest time for query (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--latest_time_str", required=True, help="Latest time for query (YYYY-MM-DD HH:MM:SS)")

    args = parser.parse_args()

    try:
        earliest_time = datetime.strptime(args.earliest_time_str, '%Y-%m-%d %H:%M:%S')
        latest_time = datetime.strptime(args.latest_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print("Error: Please provide earliest and latest times in 'YYYY-MM-DD HH:MM:SS' format.")
        sys.exit(1)
    
    # Join all parts of the query argument and then use shlex to parse it
    # This allows for more flexible command-line input where the user might not quote the entire query
    full_query_string = " ".join(args.query)
    parsed_query_parts = shlex.split(full_query_string)
    reconstructed_query = " ".join(parsed_query_parts)

    searcher = SplunkSearcher(args.host, args.port, args.username, args.password)
    searcher.run_query_in_chunks(reconstructed_query, args.output_file, earliest_time, latest_time)