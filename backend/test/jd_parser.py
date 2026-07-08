import os
import json
from pypdf import PdfReader
import ollama

def extract_text_from_pdf(file_path):
    """Extracts text from the JD PDF."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find target file: {file_path}")
        
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def parse_jd_with_nemotron(file_path, model_name="nemotron-3-super:cloud"):
    # 1. Load and extract text from the JD file
    print(f"Extracting text from {file_path}...")
    raw_text = extract_text_from_pdf(file_path)
    
    # 2. Build the strict JSON extraction prompt for Job Descriptions
    prompt = f"""
Extract the core structural requirements from the Job Description text provided below.
Return ONLY valid JSON matching the exact key names and types specified. Do not include markdown code block formatting (like ```json), commentary, or extra text.

Fields:
- role (String - the target job title, e.g., "Senior IT Manager")
- skills (Array of Strings - key technical skills, tools, and methodologies required, e.g., ["SQL", "Active Directory"])
- minimum_years (Integer - the minimum years of experience required. Extract ONLY the number. Default to 0 if not stated)

Job Description Text:
{raw_text[:6000]}
"""

    print(f"Sending request to Ollama using model '{model_name}'...")
    
    try:
        # 3. Query the model via Ollama with strict JSON enforcement
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            format='json',
            options={
                'temperature': 0.0  # Kept at 0 for strict, deterministic extraction
            }
        )
        
        # 4. Print and return the output text string
        parsed_output = response['response'].strip()
        print("\n=== Expected Output (Parsed JD JSON) ===")
        print(parsed_output)
        print("=========================================\n")
        
        return json.loads(parsed_output)
        
    except Exception as e:
        print(f"An error occurred during LLM processing: {str(e)}")
        return None

if __name__ == "__main__":
    # Point this to one of your JD PDFs to test it out!
    try:

        TARGET_JD = "../data/jds/jd.json" 
        
        # Run the parser
        parse_jd_with_nemotron(TARGET_JD, model_name="nemotron-3-super:cloud")
        
    except Exception as e:
        print(f"\n[CRITICAL RUNTIME ERROR] Script crashed due to: {e}")
    finally:
        # This keeps the terminal session alive so you can actually read what went wrong!
        input("\nPress ENTER to close the terminal window...")