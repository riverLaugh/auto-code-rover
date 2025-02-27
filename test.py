import os
from pathlib import Path
from app.search.search_utils import (
    find_python_files,
    parse_python_file,
    get_code_snippets,
    get_code_region_containing_code,
    get_struct_signature,
    get_code_region_around_line,
)

# 测试目录路径
TEST_DIR = "test_rust_project"

# 创建一个简单的 Rust 项目用于测试
def create_test_project():
    os.makedirs(TEST_DIR, exist_ok=True)
    with open(os.path.join(TEST_DIR, "main.rs"), "w") as f:
        f.write(
            """
struct Point {
    x: i32,
    y: i32,
}

impl Point {
    fn new(x: i32, y: i32) -> Self {
        Point { x, y }
    }

    fn distance(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        ((dx * dx + dy * dy) as f64).sqrt()
    }
}

fn main() {
    let p1 = Point::new(0, 0);
    let p2 = Point::new(3, 4);
    println!("Distance: {}", p1.distance(&p2));
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
        structs, impls, functions, struct_relation_map = parse_python_file(rs_files[0])

        # 验证结构体
        assert len(structs) == 1, f"Expected 1 struct, got {len(structs)}"
        assert structs[0][0] == "Point", f"Expected struct 'Point', got {structs[0][0]}"

        # 验证实现
        assert "Point" in impls, f"Expected impl for 'Point'"
        assert len(impls["Point"]) == 2, f"Expected 2 functions in impl, got {len(impls['Point'])}"
        assert impls["Point"][0][0] == "new", f"Expected function 'new', got {impls['Point'][0][0]}"
        assert impls["Point"][1][0] == "distance", f"Expected function 'distance', got {impls['Point'][1][0]}"

        # 验证顶层函数
        assert len(functions) == 1, f"Expected 1 top-level function, got {len(functions)}"
        assert functions[0][0] == "main", f"Expected function 'main', got {functions[0][0]}"

        print("✅ parse_python_file passed!")
    except AssertionError as e:
        print(f"❌ parse_python_file failed: {e}")

# 测试 get_code_snippets 函数
def test_get_code_snippets():
    print("Testing get_code_snippets...")
    try:
        rs_files = find_python_files(TEST_DIR)
        snippet = get_code_snippets(rs_files[0], 2, 5)
        expected_snippet = """2 struct Point {
3     x: i32,
4     y: i32,
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
        signature = get_struct_signature(rs_files[0], "Point")
        expected_signature = """2 struct Point {
3     x: i32,
4     y: i32,
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
        test_find_python_files()
        test_parse_python_file()
        test_get_code_snippets()
        test_get_code_region_containing_code()
        test_get_struct_signature()
        test_get_code_region_around_line()
    finally:
        cleanup_test_project()

if __name__ == "__main__":
    main()