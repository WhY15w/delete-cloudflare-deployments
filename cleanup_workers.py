import os
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional, Any

# 从环境变量获取配置
API_TOKEN = os.getenv('CF_API_TOKEN')
ACCOUNT_ID = os.getenv('CF_ACCOUNT_ID')
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
KEEP_COUNT = int(os.getenv('KEEP_COUNT', '10'))

# API 配置
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 0.5  # 请求间隔，避免触发API限流
MAX_RETRIES = 3
RETRY_DELAY = 2

def check_environment() -> bool:
    """检查环境变量是否已正确设置"""
    required_vars = ['CF_API_TOKEN', 'CF_ACCOUNT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\n❌ 错误：未找到以下环境变量：")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请确保环境变量已正确设置")
        return False
    
    print("✅ 环境变量验证通过")
    if DRY_RUN:
        print("🔍 运行模式：预览模式（不会实际删除）")
    else:
        print("🗑️ 运行模式：实际删除模式")
    print(f"📊 保留最新 {KEEP_COUNT} 个部署")
    return True

def make_api_request(url: str, method: str = 'GET', **kwargs) -> Optional[Dict[str, Any]]:
    """发送API请求，包含重试和错误处理"""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(RATE_LIMIT_DELAY)  # 避免API限流
            
            response = requests.request(
                method, url, headers=headers, timeout=REQUEST_TIMEOUT, **kwargs
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                wait_time = min(RETRY_DELAY * (2 ** attempt), 30)
                print(f"⚠️ API限流，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ API请求失败 (状态码: {response.status_code}): {response.text}")
                if attempt < MAX_RETRIES - 1:
                    print(f"🔄 重试 {attempt + 1}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏱️ 请求超时，重试 {attempt + 1}/{MAX_RETRIES}...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络错误: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return None
    
    return None

def get_all_projects() -> Optional[List[Dict[str, Any]]]:
    """获取账号下所有的项目"""
    print("📋 获取项目列表...")
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/projects"
    
    response_data = make_api_request(url)
    if not response_data:
        print("❌ 获取项目列表失败")
        return None
        
    result = response_data.get('result', [])
    print(f"📊 找到 {len(result)} 个项目")
    return result

def get_deployments(project_name: str) -> Optional[List[Dict[str, Any]]]:
    """获取指定项目的所有部署记录"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/projects/{project_name}/deployments"
    
    response_data = make_api_request(url)
    if not response_data:
        print(f"❌ 获取项目 {project_name} 的部署记录失败")
        return None
        
    result = response_data.get('result', [])
    return result

def delete_deployment(project_name: str, deployment_id: str) -> bool:
    """删除指定项目的指定部署记录"""
    if DRY_RUN:
        print(f"🔍 [预览] 将删除部署 {deployment_id}")
        return True
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/projects/{project_name}/deployments/{deployment_id}"
    
    response_data = make_api_request(url, method='DELETE')
    if response_data:
        print(f"✅ 成功删除部署 {deployment_id}")
        return True
    else:
        print(f"❌ 删除部署 {deployment_id} 失败")
        return False

def main():
    """主函数"""
    print("🚀 开始清理 Cloudflare Pages 部署记录")
    print("=" * 50)
    
    if not check_environment():
        return 1

    projects = get_all_projects()
    if not projects:
        print("❌ 没有找到任何项目")
        return 1

    total_projects = len(projects)
    processed_projects = 0
    total_deleted = 0
    
    # 遍历每个项目
    for i, project in enumerate(projects, 1):
        project_name = project['name']
        print(f"\n📦 处理项目 {i}/{total_projects}: {project_name}")
        print("-" * 40)
        
        project_deleted = 0
        
        while True:
            # 获取该项目的部署记录
            deployments = get_deployments(project_name)
            if not deployments:
                print(f"⚠️ 项目 {project_name} 没有找到部署记录")
                break

            print(f"📊 当前获取到 {len(deployments)} 个部署记录")
            
            # 如果部署记录数量小于等于目标值，退出循环
            if len(deployments) <= KEEP_COUNT:
                print(f"✅ 项目 {project_name} 当前部署数量为 {len(deployments)}，不需要清理")
                break
                
            # 按创建时间排序
            try:
                sorted_deployments = sorted(
                    deployments, 
                    key=lambda x: x['created_on'], 
                    reverse=True
                )
            except KeyError as e:
                print(f"❌ 部署记录格式错误: {e}")
                break
            
            # 保留最新的指定数量部署，删除其余的
            deployments_to_delete = sorted_deployments[KEEP_COUNT:]
            
            if not deployments_to_delete:
                print(f"✅ 项目 {project_name} 已满足保留要求")
                break
                
            print(f"🗑️ 本轮需要删除 {len(deployments_to_delete)} 个旧部署")
            
            batch_deleted = 0
            for j, deployment in enumerate(deployments_to_delete, 1):
                deployment_id = deployment['id']
                try:
                    created_date = datetime.fromisoformat(
                        deployment['created_on'].replace('Z', '+00:00')
                    )
                    date_str = created_date.strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, KeyError):
                    date_str = "未知时间"
                
                print(f"   {j:2d}. 删除部署 {deployment_id} (创建于 {date_str})")
                
                if delete_deployment(project_name, deployment_id):
                    batch_deleted += 1
                    project_deleted += 1
                    total_deleted += 1
                else:
                    print(f"   ❌ 删除失败，跳过剩余部署")
                    break
                    
                # 避免过快请求
                if j % 5 == 0:  # 每删除5个休息一下
                    time.sleep(1)
            
            print(f"🎯 本轮删除了 {batch_deleted} 个部署")
            
            # 如果删除数量小于预期，可能遇到错误，退出循环
            if batch_deleted == 0:
                print("⚠️ 未能删除任何部署，停止处理此项目")
                break
        
        processed_projects += 1
        print(f"✅ 项目 {project_name} 处理完成，共删除 {project_deleted} 个部署")
    
    # 输出最终统计
    print("\n" + "=" * 50)
    print("📊 清理完成统计:")
    print(f"   - 处理项目数: {processed_projects}/{total_projects}")
    print(f"   - 总删除数量: {total_deleted} 个部署")
    if DRY_RUN:
        print("   - 模式: 🔍 预览模式（未实际删除）")
    else:
        print("   - 模式: 🗑️ 实际删除模式")
    print("🎉 清理任务完成！")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)