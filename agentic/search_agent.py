from utils import SEARCH_AGENT_URL, SEARCH_TOOL_URL, SEARCH_AGENT_INIT_PROMPT, SEARCH_AGENT_OUTPUT_PROMPT
import requests
import json
import re


class SearchAgent:
    def __init__(self):
        self.llm = SEARCH_AGENT_URL
        self.search_tool = SEARCH_TOOL_URL
    
    def search(self, query):
        # search tool api:
        # request
        #{
        #    "query": "query_1",
        #    "recency": int | None
        #},

        # return
        # {
            # "snippets": ["s1", "s2", ]
            # "count": int
        # }
        payload = {
            "query": query["query"],
            "recency": query["recency"]
        }
        response = requests.post(self.search_tool, json=payload)
        return response.json()
    
    def send_request(self, messages):
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.llm, headers=headers, json={"model": "GLM-4.6", "messages": messages})
        output = response.json()
        return output

    def parse_search_args(self, llm_output):
        content = llm_output

        match = re.search(r"<arg_value>(.*?)</arg_value>", content, re.DOTALL)
        
        if not match:
            print("[Search Agent] Not found <arg_value> in output!")
            return "[Search Agent] Not found <arg_value> in output!"

        json_str = match.group(1).strip()
        search_items = json.loads(json_str)
        
        parsed_results = []
        for item in search_items:
            parsed_results.append({
                "query": item.get("q"),
                "recency": item.get("recency") # null -> None
            })
            
        return parsed_results

    def response(self, core_agent_query):
        messages = [
            {"role": "system", "content": SEARCH_AGENT_INIT_PROMPT},
            {"role": "user", "content": core_agent_query}
        ] 
        
        output_tool_call = self.send_request(messages)["choices"][0]["message"]["content"]
        output_queries = self.parse_search_args(output_tool_call)
        searches = []
        for query in output_queries:
            search_obs = self.search(query)
            for item in search_obs["snippets"]:
                searches.append(item)
        messages.append({"role":"tool","content":"".join(searches)})
        messages.append({"role":"user","content":SEARCH_AGENT_OUTPUT_PROMPT})
        answer = self.send_request(messages)["choices"][0]["message"]["content"]
        return answer


if __name__ == "__main__":
    # test
    agent = SearchAgent()
    result = agent.response("What is '母鸡卡'? How to translate it into English?")
    print("="*32)
    print(result)