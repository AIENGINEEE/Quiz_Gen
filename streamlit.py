import streamlit as st
import re
import json
from Main import generate_quiz
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

# Create sidebar navigation
with st.sidebar:
    st.title("🤖 AI Quiz Generator")
    
    # Navigation buttons
    if st.button("📝 Create New Quiz", use_container_width=True):
        st.session_state.current_mode = GENERATE_MODE
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
                "English", "Spanish", "French", "German", "Italian", "Portuguese", 
                "Russian", "Chinese", "Japanese", "Korean", "Arabic", "Hindi", 
                "Dutch", "Swedish", "Norwegian", "Finnish", "Danish", "Greek", 
                "Turkish", "Polish", "Czech", "Hungarian", "Thai", "Vietnamese"
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
                    
                    # Extract options
                    options = re.findall(r'([A-D])\)\s*(.+?)(?:\n|$)', q)
                    options_dict = {letter: text.strip() for letter, text in options}
                    
                    # Extract answer
                    answer_match = re.search(r'\*\*Answer:\*\*\s*([A-D])', q)
                    correct_answer = answer_match.group(1).strip() if answer_match else None
                    
                    st.session_state.quiz_data.append({
                        "question": question_text,
                        "options": options_dict,
                        "answer": correct_answer
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
            if st.button("Take This Quiz Now", type="primary", use_container_width=True):
                st.session_state.current_mode = PLAY_MODE
                st.session_state.quiz_submitted = False
                st.rerun()
        
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
                
                st.divider()

# Play Mode
elif st.session_state.current_mode == PLAY_MODE:
    st.title("🎮 Play Quiz")
    
    # Quiz selection if there are saved quizzes
    if st.session_state.saved_quizzes:
        # Create a list of quiz topics for selection
        quiz_options = [f"{q['metadata']['topic']} ({q['metadata']['difficulty']}, {q['metadata']['language']})" 
                        for q in st.session_state.saved_quizzes]
        
        selected_quiz_index = st.selectbox(
            "Select a quiz to play:",
            range(len(quiz_options)),
            format_func=lambda x: quiz_options[x]
        )
        
        # Load the selected quiz
        selected_quiz = st.session_state.saved_quizzes[selected_quiz_index]
        st.session_state.quiz_data = selected_quiz["questions"]
        st.session_state.quiz_metadata = selected_quiz["metadata"]
        
        if len(st.session_state.user_answers) != len(st.session_state.quiz_data):
            st.session_state.user_answers = [None] * len(st.session_state.quiz_data)
        
        # Display quiz details
        st.markdown(f"""
        ### Quiz Information
        - **Topic:** {st.session_state.quiz_metadata['topic']}
        - **Difficulty:** {st.session_state.quiz_metadata['difficulty']}
        - **Language:** {st.session_state.quiz_metadata['language']}
        - **Questions:** {len(st.session_state.quiz_data)}
        """)
        
        # Display quiz for playing
        st.divider()
        st.subheader("Answer the questions below")
        
        # Create a form for submitting answers
        with st.form("quiz_play_form"):
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Question {i+1}: {q['question']}**")
                
                # Only show options if we have them
                if q['options'] and isinstance(q['options'], dict) and len(q['options']) > 0:
                    selected_option = st.radio(
                        label=f"Select your answer for Question {i+1}:",
                        options=list(q['options'].keys()),
                        format_func=lambda x: f"{x}) {q['options'][x]}",
                        key=f"play_q_{i}",
                        horizontal=st.session_state.quiz_metadata['q_type'] == "True/False",
                        index=None
                    )
                    
                    # Store answer in session state
                    if selected_option:
                        st.session_state.user_answers[i] = selected_option
                
                st.divider()
            
            # Submit button
            submit_quiz = st.form_submit_button("Submit Answers", use_container_width=True)
        
        # Process quiz submission
        if submit_quiz:
            st.session_state.quiz_submitted = True
            
            # Display results
            st.subheader("📊 Results")
            
            score = 0
            results_data = []
            
            for i, q in enumerate(st.session_state.quiz_data):
                user_answer = st.session_state.user_answers[i]
                correct_answer = q["answer"]
                
                # Calculate score
                is_correct = user_answer == correct_answer
                if is_correct:
                    score += 1
                
                # Display result for each question
                result_color = "green" if is_correct else "red"
                result_icon = "✅" if is_correct else "❌"
                
                st.markdown(
                    f"<div style='color:{result_color};'>{result_icon} <b>Question {i+1}:</b> "
                    f"You selected {user_answer or 'nothing'}, "
                    f"Correct answer: {correct_answer}</div>",
                    unsafe_allow_html=True
                )
            
            # Show final score with percentage
            percentage = (score / len(st.session_state.quiz_data)) * 100
            st.info(f"Your Score: **{score} / {len(st.session_state.quiz_data)}** ({percentage:.1f}%)")
            
            # Option to download results
            pdf_data = get_pdf_download_link(
                st.session_state.quiz_data, 
                st.session_state.quiz_metadata["topic"],
                st.session_state.quiz_metadata["difficulty"],
                st.session_state.quiz_metadata["language"],
                user_answers=st.session_state.user_answers,
                show_answers=True
            )
            
            file_name = f"{st.session_state.quiz_metadata['topic'].replace(' ', '_')}_quiz_results.pdf"
            st.markdown("#### Download your results")
            st.markdown(
                create_download_button(pdf_data, file_name, "Download Results as PDF"),
                unsafe_allow_html=True
            )
            
            # Option to play again
            if st.button("Play Another Quiz", type="primary"):
                st.session_state.quiz_submitted = False
                st.rerun()
    else:
        st.info("No saved quizzes found. Please create a quiz first.")
        if st.button("Create a Quiz", type="primary"):
            st.session_state.current_mode = GENERATE_MODE
            st.rerun()