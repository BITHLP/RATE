from utils import CORE_AGENT_URL, CORE_AGENT_TASK_PROMPT
from search_agent import SearchAgent
from general_evaluation_agent import GeneralEvaluationAgent
from comparison_agent import ComparisonAgent
import requests
import re
from typing import Optional, Tuple, Dict, Any
import json
import threading
from concurrent.futures import ThreadPoolExecutor


class CoreAgentOutputParser:
    def __init__(self):
        self.tool_pattern = re.compile(
            r"<tool_call>\s*(\w+)(.*?)</tool_call>", 
            re.DOTALL
        )
        
        # <arg_key>key</arg_key>...<arg_value>value</arg_value>
        self.arg_pattern = re.compile(
            r"<arg_key>(.*?)</arg_key>\s*<arg_value>(.*?)</arg_value>", 
            re.DOTALL
        )

    def parse(self, llm_output: str) -> Tuple[Optional[str], Dict[str, Any]]:
        # <tool_call> 
        match = self.tool_pattern.search(llm_output)
        
        if not match:
            return None, {}

        tool_name = match.group(1).strip()
        args_content = match.group(2)

        arguments = {}
        arg_matches = self.arg_pattern.findall(args_content)
        
        for key, value in arg_matches:
            clean_key = key.strip()
            clean_value = value.strip()
            
            if clean_value.isdigit():
                clean_value = int(clean_value)
            
            arguments[clean_key] = clean_value

        return tool_name, arguments


class CoreAgent:
    def __init__(self, search_agent, general_evaluation_agent, comparison_agent, max_round):
        self.llm = CORE_AGENT_URL
        self.task = CORE_AGENT_TASK_PROMPT
        self.parser = CoreAgentOutputParser()
        self.search_agent = search_agent
        self.eval_agent = general_evaluation_agent
        self.comparison_agent = comparison_agent
        self.max_round = max_round
        self.accumulated_context = []
        

    def handle_core_response(self, llm_output: str):
        tool_name, args = self.parser.parse(llm_output)

        if tool_name == "search_agent":
            print(f"Decision: Searching for '{args.get('query')}'...")
            return self._execute_search(args)

        elif tool_name == "general_evaluation_agent":
            print("Decision: Running General Evaluation...")
            return self._execute_eval(args)

        elif tool_name == "comparison_agent":
            target_score = args.get('tentative_score')
            
            if target_score in self.compared_scores:
                print(f"[Controller] Loop Prevention: Skipping repeat comparison for Score {target_score}.")
                return json.dumps({
                    "tool_status": "skipped",
                    "suggestion": "confirm",
                    "message": f"System Notice: You have already verified score {target_score}. Please proceed to make a final decision."
                })
            
            print(f"[Controller] Running Comparison for Score {target_score}...")
            self.compared_scores.add(target_score)
            
            return self._execute_compare(args)

        elif tool_name == "finish_evaluation":
            print("Decision: Finalizing Report...")
            return self._finalize(args)

        else:
            return "[System Error] No valid tool call found or unknown tool."

    def _execute_search(self, args):
        query = args.get("query")
        result = self.search_agent.response(query) 
        
        self.accumulated_context.append(f"Query: {query} -> Result: {result}")
        print(f"Response: {result}")
        return f"search_agent: {result}"

    def _execute_eval(self, args):

        # system_memory = "\n".join(self.accumulated_context)
        
        response = self.eval_agent.response(
            source_text=args.get("source_text"),
            translation_text=args.get("translation_text"),
            context_notes = args.get("context_notes"),
            specific_instruction=args.get("specific_instruction")
        )
        print(f"Response: {response}")
        return f"general_evaluation_agent: {response}"

    def _execute_compare(self, args):
        system_memory = "\n".join(self.accumulated_context)
        
        response = self.comparison_agent.response(
            src=args.get("source_text"),
            trans=args.get("target_text"),
            tentative_score=float(args.get("tentative_score")),
            context=system_memory,
            syn_low=args.get("synthetic_low_anchor"),
            syn_high=args.get("synthetic_high_anchor")
        )
        print(f"Response: {response}")
        
        return f"comparison_agent: {response}"

    def _finalize(self, args):
        self.comparison_agent.update_anchor(args.get("translation_text"), float(args.get("final_score")))
        return {
            "status": "completed",
            "translation": args.get("translation_text"),
            "score": args.get("final_score"),
            "rationale": args.get("final_rationale")
        }

    def send_request(self, messages):
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.llm, headers=headers, json={"model": "GLM-4.6", "messages": messages})
        output = response.json()
        return output

    def eval(self, src, trans):
        log = {}
        self.compared_scores = set()
        existing_context = "\n".join(self.accumulated_context)
        init_query = ""
        init_query += f"**[System Memory] Known Context for this Source Text:**\n{existing_context}\n"
        init_query += f"""**Source Text:** "{src}"\n**Translation Text:** "{trans}"\n"""
        
        messages = [{"role": "system", "content": self.task}]
        messages.append({"role": "user", "content": init_query})
        
        for r in range(self.max_round):
            print("="*32+f"Round {r+1}"+"="*32)
            log[f"Round_{r+1}"] = {
                "call_func": "",
                "call_func_args": "",
                "reasoning": "",
                "request_content": "",
                "response_content": ""
            }
            output = self.send_request(messages)["choices"][0]["message"]
            output_content = output["content"]
            output_reasoning = output["reasoning_content"]
            messages.append({"role": "assistant", "content": output_content})
            
            tool_name, tool_args = self.parser.parse(output_content)
            log[f"Round_{r+1}"]["call_func"] = tool_name
            log[f"Round_{r+1}"]["call_func_args"] = tool_args
            log[f"Round_{r+1}"]["reasoning"] = output_reasoning
            log[f"Round_{r+1}"]["request_content"] = output_content
            print(tool_name, tool_args)
            
            result = self.handle_core_response(output_content)
            messages.append({"role": "tool", "content": result})
            log[f"Round_{r+1}"]["response_content"] = result

            if tool_name == "finish_evaluation":
                return result, log

        force_prompt = """[SYSTEM OVERRIDE: MAXIMUM STEPS EXCEEDED]\n**CRITICAL:** You have reached the maximum reasoning steps.\nYou are STRICTLY FORBIDDEN from using any tool other than `finish_evaluation`.\nBased on the information gathered so far, you MUST provide your best estimate score IMMEDIATELY.\nCall `finish_evaluation` now."""
        messages.append({"role": "user", "content": force_prompt})
        output = self.send_request(messages)["choices"][0]["message"]
        output_content = output["content"]
        output_reasoning = output["reasoning_content"]
        messages.append({"role": "assistant", "content": output_content})
        tool_name, tool_args = self.parser.parse(output_content)
        log[f"Round_{self.max_round}"]["call_func"] = tool_name
        log[f"Round_{self.max_round}"]["call_func_args"] = tool_args
        log[f"Round_{self.max_round}"]["reasoning"] = output_reasoning
        log[f"Round_{self.max_round}"]["request_content"] = output_content
        print(tool_name, tool_args)
    
        result = self.handle_core_response(output_content)
        messages.append({"role": "tool", "content": result})
        log[f"Round_{self.max_round}"]["response_content"] = result
        return result, log
    

