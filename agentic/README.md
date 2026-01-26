# API Setup
**RATE** (<u>R</u>eflective <u>A</u>gentic <u>T</u>ranslation <u>E</u>valuation) relies on two external services to function: an LLM API (for the Core Agent and sub-agents) and a Search Engine API (for the Search Agent). 
Before running RATE, please ensure these services are deployed and accessible.

## 1. LLM API (OpenAI-Compatible)
RATE is designed to work with OpenAI-compatible API.

### Verification Script
Run the following script to verify your LLM connection.

> Note: If you are using reasoning models (e.g., GLM-4.6), ensure your backend supports the `reasoning_content` field.

```python
import requests
def send_request(messages):
    url = "http://localhost:7890/v1/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json={"model": "gpt-4o", "messages": messages})
    output = response.json()
    return output

messages = [{"role":"user", "content": "Briefly introduce LLM to me."}]
response = send_request(messages)
print(response["choices"][0]["message"]["content"])
print(response["choices"][0]["message"]["reasoning_content"]) # for reasoning model
```

## 2. Search Engine API
The Search Agent requires a custom search wrapper. You must host a lightweight server (e.g., FastAPI) that wraps a real search engine (e.g., Bing) and exposes it via the interface defined below.

### API Specification
- **Method**: `POST`
- **Endpoint**: `/search`
- **Input Schema**: 
    ```json
    {
        "query": "string",       // The search query
        "recency": "int | null"  // Optional: Filter by days
    }
    ```
- **Output Schema**: 
    ```json
    {
        "snippets": [
            "Snippet1: ...",
            "Snippet2: ..."
        ],
        "count": "int" // Number of results returned
    }
    ```

### Verification Script
Use the following script to verify your Search Wrapper is functioning correctly.

```python
import requests
def search(query):
    # search tool api:
    # request
    # {
    #    "query": "query_1",
    #    "recency": int | None
    # },

    # return
    # {
    # "snippets": ["s1", "s2", ]
    # "count": int
    # }
    url = "http://localhost:7870/search"
    payload = {
        "query": query["query"],
        "recency": query["recency"]
    }
    response = requests.post(url, json=payload)
    return response.json()
query = {"query": "Large Language Models", "recency": None}
response = search(query)
print(response)
```

# Running RATE

## MENT Dataset
To reproduce the experiments on the MENT dataset, use the generic entry point `core_agent.py`. Before running the script, you need to configure:
- `meta_data_file_path` (Line 208): Path to the meta-evaluation dataset.
- `failed_file_path` (Line209): Path to file saving the failed data.

## WMT23 Dataset

For experiments specifically targeting the WMT23 Metrics Shared Task, please refer to `wmt23/README.md`.

# Released Trajectories
To facilitate reproducibility and in-depth analysis of the agent's evaluation process, we release the full evaluation trajectories in `trajectory_gp4o_judger.tar.gz`.
These trajectories were generated using the configuration aligned with the Main Experiments reported in our paper.
