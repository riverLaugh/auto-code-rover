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

# 测试目录路径
TEST_DIR = "test_rust_project"

# 创建一个简单的 Rust 项目用于测试
def create_test_project():
    os.makedirs(TEST_DIR, exist_ok=True)
    with open(os.path.join(TEST_DIR, "main.rs"), "w") as f:
        f.write(
            """
pub struct BarChart<'a> {
    /// Block to wrap the widget in
    block: Option<Block<'a>>,
    /// The width of each bar
    bar_width: u16,
    /// The gap between each bar
    bar_gap: u16,
    /// The gap between each group
    group_gap: u16,
    /// Set of symbols used to display the data
    bar_set: symbols::bar::Set,
    /// Style of the bars
    bar_style: Style,
    /// Style of the values printed at the bottom of each bar
    value_style: Style,
    /// Style of the labels printed under each bar
    label_style: Style,
    /// Style for the widget
    style: Style,
    /// vector of groups containing bars
    data: Vec<BarGroup<'a>>,
    /// Value necessary for a bar to reach the maximum height (if no value is specified,
    /// the maximum value in the data is taken as reference)
    max: Option<u64>,
    /// direction of the bars
    direction: Direction,
}

"""
        )

# 清理测试目录
def cleanup_test_project():
    if os.path.exists(TEST_DIR):
        for root, dirs, files in os.walk(TEST_DIR, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(TEST_DIR)

# 测试 find_python_files 函数
def test_find_python_files():
    print("Testing find_python_files...")
    try:
        rs_files = find_python_files(TEST_DIR)
        assert len(rs_files) == 1, f"Expected 1 .rs file, got {len(rs_files)}"
        assert rs_files[0].endswith("main.rs"), f"Expected main.rs, got {rs_files[0]}"
        print("✅ find_python_files passed!")
    except AssertionError as e:
        print(f"❌ find_python_files failed: {e}")

# 测试 parse_python_file 函数
def test_parse_python_file():
    print("Testing parse_python_file...")
    try:
        rs_files = find_python_files(TEST_DIR)
        structs, impls, functions, struct_relation_map, traits = parse_python_file(rs_files[0])
        print(structs, impls, functions, struct_relation_map, traits)
        # 验证结构体
        # assert len(structs) == 1, f"Expected 1 struct, got {len(structs)}"
        # assert structs[0][0] == "Terminal<B>", f"Expected struct 'Terminal<B>', got {structs[0][0]}"
        
        # # 验证实现块
        # assert "Terminal<B>" in impls, f"Expected impl for 'Terminal<B>'"
        # assert len(impls["Terminal<B>"]) == 1, f"Expected 1 method in impl, got {len(impls['Terminal<B>'])}"
        # assert impls["Terminal<B>"][0][0] == "drop", f"Expected method 'drop' in impl"

        # # 验证 trait 实现关系
        # terminal_key = None
        # for key in struct_relation_map:
        #     if key[0] == "Terminal<B>":
        #         terminal_key = key
        #         break
        # assert terminal_key is not None, "Terminal<B> not found in struct_relation_map"
        # assert len(struct_relation_map[terminal_key]) == 0, f"Expected no trait implementations, got {len(struct_relation_map[terminal_key])}"

        print("✅ parse_python_file passed!")
    except AssertionError as e:
        print(f"❌ parse_python_file failed: {e}")


# 测试 get_code_snippets 函数
def test_get_code_snippets():
    print("Testing get_code_snippets...")
    try:
        rs_files = find_python_files(TEST_DIR)
        snippet = get_code_snippets(rs_files[0], 2, 5)
        expected_snippet = """2 struct Rectangle {
3     width: u32,
4     height: u32,
5 }
"""
        assert snippet == expected_snippet, f"Unexpected snippet:\n{snippet}"
        print("✅ get_code_snippets passed!")
    except AssertionError as e:
        print(f"❌ get_code_snippets failed: {e}")

# 测试 get_code_region_containing_code 函数
def test_get_code_region_containing_code():
    print("Testing get_code_region_containing_code...")
    try:
        rs_files = find_python_files(TEST_DIR)
        occurrences = get_code_region_containing_code(rs_files[0], "fn new")
        assert len(occurrences) == 1, f"Expected 1 occurrence, got {len(occurrences)}"
        assert "fn new" in occurrences[0][1], f"Expected 'fn new' in context:\n{occurrences[0][1]}"
        print("✅ get_code_region_containing_code passed!")
    except AssertionError as e:
        print(f"❌ get_code_region_containing_code failed: {e}")

# 测试 get_struct_signature 函数
def test_get_struct_signature():
    print("Testing get_struct_signature...")
    try:
        rs_files = find_python_files(TEST_DIR)
        signature = get_class_signature(rs_files[0], "Rectangle")
        expected_signature = """2 struct Rectangle {
3     width: u32,
4     height: u32,
5 }
"""
        assert signature == expected_signature, f"Unexpected signature:\n{signature}"
        print("✅ get_struct_signature passed!")
    except AssertionError as e:
        print(f"❌ get_struct_signature failed: {e}")

# 测试 get_code_region_around_line 函数
def test_get_code_region_around_line():
    print("Testing get_code_region_around_line...")
    try:
        rs_files = find_python_files(TEST_DIR)
        snippet = get_code_region_around_line(rs_files[0], 10)
        assert "fn new" in snippet, f"Expected 'fn new' in snippet:\n{snippet}"
        print("✅ get_code_region_around_line passed!")
    except AssertionError as e:
        print(f"❌ get_code_region_around_line failed: {e}")

# 主函数
def main():
    create_test_project()
    try:
        # test_find_python_files()
        test_parse_python_file()
        # test_get_code_snippets()
        # test_get_code_region_containing_code()
        # test_get_struct_signature()
        # test_get_code_region_around_line()
    finally:
        cleanup_test_project()

def print_ast_example():
    """打印AST结构示例。"""
    print("\nPrinting AST structure example...")
    create_test_project()
    try:
        rs_files = find_python_files(TEST_DIR)
        parser = RustParser()
        parser.print_ast(rs_files[0])
    finally:
        cleanup_test_project()


def test_run_script_in_docker():
    """测试在Docker中运行脚本。"""
    test_content = """
    fn main() {
        println!("Hello, world!");
    }
    """
    with NamedTemporaryFile(
        buffering=0, prefix="reproducer-", suffix=".rs"
    ) as f:
        f.write(test_content.encode())
        docker_image_name = "sweb.eval.x86_64.ratatui__ratatui-518:latest"
        try:
            cp = run_script_in_docker(
                f.name,
                docker_image_name,
                text=True,
                capture_output=True,
                timeout=120,  # 2 min for reproducer should be enough
            )
            cp_stdout = cp.stdout
            cp_stderr = cp.stderr
            cp_returncode = cp.returncode
        except subprocess.TimeoutExpired:
            cp_stdout = ""
            cp_stderr = "Test execution timeout."
            cp_returncode = -1
        print(cp_stdout)
        print(cp_stderr)
        print(cp_returncode)

import app.search.search_backend as search_backend

def test_search():
    with open("/home/riv3r/auto-code-rover/setup/ratatui__ratatui-518/src/widgets/barchart.rs", "r") as f:
        content = f.read()
        structs, impls, functions, struct_relation_map, traits = parse_python_file(content)
        print(structs, impls, functions, struct_relation_map, traits)
    search_backend = search_backend.SearchBackend("/home/riv3r/auto-code-rover/setup/ratatui__ratatui-518/src/widgets/barchart.rs")

    # res = search_backend.search("fn main")
    # print(res)

import json
from typing import Dict, List, Optional, Any
def parse_file(file_path: str) -> Any:
    if file_path.endswith(".rs"):
        with open(file_path) as fp:
            # 解析Rust文件并存储
            return json.loads(parser.parse_rust_code(fp.read()))
    else:
        # 处理非Rust文件（此处只记录文件名）
        return None




if __name__ == "__main__":
    # test_run_script_in_docker()
    # main()
    jsonsss = parse_file("/home/riv3r/auto-code-rover/setup/ratatui__ratatui-518/src/widgets/barchart.rs")

    with open("test.json", "w") as f:
        json.dump(jsonsss, f , indent=4)
    # print_ast_example()
    # test_search()