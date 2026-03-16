# Copyright 2026 Junjie Ye
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from openai import OpenAI


BASE_URL = "https://example.com"
KIMI_BASE_URL = "https://example.com"


class GPT:
    def __init__(self, user, api_key, base_url=None, model=None, thinking=True, timeout=3600):
        assert model in ["api_azure_openai_gpt-5.2", "api_azure_openai_gpt-5.1"], f"model {model} is not supported"
        self.client = OpenAI(
            api_key=f'{user}:{api_key}',
            base_url=base_url if base_url else BASE_URL,
        )
        self.model = model
        self.thinking = thinking
        self.timeout = timeout
    
    def chat(self, messages, tools=None, **kwargs):
        if self.thinking:
            reasoning_effort = "high"
        else:
            reasoning_effort = "none"
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            reasoning_effort=reasoning_effort,
            timeout=self.timeout,
            **kwargs
        )
        responses = responses.model_dump()
        return responses
    

class Openai:
    def __init__(self, user, api_key, base_url=None, model=None, thinking=True, timeout=3600):
        assert model in ["api_azure_openai_o3"], f"model {model} is not supported"
        self.client = OpenAI(
            api_key=f'{user}:{api_key}',
            base_url=base_url if base_url else BASE_URL,
        )
        self.model = model
        self.thinking = thinking
        self.timeout = timeout
    
    def chat(self, messages, tools=None, **kwargs):
        if self.thinking:
            reasoning_effort = "high"
        else:
            reasoning_effort = "low"
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            reasoning_effort=reasoning_effort,
            timeout=self.timeout,
            **kwargs
        )
        responses = responses.model_dump()
        return responses
    

class Doubao:
    def __init__(self, user, api_key, base_url=None, model=None, thinking=True, timeout=3600):
        assert model in ["api_doubao_doubao-seed-1-8-251228", "api_doubao_doubao-seed-2-0-pro-260215"], f"model {model} is not supported"
        self.client = OpenAI(
            api_key=f'{user}:{api_key}',
            base_url=base_url if base_url else BASE_URL,
        )
        self.model = model
        self.thinking = thinking
        self.timeout = timeout
    
    def chat(self, messages, tools=None, **kwargs):
        if self.thinking:
            thinking = {"type": "enabled"}
        else:
            thinking = {"type": "disabled"}
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            extra_body={"thinking": thinking},
            timeout=self.timeout,
            **kwargs
        )
        responses = responses.model_dump()
        return responses
    

class Qwen:
    def __init__(self, user, api_key, base_url=None, model=None, thinking=True, timeout=3600):
        assert model in ["api_ali_qwen3-max", "api_ali_qwen3.5-plus"], f"model {model} is not supported"
        self.client = OpenAI(
            api_key=f'{user}:{api_key}',
            base_url=base_url if base_url else BASE_URL,
        )
        self.model = model
        self.thinking = thinking
        self.timeout = timeout
    
    def chat(self, messages, tools=None, **kwargs):
        if self.thinking:
            enable_thinking = True
        else:
            enable_thinking = False
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            extra_body={"enable_thinking": enable_thinking},
            timeout=self.timeout,
            **kwargs
        )
        responses = responses.model_dump()
        return responses
    

class Deepseek:
    def __init__(self, user, api_key, base_url=None, model=None, thinking=True, timeout=3600):
        assert model in ["api_ali_deepseek-v3.2"], f"model {model} is not supported"
        self.client = OpenAI(
            api_key=f'{user}:{api_key}',
            base_url=base_url if base_url else BASE_URL,
        )
        self.model = model
        self.thinking = thinking
        self.timeout = timeout
    
    def chat(self, messages, tools=None, **kwargs):
        if self.thinking:
            enable_thinking = True
        else:
            enable_thinking = False
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            extra_body={"enable_thinking": enable_thinking},
            timeout=self.timeout,
            **kwargs
        )
        responses = responses.model_dump()
        return responses
    