file_write_lock = threading.Lock()

judger_model = "gpt4o"
meta_data_file_path = f"./wmt23/wmt23-ende.jsonl"
failed_file_path = f"./wmt23/trajectory_{judger_model}_judger/failed_qids.jsonl"

def process_metadata(metadata, max_round=10):
    qid = metadata.get('qid', 'unknown')
    # qid = qid.replace("/", "-")
    logs = {}

    search_agent = SearchAgent()
    general_evaluation_agent = GeneralEvaluationAgent()
    comparison_agent = ComparisonAgent()

    
    Rate = CoreAgent(search_agent, general_evaluation_agent, comparison_agent, max_round)

    try:
        # evaluate only annotated data for WMT23 (not none in human mqm)
        if metadata["flag"] == "None":
            logs  = {}
            for sys in metadata["system_names"]:
                logs[sys] = {"response_content": {"score":0}}
        else:
            for sys in metadata["system_names"]:
                system_name = f"trans_{sys}"
                src = metadata["src"]
                trans = metadata[f"trans_{sys}"]
                
                print(f"[Thread-{threading.get_ident()}] Processing {qid} - {system_name}...")
                
                result, log = Rate.eval(src, trans)
                logs[system_name] = log
            
        with open(f"./wmt23/trajectory_{judger_model}_judger/{qid}.json", "w") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        print(f"Error processing {qid}: {e}")
        
        with file_write_lock:
            with open(failed_file_path, "a") as failed_f:
                failed_f.write(json.dumps(metadata, ensure_ascii=False) + "\n")
                failed_f.flush()

if __name__ == "__main__":
    metadatas = []
    with open(meta_data_file_path, "r") as f:
        for line in f:
            if line.strip():
                metadatas.append(json.loads(line))
    
    open(failed_file_path, "w")

    MAX_WORKERS = 10

    MAX_ROUND = 10
    
    print(f"Starting evaluation with {MAX_WORKERS} threads...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_metadata, meta, max_round=MAX_ROUND) for meta in metadatas]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Thread generated an unhandled exception: {e}")

    print("All tasks completed.")