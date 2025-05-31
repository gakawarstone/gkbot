from services.llm import Gemini


class ImagePromptEnhancer:
    @staticmethod
    async def enhance(prompt: str) -> str:
        _prompt = f"""
        enhance image generation prompt {prompt}
        return only prompt without any explanations
        return without enters in plain text
        make minimum 10 points
        points must be separate with , without numbers or dots
        make prompt in english
        """
        return await Gemini.generate(_prompt)