class Claude:
    def __init__(self, user, api_key, base_url=None, model=None, thinking=True, timeout=3600):
        assert model in ["api_aws_third_anthropic.claude-opus-4-6-v1", "api_aws_third_anthropic.claude-opus-4-5-20251101-v1:0"], f"model {model} is not supported"
        self.client = OpenAI(
            api_key=f'{user}:{api_key}',
            base_url=base_url if base_url else BASE_URL,
        )
        self.model = model
        self.thinking = thinking
        self.timeout = timeout
    
    def chat(self, messages, tools=None, **kwargs):
        if self.thinking:
            thinking={"type": "enabled", "budget_tokens": 8191}
        else:
            thinking={"type": "disabled"}
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            extra_body={"thinking": thinking},
            timeout=self.timeout,
            **kwargs
        )
        responses = responses.model_dump()
        return responses
    

class Gemini:
    def __init__(self, user, api_key, base_url=None, model=None, thinking=True, timeout=3600):
        assert model in ["api_google_gemini-3-pro-preview"], f"model {model} is not supported"
        self.client = OpenAI(
            api_key=f'{user}:{api_key}',
            base_url=base_url if base_url else BASE_URL,
        )
        self.model = model
        self.thinking = thinking
        self.timeout = timeout
    
    def chat(self, messages, tools=None, **kwargs):
        if self.thinking:
            thinkingConfig = {"thinkingLevel": "high"}
        else:
            thinkingConfig = {"thinkingLevel": "low"}
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            extra_body={"thinkingConfig": thinkingConfig},
            timeout=self.timeout,
            **kwargs
        )
        responses = responses.model_dump()
        return responses
    

class Kimi:
    def __init__(self, user, api_key, base_url=None, model=None, thinking=True, timeout=3600):
        assert model in ["kimi-k2.5"], f"model {model} is not supported"
        self.client = OpenAI(
            api_key=f'{user}:{api_key}?provider=moonshot&timeout={timeout}&model={model}',
            base_url=base_url if base_url else KIMI_BASE_URL,
        )
        self.model = model
        self.thinking = thinking

    def chat(self, messages, tools=None, **kwargs):
        if self.thinking:
            thinking={"type": "enabled"}
        else:
            thinking={"type": "disabled"}
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            extra_body={"thinking": thinking},
            **kwargs
        )
        responses = responses.model_dump()
        return responses


def client(model, user, api_key, base_url=None, thinking=True):
    match model:
        case 'GPT-5.2':
            return GPT(user=user, api_key=api_key, base_url=base_url, model=f'api_azure_openai_gpt-5.2', thinking=thinking)
        case 'GPT-5.1':
            return GPT(user=user, api_key=api_key, base_url=base_url, model=f'api_azure_openai_gpt-5.1', thinking=thinking)
        case 'OpenAI o3':
            return Openai(user=user, api_key=api_key, base_url=base_url, model=f'api_azure_openai_o3', thinking=thinking)
        case 'Seed-2.0-Pro':
            return Doubao(user=user, api_key=api_key, base_url=base_url, model=f'api_doubao_doubao-seed-2-0-pro-260215', thinking=thinking)
        case 'Qwen3.5-Plus':
            return Qwen(user=user, api_key=api_key, base_url=base_url, model=f'api_ali_qwen3.5-plus', thinking=thinking)
        case 'DeepSeek-V3.2':
            return Deepseek(user=user, api_key=api_key, base_url=base_url, model=f'api_ali_deepseek-v3.2', thinking=thinking)
        case 'Claude Opus 4.6':
            return Claude(user=user, api_key=api_key, base_url=base_url, model=f'api_aws_third_anthropic.claude-opus-4-6-v1', thinking=thinking)
        case 'Gemini 3 Pro':
            return Gemini(user=user, api_key=api_key, base_url=base_url, model=f'api_google_gemini-3-pro-preview', thinking=thinking)
        case 'Kimi K2.5':
            return Kimi(user=user, api_key=api_key, base_url=base_url, model=f'kimi-k2.5', thinking=thinking)
        case _:
            raise ValueError(f"model {model} is not supported")
