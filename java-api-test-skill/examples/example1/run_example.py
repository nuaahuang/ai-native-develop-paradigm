import os
import sys
import subprocess
import time
import signal
import re
from datetime import datetime

def parse_pytest_output(output):
    """解析pytest输出结果"""
    results = []
    lines = output.strip().split('\n')
    
    for line in lines:
        match = re.match(r'.*::(Test\w+)::(\w+)\s+(PASSED|FAILED|SKIPPED)\s*\[?.*', line)
        if match:
            class_name = match.group(1)
            method_name = match.group(2)
            status = match.group(3).lower()
            
            time_match = re.search(r'(\d+\.\d+)s$', line)
            duration = float(time_match.group(1)) if time_match else 0.0
            
            results.append({
                'test_name': f"{class_name}.{method_name}",
                'status': status,
                'duration': duration,
                'module': os.path.basename(line.split('/')[-1]) if '/' in line else 'unknown'
            })
    
    return results


def generate_report(results, output_dir):
    """生成测试报告"""
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    passed = sum(1 for r in results if r.get('status') == 'passed')
    failed = sum(1 for r in results if r.get('status') == 'failed')
    skipped = sum(1 for r in results if r.get('status') == 'skipped')
    
    report = {
        "timestamp": timestamp,
        "run_type": "full",
        "total_tests": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "success_rate": round(passed / len(results) * 100, 2) if results else 0,
        "results": results
    }
    
    os.makedirs(output_dir, exist_ok=True)
    
    json_path = os.path.join(output_dir, f'test_report_{timestamp_str}.json')
    html_path = os.path.join(output_dir, f'test_report_{timestamp_str}.html')
    
    import json
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    html_content = generate_html(report)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return json_path, html_path


def generate_html(report):
    """生成HTML报告"""
    status_colors = {
        'passed': '#10b981',
        'failed': '#ef4444',
        'skipped': '#f59e0b'
    }
    
    status_labels = {
        'passed': '通过',
        'failed': '失败',
        'skipped': '跳过'
    }
    
    rows = []
    for result in report['results']:
        status = result.get('status', 'unknown')
        color = status_colors.get(status, '#6b7280')
        label = status_labels.get(status, status)
        
        row = f"""
        <tr>
            <td>{result.get('test_name', '')}</td>
            <td>{result.get('module', '')}</td>
            <td>
                <span style="display: inline-block; padding: 4px 12px; border-radius: 20px; background-color: {color}20; color: {color}; font-weight: 500;">
                    {label}
                </span>
            </td>
            <td>{result.get('duration', '0')}s</td>
        </tr>
        """
        rows.append(row)
    
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 24px; border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header p {{ opacity: 0.9; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .stat-card .number {{ font-size: 32px; font-weight: 700; }}
        .stat-card .label {{ color: #6b7280; margin-top: 4px; }}
        .stat-card.passed .number {{ color: #10b981; }}
        .stat-card.failed .number {{ color: #ef4444; }}
        .stat-card.skipped .number {{ color: #f59e0b; }}
        .stat-card.rate .number {{ color: #667eea; }}
        .table-container {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; color: #374151; }}
        tr:hover {{ background: #f9fafb; }}
        .footer {{ text-align: center; color: #9ca3af; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>API自动化测试报告</h1>
            <p>运行时间: {report['timestamp']} | 运行类型: {'全量测试' if report['run_type'] == 'full' else '增量测试' if report['run_type'] == 'incremental' else '指定测试'}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card passed">
                <div class="number">{report['passed']}</div>
                <div class="label">通过</div>
            </div>
            <div class="stat-card failed">
                <div class="number">{report['failed']}</div>
                <div class="label">失败</div>
            </div>
            <div class="stat-card skipped">
                <div class="number">{report['skipped']}</div>
                <div class="label">跳过</div>
            </div>
            <div class="stat-card rate">
                <div class="number">{report['success_rate']}%</div>
                <div class="label">成功率</div>
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>测试用例</th>
                        <th>模块</th>
                        <th>状态</th>
                        <th>耗时</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>共 {report['total_tests']} 个测试用例 | Java API测试自动化工具</p>
        </div>
    </div>
</body>
</html>
        """


def main():
    script_dir = os.path.dirname(__file__)
    output_dir = os.path.join(script_dir, 'output')
    reports_dir = os.path.join(output_dir, 'reports')
    
    print("🚀 启动Mock服务器...")
    
    # 启动Mock服务器
    mock_process = subprocess.Popen(
        [sys.executable, 'mock_server.py'],
        cwd=script_dir
    )
    
    # 等待服务器启动
    time.sleep(2)
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['API_BASE_URL'] = 'http://localhost:8888'
        env['PYTHONPATH'] = f"{script_dir}/../../references:{output_dir}"
        
        # 运行测试
        print("\n🔍 运行测试...")
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'output/tests/', '-v', '--tb=short'],
            env=env,
            cwd=script_dir,
            capture_output=True,
            text=True
        )
        
        print("\n📊 测试结果：")
        print(result.stdout)
        
        if result.stderr:
            print("\n❌ 错误信息：")
            print(result.stderr)
        
        # 解析测试结果并生成报告
        test_results = parse_pytest_output(result.stdout)
        
        if test_results:
            print("\n📝 生成测试报告...")
            json_path, html_path = generate_report(test_results, reports_dir)
            print(f"   JSON报告: {json_path}")
            print(f"   HTML报告: {html_path}")
            
    finally:
        # 停止Mock服务器
        print("\n🛑 停止Mock服务器...")
        mock_process.send_signal(signal.SIGINT)
        mock_process.wait()


if __name__ == '__main__':
    main()