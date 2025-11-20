from litellm import completion
import logging

# ... (保留你的日志配置代码)

class BaseLiteLLMAgent:
    def __init__(
        self, 
        system_prompt: str, 
        model: str,
        base_url: str | None = None,  # 新增参数
        api_key: str | None = None,
        **kwargs
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.base_url = base_url  # 存储 base_url
        self.api_key = api_key
        self.kwargs = kwargs # 存储 temperature, top_p 等

    def build_messages(self, **prompt_vars):
        """子类应该重写此方法来构建消息列表"""
        return [{"role": "system", "content": self.system_prompt}]
    
    def run(self, **prompt_vars):
        messages = self.build_messages(**prompt_vars)
        
        response = completion(
            model=self.model,
            messages=messages,
            api_base=self.base_url,  # 关键点：LiteLLM 使用 api_base
            api_key=self.api_key,
            **self.kwargs
        )
        return response.choices[0].message.content

# --- 使用示例 ---

# 1. 连接 DeepSeek (深度求索)
agent_deepseek = BaseLiteLLMAgent(
    system_prompt="你是一个助手",
    model="openai/deepseek-chat",  # LiteLLM 甚至支持前缀来指定不同厂商
    base_url="https://api.deepseek.com",
    api_key="sk-..."
)

# 2. 连接 Ollama (本地模型)
agent_ollama = BaseLiteLLMAgent(
    system_prompt="你是一个助手",
    model="ollama/llama3", 
    base_url="http://localhost:11434"
)