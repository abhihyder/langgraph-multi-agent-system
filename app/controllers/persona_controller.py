"""
Persona controller.
Handles persona management requests and response formatting.
"""

from database import User
from app.services.persona_service import PersonaService


class PersonaController:
    """Controller for persona management operations."""
    
    def __init__(self):
        self.persona_service = PersonaService()
    
    async def get_persona(self, user: User) -> dict:
        """
        Get user's persona profile.
        
        Args:
            user: Authenticated user
            
        Returns:
            Persona information with preferences and statistics
        """
        persona = self.persona_service.get_or_create_persona(user_id=user.id)  # type: ignore
        
        return {
            "id": persona.id,
            "user_id": persona.user_id,
            "communication_style": persona.communication_style or "formal",
            "expertise_level": "intermediate",
            "interests": persona.domain_knowledge or [],
            "preferred_agents": [],
            "interaction_count": persona.accepted_responses + persona.rejected_responses,
            "learning_data": {
                "tone": persona.tone,
                "verbosity": persona.verbosity,
                "accepted": persona.accepted_responses,
                "rejected": persona.rejected_responses,
            },
            "created_at": persona.created_at,
            "updated_at": persona.updated_at,
        }
    
    async def update_persona(
        self,
        user: User,
        communication_style: str | None = None,
        preferred_response_length: str | None = None,
        custom_preferences: dict | None = None
    ) -> dict:
        """
        Update user persona preferences.
        
        Args:
            user: Authenticated user
            communication_style: Communication style preference
            preferred_response_length: Response length preference
            custom_preferences: Custom preferences
            
        Returns:
            Updated persona information
        """
        persona = self.persona_service.update_persona(
            user_id=user.id,  # type: ignore
            communication_style=communication_style,
            preferred_response_length=preferred_response_length,
            custom_preferences=custom_preferences
        )
        
        return {
            "id": persona.id,
            "user_id": persona.user_id,
            "communication_style": persona.communication_style or "formal",
            "expertise_level": "intermediate",
            "interests": persona.domain_knowledge or [],
            "preferred_agents": [],
            "interaction_count": persona.accepted_responses + persona.rejected_responses,
            "learning_data": {
                "tone": persona.tone,
                "verbosity": persona.verbosity,
                "accepted": persona.accepted_responses,
                "rejected": persona.rejected_responses,
                "style_preferences": persona.style_preferences,
            },
            "created_at": persona.created_at,
            "updated_at": persona.updated_at,
        }
