import argparse
import subprocess
import os
import sys
import re
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from report_generator import ReportGenerator

MAX_WORKERS = 10  # 最大线程数


def find_test_files(include_pattern=None, exclude_pattern=None):
    test_dir = os.path.join(os.getcwd(), 'output/tests')
    test_files = []
    
    if not os.path.exists(test_dir):
        return test_files
    
    for filename in os.listdir(test_dir):
        if filename.startswith('test_') and filename.endswith('.py'):
            if exclude_pattern and re.search(exclude_pattern, filename):
                continue
            if include_pattern and not re.search(include_pattern, filename):
                continue
            test_files.append(os.path.join(test_dir, filename))
    
    return sorted(test_files)


def detect_incremental_tests(git_path='.', base_branch='main'):
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{base_branch}...HEAD'],
            cwd=git_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return []
        
        changed_files = result.stdout.strip().split('\n')
        api_files = [f for f in changed_files if f.startswith('apis/') and f.endswith('.py')]
        
        test_files = []
        for api_file in api_files:
            module_name = os.path.basename(api_file).replace('_api.py', '')
            test_file = os.path.join('tests', f'test_{module_name}.py')
            if os.path.exists(test_file):
                test_files.append(test_file)
        
        return test_files
    except Exception as e:
        print(f"Error detecting incremental tests: {e}")
        return []


def run_single_test(test_file, headers=None, base_url=None):
    """运行单个测试文件"""
    env = os.environ.copy()
    if headers:
        env['API_HEADERS'] = json.dumps(headers)
    if base_url:
        env['API_BASE_URL'] = base_url
    
    results = []
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short', '--no-header'],
            env=env,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        test_results = parse_pytest_output(result.stdout)
        for tr in test_results:
            tr['module'] = os.path.basename(test_file)
            results.append(tr)
            
    except Exception as e:
        results.append({
            'test_name': os.path.basename(test_file),
            'status': 'failed',
            'duration': 0,
            'module': os.path.basename(test_file),
            'error': str(e)
        })
    
    return results


def run_tests(test_files, headers=None, base_url=None):
    """使用多线程运行测试（线程数不超过10）"""
    results = []
    
    if not test_files:
        return results
    
    # 计算实际线程数（不超过MAX_WORKERS）
    num_workers = min(len(test_files), MAX_WORKERS)
    print(f"使用 {num_workers} 个线程并行执行测试...")
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # 提交所有测试任务
        future_to_file = {
            executor.submit(run_single_test, test_file, headers, base_url): test_file
            for test_file in test_files
        }
        
        # 收集结果
        for future in as_completed(future_to_file):
            test_file = future_to_file[future]
            try:
                test_results = future.result()
                results.extend(test_results)
            except Exception as e:
                results.append({
                    'test_name': os.path.basename(test_file),
                    'status': 'failed',
                    'duration': 0,
                    'module': os.path.basename(test_file),
                    'error': f"线程执行异常: {str(e)}"
                })
    
    return results


def prompt_for_headers():
    headers = {}
    print("\n请配置自定义HTTP Headers（按回车跳过）")
    print("示例：Authorization: Bearer xxx")
    print("输入 'done' 或直接回车结束")
    
    while True:
        line = input("Header (格式: Key: Value): ").strip()
        if not line or line.lower() == 'done':
            break
        
        parts = line.split(':', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            if key:
                headers[key] = value
                print(f"已添加: {key} = {value}")
        else:
            print("格式错误，请输入 'Key: Value' 格式")
    
    return headers


def parse_pytest_output(output):
    results = []
    lines = output.strip().split('\n')
    
    for line in lines:
        match = re.match(r'.*::(Test\w+)::(\w+)\s+(PASSED|FAILED|SKIPPED)\s*\[?.*', line)
        if match:
            class_name = match.group(1)
            method_name = match.group(2)
            status = match.group(3).lower()
            
            # 尝试提取时间
            time_match = re.search(r'(\d+\.\d+)s$', line)
            duration = float(time_match.group(1)) if time_match else 0.0
            
            results.append({
                'test_name': f"{class_name}.{method_name}",
                'status': status,
                'duration': duration
            })
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Java API测试自动化工具')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    parser.add_argument('--include', help='运行匹配正则表达式的测试（如 user|order）')
    parser.add_argument('--exclude', help='排除匹配正则表达式的测试')
    parser.add_argument('--incremental', action='store_true', help='仅运行增量测试')
    parser.add_argument('--header', action='append', nargs=2, metavar=('KEY', 'VALUE'), 
                        help='添加自定义HTTP Header（可多次使用）')
    parser.add_argument('--base-url', help='API基础URL')
    parser.add_argument('--prompt-headers', action='store_true', help='交互式输入自定义Headers')
    
    args = parser.parse_args()
    
    headers = {}
    
    if args.header:
        for key, value in args.header:
            headers[key] = value
    
    if args.prompt_headers:
        prompt_headers = prompt_for_headers()
        headers.update(prompt_headers)
    
    if args.incremental:
        test_files = detect_incremental_tests()
        run_type = "incremental"
    elif args.all:
        test_files = find_test_files()
        run_type = "full"
    elif args.include:
        test_files = find_test_files(include_pattern=args.include, exclude_pattern=args.exclude)
        run_type = "partial"
    else:
        test_files = find_test_files(exclude_pattern=args.exclude)
        run_type = "full"
    
    if not test_files:
        print("未找到测试文件")
        return
    
    print(f"找到 {len(test_files)} 个测试文件")
    for f in test_files:
        print(f"  - {os.path.basename(f)}")
    
    if headers:
        print("\n使用的Headers：")
        for key, value in headers.items():
            masked_value = value[:10] + '...' if len(value) > 15 else value
            print(f"  {key}: {masked_value}")
    
    print("\n开始执行测试...")
    results = run_tests(test_files, headers, args.base_url)
    
    print("\n测试结果汇总：")
    passed = sum(1 for r in results if r['status'] == 'passed')
    failed = sum(1 for r in results if r['status'] == 'failed')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"⏭️ 跳过: {skipped}")
    
    if results:
        report_gen = ReportGenerator()
        json_path, html_path = report_gen.generate_report(results, run_type)
        print(f"\n📊 测试报告已生成：")
        print(f"   JSON: {json_path}")
        print(f"   HTML: {html_path}")


if __name__ == '__main__':
    main()
