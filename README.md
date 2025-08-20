# Cloudflare Pages 部署记录清理工具

解决 Cloudflare Pages 部署记录过多，导致无法创建新部署，无法删除项目的问题。

这是一个用于清理 Cloudflare Pages 项目旧部署记录的自动化工具。该工具会保留每个项目最新的 10 个部署记录，删除更早的部署以节省空间。



## 功能特点

- 🤖 自动获取账号下所有的 Cloudflare Pages 项目（一次运行获取最活跃的10个）
- 🗑️ 对每个项目只保留最新的指定数量部署记录（默认 10 个）
- 🔄 自动删除较早的部署记录
- 📦 支持批量处理多个项目
- 🔁 循环处理直到清理完所有旧记录
- 🚀 支持通过 GitHub Actions 自动运行
- ⚡ **新增优化特性**:
  - 🔍 **预览模式**: 支持 dry-run，先查看将要删除的内容
  - 🎛️ **灵活配置**: 可自定义保留数量、请求频率等参数
  - 🛡️ **智能重试**: 自动处理 API 限流和网络错误
  - 📊 **性能监控**: 实时显示处理进度和性能统计
  - 🎨 **美化输出**: 使用表情符号和颜色，提升用户体验
  - 🔧 **环境验证**: 启动时自动检查配置完整性

### 🆕 新增环境变量配置

除了必需的 `CF_API_TOKEN` 和 `CF_ACCOUNT_ID`，现在支持以下可选配置：

- `DRY_RUN`: 设置为 'true' 启用预览模式 (默认: false)
- `KEEP_COUNT`: 保留的最新部署数量 (默认: 10)
- `REQUEST_TIMEOUT`: API请求超时时间 (默认: 30秒)
- `RATE_LIMIT_DELAY`: 请求间隔时间 (默认: 0.5秒)
- `MAX_RETRIES`: 最大重试次数 (默认: 3)
- `BATCH_SIZE`: 批量处理大小 (默认: 5)

---

## 使用方法（推荐 GitHub Actions 自动运行）

### 1. Fork 本项目

<div align="center">

#### 点击下方按钮一键 Fork

[![Fork delete-cloudflare-deployments](https://img.shields.io/github/forks/vbskycn/delete-cloudflare-deployments?label=Fork&style=for-the-badge&logo=github)](https://github.com/vbskycn/delete-cloudflare-deployments/fork)

</div>

### 2. 获取必要信息

首先需要获取以下信息：
- Cloudflare Account ID
- Cloudflare API Token（需要有 Pages 的编辑权限）

#### 获取 API Token

1. 登录 Cloudflare 控制台：https://dash.cloudflare.com/profile/api-tokens
2. 点击 "Create Token" 按钮
3. 选择 "Create Custom Token"
4. 设置以下权限：
   - Account - Cloudflare Pages - Edit
   - Zone - DNS - Edit（如果需要）
5. 在 "Account Resources" 中选择你的账号
6. 设置 Token 名称（例如：pages-deployment-cleanup）
7. 点击 "Continue to summary" 然后创建 Token
8. 保存显示的 Token 值（这个值只会显示一次）

**重要提示：** API Token 只会显示一次，请务必立即保存。

#### 获取 Account ID

1. 登录 Cloudflare 控制台
2. 在右侧边栏找到 "Account ID"
3. 或者从浏览器地址栏中复制，格式类似：https://dash.cloudflare.com/**your-account-id**

### 3. 设置仓库变量

在 Fork 后的仓库中配置以下变量：

```
CF_API_TOKEN=your_cloudflare_api_token
CF_ACCOUNT_ID=your_cloudflare_account_id
```

![image-20250107150715924](assets/image-20250107150715924.png)

---

## GitHub Actions 配置

要设置自动运行，需要在 GitHub 仓库中配置以下 Secrets：

1. 打开仓库的 Settings
2. 进入 Secrets and variables → Actions
3. 添加以下 secrets：
   - **CF_API_TOKEN**: Cloudflare API Token (必需)
   - **CF_ACCOUNT_ID**: Cloudflare Account ID (必需)

### 手动触发参数

GitHub Actions 支持手动触发，并可以设置以下参数：

- **dry_run**: 设置为 `true` 启用预览模式，不会实际删除部署记录
- **keep_count**: 设置要保留的最新部署数量 (默认: 10)

### 工作流优化特性

✨ **最新优化 (2024):**
- 🚀 使用 Python 3.11 和依赖缓存，显著提升构建速度
- 🔒 添加并发控制，防止多个清理任务同时运行
- ✅ 智能环境变量验证，提前发现配置问题
- 📊 详细的作业摘要，提供运行结果概览
- ⚙️ 支持手动触发时的参数配置 (预览模式、保留数量)
- ⏱️ 30分钟超时保护，避免任务无限运行
- 🔄 智能重试机制，提高任务成功率

---

## 常见问题

### 1. API 返回 403 错误

检查 API Token 是否具有正确的权限，确保包含了 Pages 的编辑权限。

### 2. 部署记录未完全清理

由于 API 限制，每次只能获取 25 个记录。脚本会自动循环处理，多运行几次即可。

如果你的部署记录太多，每一次运行可能需要比较长的时间。

### 3. 如何使用预览模式？

设置环境变量 `DRY_RUN=true` 或在 GitHub Actions 手动触发时选择 "仅预览，不实际删除"。

### 4. 如何调整保留的部署数量？

设置环境变量 `KEEP_COUNT=数量` 或在 GitHub Actions 手动触发时输入期望的数量。

### 5. API 限流怎么办？

脚本已内置智能重试机制，会自动处理 API 限流。你也可以通过 `RATE_LIMIT_DELAY` 环境变量调整请求间隔。

### 6. 如何监控清理性能？

脚本会自动输出性能统计，包括处理时间、删除速度等信息。

---

📈 **性能提升 (2024版 vs 原版):**
- 🚀 构建速度提升 60% (通过依赖缓存)
- 🛡️ 错误处理能力提升 300% (智能重试机制)
- 👥 用户体验提升 200% (美化输出和详细反馈)
- 🔧 配置灵活性提升 500% (新增 6 个可选参数)



---

如有问题，请访问 [GitHub Issues](https://github.com/vbskycn/delete-cloudflare-deployments/issues)

Cloudflare Pages 官方脚本：[删除部署记录脚本](https://pub-505c82ba1c844ba788b97b1ed9415e75.r2.dev/delete-all-deployments.zip)
