from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from typing import Dict, List, Union
from prompts import prompt
from unstructured.partition.api import partition_via_api
from unstructured.chunking.title import chunk_by_title

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process_pdf(filename: str) -> List[str]:
    """Process PDF file and return text chunks"""
    try:
        # Get the API key from the environment variable
        api_key = os.getenv("UNSTRUCTURED_API_KEY")
        
        # Process PDF using unstructured API
        elements = partition_via_api(
            filename=filename, 
            api_key=api_key, 
            strategy="hi_res",
            ocr_language=['eng'],
            extract_image_block_types=["Table"]
        )
        
        # Chunk the elements by title
        chunk_elements = chunk_by_title(elements)
        
        # Convert chunks to strings
        return [str(chunk) for chunk in chunk_elements]
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return []

def generate_mcq(text_chunk: str) -> Dict:
    """Generate a single MCQ from text chunk"""
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"""Generate 1 multiple choice question from this text: {text_chunk}
                Format as JSON with question, options (array of 4), correct_answer, and explanation."""
            }],
            temperature=0.3
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error generating MCQ: {str(e)}")
        return None

def run_conversation(text_chunk: str, filename: str = None) -> List[Dict]:
    """Run the ReAct agent conversation"""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Generate MCQs for this text: {text_chunk}"}
    ]
    
    mcqs = []
    max_turns = 5  # Limit to 5 MCQs
    available_actions = {
        "process_pdf": process_pdf,
        "generate_mcqs": generate_mcq  # Use the actual MCQ generation function
    }
    
    while len(mcqs) < max_turns:
        try:
            # Get AI response
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3
            )
            response = completion.choices[0].message.content
            print(f"AI Response: {response}")
            
            # If we got an answer, process it and return
            if response.startswith("Answer:"):
                try:
                    mcqs_str = response.replace("Answer: Here are the generated MCQs: ", "")
                    final_mcqs = json.loads(mcqs_str)
                    return final_mcqs if isinstance(final_mcqs, list) else [final_mcqs]
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    return mcqs
            
            # Process Thought/Action
            if "Action:" in response:
                try:
                    # Extract thought and action
                    thought = response.split("Thought:")[1].split("Action:")[0].strip()
                    action_str = response.split("Action:")[1].split("PAUSE")[0].strip()
                    print(f"Thought: {thought}")
                    print(f"Action: {action_str}")
                    
                    # Parse and execute action
                    action_data = json.loads(action_str)
                    function_name = action_data["function_name"]
                    function_parms = action_data["function_parms"]
                    
                    # Execute the appropriate action
                    if function_name in available_actions:
                        result = available_actions[function_name](**function_parms)
                        if result and function_name == "generate_mcqs":
                            mcqs.append(result)
                    
                    # Add to conversation
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Action_Response: {json.dumps(result if result else [])}"})
                    
                except Exception as e:
                    print(f"Error in action execution: {str(e)}")
                    messages.append({"role": "user", "content": f"Error: {str(e)}"})
            else:
                messages.append({"role": "user", "content": "Error: No action found"})
                
        except Exception as e:
            print(f"Error in conversation: {str(e)}")
            return mcqs
    
    return mcqs

def generate_mcqs(text_chunk: str) -> List[Dict]:
    """Main function to generate MCQs using ReAct pattern"""
    try:
        mcqs = run_conversation(text_chunk)
        return mcqs if mcqs else []
    except Exception as e:
        print(f"Error generating MCQs: {str(e)}")
        return []

# Add test code
if __name__ == "__main__":
    test_text = """
    Artificial Intelligence (AI) is the simulation of human intelligence in machines. 
    It enables machines to learn from experience, adjust to new inputs, and perform human-like tasks.
    """
    mcqs = generate_mcqs(test_text)
    print("\nGenerated MCQs:")
    print(json.dumps(mcqs, indent=2))