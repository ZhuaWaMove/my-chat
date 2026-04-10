import anthropic
from typing import List, Dict, Any
from app.core.config import settings

class ClaudeService:
    # Constants
    CONTENT_BLOCK_DELTA = "content_block_delta"
    MOCK_MODEL = "mock-model"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    FIELD_ROLE = "role"
    FIELD_CONTENT = "content"

    def __init__(self):
        self.use_mock = False
        self.client = None
        self.model = "mock-model"

        try:
            # Check if API key is available
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is not set in .env file")

            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.model = settings.anthropic_model
            print(f"Anthropic client initialized with model: {self.model}")
        except Exception as e:
            print(f"Failed to initialize Anthropic client: {str(e)}. Using mock mode.")
            self.use_mock = True
            self.model = "mock-model"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send messages to Claude and get response"""
        if self.use_mock:
            # Return mock response for UI testing
            last_message = messages[-1]["content"] if messages else "Hello"
            return f"""This is a mock response since Claude API is not available.

Original user message: "{last_message}"

Here's a sample response with various formatting to test UI features:

## Code Example
```python
def hello_world():
    print("Hello from Claude Agent!")
    return "Testing code highlighting"
```

## List Example
1. First item
2. Second item
3. Third item

## Table Example
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data A   | Data B   | Data C   |
| Data X   | Data Y   | Data Z   |

This response includes:
- **Markdown formatting**
- Code blocks with syntax highlighting
- Lists and tables
- Bold and italic text

You can test the Copy, Regenerate, Like, Dislike, and Share buttons below!"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            # Fallback to mock response for testing UI
            print(f"Claude API error: {str(e)}. Using mock response.")
            last_message = messages[-1]["content"] if messages else "Hello"
            return f"""Claude API Error - Using Mock Response

Original message: "{last_message}"

This is a fallback response due to API connection issues.
Please check your API key configuration in the .env file.

The UI features should still work for testing purposes."""

    def chat_stream(self, messages: List[Dict[str, str]]):
        """Send messages to Claude and get streaming response"""
        if self.use_mock:
            # Return mock streaming response for UI testing
            mock_text = """This is a mock streaming response since Claude API is not available.

Let me show you how streaming works:

1. First chunk of text...
2. Second chunk with **bold** formatting...
3. Third chunk with `inline code`...
4. Final chunk with complete message!

You can test all UI features including the 5 action buttons below."""

            # Simulate streaming by yielding chunks
            chunks = mock_text.split('...')
            for chunk in chunks:
                yield chunk + "..." if chunk != chunks[-1] else chunk
                import time
                time.sleep(0.1)
            return

        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=1024,
                messages=messages
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        yield event.delta.text
        except Exception as e:
            # Fallback to mock streaming response
            print(f"Claude API error: {str(e)}. Using mock streaming response.")
            mock_text = """Claude API Error - Using Mock Streaming Response

This is a fallback due to API connection issues.
Please check your API key configuration."""

            chunks = mock_text.split(' ')
            for chunk in chunks:
                yield chunk + " "
                import time
                time.sleep(0.05)

    def format_messages(self, messages: List[Dict]) -> List[Dict[str, str]]:
        """Format messages for Claude API"""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return formatted

# Singleton instance
claude_service = ClaudeService()
