import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from pdf_rag_utils import extract_text_from_pdf, create_vector_store, generate_rag_quiz

load_dotenv()

def generate_quiz(topic, difficulty, q_type, language="English", num_questions=5):
    """Generate quiz questions using Groq LLM in the specified language"""
    try:
        # Initialize the LLM
        llm = ChatGroq(
            temperature=0.7,
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="deepseek-r1-distill-llama-70b"
        )
        
        # Create prompt dynamically based on question type
        if q_type == "MCQ":
            prompt_str = f"""Generate {{num_questions}} {{difficulty}} MCQ quiz questions on the topic: {{topic}} in {{language}} language.

Format each question as follows:
### Question X
**Question:** [Question text here in {{language}}]

Options:
A) [Option A in {{language}}]
B) [Option B in {{language}}]
C) [Option C in {{language}}]
D) [Option D in {{language}}]

**Answer:** [Correct letter]

**Hint:** [Hint text here]

**Explanation:** [Explanation text here]

Please ensure all questions are well-formatted and clearly indicate the correct answer, hint, and explanation.
The entire quiz should be in {{language}}, including all questions, options, hints, and explanations.
"""
        elif q_type == "True/False":
            prompt_str = f"""Generate {{num_questions}} {{difficulty}} True/False quiz questions on the topic: {{topic}} in {{language}} language.

Format each question as follows:
### Question X
**Question:** [Question text here in {{language}}]

Options:
A) True
B) False

**Answer:** [Correct letter: A or B]

**Hint:** [Hint text here]

**Explanation:** [Explanation text here]

Please ensure all questions are well-formatted and clearly indicate the correct answer, hint, and explanation.
The entire quiz should be in {{language}}, including all questions, options, hints, and explanations.
"""
        elif q_type == "Short Answer":
            prompt_str = f"""Generate {{num_questions}} {{difficulty}} Short Answer quiz questions on the topic: {{topic}} in {{language}} language.

Format each question as follows:
### Question X
**Question:** [Question text here in {{language}}]

**Answer:** [Short answer text in {{language}}]

**Hint:** [Hint text here]

**Explanation:** [Explanation text here]

Please ensure all questions are well-formatted and clearly indicate the correct answer, hint, and explanation.
The entire quiz should be in {{language}}, including all questions, options, hints, and explanations.
"""
        else:
            # Default to MCQ if unknown type
            prompt_str = f"""Generate {{num_questions}} {{difficulty}} MCQ quiz questions on the topic: {{topic}} in {{language}} language.

Format each question as follows:
### Question X
**Question:** [Question text here in {{language}}]

Options:
A) [Option A in {{language}}]
B) [Option B in {{language}}]
C) [Option C in {{language}}]
D) [Option D in {{language}}]

**Answer:** [Correct letter]

**Hint:** [Hint text here]

**Explanation:** [Explanation text here]

Please ensure all questions are well-formatted and clearly indicate the correct answer, hint, and explanation.
The entire quiz should be in {{language}}, including all questions, options, hints, and explanations.
"""
        prompt = PromptTemplate.from_template(prompt_str)
        
        # Create and execute the chain with the updated syntax
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"topic": topic, "difficulty": difficulty, "q_type": q_type, "language": language, "num_questions": num_questions})
        
        return result
    except Exception as e:
        return f"Error generating quiz: {str(e)}"