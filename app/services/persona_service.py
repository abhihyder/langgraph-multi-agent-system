"""
Persona service.
Handles persona management and user preferences.
"""

from typing import Optional
from database import SessionLocal, Persona


class PersonaService:
    """Service for persona management."""
    
    def get_or_create_persona(self, user_id: int) -> Persona:
        """
        Get or create a persona for the user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Persona object
        """
        db = SessionLocal()
        try:
            persona = db.query(Persona).filter(
                Persona.user_id == user_id,
                Persona.agent_type == "general"
            ).first()
            
            if not persona:
                persona = Persona(
                    user_id=user_id,
                    agent_type="general",
                    tone="professional",
                    verbosity="balanced",
                    communication_style="formal",
                )
                db.add(persona)
                db.commit()
                db.refresh(persona)
            
            return persona
        finally:
            db.close()
    
    def update_persona(
        self,
        user_id: int,
        communication_style: str | None = None,
        preferred_response_length: str | None = None,
        custom_preferences: dict | None = None
    ) -> Persona:
        """
        Update persona preferences.
        
        Args:
            user_id: ID of the user
            communication_style: Communication style preference
            preferred_response_length: Response length preference
            custom_preferences: Custom preferences
            
        Returns:
            Updated persona object
        """
        db = SessionLocal()
        try:
            persona = db.query(Persona).filter(
                Persona.user_id == user_id,
                Persona.agent_type == "general"
            ).first()
            
            if not persona:
                persona = Persona(
                    user_id=user_id,
                    agent_type="general",
                    tone="professional",
                    verbosity="balanced",
                )
                db.add(persona)
            
            # Update fields
            if communication_style:
                persona.communication_style = communication_style
                tone_map = {"casual": "casual", "formal": "professional", "technical": "technical"}
                persona.tone = tone_map.get(communication_style, "professional")
            
            if preferred_response_length:
                verbosity_map = {"concise": "brief", "moderate": "balanced", "detailed": "comprehensive"}
                persona.verbosity = verbosity_map.get(preferred_response_length, "balanced")
            
            if custom_preferences:
                if persona.style_preferences is None:
                    persona.style_preferences = {}
                persona.style_preferences.update(custom_preferences)
            
            db.commit()
            db.refresh(persona)
            return persona
        finally:
            db.close()
