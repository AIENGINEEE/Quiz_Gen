import os
import io
import fitz  # PyMuPDF
import tempfile
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.chains.retrieval_qa.base import RetrievalQA
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes"""
    text = ""
    try:
        # Open the PDF from memory
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def create_vector_store(pdf_text):
    """Create a vector store from the PDF text"""
    try:
        # Split the text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(pdf_text)
        
        # Create embeddings and vector store
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create and return the vector store
        vector_store = FAISS.from_texts(chunks, embeddings)
        return vector_store
    except Exception as e:
        print(f"Error creating vector store: {str(e)}")
        return None

def generate_rag_quiz(topic, difficulty, q_type, vector_store, language="English", num_questions=5):
    """Generate quiz questions using RAG with Groq LLM"""
    try:
        # Initialize the LLM
        llm = ChatGroq(
            temperature=0.7,
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="deepseek-r1-distill-llama-70b"
        )
        
        # Create retriever
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        
        # First, retrieve relevant documents about the topic
        search_query = f"information about {topic}"
        relevant_docs = retriever.get_relevant_documents(search_query)
        
        # Extract the text from the documents
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Create template based on question type
        if q_type == "MCQ":
            prompt_template = """You are a quiz generation expert. Using the provided context, create {num_questions} {difficulty} MCQ quiz questions on the topic: {topic} in {language} language.
            
Context from document:
{context}

Format each question as follows:
### Question X
**Question:** [Question text here in {language}]

Options:
A) [Option A in {language}]
B) [Option B in {language}]
C) [Option C in {language}]
D) [Option D in {language}]

**Answer:** [Correct letter]

**Hint:** [Hint text here]

**Explanation:** [Explanation text here]

Use ONLY information from the context to create accurate questions. If the context doesn't contain enough information about {topic}, create basic questions based on the available information.
The entire quiz should be in {language}, including all questions, options, hints, and explanations.
"""
        elif q_type == "True/False":
            prompt_template = """You are a quiz generation expert. Using the provided context, create {num_questions} {difficulty} True/False quiz questions on the topic: {topic} in {language} language.
            
Context from document:
{context}

Format each question as follows:
### Question X
**Question:** [Question text here in {language}]

Options:
A) True
B) False

**Answer:** [Correct letter: A or B]

**Hint:** [Hint text here]

**Explanation:** [Explanation text here]

Use ONLY information from the context to create accurate questions. If the context doesn't contain enough information about {topic}, create basic questions based on the available information.
The entire quiz should be in {language}, including all questions, options, hints, and explanations.
"""
        elif q_type == "Short Answer":
            prompt_template = """You are a quiz generation expert. Using the provided context, create {num_questions} {difficulty} Short Answer quiz questions on the topic: {topic} in {language} language.
            
Context from document:
{context}

Format each question as follows:
### Question X
**Question:** [Question text here in {language}]

**Answer:** [Short answer text in {language}]

**Hint:** [Hint text here]

**Explanation:** [Explanation text here]

Use ONLY information from the context to create accurate questions. If the context doesn't contain enough information about {topic}, create basic questions based on the available information.
The entire quiz should be in {language}, including all questions, options, hints, and explanations.
"""
        else:
            # Default to MCQ
            prompt_template = """You are a quiz generation expert. Using the provided context, create {num_questions} {difficulty} MCQ quiz questions on the topic: {topic} in {language} language.
            
Context from document:
{context}

Format each question as follows:
### Question X
**Question:** [Question text here in {language}]

Options:
A) [Option A in {language}]
B) [Option B in {language}]
C) [Option C in {language}]
D) [Option D in {language}]

**Answer:** [Correct letter]

**Hint:** [Hint text here]

**Explanation:** [Explanation text here]

Use ONLY information from the context to create accurate questions. If the context doesn't contain enough information about {topic}, create basic questions based on the available information.
The entire quiz should be in {language}, including all questions, options, hints, and explanations.
"""
        
        # Create a simple LLMChain instead of RetrievalQA
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "topic", "difficulty", "num_questions", "language"]
        )
        
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        
        # Execute the chain with all parameters explicitly
        response = llm_chain.invoke({
            "context": context_text,
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": num_questions,
            "language": language
        })
        
        # Return the text output
        return response["text"]
        
    except Exception as e:
        return f"Error generating RAG quiz: {str(e)}"