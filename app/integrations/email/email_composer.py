"""
Email Composer

AI-powered email composition using language models.

Generates professional emails based on:
- User intent
- Context
- Tone preferences
- Previous email threads
"""

from typing import Dict, Any, Optional, List
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from config.llm_config import get_llm_config

logger = logging.getLogger(__name__)


class EmailComposer:
    """
    AI-powered email composition service.
    
    Uses language models to generate professional emails based on user intent.
    """
    
    def __init__(self):
        """Initialize email composer with LLM."""
        self.llm_config = get_llm_config()
        # Use GENERAL_LLM configuration (provider:model format)
        llm_spec = self.llm_config.GENERAL_LLM.split(":")
        model = llm_spec[1] if len(llm_spec) > 1 else "gpt-4o-mini"
        
        api_key = self.llm_config.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.7,  # Creative but controlled
            api_key=SecretStr(api_key)
        )
        
        # Email composition prompt template
        self.compose_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional email composition assistant.

                Your task is to compose clear, professional emails based on user intent.

                Guidelines:
                1. Match the requested tone (formal, casual, friendly, etc.)
                2. Be concise and clear
                3. Include appropriate greeting and closing
                4. Use proper email etiquette
                5. Format for readability (paragraphs, bullets if needed)
                6. Proofread for grammar and spelling

                Output only the email body (no subject line unless requested).
            """),
            ("human", """Compose an email with the following details:

                **Intent/Purpose**: {intent}
                **Recipient Context**: {recipient_context}
                **Key Points to Include**: {key_points}
                **Tone**: {tone}
                **Additional Context**: {additional_context}

                Please compose the email:
            """)
        ])
        
        # Reply composition prompt
        self.reply_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional email reply assistant.

            Your task is to compose appropriate replies to emails.

            Guidelines:
            1. Address all points from the original email
            2. Maintain professional tone
            3. Be concise and clear
            4. Include appropriate closing
            5. Quote relevant parts if needed
            """),
                        ("human", """Original Email:
            ---
            From: {from_address}
            Subject: {subject}
            Date: {date}

            {original_body}
            ---

            **Reply Intent**: {reply_intent}
            **Key Points to Address**: {key_points}
            **Tone**: {tone}

            Please compose the reply:""")
        ])
    
    async def compose_email(
        self,
        intent: str,
        recipient_context: Optional[str] = None,
        key_points: Optional[List[str]] = None,
        tone: str = "professional",
        additional_context: Optional[str] = None
    ) -> str:
        """
        Compose an email using AI.
        
        Args:
            intent: Purpose/intent of the email
            recipient_context: Information about recipient (name, relationship, etc.)
            key_points: List of key points to include
            tone: Tone of email (professional, casual, friendly, formal)
            additional_context: Any additional context or requirements
            
        Returns:
            Composed email body as string
        """
        try:
            # Format key points
            points_str = "\n".join(f"- {point}" for point in (key_points or []))
            
            # Create chain
            chain = self.compose_prompt | self.llm
            
            # Generate email
            response = await chain.ainvoke({
                "intent": intent,
                "recipient_context": recipient_context or "General recipient",
                "key_points": points_str or "No specific points provided",
                "tone": tone,
                "additional_context": additional_context or "None"
            })
            
            email_body = str(response.content).strip() if response.content else ""
            
            logger.info(f"Composed email with intent: {intent[:50]}...")
            return email_body
            
        except Exception as e:
            logger.error(f"Email composition failed: {e}")
            raise Exception(f"Failed to compose email: {str(e)}")
    
    async def compose_reply(
        self,
        original_email: Dict[str, Any],
        reply_intent: str,
        key_points: Optional[List[str]] = None,
        tone: str = "professional"
    ) -> str:
        """
        Compose a reply to an existing email.
        
        Args:
            original_email: Original email dict with from, subject, date, body
            reply_intent: Purpose of the reply
            key_points: Points to address in reply
            tone: Tone of reply
            
        Returns:
            Composed reply body
        """
        try:
            # Format key points
            points_str = "\n".join(f"- {point}" for point in (key_points or []))
            
            # Create chain
            chain = self.reply_prompt | self.llm
            
            # Generate reply
            response = await chain.ainvoke({
                "from_address": original_email.get('from', 'Unknown'),
                "subject": original_email.get('subject', 'No subject'),
                "date": original_email.get('date', 'Unknown date'),
                "original_body": original_email.get('body', '')[:1000],  # Limit context
                "reply_intent": reply_intent,
                "key_points": points_str or "No specific points",
                "tone": tone
            })
            
            reply_body = str(response.content).strip() if response.content else ""
            
            logger.info(f"Composed reply to: {original_email.get('subject', 'email')}")
            return reply_body
            
        except Exception as e:
            logger.error(f"Reply composition failed: {e}")
            raise Exception(f"Failed to compose reply: {str(e)}")
    
    async def generate_subject(
        self,
        email_body: str,
        context: Optional[str] = None
    ) -> str:
        """
        Generate an appropriate subject line for an email.
        
        Args:
            email_body: The email body content
            context: Additional context about the email purpose
            
        Returns:
            Suggested subject line
        """
        try:
            prompt = f"""Based on this email content, suggest a concise, professional subject line (max 10 words):

            Context: {context or 'General email'}

            Email Body:
            {email_body[:500]}

            Subject line:"""
            
            response = await self.llm.ainvoke(prompt)
            content = str(response.content) if response.content else "Follow-up"
            subject = content.strip().strip('"').strip("'")
            
            logger.info(f"Generated subject: {subject}")
            return subject
            
        except Exception as e:
            logger.error(f"Subject generation failed: {e}")
            return "Follow-up"  # Fallback subject
    
    async def summarize_email(
        self,
        email: Dict[str, Any],
        max_length: int = 100
    ) -> str:
        """
        Generate a concise summary of an email.
        
        Args:
            email: Email dict with subject and body
            max_length: Maximum summary length in words
            
        Returns:
            Email summary
        """
        try:
            prompt = f"""Summarize this email in {max_length} words or less. Focus on key points and action items.

Subject: {email.get('subject', 'No subject')}
From: {email.get('from', 'Unknown')}

Body:
{email.get('body', '')[:1000]}

Summary:"""
            
            response = await self.llm.ainvoke(prompt)
            summary = str(response.content).strip() if response.content else ""
            
            logger.info(f"Summarized email: {email.get('subject', 'email')}")
            return summary
            
        except Exception as e:
            logger.error(f"Email summarization failed: {e}")
            return email.get('snippet', '')[:max_length]  # Fallback to snippet
    
    async def extract_action_items(
        self,
        email: Dict[str, Any]
    ) -> List[str]:
        """
        Extract action items from an email.
        
        Args:
            email: Email dict with body
            
        Returns:
            List of action items
        """
        try:
            prompt = f"""Extract any action items, tasks, or requests from this email. List them as bullet points.

Subject: {email.get('subject', 'No subject')}
Body:
{email.get('body', '')[:1000]}

Action items (if any):"""
            
            response = await self.llm.ainvoke(prompt)
            content = str(response.content).strip() if response.content else ""
            
            # Parse bullet points
            action_items = [
                line.strip().lstrip('-•*').strip()
                for line in content.split('\n')
                if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•') or line.strip().startswith('*'))
            ]
            
            logger.info(f"Extracted {len(action_items)} action items")
            return action_items
            
        except Exception as e:
            logger.error(f"Action item extraction failed: {e}")
            return []
    
    def get_tone_examples(self) -> Dict[str, str]:
        """
        Get example tones with descriptions.
        
        Returns:
            Dict mapping tone names to descriptions
        """
        return {
            "professional": "Business-appropriate, clear, and respectful",
            "formal": "Very polite, structured, appropriate for executives",
            "casual": "Friendly but still professional, conversational",
            "friendly": "Warm and approachable, for colleagues",
            "urgent": "Direct and action-oriented, for time-sensitive matters",
            "apologetic": "Acknowledging mistakes, seeking resolution",
            "persuasive": "Convincing, presenting benefits clearly"
        }
