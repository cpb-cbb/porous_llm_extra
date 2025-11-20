from servers.agents.manager import AgentFactory, AgentType

pdf_content ="这是一个测试内容，若接收到，请输出“大哥，测试成功”"

# 1. 获取实例调用
process_agent = AgentFactory.get_agent(AgentType.PROCESS)
print("初始化成功，开始运行...")
res1 = process_agent.run(text_input=pdf_content)
print("初始化成功，开始运行2...")
electro_agent = AgentFactory.get_agent(AgentType.ELECTRO_CHEM)
res2 = electro_agent.run(text_input=pdf_content)

# 2. 或者使用快捷函数 (推荐)
from servers.agents.manager import run_agent
print("初始化成功，开始运行3...")
res1 = run_agent("process", text_input=pdf_content)
# res3 = run_agent("pre_judge", text_input=pdf_content)

# # 验证 Agent 需要传两个参数，一样支持：
# res_verify = run_agent("verifier", text_input=pdf_content, answer="some_json")