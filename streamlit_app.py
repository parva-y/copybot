import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import io
import re

# Import the agent framework (assuming it's in the same directory)
from agent_framework import (
    MultiModalCopyAgent, 
    BrandGuidelines, 
    CopyRequest, 
    CopyConstraints,
    GeneratedCopy
)

# Page configuration
st.set_page_config(
    page_title="AI Copywriting Agent",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'copy_history' not in st.session_state:
    st.session_state.copy_history = []
if 'brand_guidelines' not in st.session_state:
    st.session_state.brand_guidelines = None

def initialize_agent(brand_guidelines: BrandGuidelines):
    """Initialize the copywriting agent"""
    st.session_state.agent = MultiModalCopyAgent(brand_guidelines)
    st.session_state.brand_guidelines = brand_guidelines

def main():
    st.markdown('<h1 class="main-header">🤖 AI Copywriting Agent</h1>', unsafe_allow_html=True)
    
    # Sidebar for brand guidelines and settings
    with st.sidebar:
        st.header("🎯 Brand Guidelines")
        
        # Brand configuration
        brand_name = st.text_input("Brand Name", value="YourBrand", key="brand_name")
        
        # Tone of voice
        tone_options = ["Professional", "Friendly", "Conversational", "Authoritative", "Creative", "Casual"]
        selected_tones = st.multiselect("Tone of Voice", tone_options, default=["Professional", "Friendly"])
        
        # Key messaging
        st.subheader("Key Messaging")
        key_messages = st.text_area(
            "Enter key messages (one per line)",
            value="We deliver exceptional results\nYour trusted partner in success",
            height=100
        ).split('\n')
        key_messages = [msg.strip() for msg in key_messages if msg.strip()]
        
        # Words to avoid/prefer
        avoid_words = st.text_input("Words to Avoid (comma-separated)", 
                                   value="cheap, basic, simple").split(',')
        avoid_words = [word.strip().lower() for word in avoid_words if word.strip()]
        
        prefer_words = st.text_input("Preferred Words (comma-separated)", 
                                    value="premium, advanced, innovative, quality").split(',')
        prefer_words = [word.strip().lower() for word in prefer_words if word.strip()]
        
        # Target audience
        target_audience = st.text_area("Target Audience", 
                                      value="Business professionals and decision makers",
                                      height=60)
        
        # Create brand guidelines
        if st.button("💾 Save Brand Guidelines", type="primary"):
            brand_guidelines = BrandGuidelines(
                brand_name=brand_name,
                tone_of_voice=selected_tones,
                key_messaging=key_messages,
                avoid_words=avoid_words,
                preferred_words=prefer_words,
                style_rules={"max_sentence_length": "20 words"},
                target_audience=target_audience
            )
            initialize_agent(brand_guidelines)
            st.success("Brand guidelines saved!")
    
    # Main content area
    if st.session_state.agent is None:
        st.warning("⚠️ Please configure and save your brand guidelines in the sidebar first.")
        return
    
    # Tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Generate Copy", "📊 Copy History", "📈 Analytics", "⚙️ Settings"])
    
    with tab1:
        generate_copy_interface()
    
    with tab2:
        copy_history_interface()
    
    with tab3:
        analytics_interface()
    
    with tab4:
        settings_interface()

def generate_copy_interface():
    """Interface for generating new copy"""
    st.markdown('<h2 class="section-header">Generate New Copy</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Content type selection
        content_type = st.selectbox(
            "Content Type",
            ["Product Launch", "Service Description", "Blog Post", "Email Campaign", 
             "Social Media", "Website Copy", "Advertisement", "Press Release"]
        )
        
        # Input data
        st.subheader("📥 Input Content")
        
        # Text input
        text_input = st.text_area("Main Content/Description", height=150,
                                 placeholder="Enter your product details, key features, or main content here...")
        
        # File uploads
        uploaded_files = st.file_uploader(
            "Upload Supporting Files (images, documents, etc.)",
            accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'txt', 'csv']
        )
        
        # Additional context
        context = st.text_area("Additional Context", height=100,
                              placeholder="Any specific requirements, competitor info, or campaign context...")
        
        # Reference copies
        reference_copies = st.text_area("Reference Copies (paste previous successful copies for learning)",
                                       height=120,
                                       placeholder="Paste examples of successful copies to help the AI learn your style...")
    
    with col2:
        # Copy format settings
        st.subheader("📐 Format Settings")
        
        format_type = st.selectbox("Output Format", ["table", "paragraph", "bullet_points"])
        
        # Length constraints
        min_length = st.number_input("Minimum Words", min_value=1, value=10, step=1)
        max_length = st.number_input("Maximum Words", min_value=min_length, value=50, step=1)
        
        # Table-specific settings
        if format_type == "table":
            st.subheader("Table Columns")
            default_columns = ["Feature", "Benefit", "Description"]
            columns_input = st.text_area("Column Names (one per line)", 
                                        value="\n".join(default_columns), height=80)
            required_columns = [col.strip() for col in columns_input.split('\n') if col.strip()]
        else:
            required_columns = []
        
        # Copy tone
        copy_tone = st.selectbox("Copy Tone", ["professional", "friendly", "conversational", "persuasive"])
        
        # Call to action
        cta_required = st.checkbox("Include Call-to-Action")
        
        # Generate button
        if st.button("🚀 Generate Copy", type="primary", use_container_width=True):
            generate_copy(content_type, text_input, uploaded_files, context, reference_copies,
                         format_type, min_length, max_length, required_columns, copy_tone, cta_required)

def generate_copy(content_type, text_input, uploaded_files, context, reference_copies,
                 format_type, min_length, max_length, required_columns, copy_tone, cta_required):
    """Generate copy based on inputs"""
    
    if not text_input.strip():
        st.error("Please provide main content/description.")
        return
    
    with st.spinner("🤖 Generating copy..."):
        try:
            # Process uploaded files
            file_data = {}
            if uploaded_files:
                for file in uploaded_files:
                    file_content = file.read()
                    file_data[file.name] = {
                        "type": file.type,
                        "size": len(file_content),
                        "content": file_content
                    }
            
            # Create copy constraints
            constraints = CopyConstraints(
                max_length=max_length,
                min_length=min_length,
                format_type=format_type,
                required_columns=required_columns,
                tone=copy_tone,
                call_to_action_required=cta_required
            )
            
            # Create copy request
            input_data = {
                "main_content": text_input,
                "files": file_data,
                "content_type": content_type
            }
            
            request = CopyRequest(
                content_type=content_type,
                input_data=input_data,
                target_format=constraints,
                context=context,
                reference_copies=[ref.strip() for ref in reference_copies.split('\n') if ref.strip()] if reference_copies else None
            )
            
            # Generate copy
            result = st.session_state.agent.generate_copy(request)
            
            # Store in session state
            st.session_state.copy_history.append(result)
            
            # Display results
            display_generated_copy(result)
            
        except Exception as e:
            st.error(f"Error generating copy: {str(e)}")

def display_generated_copy(result: GeneratedCopy):
    """Display the generated copy results"""
    st.markdown('<div class="success-message">✅ Copy generated successfully!</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Word Count", result.word_count)
    with col2:
        st.metric("Brand Compliance", f"{result.compliance_score:.1%}")
    with col3:
        st.metric("Generated", result.timestamp.strftime("%H:%M"))
    with col4:
        st.metric("Request ID", result.request_id[-6:])
    
    # Generated content
    st.subheader("📄 Generated Copy")
    
    if isinstance(result.content, pd.DataFrame):
        st.dataframe(result.content, use_container_width=True)
        
        # Download options for table
        col1, col2 = st.columns(2)
        with col1:
            csv_data = result.content.to_csv(index=False)
            st.download_button("📥 Download CSV", csv_data, "generated_copy.csv", "text/csv")
        with col2:
            excel_buffer = io.BytesIO()
            result.content.to_excel(excel_buffer, index=False)
            st.download_button("📥 Download Excel", excel_buffer.getvalue(), "generated_copy.xlsx")
    else:
        st.text_area("Generated Copy", value=str(result.content), height=200)
        
        # Download option for text
        st.download_button("📥 Download Text", str(result.content), "generated_copy.txt", "text/plain")
    
    # Metadata
    with st.expander("📊 Generation Details"):
        st.json(result.metadata)

def copy_history_interface():
    """Interface for viewing copy history"""
    st.markdown('<h2 class="section-header">Copy History</h2>', unsafe_allow_html=True)
    
    if not st.session_state.copy_history:
        st.info("No copies generated yet. Go to the 'Generate Copy' tab to create your first copy!")
        return
    
    # History overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Copies", len(st.session_state.copy_history))
    with col2:
        avg_compliance = sum(copy.compliance_score for copy in st.session_state.copy_history) / len(st.session_state.copy_history)
        st.metric("Avg. Brand Compliance", f"{avg_compliance:.1%}")
    with col3:
        avg_words = sum(copy.word_count for copy in st.session_state.copy_history) / len(st.session_state.copy_history)
        st.metric("Avg. Word Count", f"{avg_words:.0f}")
    
    # Copy list
    st.subheader("📋 Recent Copies")
    
    for i, copy in enumerate(reversed(st.session_state.copy_history[-10:])):  # Show last 10
        with st.expander(f"Copy #{len(st.session_state.copy_history)-i} - {copy.timestamp.strftime('%Y-%m-%d %H:%M')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if isinstance(copy.content, pd.DataFrame):
                    st.dataframe(copy.content)
                else:
                    st.text_area("Content", value=str(copy.content), height=100, key=f"history_{i}")
            
            with col2:
                st.metric("Words", copy.word_count)
                st.metric("Compliance", f"{copy.compliance_score:.1%}")
                st.json(copy.metadata)

def analytics_interface():
    """Interface for analytics and insights"""
    st.markdown('<h2 class="section-header">Analytics & Insights</h2>', unsafe_allow_html=True)
    
    if not st.session_state.copy_history:
        st.info("Generate some copies first to see analytics!")
        return
    
    # Performance metrics
    if st.session_state.agent:
        metrics = st.session_state.agent.get_performance_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Copies", metrics.get("total_copies_generated", 0))
        with col2:
            st.metric("Avg. Compliance", f"{metrics.get('average_compliance_score', 0):.1%}")
        with col3:
            st.metric("Avg. Words", f"{metrics.get('average_word_count', 0):.0f}")
        with col4:
            st.metric("Recent Copies", metrics.get("recent_copies", 0))
    
    # Trends over time
    if len(st.session_state.copy_history) > 1:
        st.subheader("📈 Trends Over Time")
        
        # Create dataframe for plotting
        history_data = []
        for i, copy in enumerate(st.session_state.copy_history):
            history_data.append({
                "Copy #": i + 1,
                "Brand Compliance": copy.compliance_score,
                "Word Count": copy.word_count,
                "Timestamp": copy.timestamp
            })
        
        df = pd.DataFrame(history_data)
        
        col1, col2 = st.columns(2)
        with col1:
            st.line_chart(df.set_index("Copy #")["Brand Compliance"])
            st.caption("Brand Compliance Over Time")
        
        with col2:
            st.line_chart(df.set_index("Copy #")["Word Count"])
            st.caption("Word Count Over Time")
    
    # Content type analysis
    st.subheader("📊 Content Type Distribution")
    content_types = [copy.metadata.get("request_type", "Unknown") for copy in st.session_state.copy_history]
    content_type_counts = pd.Series(content_types).value_counts()
    st.bar_chart(content_type_counts)

def settings_interface():
    """Interface for app settings and configurations"""
    st.markdown('<h2 class="section-header">Settings & Configuration</h2>', unsafe_allow_html=True)
    
    # Export/Import settings
    st.subheader("📤 Export/Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Copy History"):
            if st.session_state.copy_history:
                export_data = []
                for copy in st.session_state.copy_history:
                    export_data.append({
                        "timestamp": copy.timestamp.isoformat(),
                        "content": str(copy.content),
                        "word_count": copy.word_count,
                        "compliance_score": copy.compliance_score,
                        "metadata": copy.metadata
                    })
                
                json_data = json.dumps(export_data, indent=2)
                st.download_button(
                    "📥 Download History JSON",
                    json_data,
                    "copy_history.json",
                    "application/json"
                )
            else:
                st.info("No copy history to export.")
    
    with col2:
        if st.button("🗑️ Clear History"):
            if st.button("⚠️ Confirm Clear History", type="secondary"):
                st.session_state.copy_history = []
                st.success("History cleared!")
                st.rerun()
    
    # Brand guidelines export
    st.subheader("📋 Brand Guidelines")
    if st.session_state.brand_guidelines:
        guidelines_json = json.dumps(asdict(st.session_state.brand_guidelines), indent=2)
        st.download_button(
            "📥 Export Brand Guidelines",
            guidelines_json,
            "brand_guidelines.json",
            "application/json"
        )
    
    # App information
    st.subheader("ℹ️ About")
    st.info("""
    **AI Copywriting Agent v1.0**
    
    This application helps you generate brand-compliant copy using AI while maintaining consistency 
    with your brand guidelines and learning from your previous successful copies.
    
    **Features:**
    - Multi-modal input processing
    - Brand compliance scoring
    - Multiple output formats
    - Copy history and analytics
    - Export/import capabilities
    """)

if __name__ == "__main__":
    main()
