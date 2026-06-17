# 配置指南

## API Key 获取

### 阿里云百炼平台

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 登录（如无账号需注册）
3. 在左侧菜单找到 **API-KEY 管理**
4. 点击 **创建API-KEY**
5. 复制生成的 Key

### 环境变量配置

**Hermes 用户**（推荐）：

```bash
echo 'QWEN_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.hermes/.env
```

或复用已有的 DASHSCOPE_API_KEY（脚本自动读取）：

```bash
echo 'DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.hermes/.env
```

**非 Hermes 用户**：

```bash
export QWEN_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

建议写入 `~/.bashrc` 或 `~/.zshrc` 以持久化。

## API 基础地址

默认值：`https://dashscope.aliyuncs.com/compatible-mode/v1`

可通过环境变量 `QWEN_API_BASE` 自定义（如使用代理或私有部署）。

## 可用模型

| 模型ID | 说明 | 适用场景 |
|--------|------|---------|
| `qwen-vl-plus` | 性价比首选 | 一般文档、清晰图片 |
| `qwen-vl-max` | 更强能力 | 复杂排版、低质量图片、小字体 |

更多模型请查阅 [阿里云百炼文档](https://help.aliyun.com/zh/model-studio/)

## 费用

- **qwen-vl-plus**: 约 0.003元/次
- **qwen-vl-max**: 约 0.008元/次

具体以阿里云百炼官网最新定价为准。
