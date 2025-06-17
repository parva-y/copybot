import json
import pandas as pd
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import re
from pathlib import Path

@dataclass
class BrandGuidelines:
    """Brand guidelines configuration"""
    brand_name: str
    tone_of_voice: List[str]  # e.g., ["professional", "friendly", "conversational"]
    key_messaging: List[str]
    avoid_words: List[str]
    preferred_words: List[str]
    style_rules: Dict[str, str]
    target_audience: str

@dataclass
class CopyConstraints:
    """Copy format and length constraints"""
    max_length: int
    min_length: int
    format_type: str  # "table", "bullet", "paragraph"
    required_columns: List[str]  # for table format
    tone: str
    call_to_action_required: bool = False

@dataclass
class CopyRequest:
    """Input request for copy generation"""
    content_type: str  # "product", "service", "announcement", etc.
    input_data: Dict[str, Any]  # product info, images, etc.
    target_format: CopyConstraints
    context: Optional[str] = None
    reference_copies: Optional[List[str]] = None

@dataclass
class GeneratedCopy:
    """Output structure for generated copy"""
    content: Union[str, pd.DataFrame]
    metadata: Dict[str, Any]
    word_count: int
    compliance_score: float  # brand guideline adherence
    timestamp: datetime
    request_id: str

class MultiModalCopyAgent:
    """Main agent class for multi-modal copywriting"""
    
    def __init__(self, brand_guidelines: BrandGuidelines):
        self.brand_guidelines = brand_guidelines
        self.copy_history = []
        self.context_memory = {}
        
    def process_input(self, request: CopyRequest) -> Dict[str, Any]:
        """Process multi-modal input data"""
        processed_data = {
            "text_content": "",
            "image_descriptions": [],
            "structured_data": {},
            "context": request.context or ""
        }
        
        # Process different input types
        for key, value in request.input_data.items():
            if isinstance(value, str):
                processed_data["text_content"] += f"{key}: {value}\n"
            elif isinstance(value, dict):
                processed_data["structured_data"][key] = value
            elif isinstance(value, list):
                if key.lower() in ["images", "photos", "visuals"]:
                    processed_data["image_descriptions"].extend(value)
        
        return processed_data
    
    def analyze_brand_compliance(self, text: str) -> float:
        """Check brand guideline compliance"""
        score = 1.0
        text_lower = text.lower()
        
        # Check avoided words
        for avoid_word in self.brand_guidelines.avoid_words:
            if avoid_word.lower() in text_lower:
                score -= 0.1
        
        # Check preferred words usage
        preferred_count = sum(1 for word in self.brand_guidelines.preferred_words 
                            if word.lower() in text_lower)
        score += min(preferred_count * 0.05, 0.2)
        
        # Tone analysis (simplified)
        tone_keywords = {
            "professional": ["solution", "expertise", "quality", "reliable"],
            "friendly": ["help", "support", "easy", "simple", "welcome"],
            "conversational": ["you", "your", "we", "let's", "together"]
        }
        
        for tone in self.brand_guidelines.tone_of_voice:
            if tone in tone_keywords:
                tone_matches = sum(1 for keyword in tone_keywords[tone] 
                                 if keyword in text_lower)
                score += min(tone_matches * 0.02, 0.1)
        
        return min(max(score, 0.0), 1.0)
    
    def format_as_table(self, content: Dict[str, Any], constraints: CopyConstraints) -> pd.DataFrame:
        """Format content as structured table"""
        if not constraints.required_columns:
            constraints.required_columns = ["Feature", "Benefit", "Description"]
        
        # Create table structure
        table_data = []
        
        # Extract key information for table format
        if "structured_data" in content:
            for item_key, item_data in content["structured_data"].items():
                row = {}
                for col in constraints.required_columns:
                    if col.lower() in ["feature", "title", "name"]:
                        row[col] = item_key
                    elif col.lower() in ["benefit", "value", "advantage"]:
                        row[col] = self.generate_benefit_copy(item_data, constraints)
                    elif col.lower() in ["description", "detail", "copy"]:
                        row[col] = self.generate_description_copy(item_data, constraints)
                    else:
                        row[col] = str(item_data.get(col.lower(), ""))
                table_data.append(row)
        
        return pd.DataFrame(table_data)
    
    def generate_benefit_copy(self, data: Dict, constraints: CopyConstraints) -> str:
        """Generate benefit-focused copy"""
        # This would integrate with your chosen LLM
        # Placeholder implementation
        benefits = []
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ["benefit", "advantage", "value"]:
                    benefits.append(str(value))
        
        if not benefits:
            benefits = ["Enhanced user experience", "Improved efficiency", "Better results"]
        
        copy = " | ".join(benefits[:2])  # Limit for length
        return self.ensure_length_compliance(copy, constraints)
    
    def generate_description_copy(self, data: Dict, constraints: CopyConstraints) -> str:
        """Generate descriptive copy"""
        # This would integrate with your chosen LLM
        # Placeholder implementation
        description = str(data) if not isinstance(data, dict) else json.dumps(data)
        
        # Apply brand voice
        if "professional" in self.brand_guidelines.tone_of_voice:
            description = f"Our solution delivers {description}"
        elif "friendly" in self.brand_guidelines.tone_of_voice:
            description = f"We help you with {description}"
        
        return self.ensure_length_compliance(description, constraints)
    
    def ensure_length_compliance(self, text: str, constraints: CopyConstraints) -> str:
        """Ensure text meets length requirements"""
        words = text.split()
        
        if len(words) > constraints.max_length:
            return " ".join(words[:constraints.max_length])
        elif len(words) < constraints.min_length:
            # Add filler content that matches brand guidelines
            filler_phrases = [
                f"with {self.brand_guidelines.brand_name}",
                "for optimal results",
                "designed for you"
            ]
            while len(words) < constraints.min_length and filler_phrases:
                phrase = filler_phrases.pop(0)
                text += f" {phrase}"
                words = text.split()
        
        return text
    
    def learn_from_context(self, reference_copies: List[str]):
        """Learn patterns from previous successful copies"""
        # Analyze patterns in reference copies
        patterns = {
            "common_phrases": [],
            "structure_patterns": [],
            "length_distribution": []
        }
        
        for copy in reference_copies:
            # Extract common phrases
            sentences = re.split(r'[.!?]+', copy)
            patterns["common_phrases"].extend(sentences)
            
            # Analyze structure
            word_count = len(copy.split())
            patterns["length_distribution"].append(word_count)
        
        # Store patterns for future use
        self.context_memory["patterns"] = patterns
    
    def generate_copy(self, request: CopyRequest) -> GeneratedCopy:
        """Main method to generate copy"""
        # Process input
        processed_input = self.process_input(request)
        
        # Learn from reference copies if provided
        if request.reference_copies:
            self.learn_from_context(request.reference_copies)
        
        # Generate content based on format type
        if request.target_format.format_type == "table":
            content = self.format_as_table(processed_input, request.target_format)
            word_count = content.to_string().count(' ') + 1
        else:
            # Generate paragraph or bullet format
            content = self.generate_text_copy(processed_input, request.target_format)
            word_count = len(content.split())
        
        # Check brand compliance
        text_for_analysis = content.to_string() if isinstance(content, pd.DataFrame) else content
        compliance_score = self.analyze_brand_compliance(text_for_analysis)
        
        # Create result
        result = GeneratedCopy(
            content=content,
            metadata={
                "request_type": request.content_type,
                "format": request.target_format.format_type,
                "brand_compliance": compliance_score
            },
            word_count=word_count,
            compliance_score=compliance_score,
            timestamp=datetime.now(),
            request_id=f"copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Store in history
        self.copy_history.append(result)
        
        return result
    
    def generate_text_copy(self, processed_input: Dict, constraints: CopyConstraints) -> str:
        """Generate text-based copy (paragraph/bullet format)"""
        # This would integrate with your chosen LLM (OpenAI, Claude, etc.)
        # Placeholder implementation
        
        base_content = processed_input["text_content"]
        context = processed_input["context"]
        
        # Apply brand voice and messaging
        copy_elements = []
        
        # Add brand messaging
        if self.brand_guidelines.key_messaging:
            copy_elements.append(self.brand_guidelines.key_messaging[0])
        
        # Add main content
        copy_elements.append(base_content)
        
        # Add call to action if required
        if constraints.call_to_action_required:
            cta = f"Experience the {self.brand_guidelines.brand_name} difference today."
            copy_elements.append(cta)
        
        final_copy = " ".join(copy_elements)
        return self.ensure_length_compliance(final_copy, constraints)
    
    def export_copy(self, generated_copy: GeneratedCopy, file_path: str):
        """Export generated copy to file"""
        if isinstance(generated_copy.content, pd.DataFrame):
            generated_copy.content.to_csv(file_path, index=False)
        else:
            with open(file_path, 'w') as f:
                f.write(str(generated_copy.content))
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        if not self.copy_history:
            return {"message": "No copies generated yet"}
        
        compliance_scores = [copy.compliance_score for copy in self.copy_history]
        word_counts = [copy.word_count for copy in self.copy_history]
        
        return {
            "total_copies_generated": len(self.copy_history),
            "average_compliance_score": sum(compliance_scores) / len(compliance_scores),
            "average_word_count": sum(word_counts) / len(word_counts),
            "recent_copies": len([c for c in self.copy_history 
                                if (datetime.now() - c.timestamp).days <= 7])
        }


# Example usage and integration setup
def setup_agent_example():
    """Example setup for the copywriting agent"""
    
    # Define brand guidelines
    brand_guidelines = BrandGuidelines(
        brand_name="TechFlow Solutions",
        tone_of_voice=["professional", "innovative", "trustworthy"],
        key_messaging=[
            "Streamlining business operations through technology",
            "Your trusted partner in digital transformation"
        ],
        avoid_words=["cheap", "basic", "simple"],
        preferred_words=["premium", "advanced", "sophisticated", "streamlined"],
        style_rules={
            "sentence_length": "Keep sentences under 20 words",
            "paragraph_length": "Maximum 3 sentences per paragraph"
        },
        target_audience="Enterprise decision makers and IT professionals"
    )
    
    # Initialize agent
    agent = MultiModalCopyAgent(brand_guidelines)
    
    # Example copy constraints for table format
    table_constraints = CopyConstraints(
        max_length=25,  # words per cell
        min_length=5,
        format_type="table",
        required_columns=["Feature", "Benefit", "Business Impact"],
        tone="professional",
        call_to_action_required=False
    )
    
    # Example request
    copy_request = CopyRequest(
        content_type="product_launch",
        input_data={
            "product_name": "AI Analytics Platform",
            "key_features": {
                "real_time_analytics": "Process data instantly",
                "predictive_modeling": "Forecast trends accurately",
                "automated_reporting": "Generate insights automatically"
            },
            "target_market": "Enterprise customers",
            "images": ["dashboard_screenshot.jpg", "analytics_chart.png"]
        },
        target_format=table_constraints,
        context="Launching Q3 2024, competitor analysis shows need for emphasis on speed and accuracy"
    )
    
    return agent, copy_request

# Integration points for LLM APIs
class LLMIntegration:
    """Integration layer for different LLM providers"""
    
    def __init__(self, provider: str = "openai", api_key: str = None):
        self.provider = provider
        self.api_key = api_key
    
    def generate_copy_with_llm(self, prompt: str, constraints: CopyConstraints) -> str:
        """Generate copy using external LLM"""
        # This would integrate with OpenAI, Claude, or other APIs
        # Example structure for API integration
        
        system_prompt = f"""
        You are a professional copywriter. Generate copy that:
        - Stays within {constraints.min_length}-{constraints.max_length} words
        - Matches {constraints.tone} tone
        - Follows the format: {constraints.format_type}
        """
        
        # Placeholder - implement actual API calls here
        return "Generated copy would appear here from LLM API"

if __name__ == "__main__":
    # Demo the framework
    agent, request = setup_agent_example()
    result = agent.generate_copy(request)
    
    print("Generated Copy:")
    print(result.content)
    print(f"\nCompliance Score: {result.compliance_score}")
    print(f"Word Count: {result.word_count}")
