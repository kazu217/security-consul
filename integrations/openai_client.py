import time
import json
from openai import OpenAI, RateLimitError, APIError
from config.settings import OPENAI_API_KEY


class OpenAIClient:
    MODEL = "gpt-4o-mini"
    MAX_RETRIES = 3
    RETRY_BACKOFF = [5, 15, 45]

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def complete(self, system: str, user: str, max_tokens: int = 1024, **kwargs) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        for attempt, wait in enumerate(self.RETRY_BACKOFF):
            try:
                response = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                )
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens
                return response.choices[0].message.content
            except RateLimitError:
                if attempt < len(self.RETRY_BACKOFF) - 1:
                    time.sleep(wait)
                else:
                    raise
            except APIError:
                if attempt < len(self.RETRY_BACKOFF) - 1:
                    time.sleep(wait)
                else:
                    raise

    def complete_json(self, system: str, user: str, max_tokens: int = 1024, **kwargs) -> dict:
        messages = [
            {"role": "system", "content": system + "\nJSON形式で出力してください。"},
            {"role": "user", "content": user},
        ]
        for attempt, wait in enumerate(self.RETRY_BACKOFF):
            try:
                response = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens
                return json.loads(response.choices[0].message.content)
            except RateLimitError:
                if attempt < len(self.RETRY_BACKOFF) - 1:
                    time.sleep(wait)
                else:
                    raise
            except APIError:
                if attempt < len(self.RETRY_BACKOFF) - 1:
                    time.sleep(wait)
                else:
                    raise

    def get_cost_estimate_jpy(self) -> float:
        input_cost = (self.total_input_tokens / 1_000_000) * 0.15 * 150
        output_cost = (self.total_output_tokens / 1_000_000) * 0.60 * 150
        return round(input_cost + output_cost, 4)
