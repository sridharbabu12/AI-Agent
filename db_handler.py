from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Optional
import json

load_dotenv()

class SupabaseHandler:
    def __init__(self):
        # Load Supabase credentials from environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        # Initialize Supabase client
        self.client = create_client(supabase_url, supabase_key)

    def store_mcqs(self, mcq_data: Optional[Dict], material_id: str) -> str:
        """
        Store MCQs in Supabase in JSON format
        """
        try:
            if not mcq_data:
                print("No valid MCQ data to store")
                return ""

            # Format the MCQ data
            data = {
                "material_id": material_id,
                "question": mcq_data.get("question", ""),
                "options": json.dumps(mcq_data.get("options", [])),
                "correct_answer": mcq_data.get("correct_answer", ""),
                "explanation": mcq_data.get("explanation", ""),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table('mcqs').insert(data).execute()
            return result.data[0]['id']
        
        except Exception as e:
            print(f"Error storing MCQs: {str(e)}")
            return ""

    def get_mcqs(self, material_id: str) -> List[Dict]:
        """
        Retrieve MCQs for a specific study material
        """
        try:
            result = self.client.table('mcqs')\
                .select('*')\
                .eq('material_id', material_id)\
                .execute()
            
            # Convert the options back from JSON string to list
            mcqs = []
            for row in result.data:
                mcq = {
                    "question": row["question"],
                    "options": json.loads(row["options"]),  # Parse JSON string back to list
                    "correct_answer": row["correct_answer"],
                    "explanation": row["explanation"]
                }
                mcqs.append(mcq)
            
            return mcqs
        
        except Exception as e:
            print(f"Error retrieving MCQs: {str(e)}")
            return []

    def store_user_response(self, user_id: str, question_id: int, 
                          answer: str, is_correct: bool):
        """
        Store user's response to a question
        """
        try:
            data = {
                "user_id": user_id,
                "question_id": question_id,
                "answer": answer,
                "is_correct": is_correct,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.client.table('user_responses').insert(data).execute()
        
        except Exception as e:
            print(f"Error storing user response: {str(e)}")
            raise

    def get_user_stats(self, user_id: str) -> Dict:
        """
        Get user's performance statistics
        """
        try:
            result = self.client.table('user_responses')\
                .select('is_correct')\
                .eq('user_id', user_id)\
                .execute()
            
            responses = result.data
            total = len(responses)
            correct = sum(1 for r in responses if r['is_correct'])
            
            return {
                "total_questions": total,
                "correct_answers": correct,
                "accuracy": (correct / total * 100) if total > 0 else 0
            }
        
        except Exception as e:
            print(f"Error retrieving user stats: {str(e)}")
            return {"total_questions": 0, "correct_answers": 0, "accuracy": 0}
