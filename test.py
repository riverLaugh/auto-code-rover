import os
from pathlib import Path
import subprocess
from tempfile import NamedTemporaryFile
from app.search.search_utils import (
    find_python_files,
    parse_python_file,
    get_code_snippets,
    get_code_region_containing_code,
    get_class_signature,
    get_code_region_around_line,
)
from app.search.search_utils import RustParser,parse_python_file
from app.utils import run_script_in_docker
import parser


# 主函数
# def main():




# def test_run_script_in_docker():
#     """测试在Docker中运行脚本。"""
#     test_content = """
#     fn main() {
#         println!("Hello, world!");
#     }
#     """
#     with NamedTemporaryFile(
#         buffering=0, prefix="reproducer-", suffix=".rs"
#     ) as f:
#         f.write(test_content.encode())
#         docker_image_name = "sweb.eval.x86_64.ratatui__ratatui-518:latest"
#         try:
#             cp = run_script_in_docker(
#                 f.name,
#                 docker_image_name,
#                 text=True,
#                 capture_output=True,
#                 timeout=120,  # 2 min for reproducer should be enough
#             )
#             cp_stdout = cp.stdout
#             cp_stderr = cp.stderr
#             cp_returncode = cp.returncode
#         except subprocess.TimeoutExpired:
#             cp_stdout = ""
#             cp_stderr = "Test execution timeout."
#             cp_returncode = -1
#         print(cp_stdout)
#         print(cp_stderr)
#         print(cp_returncode)

# import app.search.search_backend as search_backend

# def test_search():
#     with open("/home/riv3r/auto-code-rover/setup/ratatui__ratatui-518/src/widgets/barchart.rs", "r") as f:
#         content = f.read()
#         structs, impls, functions, struct_relation_map, traits = parse_python_file(content)
#         print(structs, impls, functions, struct_relation_map, traits)
#     search_backend = search_backend.SearchBackend("/home/riv3r/auto-code-rover/setup/ratatui__ratatui-518/src/widgets/barchart.rs")

#     # res = search_backend.search("fn main")
    # print(res)

# import json
# from typing import Dict, List, Optional, Any
# def parse_file(file_path: str) -> Any:
#     if file_path.endswith(".rs"):
#         with open(file_path) as fp:
#             # 解析Rust文件并存储
#             return json.loads(parser.parse_rust_code(fp.read()))
#     else:
#         # 处理非Rust文件（此处只记录文件名）
#         return None


from app.post_process import convert_response_to_diff,extract_diff_one_instance
from app.utils import find_file
if __name__ == "__main__":
    status, data = extract_diff_one_instance("/home/riv3r/auto-code-rover/output/ratatui__ratatui-518_2025-03-18_16-30-29/output_0/patch_raw_0.md", "test.rs")
    # str = find_file("/home/riv3r/auto-code-rover/SWE-bench/testbed/ratatui__ratatui/setup_ratatui__ratatui__0.23", "src/widgets/barchart.rs")
    # print(str)