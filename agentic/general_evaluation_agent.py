import json
from typing import Dict, Optional, Any
from utils import GENERAL_EVALUATION_AGENT_TASK_PROMPT, GENERAL_EVALUATION_AGENT_URL
import requests


class GeneralEvaluationAgent:
    def __init__(self):
        self.llm = GENERAL_EVALUATION_AGENT_URL
        self.system_prompt = GENERAL_EVALUATION_AGENT_TASK_PROMPT

    def send_request(self, messages):
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.llm, headers=headers, json={"model": "gpt-4o", "messages": messages})
        output = response.json()
        return output
    
    def response(self, 
                 source_text: str, 
                 translation_text: str, 
                 context_notes: Optional[str] = None, 
                 specific_instruction: Optional[str] = None) -> Dict[str, Any]:

        user_content = f"""**Source Text:** "{source_text}"\n**Translation Text:** "{translation_text}"\n"""
        if context_notes:
            user_content += f"\n**Context Notes:** {context_notes}"
        if specific_instruction:
            user_content += f"\n**Specific Instruction:** {specific_instruction}"
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]

        response_text = self.send_request(messages)["choices"][0]["message"]["content"]

        cleaned_response = self._clean_json_string(response_text)
        result = json.loads(cleaned_response)
        return result

    def _clean_json_string(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

if __name__ == "__main__":
    # test
    agent = GeneralEvaluationAgent()
    result = agent.response(
        source_text = "这些我都只看了一半 母鸡卡应该还会看完吧",
        target_text = "I've only watched half of these, but I'll probably finish watching Ave Mujica.",
    )

    print("="*32)
    print(result)

    print("+"*32)

    agent = GeneralEvaluationAgent()
    result = agent.response(
        source_text = "这些我都只看了一半 母鸡卡应该还会看完吧",
        target_text = "I've only watched half of these, but I'll probably finish watching Ave Mujica.",
        context_notes = "'母鸡卡'是中文粉丝对BanG Dream!企划中的乐队'Ave Mujica'的昵称，取其发音的谐音。英文翻译就是'Ave Mujica'。"
    )
    print("="*32)
    print(result)

