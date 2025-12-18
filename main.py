from servers.work_flows.extract_por_super import run_extraction_workflow
from servers.work_flows.mat_simple_1by1 import GeneralLiteratureWorkflow
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from servers.utils.TextProcess import TextProcessor
from tqdm import tqdm
workflow = GeneralLiteratureWorkflow()
txt_processor = TextProcessor()
def _process_single_file(args):
    #处理，并解析文件
    input_path, output_dir = args
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_extracted.json")
    doc = txt_processor.read_pdf(input_path)
    #定义工作流并运行
    # run_extraction_workflow(input_path, output_path)
    result = workflow.process_document(doc)
    return input_path, output_path, "completed"



def process_directory(input_dir, output_dir, max_workers=None):
    if not os.path.isdir(input_dir):
        print(f"输入目录 {input_dir} 不存在。请确保路径正确。")
        return
    os.makedirs(output_dir, exist_ok=True)
    json_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.endswith(".json") and os.path.isfile(os.path.join(input_dir, f))
    ]
    if not json_files:
        print(f"目录 {input_dir} 中未找到 JSON 文件。")
        return
    
    # 在提交任务前先过滤已存在的文件
    files_to_process = []
    skipped = 0
    for path in json_files:
        base_name = os.path.splitext(os.path.basename(path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_extracted.json")
        if os.path.exists(output_path):
            skipped += 1
            print(f"跳过: {os.path.basename(path)} (已存在)")
        else:
            files_to_process.append(path)
    
    if not files_to_process:
        print(f"所有文件都已处理完成,跳过 {skipped} 个文件。")
        return
    
    workers = max_workers or os.cpu_count() or 1
    print(f"开始处理 {len(files_to_process)} 个文件,已跳过 {skipped} 个,使用 {workers} 个并发工作进程。")
    # 输出需要处理的文件名称
    for f in files_to_process:
        print(f"待处理: {os.path.basename(f)}")
    
    completed = 0
    failed = 0
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_process_single_file, (path, output_dir)): path
            for path in files_to_process
        }
        
        with tqdm(total=len(files_to_process), desc="处理进度", unit="文件") as pbar:
            for future in as_completed(futures):
                src = futures[future]
                try:
                    _, dst, status = future.result()
                    completed += 1
                    pbar.set_postfix({"完成": completed, "失败": failed})
                    tqdm.write(f"✓ 完成: {os.path.basename(src)}")
                except Exception as exc:
                    failed += 1
                    pbar.set_postfix({"完成": completed, "失败": failed})
                    tqdm.write(f"✗ 错误: {os.path.basename(src)} - {exc}")
                finally:
                    pbar.update(1)
    
    print(f"\n处理完成!")
    print(f"总计: {len(json_files)} 个文件")
    print(f"完成: {completed} 个")
    print(f"跳过: {skipped} 个")
    print(f"失败: {failed} 个")

if __name__ == "__main__":
    # 单文件示例；如需批量处理将其设为 None
    input_txt_path ="/Volumes/mac_outstore/毕业/jsol文献/biomass_super_2000/core_json/10.1016_j.carbon.2020.07.017.json"
    output_json_path = "/Volumes/mac_outstore/毕业/测试集文献/data/extracted_output.json"

    if input_txt_path:
        if not os.path.exists(os.path.dirname(output_json_path)):
            os.makedirs(os.path.dirname(output_json_path))
        if not os.path.exists(input_txt_path):
            print(f"输入文件 {input_txt_path} 不存在。请确保文件路径正确。")
        else:
            run_extraction_workflow(input_txt_path, output_json_path)
            print(f"抽取结果已保存到 {output_json_path}。")
    else:
        input_dir = "/Volumes/mac_outstore/毕业/jsol文献/biomass_super_2000/filtered_json"
        max_workers = 10
        process_directory(input_dir, max_workers=max_workers)