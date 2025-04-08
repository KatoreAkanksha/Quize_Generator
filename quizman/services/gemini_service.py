import os
import json
import requests
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import logging

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('VITE_GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash:generateContent"
        self.logger = logging.getLogger(__name__)

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from various file formats"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                reader = PdfReader(file_path)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                return text
            
            elif file_extension == '.docx':
                doc = Document(file_path)
                return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            
            elif file_extension in ['.png', '.jpg', '.jpeg']:
                image = Image.open(file_path)
                return pytesseract.image_to_string(image)
            
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            
            return ''
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return ''

    def generate_questions_with_gemini(self, text: str, count: int = 5, difficulty: str = 'medium') -> List[Dict]:
        """Generate MCQ questions using Gemini API"""
        if not self.api_key:
            self.logger.error("Gemini API key not found in environment variables")
            return self._generate_fallback_questions(count)
        
        # Truncate text if it's too long (Gemini has token limits)
        max_chars = 10000
        if len(text) > max_chars:
            text = text[:max_chars]
            self.logger.info(f"Text truncated to {max_chars} characters")
        
        prompt = f"""
        Generate {count} multiple-choice questions based on the following text. 
        The difficulty level should be {difficulty}.
        
        For each question:
        1. Create a clear, concise question
        2. Provide exactly 4 options labeled a, b, c, and d
        3. Indicate which option is correct
        
        Text content:
        {text}
        
        Format your response as a JSON array with this structure:
        [
          {{
            "question_text": "Question here?",
            "options": {{
              "a": "First option",
              "b": "Second option",
              "c": "Third option",
              "d": "Fourth option"
            }},
            "correct_option": "a"  // The letter of the correct option
          }}
        ]
        
        Ensure all questions are factually accurate based on the provided text.
        """
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            response_data = response.json()
            
            # Extract the text from the response
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                candidate = response_data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            # Extract JSON from the text response
                            text_response = part['text']
                            # Find JSON array in the response
                            start_idx = text_response.find('[{')
                            end_idx = text_response.rfind('}]') + 2
                            
                            if start_idx != -1 and end_idx != -1:
                                json_str = text_response[start_idx:end_idx]
                                try:
                                    questions = json.loads(json_str)
                                    # Validate the structure of each question
                                    valid_questions = []
                                    for q in questions:
                                        if self._validate_question_format(q):
                                            valid_questions.append(q)
                                    
                                    if valid_questions:
                                        return valid_questions
                                except json.JSONDecodeError:
                                    self.logger.error("Failed to parse JSON from Gemini response")
            
            self.logger.error("Failed to extract valid questions from Gemini response")
            return self._generate_fallback_questions(count)
            
        except Exception as e:
            self.logger.error(f"Error calling Gemini API: {str(e)}")
            return self._generate_fallback_questions(count)
    
    def _validate_question_format(self, question: Dict[str, Any]) -> bool:
        """Validate that a question has the correct format"""
        required_keys = ['question_text', 'options', 'correct_option']
        if not all(key in question for key in required_keys):
            return False
        
        options = question.get('options', {})
        if not isinstance(options, dict) or not all(key in options for key in ['a', 'b', 'c', 'd']):
            return False
        
        correct_option = question.get('correct_option', '')
        if correct_option not in ['a', 'b', 'c', 'd']:
            return False
        
        return True
    
    def _generate_fallback_questions(self, count: int = 5) -> List[Dict]:
        """Generate fallback questions when API fails"""
        self.logger.info("Using fallback questions")
        fallback_questions = [
            {
                'question_text': 'What is the primary purpose of a database?',
                'options': {
                    'a': 'To store and organize data',
                    'b': 'To create user interfaces',
                    'c': 'To process images',
                    'd': 'To send emails'
                },
                'correct_option': 'a'
            },
            {
                'question_text': 'Which programming language is commonly used for web development?',
                'options': {
                    'a': 'Assembly',
                    'b': 'Python',
                    'c': 'COBOL',
                    'd': 'Fortran'
                },
                'correct_option': 'b'
            },
            {
                'question_text': 'What does HTML stand for?',
                'options': {
                    'a': 'Hyper Text Markup Language',
                    'b': 'High Tech Modern Language',
                    'c': 'Hybrid Text Management Logic',
                    'd': 'Home Tool Markup Language'
                },
                'correct_option': 'a'
            },
            {
                'question_text': 'Which of these is a version control system?',
                'options': {
                    'a': 'MySQL',
                    'b': 'Apache',
                    'c': 'Git',
                    'd': 'Node.js'
                },
                'correct_option': 'c'
            },
            {
                'question_text': 'What is the purpose of CSS?',
                'options': {
                    'a': 'To handle server-side logic',
                    'b': 'To style web pages',
                    'c': 'To manage databases',
                    'd': 'To create web servers'
                },
                'correct_option': 'b'
            }
        ]
        
        return fallback_questions[:min(count, len(fallback_questions))]

    def process_file_and_generate_questions(self, file_path: str, count: int = 5, difficulty: str = 'medium') -> List[Dict]:
        """Process a file and generate quiz questions"""
        text = self.extract_text_from_file(file_path)
        if not text:
            self.logger.warning(f"No text extracted from {file_path}")
            return self._generate_fallback_questions(count)
        
        return self.generate_questions_with_gemini(text, count, difficulty)