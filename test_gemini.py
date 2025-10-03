from openai import OpenAI

client = OpenAI(
    api_key="sk-wtsEgJffHLrbMMQLZ9AMuA3BGydYnvWph5bvVhEcYc2FbHq4",
    base_url="https://hiapi.online/v1"

)

completion = client.chat.completions.create(
    model="gemini-2.5-pro",
    messages=[
        {"role": "system", "content": "你是一个聪明且富有创造力的小说作家"},
        {"role": "user", "content": "请你作为童话故事大王，写一篇短篇童话故事"}
    ],
    top_p=0.7,
    temperature=0.9
)

print(completion.choices[0].message.content)