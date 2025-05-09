import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

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
        
        # Create prompt with improved structure for better parsing and language specification
        prompt = PromptTemplate.from_template(
            """Generate {num_questions} {difficulty} {q_type} quiz questions on the topic: {topic} in {language} language.
            
            Format each question as follows:
            ### Question X
            **Question:** [Question text here in {language}]
            
            Options:
            A) [Option A in {language}]
            B) [Option B in {language}]
            C) [Option C in {language}]
            D) [Option D in {language}]
            
            **Answer:** [Correct letter]
            
            Please ensure all questions are well-formatted and clearly indicate the correct answer.
            The entire quiz should be in {language}, including all questions, options, and any explanations.
            """
        )
        
        # Create and execute the chain with the updated syntax
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"topic": topic, "difficulty": difficulty, "q_type": q_type, "language": language, "num_questions": num_questions})
        
        return result
    except Exception as e:
        return f"Error generating quiz: {str(e)}"