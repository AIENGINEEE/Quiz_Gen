import streamlit as st
import re
import json
import time
from Main import generate_quiz
from pdf_rag_utils import extract_text_from_pdf, create_vector_store, generate_rag_quiz
from pdf_utils import get_pdf_download_link, create_download_button

# Set page config
st.set_page_config(
    page_title="AI Quiz Generator", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define app modes
GENERATE_MODE = "Generate Quiz"
PLAY_MODE = "Play Quiz"
RAG_MODE = "PDF-Based Quiz"

# Initialize session state variables
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "current_mode" not in st.session_state:
    st.session_state.current_mode = GENERATE_MODE
if "saved_quizzes" not in st.session_state:
    st.session_state.saved_quizzes = []
if "quiz_metadata" not in st.session_state:
    st.session_state.quiz_metadata = {
        "topic": "",
        "difficulty": "Medium",
        "language": "English",
        "q_type": "MCQ"
    }
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = ""

# Create sidebar navigation
with st.sidebar:
    st.title("🤖 AI Quiz Generator")
    
    # Navigation buttons
    if st.button("📝 Create New Quiz", use_container_width=True):
        st.session_state.current_mode = GENERATE_MODE
        st.session_state.quiz_submitted = False
        st.rerun()
        
    if st.button("📄 Create PDF-Based Quiz", use_container_width=True):
        st.session_state.current_mode = RAG_MODE
        st.session_state.quiz_submitted = False
        st.rerun()
        
    if st.button("🎮 Play Saved Quiz", use_container_width=True):
        st.session_state.current_mode = PLAY_MODE
        st.session_state.quiz_submitted = False
        st.rerun()
    
    st.divider()
    
    # About section in sidebar
    st.markdown("### About")
    st.info("""
    This app uses AI to generate custom quizzes on any topic.
    - Choose any topic
    - Upload your own PDF
    - Select difficulty and question type
    - Pick your preferred language
    - Customize number of questions
    - Download as PDF
    """)

# Main area content based on mode
if st.session_state.current_mode == GENERATE_MODE:
    st.title("📝 Create a New Quiz")
    
    st.markdown("""
    Generate custom quizzes on any topic instantly using AI. Fill in the form below and click 'Generate Quiz'.
    """)
    
    # Input form
    with st.form("quiz_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            topic = st.text_input("📚 Topic", placeholder="e.g., Ancient Egypt, JavaScript, Climate Change")
            difficulty = st.selectbox("🎯 Difficulty", ["Easy", "Medium", "Hard"])
            language = st.selectbox("🌍 Language", [
                "English", "French", "Japanese", "Korean", "Arabic", "Hindi", 
                "Dutch", "Swedish","Danish", "Greek", "Malayalam","Tamil","Kannada",
                "Turkish", "Hungarian", "Thai", "Vietnamese"
            ])
        
        with col2:
            q_type = st.selectbox("❓ Question type", ["MCQ", "True/False", "Short Answer"])
            num_questions = st.slider("🔢 Number of questions", min_value=3, max_value=15, value=5)
            st.write("")  # Spacer
        
        generate_button = st.form_submit_button("Generate Quiz", use_container_width=True)
    
    # Generate quiz when form is submitted
    if generate_button and topic.strip():
        with st.spinner(f"Generating {num_questions} quiz questions in {language}..."):
            raw_output = generate_quiz(topic, difficulty, q_type, language, num_questions)
            print(raw_output)
            
            # Check if raw_output is an error message
            if raw_output.startswith("Error generating quiz:"):
                st.error(raw_output)
            else:
                st.session_state.quiz_data = []
                st.session_state.user_answers = []
                st.session_state.quiz_submitted = False
                
                # Save metadata
                st.session_state.quiz_metadata = {
                    "topic": topic,
                    "difficulty": difficulty,
                    "language": language,
                    "q_type": q_type,
                    "num_questions": num_questions
                }
    
                # Parse questions from raw LLM output with improved regex
                questions = re.split(r'###\s*Question\s*\d+', raw_output)
                if len(questions) > 1:  # Skip first empty split
                    questions = questions[1:]
                    
                    for q in questions:
                        # Extract question text
                        question_match = re.search(r'\*\*Question:\*\*\s*(.*?)(?:\n|$)', q, re.DOTALL)
                        question_text = question_match.group(1).strip() if question_match else "Question parsing error"
                        
                        # Extract options and answer based on question type
                        options_dict = {}
                        correct_answer = None
                        q_type = st.session_state.quiz_metadata.get("q_type", "MCQ")
                        
                        if q_type == "MCQ":
                            options = re.findall(r'([A-D])\)\s*(.+?)(?:\n|$)', q)
                            options_dict = {letter: text.strip() for letter, text in options}
                            answer_match = re.search(r'\*\*Answer:\*\*\s*([A-D])', q)
                            hint= re.search(r'\*\*Hint:\*\*\s*(.+)', q)
                            if hint:
                                hint_text = hint.group(1).strip()
                            else:       
                                hint_text = "No hint provided"
                            explanation = re.search(r'\*\*Explanation:\*\*\s*(.+)', q)
                            if explanation:
                                explanation_text = explanation.group(1).strip()
                            else:
                                explanation_text = "No explanation provided"
                            # Extract the correct answer    
                            if answer_match:
                                correct_answer = answer_match.group(1).strip()
                            else:   
                                correct_answer = "No answer provided"


                        elif q_type == "True/False":
                            options_dict = {"A": "True", "B": "False"}
                            answer_match = re.search(r'\*\*Answer:\*\*\s*([AB])', q)
                            hint= re.search(r'\*\*Hint:\*\*\s*(.+)', q)
                            if hint:
                                hint_text = hint.group(1).strip()
                            else:       
                                hint_text = "No hint provided"
                            explanation = re.search(r'\*\*Explanation:\*\*\s*(.+)', q)
                            if explanation:
                                explanation_text = explanation.group(1).strip()
                            else:
                                explanation_text = "No explanation provided"
                            correct_answer = answer_match.group(1).strip() if answer_match else None

                        elif q_type == "Short Answer":
                            # No options for short answer
                            answer_match = re.search(r'\*\*Answer:\*\*\s*(.+)', q)
                            hint= re.search(r'\*\*Hint:\*\*\s*(.+)', q)
                            if hint:
                                hint_text = hint.group(1).strip()
                            else:       
                                hint_text = "No hint provided"
                            explanation = re.search(r'\*\*Explanation:\*\*\s*(.+)', q)
                            if explanation:
                                explanation_text = explanation.group(1).strip()
                            else:
                                explanation_text = "No explanation provided"
                            correct_answer = answer_match.group(1).strip() if answer_match else None
                        
                        st.session_state.quiz_data.append({
                            "question": question_text,
                            "options": options_dict,
                            "answer": correct_answer,
                            "hint": hint_text,
                            "explanation": explanation_text
                        })
                    
                    st.session_state.user_answers = [None] * len(st.session_state.quiz_data)
                    
                    # Save quiz for later use
                    new_quiz = {
                        "metadata": st.session_state.quiz_metadata.copy(),
                        "questions": st.session_state.quiz_data.copy()
                    }
                    st.session_state.saved_quizzes.append(new_quiz)
    
    # Display quiz preview and options
    if st.session_state.quiz_data:
        st.divider()
        st.subheader(f"🧠 {st.session_state.quiz_metadata['topic'].title()} Quiz Preview")
        
        # Options for the quiz
        col1, col2 = st.columns(2)
        with col1:
            # PDF Download options
            st.markdown("### 📄 PDF Options")
            pdf_options = st.radio(
                "Choose PDF Content:",
                ["Quiz Only", "Quiz with Answers"],
                horizontal=True
            )
            
            # Get PDF data
            show_answers = pdf_options == "Quiz with Answers"
            pdf_data = get_pdf_download_link(
                st.session_state.quiz_data, 
                st.session_state.quiz_metadata["topic"],
                st.session_state.quiz_metadata["difficulty"],
                st.session_state.quiz_metadata["language"],
                show_answers=show_answers
            )
            
            # Create download button
            file_name = f"{st.session_state.quiz_metadata['topic'].replace(' ', '_')}_quiz.pdf"
            st.markdown(
                create_download_button(pdf_data, file_name),
                unsafe_allow_html=True
            )
        
        with col2:
            # Play options
            st.markdown("### 🎮 Play Options")
            if st.session_state.quiz_metadata.get("q_type") != "Short Answer":
                if st.button("Take This Quiz Now", type="primary", use_container_width=True):
                    st.session_state.current_mode = PLAY_MODE
                    st.session_state.quiz_submitted = False
                    st.rerun()
            else:
                st.info("Short Answer quizzes cannot be taken online. Please download the PDF to take the quiz.")
        
        # Display quiz preview
        with st.expander("Quiz Preview", expanded=True):
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                
                # Display options
                if q['options'] and isinstance(q['options'], dict):
                    for letter, text in q['options'].items():
                        st.markdown(f"{letter}) {text}")
                
                # Show correct answer in the preview
                if q['answer']:
                    st.markdown(f"<span style='color:green'>Correct answer: {q['answer']}</span>", unsafe_allow_html=True)
                # Show hint and explanation
                if q.get('hint') or q.get('explanation'):   
                    st.markdown(f"<span style='color:blue'>Hint: {q.get('hint', 'No hint provided')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:purple'>Explanation: {q.get('explanation', 'No explanation provided')}</span>", unsafe_allow_html=True)

        # Save quiz button
                st.divider()

# PDF RAG Mode
elif st.session_state.current_mode == RAG_MODE:
    st.title("📄 PDF-Based Quiz Generator")
    
    st.markdown("""
    Generate custom quizzes based on your own PDF documents. Upload a PDF, choose a topic, and let AI create relevant questions from your content.
    """)
    
    # PDF Upload Section
    st.subheader("1️⃣ Upload Your PDF Document")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    with col2:
        if st.session_state.pdf_uploaded:
            st.success(f"✅ PDF Uploaded: {st.session_state.pdf_filename}")
    
    # Process uploaded PDF
    if uploaded_file is not None and (not st.session_state.pdf_uploaded or uploaded_file.name != st.session_state.pdf_filename):
        with st.spinner("Processing PDF..."):
            # Save the filename
            st.session_state.pdf_filename = uploaded_file.name
            
            # Read PDF content
            pdf_bytes = uploaded_file.getvalue()
            pdf_text = extract_text_from_pdf(pdf_bytes)
            
            if pdf_text.startswith("Error extracting text:"):
                st.error(pdf_text)
                st.session_state.pdf_uploaded = False
                st.session_state.pdf_text = None
                st.session_state.vector_store = None
            else:
                # Create vector store
                st.session_state.pdf_text = pdf_text
                
                # Show a small preview of the extracted text
                with st.expander("PDF Text Preview"):
                    st.text(pdf_text[:500] + "..." if len(pdf_text) > 500 else pdf_text)
                
                # Create vector store
                st.session_state.vector_store = create_vector_store(pdf_text)
                if st.session_state.vector_store:
                    st.session_state.pdf_uploaded = True
                    st.success(f"✅ PDF processed successfully: {uploaded_file.name}")
                else:
                    st.error("Failed to create vector store from PDF")
                    st.session_state.pdf_uploaded = False
    
    # Quiz Generation Form - only show if PDF uploaded
    if st.session_state.pdf_uploaded and st.session_state.vector_store:
        st.divider()
        st.subheader("2️⃣ Configure Your Quiz")
        
        with st.form("pdf_quiz_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                topic = st.text_input("📚 Topic or Focus Area", 
                                      placeholder="Specify a topic from your PDF or leave blank for general questions")
                difficulty = st.selectbox("🎯 Difficulty", ["Easy", "Medium", "Hard"])
                language = st.selectbox("🌍 Language", [
                "English", "French", "Japanese", "Korean", "Arabic", "Hindi", 
                "Dutch", "Swedish","Danish", "Greek", "Malayalam","Tamil","Kannada",
                "Turkish", "Hungarian", "Thai", "Vietnamese"
            ])
            
            with col2:
                q_type = st.selectbox("❓ Question type", ["MCQ", "True/False", "Short Answer"])
                num_questions = st.slider("🔢 Number of questions", min_value=3, max_value=10, value=5)
                st.write("")  # Spacer
            
            generate_button = st.form_submit_button("Generate PDF-Based Quiz", use_container_width=True)
        
        # Generate quiz when form is submitted
        if generate_button:
            # Use the PDF filename as default topic if none provided
            if not topic.strip():
                topic = st.session_state.pdf_filename.replace(".pdf", "").replace("_", " ").title()
            
            with st.spinner(f"Generating {num_questions} {difficulty} questions from your PDF..."):
                raw_output = generate_rag_quiz(
                    topic, 
                    difficulty, 
                    q_type, 
                    st.session_state.vector_store,
                    language, 
                    num_questions
                )
                
                # Check if raw_output is an error message
                if raw_output.startswith("Error generating RAG quiz:"):
                    st.error(raw_output)
                else:
                    st.session_state.quiz_data = []
                    st.session_state.user_answers = []
                    st.session_state.quiz_submitted = False
                    
                    # Save metadata
                    st.session_state.quiz_metadata = {
                        "topic": topic,
                        "difficulty": difficulty,
                        "language": language,
                        "q_type": q_type,
                        "num_questions": num_questions,
                        "source": f"PDF: {st.session_state.pdf_filename}"
                    }
        
                    # Parse questions from raw LLM output with improved regex
                    questions = re.split(r'###\s*Question\s*\d+', raw_output)
                    if len(questions) > 1:  # Skip first empty split
                        questions = questions[1:]
                        
                        for q in questions:
                            # Extract question text
                            question_match = re.search(r'\*\*Question:\*\*\s*(.*?)(?:\n|$)', q, re.DOTALL)
                            question_text = question_match.group(1).strip() if question_match else "Question parsing error"
                            
                            # Extract options and answer based on question type
                            options_dict = {}
                            correct_answer = None
                            q_type = st.session_state.quiz_metadata.get("q_type", "MCQ")
                            
                            if q_type == "MCQ":
                                options = re.findall(r'([A-D])\)\s*(.+?)(?:\n|$)', q)
                                options_dict = {letter: text.strip() for letter, text in options}
                                answer_match = re.search(r'\*\*Answer:\*\*\s*([A-D])', q)
                                hint = re.search(r'\*\*Hint:\*\*\s*(.+)', q)
                                if hint:
                                    hint_text = hint.group(1).strip()
                                else:       
                                    hint_text = "No hint provided"
                                explanation = re.search(r'\*\*Explanation:\*\*\s*(.+)', q)
                                if explanation:
                                    explanation_text = explanation.group(1).strip()
                                else:
                                    explanation_text = "No explanation provided"
                                # Extract the correct answer
                                correct_answer = answer_match.group(1).strip() if answer_match else None
                            elif q_type == "True/False":
                                options_dict = {"A": "True", "B": "False"}
                                answer_match = re.search(r'\*\*Answer:\*\*\s*([AB])', q)
                                hint= re.search(r'\*\*Hint:\*\*\s*(.+)', q)
                                if hint:
                                    hint_text = hint.group(1).strip()
                                else:       
                                    hint_text = "No hint provided"
                                explanation = re.search(r'\*\*Explanation:\*\*\s*(.+)', q)
                                if explanation:
                                    explanation_text = explanation.group(1).strip()
                                else:
                                    explanation_text = "No explanation provided"
                                correct_answer = answer_match.group(1).strip() if answer_match else None
                            elif q_type == "Short Answer":
                                # No options for short answer
                                answer_match = re.search(r'\*\*Answer:\*\*\s*(.+)', q)
                                hint= re.search(r'\*\*Hint:\*\*\s*(.+)', q)
                                if hint:
                                    hint_text = hint.group(1).strip()
                                else:       
                                    hint_text = "No hint provided"
                                explanation = re.search(r'\*\*Explanation:\*\*\s*(.+)', q)
                                if explanation:
                                    explanation_text = explanation.group(1).strip()
                                else:
                                    explanation_text = "No explanation provided"
                                correct_answer = answer_match.group(1).strip() if answer_match else None
                            
                            st.session_state.quiz_data.append({
                                "question": question_text,
                                "options": options_dict,
                                "answer": correct_answer,
                                "hint": hint_text,
                                "explanation": explanation_text
                            })
                        
                        st.session_state.user_answers = [None] * len(st.session_state.quiz_data)
                        
                        # Save quiz for later use
                        new_quiz = {
                            "metadata": st.session_state.quiz_metadata.copy(),
                            "questions": st.session_state.quiz_data.copy()
                        }
                        st.session_state.saved_quizzes.append(new_quiz)
        
        # Display RAG-based quiz preview and options
        if st.session_state.quiz_data:
            st.divider()
            st.subheader(f"🧠 {st.session_state.quiz_metadata['topic'].title()} Quiz Preview")
            st.info(f"Source: {st.session_state.quiz_metadata.get('source', 'PDF Document')}")
            
            # Options for the quiz
            col1, col2 = st.columns(2)
            with col1:
                # PDF Download options
                st.markdown("### 📄 PDF Options")
                pdf_options = st.radio(
                    "Choose PDF Content:",
                    ["Quiz Only", "Quiz with Answers"],
                    horizontal=True,
                    key="rag_pdf_options"
                )
                
                # Get PDF data
                show_answers = pdf_options == "Quiz with Answers"
                pdf_data = get_pdf_download_link(
                    st.session_state.quiz_data, 
                    st.session_state.quiz_metadata["topic"],
                    st.session_state.quiz_metadata["difficulty"],
                    st.session_state.quiz_metadata["language"],
                    show_answers=show_answers
                )
                
                # Create download button
                file_name = f"{st.session_state.quiz_metadata['topic'].replace(' ', '_')}_pdf_quiz.pdf"
                st.markdown(
                    create_download_button(pdf_data, file_name),
                    unsafe_allow_html=True
                )
            
            with col2:
                # Play options
                st.markdown("### 🎮 Play Options")
                if st.session_state.quiz_metadata.get("q_type") != "Short Answer":
                    if st.button("Take This Quiz Now", type="primary", use_container_width=True, key="rag_take_quiz"):
                        st.session_state.current_mode = PLAY_MODE
                        st.session_state.quiz_submitted = False
                        st.rerun()
                else:
                    st.info("Short Answer quizzes cannot be taken online. Please download the PDF to take the quiz.")
            
            # Display quiz preview
            with st.expander("Quiz Preview", expanded=True):
                for i, q in enumerate(st.session_state.quiz_data):
                    st.markdown(f"**Q{i+1}: {q['question']}**")
                    
                    # Display options
                    if q['options'] and isinstance(q['options'], dict):
                        for letter, text in q['options'].items():
                            st.markdown(f"{letter}) {text}")
                    
                    # Show correct answer in the preview
                    if q['answer']:
                        st.markdown(f"<span style='color:green'>Correct answer: {q['answer']}</span>", unsafe_allow_html=True)
                    # Show hint and explanation
                    if q.get('hint') or q.get('explanation'):
                        st.markdown(f"<span style='color:blue'>Hint: {q.get('hint', 'No hint provided')}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color:purple'>Explanation: {q.get('explanation', 'No explanation provided')}</span>", unsafe_allow_html=True)
                    
                    st.divider()

# Play Mode
elif st.session_state.current_mode == PLAY_MODE:
    st.title("🎮 Play Quiz")
    
    # Check if there are saved quizzes
    if not st.session_state.saved_quizzes:
        st.warning("No saved quizzes found. Please generate a quiz first.")
        
        if st.button("Generate a New Quiz", type="primary"):
            st.session_state.current_mode = GENERATE_MODE
            st.rerun()
    else:
        # Quiz selection section
        st.subheader("Select a Quiz to Play")
        
        # Create a list of quiz names for selection
        quiz_names = []
        for i, quiz in enumerate(st.session_state.saved_quizzes):
            metadata = quiz["metadata"]
            topic = metadata.get("topic", "Untitled Quiz")
            difficulty = metadata.get("difficulty", "Medium")
            q_type = metadata.get("q_type", "MCQ")
            num_q = len(quiz["questions"])
            source = metadata.get("source", "Custom")
            
            # Create a display name
            if "PDF" in source:
                display_name = f"{topic} (PDF-based, {difficulty}, {q_type}, {num_q} questions)"
            else:
                display_name = f"{topic} ({difficulty}, {q_type}, {num_q} questions)"
            
            quiz_names.append(display_name)
        
        # Let user select a quiz
        selected_quiz_index = st.selectbox(
            "Choose a quiz to play:",
            range(len(quiz_names)),
            format_func=lambda i: quiz_names[i]
        )
        
        # Get the selected quiz data
        selected_quiz = st.session_state.saved_quizzes[selected_quiz_index]
        quiz_metadata = selected_quiz["metadata"]
        quiz_data = selected_quiz["questions"]
        
        # Check if it's a new quiz selection or continuing with current quiz
        if "current_quiz_index" not in st.session_state or st.session_state.current_quiz_index != selected_quiz_index:
            st.session_state.current_quiz_index = selected_quiz_index
            st.session_state.quiz_data = quiz_data
            st.session_state.quiz_metadata = quiz_metadata
            st.session_state.user_answers = [None] * len(quiz_data)
            st.session_state.quiz_submitted = False
        
        # Display quiz information
        st.markdown(f"### 📚 {quiz_metadata['topic'].title()}")
        
        # Add quiz metadata display
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        with meta_col1:
            st.markdown(f"**Difficulty:** {quiz_metadata['difficulty']}")
        with meta_col2:
            st.markdown(f"**Type:** {quiz_metadata['q_type']}")
        with meta_col3:
            st.markdown(f"**Language:** {quiz_metadata['language']}")
        
        # Source information if available
        if "source" in quiz_metadata:
            st.info(f"Source: {quiz_metadata['source']}")
        
        st.divider()
        
        # Display quiz questions and collect answers
        with st.form("quiz_play_form"):
            for i, question in enumerate(quiz_data):
                st.markdown(f"### Question {i+1}")
                st.markdown(f"**{question['question']}**")
                
                # Display options based on question type
                if quiz_metadata.get("q_type") == "MCQ":
                    # Use radio buttons for MCQ
                    options = list(question['options'].items())
                    radio_options = [f"{letter}) {text}" for letter, text in options]
                    letter_only_options = [letter for letter, _ in options]
                    
                    selected_option = st.radio(
                        f"Select answer for Question {i+1}:",
                        options=radio_options,
                        index=None,
                        key=f"q_{i}_radio"
                    )
                    
                    # Get just the letter part if an option was selected
                    if selected_option:
                        st.session_state.user_answers[i] = selected_option[0]
                
                elif quiz_metadata.get("q_type") == "True/False":
                    # Use radio buttons for True/False
                    options = [f"A) True", f"B) False"]
                    selected_option = st.radio(
                        f"Select answer for Question {i+1}:",
                        options=options,
                        index=None,
                        key=f"q_{i}_tf"
                    )
                    
                    # Get just the letter part if an option was selected
                    if selected_option:
                        st.session_state.user_answers[i] = selected_option[0]
                
                st.divider()
            
            # Submit button
            submit_quiz = st.form_submit_button("Submit Quiz", use_container_width=True, type="primary")
            
            if submit_quiz:
                st.session_state.quiz_submitted = True
        
        # Show results if quiz is submitted
        if st.session_state.quiz_submitted:
            st.divider()
            st.subheader("📊 Quiz Results")
            
            # Calculate score
            correct_answers = 0
            total_questions = len(quiz_data)
            
            # Display results for each question
            for i, (question, user_answer) in enumerate(zip(quiz_data, st.session_state.user_answers)):
                correct = question["answer"]
                
                # Check if user answered correctly
                is_correct = user_answer == correct
                if is_correct:
                    correct_answers += 1
                
                # Display question result
                if is_correct:
                    st.markdown(f"**Question {i+1}:** ✅ Correct!")
                elif user_answer is None:
                    st.markdown(f"**Question {i+1}:** ⚠️ Not answered. Correct answer: {correct}")
                else:
                    st.markdown(f"**Question {i+1}:** ❌ Wrong. You answered: {user_answer}, Correct answer: {correct}")
            
            # Calculate and display percentage score
            percentage_score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            
            # Display the final score with appropriate coloring
            if percentage_score >= 80:
                st.success(f"### Your Score: {correct_answers}/{total_questions} ({percentage_score:.1f}%)")
            elif percentage_score >= 60:
                st.warning(f"### Your Score: {correct_answers}/{total_questions} ({percentage_score:.1f}%)")
            else:
                st.error(f"### Your Score: {correct_answers}/{total_questions} ({percentage_score:.1f}%)")
            
            # Performance message based on score
            if percentage_score == 100:
                st.balloons()
                st.markdown("### 🏆 Perfect Score! Outstanding performance!")
            elif percentage_score >= 80:
                st.markdown("### 🌟 Great job! You've mastered this topic!")
            elif percentage_score >= 60:
                st.markdown("### 👍 Good effort! Keep studying to improve.")
            else:
                st.markdown("### 📚 Keep learning! Review the material and try again.")
            
            # Options to try again or create new quiz
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Try Again", use_container_width=True):
                    st.session_state.user_answers = [None] * len(quiz_data)
                    st.session_state.quiz_submitted = False
                    st.rerun()
            
            with col2:
                if st.button("Create New Quiz", use_container_width=True):
                    st.session_state.current_mode = GENERATE_MODE
                    st.rerun()