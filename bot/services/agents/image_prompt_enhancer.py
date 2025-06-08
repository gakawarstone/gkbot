from services.llm import Gemini


class ImagePromptEnhancer:
    @staticmethod
    async def enhance(prompt: str) -> str:
        _prompt = f"""
        You are a creative prompt engineer for AI image generation. Your job is to take a basic or vague image prompt and expand it into a highly detailed, vivid, and imaginative description that can be used with advanced text-to-image models (like DALL·E, Midjourney, or Stable Diffusion).
        Given the original prompt:
            {prompt}
        Enhance it by:
        Clarifying ambiguous elements (e.g., time period, setting, lighting).
        Adding visual details (textures, colors, atmosphere, emotions).
        Including style cues (e.g., "cyberpunk", "Baroque painting", "pixel art").
        Mentioning the subject's pose, clothing, expression, or background if relevant.
        Output the improved version in a concise yet vivid paragraph. Do not add extra commentary.
        """
        return await Gemini().generate(_prompt)
