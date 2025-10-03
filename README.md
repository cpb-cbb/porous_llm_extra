经过上次失败

原因： 

数据质量还是太差，数据不够多，若剔除比电容条件相关数据则会锐减，应该约束每个样本的比电容测试条件只取最具代表性的

能量密度，功率密度文献中的数据太少，目前仅罗列出来，基本上无法提数据。

文献中描述较为清晰的是实验数据，可作为切入点试一下

对于超级电容器多孔炭，他们不会所有的文献都将孔结构参数罗列出来。，要么是在图片，要么是在补充材料。


## LLM 切换指南

项目默认使用智谱 GLM 服务，但现在也支持任意 OpenAI 接口兼容的模型（如 Gemini、DeepSeek、Moonshot 等）。通过以下环境变量即可快速切换：

```bash
# 通用配置（.env 或 shell 中设置）
LLM_PROVIDER=gemini                 # 目标服务提供方，默认值为 zhipu
LLM_API_KEY=your-gemini-api-key     # 目标服务的 API Key
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-1.5-flash-latest   # 可选，未设置时使用默认模型

# 仍支持旧版变量作为回退
ZHIPUAI_API_KEY=...                 # 当 LLM_PROVIDER=zhipu 时继续生效
ZHIPUAI_MODEL=glm-4.5
```

配置完成后，无需修改业务代码，所有继承自 `BaseZhipuAgent` 的 Agent 会自动读取配置并调用对应的 LLM 客户端。

> 兼容性提示：如果目标服务需要额外的组织 ID、Base URL 或请求头，请在 `.env` 中设置 `LLM_ORG`、`LLM_BASE_URL` 等变量。
