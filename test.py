from servers.work_flows.extract_por_super import run_extraction_workflow
import os

if __name__ == "__main__":
    # 示例输入文本文件路径
    input_txt_path = "/Volumes/mac_outstore/毕业/测试集文献/10.1016_j.est.2023.109094.json"
    # 输出 JSON 文件路径
    output_json_path = "/Volumes/mac_outstore/毕业/测试集文献/data/extracted_output.json"
    if not os.path.exists(os.path.dirname(output_json_path)):
        os.makedirs(os.path.dirname(output_json_path))
    # 确保输入文件存在
    if not os.path.exists(input_txt_path):
        print(f"输入文件 {input_txt_path} 不存在。请确保文件路径正确。")
    else:
        # 运行抽取工作流
        run_extraction_workflow(input_txt_path, output_json_path)
        print(f"抽取结果已保存到 {output_json_path}。")