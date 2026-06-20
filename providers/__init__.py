"""GeoPilot Provider Registry - All LLM API Providers"""

from .base import BaseProvider, get_provider, list_providers, register_provider

# === Register OpenAI-Compatible Providers ===
from .openai_compat import OpenAICompatibleProvider
register_provider('openai', OpenAICompatibleProvider,
    display_name='OpenAI',
    models=['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o1-mini', 'o1-preview', 'gpt-4'])
register_provider('deepseek', OpenAICompatibleProvider,
    display_name='DeepSeek',
    models=['deepseek-chat', 'deepseek-reasoner', 'deepseek-v3', 'deepseek-r1'],
    env_key='DEEPSEEK_API_KEY', default_url='https://api.deepseek.com/v1')
register_provider('moonshot', OpenAICompatibleProvider,
    display_name='Moonshot / Kimi',
    models=['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
    env_key='MOONSHOT_API_KEY', default_url='https://api.moonshot.cn/v1')
register_provider('qwen', OpenAICompatibleProvider,
    display_name='Alibaba Qwen / Tongyi',
    models=['qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen-long', 'qwen2.5-72b-instruct'],
    env_key='QWEN_API_KEY', default_url='https://dashscope.aliyuncs.com/compatible-mode/v1')
register_provider('zhipu', OpenAICompatibleProvider,
    display_name='Zhipu AI / GLM',
    models=['glm-4-plus', 'glm-4', 'glm-4-flash', 'glm-4-air', 'glm-4-airx'],
    env_key='ZHIPU_API_KEY', default_url='https://open.bigmodel.cn/api/paas/v4')
register_provider('yi', OpenAICompatibleProvider,
    display_name='01.AI Yi',
    models=['yi-lightning', 'yi-medium', 'yi-large', 'yi-vision', 'yi-medium-200k'],
    env_key='YI_API_KEY', default_url='https://api.01.ai/v1')
register_provider('mistral', OpenAICompatibleProvider,
    display_name='Mistral AI',
    models=['mistral-large-latest', 'mistral-small-latest', 'mistral-medium-latest', 'open-mistral-nemo'],
    env_key='MISTRAL_API_KEY', default_url='https://api.mistral.ai/v1')
register_provider('cohere', OpenAICompatibleProvider,
    display_name='Cohere',
    models=['command-r-plus', 'command-r', 'command-nightly'],
    env_key='COHERE_API_KEY', default_url='https://api.cohere.ai/v1')
register_provider('perplexity', OpenAICompatibleProvider,
    display_name='Perplexity',
    models=['sonar-pro', 'sonar', 'sonar-reasoning'],
    env_key='PERPLEXITY_API_KEY', default_url='https://api.perplexity.ai')
register_provider('xai', OpenAICompatibleProvider,
    display_name='xAI Grok',
    models=['grok-beta', 'grok-2', 'grok-2-vision'],
    env_key='XAI_API_KEY', default_url='https://api.x.ai/v1')
register_provider('together', OpenAICompatibleProvider,
    display_name='Together AI',
    models=['meta-llama-3.1-405b', 'meta-llama-3.1-70b', 'mistralai/mixtral-8x22b'],
    env_key='TOGETHER_API_KEY', default_url='https://api.together.xyz/v1')
register_provider('fireworks', OpenAICompatibleProvider,
    display_name='Fireworks AI',
    models=['accounts/fireworks/models/llama-v3p1-405b', 'accounts/fireworks/models/qwen2p5-72b'],
    env_key='FIREWORKS_API_KEY', default_url='https://api.fireworks.ai/inference/v1')
register_provider('groq', OpenAICompatibleProvider,
    display_name='Groq',
    models=['llama3-70b-8192', 'llama3-8b-8192', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
    env_key='GROQ_API_KEY', default_url='https://api.groq.com/openai/v1')

# === Register Native API Providers ===
from .anthropic_provider import AnthropicProvider
register_provider('anthropic', AnthropicProvider,
    display_name='Anthropic Claude',
    models=['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229'])
from .google_provider import GoogleProvider
register_provider('google', GoogleProvider,
    display_name='Google Gemini',
    models=['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.0-flash-exp'])
from .ollama_provider import OllamaProvider
register_provider('ollama', OllamaProvider,
    display_name='Ollama (Local)',
    models=['llama3.1', 'llama3', 'mistral', 'qwen2.5', 'deepseek-r1', 'codellama', 'gemma2', 'mixtral'])
from .baidu_provider import BaiduProvider
register_provider('baidu', BaiduProvider,
    display_name='Baidu ERNIE / Wenxin',
    models=['ernie-4.0-8k', 'ernie-3.5-8k', 'ernie-speed', 'ernie-lite', 'ernie-tiny'])
from .spark_provider import SparkProvider
register_provider('spark', SparkProvider,
    display_name='iFlytek Spark / Xunfei',
    models=['4.0Ultra', '3.5', '3.0'])

# Export all
__all__ = ['BaseProvider', 'get_provider', 'list_providers', 'register_provider', 'PROVIDER_REGISTRY']
