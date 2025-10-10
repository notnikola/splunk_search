# Splunk Data Retriever

This Python module allows you to connect to a Splunk search head, run a query, and write the output to a CSV file. It supports breaking down large queries into smaller time chunks and displays a progress bar during execution.

## Features

*   Connects to Splunk using username and password authentication.
*   Executes Splunk search queries.
*   Breaks down long-running queries into configurable time chunks to prevent timeouts and manage memory.
*   Writes search results to a CSV file.
*   Provides a progress bar for searches.

## Setup

1.  **Clone the repository (or create the files manually):**
    ```bash
    mkdir splunk_data_retriever
    cd splunk_data_retriever
    # Create splunk_search.py, requirements.txt, and README.md as provided
    ```

2.  **Install dependencies:**
    Ensure you have `pip` installed. Then, navigate to the `splunk_data_retriever` directory and install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the `splunk_search.py` script from your terminal:

```bash
python splunk_search.py <host> <port> <username> <password> "<your_splunk_query>" <output_file.csv> "<earliest_time>" "<latest_time>"
```

### Arguments:

*   `<host>`: The hostname or IP address of your Splunk search head.
*   `<port>`: The management port of your Splunk instance (usually 8089).
*   `<username>`: Your Splunk username.
*   `<password>`: Your Splunk password.
*   `"<your_splunk_query>"`: The Splunk query you want to run. **Enclose in double quotes.**
    *   **NOTE:** Do NOT include `earliest` or `latest` in this query string; they will be added automatically by the script for chunking.
*   `<output_file.csv>`: The name of the CSV file where results will be saved.
*   `"<earliest_time>"`: The absolute earliest time for the search range. Format: `"YYYY-MM-DD HH:MM:SS"`. **Enclose in double quotes.**
*   `"<latest_time>"`: The absolute latest time for the search range. Format: `"YYYY-MM-DD HH:MM:SS"`. **Enclose in double quotes.**

### Example:

```bash
python splunk_search.py your_splunk_host 8089 admin changeme "index=your_index source=* error" output.csv "2024-01-01 00:00:00" "2024-10-10 23:59:59"
```

The script will display a progress bar as it fetches results in chunks.