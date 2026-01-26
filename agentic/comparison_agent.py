from utils import COMPARISON_AGENT_URL, COMPARISON_AGENT_TASK_PROMPT
import json
import requests


class ComparisonAgent:
    def __init__(self):
        self.llm = COMPARISON_AGENT_URL
        self.task_prompt = COMPARISON_AGENT_TASK_PROMPT
        self.anchors = {} 
        self.is_initialized = False

    def update_anchor(self, trans, score):
        if score not in self.anchors:
            self.anchors[score] = {"text": trans}
            print(f"[ComparisonAgent] Initialize Anchor for Score {score} with '{trans}'")
            self.is_initialized = True
        else:
            self.anchors[score] = {"text": trans}
            print(f"[ComparisonAgent] Update Anchor for Score {score} to '{trans}'")

    def get_anchor(self, target_score):
        if target_score in self.anchors:
            return self.anchors[target_score], target_score
        
        available_scores = sorted(self.anchors.keys())
        if not available_scores:
            return None, None
            
        nearest_score = min(available_scores, key=lambda x: abs(x - target_score))
        return self.anchors[nearest_score], nearest_score

    def send_request(self, messages):
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.llm, headers=headers, json={"model": "gpt-4o", "messages": messages})
        output = response.json()
        return output

    def _call_llm_compare(self, src, context, cand_a, cand_b):
        system_content = self.task_prompt
        
        user_content = f"""
        **Source Text:** "{src}"
        
        **Context Notes:** {context}
        
        **Candidate A:** "{cand_a}"
        
        **Candidate B:** "{cand_b}"
        
        Please evaluate now. Response in JSON.
        """
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        response = self.send_request(messages)["choices"][0]["message"]["content"]
        
        try:
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            print(f"[ComparisonAgent] JSON Parse Error: {e}")
            return {"winner": "Tie", "rationale": "Parse Error"}

    def response(self, src, trans, tentative_score, context, 
                         syn_low=None, syn_high=None):

        if not self.is_initialized:
            if syn_high is None or syn_low is None:
                return ("[ComparisonAgent] Warning: Cold start without both synthetic anchors may affect performance.")
            else:
                self.is_initialized = True
                print("[ComparisonAgent] Cold Start: Initializing anchors with synthetic examples.")
                self.update_anchor(syn_high, 4)
                self.update_anchor(syn_low, 1)
        else:
            if syn_high is not None and syn_low is not None:
                if self.anchors.get(4) is None:
                    self.update_anchor(syn_high, 4)
                if self.anchors.get(1) is None:
                    self.update_anchor(syn_low, 1)
        
        anchor_data, anchor_score = self.get_anchor(tentative_score)
        
        active_anchor_text = anchor_data["text"]

        print(f"[ComparisonAgent] Comparing Candidate (Score {tentative_score}) vs Anchor (Score {anchor_score})")

        # Round 1: A=Candidate, B=Anchor
        res1 = self._call_llm_compare(src, context, trans, active_anchor_text)
        
        # Round 2: A=Anchor, B=Candidate
        res2 = self._call_llm_compare(src, context, active_anchor_text, trans)

        final_result = self._resolve_consistency(res1, res2)
        
        response_data = self._generate_structured_response(
                    final_result, tentative_score, anchor_score
        )
        
        return response_data

    def _resolve_consistency(self, r1, r2):
        """
        r1: A=Cand, B=Anchor
        r2: A=Anchor, B=Cand
        """
        w1 = r1.get("winner") # 'A', 'B', 'Tie'
        w2 = r2.get("winner") # 'A', 'B', 'Tie'
        
        if w1 == "A" and w2 == "B":
            return "candidate_wins"
            
        elif w1 == "B" and w2 == "A":
            return "anchor_wins"
            
        elif w1 == "Tie" and w2 == "Tie":
            return "tie"

        elif (w1 == "A" and w2 == "Tie") or (w1 == "Tie" and w2 == "B"):
            return "borderline_candidate_wins"
            
        elif (w1 == "B" and w2 == "Tie") or (w1 == "Tie" and w2 == "A"):
            return "borderline_anchor_wins"

        else:
            print(f"[ComparisonAgent] Bias/Inconsistency Detected: R1={w1}, R2={w2}. Defaulting to Tie.")
            return "tie"

    def _generate_structured_response(self, result, tent_score, anchor_score):
        response = {
            "anchor_memory_status": "initialized" if self.is_initialized else "empty",
            "comparison_details": {
                "anchor_score": anchor_score,
                "outcome": result 
            },
            "suggestion": "review",
            "suggested_score": tent_score,
            "message": "" 
        }

        prefix = f"[Result: {result.upper()} vs Score {anchor_score} Anchor]. "
        
        if result == "candidate_wins":
            # candidate >> anchor
            target_score = min(anchor_score + 1, 4)
            if tent_score <= anchor_score:
                response["suggestion"] = "upgrade"
                response["suggested_score"] = target_score
                response["message"] = prefix + f"Candidate is CLEARLY BETTER than Score {anchor_score}. Upgrade score to {target_score}."
            else:
                response["suggestion"] = "confirm"
                response["message"] = prefix + f"Candidate correctly outperforms the lower Score {anchor_score} anchor."
        elif result == "borderline_candidate_wins":
            # candidate > anchor
            target_score = min(anchor_score + 0.5, 4)
            if tent_score <= anchor_score:
                response["suggestion"] = "adjust"
                response["suggested_score"] = target_score
                response["message"] = prefix + f"Candidate is SLIGHTLY BETTER than Score {anchor_score}. Adjust score to {target_score}."
            else:
                response["suggestion"] = "confirm"
                response["message"] = prefix + f"Candidate correctly slightly outperforms the lower Score {anchor_score} anchor."
        elif result == "tie":
            # candidate == anchor
            if tent_score != anchor_score:
                response["suggestion"] = "adjust"
                response["suggested_score"] = anchor_score
                response["message"] = prefix + f"Candidate is equivalent to Score {anchor_score}. Adjust score to {anchor_score}."
            else:
                response["suggestion"] = "confirm"
                response["suggested_score"] = anchor_score
                response["message"] = prefix + "Candidate matches the anchor quality exactly."
        elif result == "borderline_anchor_wins":
            # candidate < anchor
            target_score = max(0, anchor_score - 0.5)
            if tent_score >= anchor_score:
                response["suggestion"] = "adjust"
                response["suggested_score"] = target_score
                response["message"] = prefix + f"Candidate is slightly worse than Score {anchor_score}. Adjust score to {target_score}."
            else:
                response["suggestion"] = "confirm"
                response["message"] = prefix + f"Candidate correctly slightly underperforms the higher Score {anchor_score} anchor."
        elif result == "anchor_wins":
            # candidate << anchor
            target_score = max(0, anchor_score - 1)
            if tent_score >= anchor_score:
                response["suggestion"] = "downgrade"
                response["suggested_score"] = target_score
                response["message"] = prefix + f"Candidate is CLEARLY WORSE than Score {anchor_score}. Downgrade score to {target_score}."
            else:
                response["suggestion"] = "confirm"
                response["message"] = prefix + f"Candidate correctly underperforms the higher Score {anchor_score} anchor."
        return response
