# Dify平台API接口文档

## 概述

本文档描述了网址监控系统为Dify平台提供的实时网址检测API接口。这些接口允许Dify平台实时检测网址的可访问性状态。

## 基础信息

- **基础URL**: `http://your-domain:5002/api/dify`
- **认证方式**: API密钥认证
- **请求格式**: JSON
- **响应格式**: JSON

## 认证

所有API请求都需要在请求头中包含有效的API密钥：

```
Authorization: Bearer your_api_key
```

或者在查询参数中提供：

```
?api_key=your_api_key
```

## API接口

### 1. 单个网址检测

检测单个网址的可访问性状态。

**请求**
```
POST /api/dify/check-website
Content-Type: application/json
Authorization: Bearer your_api_key

{
    "url": "https://www.example.com",
    "timeout": 10,
    "retry_times": 1
}
```

**参数说明**
- `url` (必需): 要检测的网址
- `timeout` (可选): 超时时间，默认10秒，最大60秒
- `retry_times` (可选): 重试次数，默认1次，最大5次

**响应**
```json
{
    "success": true,
    "data": {
        "url": "https://www.example.com",
        "status": "standard",
        "status_code": 200,
        "response_time": 1.234,
        "error_message": "",
        "checked_at": "2025-06-25T14:13:20.744693",
        "details": {
            "final_url": "https://www.example.com/",
            "redirect_count": 1,
            "ssl_valid": true,
            "total_time": 1.456
        }
    }
}
```

### 2. 批量网址检测

同时检测多个网址的可访问性状态。

**请求**
```
POST /api/dify/batch-check
Content-Type: application/json
Authorization: Bearer your_api_key

{
    "urls": [
        "https://www.example1.com",
        "https://www.example2.com"
    ],
    "timeout": 10,
    "retry_times": 1,
    "max_concurrent": 5
}
```

**参数说明**
- `urls` (必需): 要检测的网址列表，最大50个
- `timeout` (可选): 超时时间，默认10秒，最大60秒
- `retry_times` (可选): 重试次数，默认1次，最大5次
- `max_concurrent` (可选): 最大并发数，默认5，最大10

**响应**
```json
{
    "success": true,
    "data": {
        "results": [
            {
                "url": "https://www.example1.com",
                "status": "standard",
                "status_code": 200,
                "response_time": 1.234,
                "error_message": "",
                "details": {
                    "final_url": "https://www.example1.com/",
                    "redirect_count": 1,
                    "ssl_valid": true
                }
            }
        ],
        "summary": {
            "total_count": 2,
            "success_count": 1,
            "failed_count": 1,
            "total_time": 3.456
        }
    }
}
```

### 3. API信息查询

获取API信息和密钥使用统计。

**请求**
```
GET /api/dify/api-info
Authorization: Bearer your_api_key
```

**响应**
```json
{
    "success": true,
    "data": {
        "api_name": "Website Monitor Dify API",
        "version": "1.0.0",
        "endpoints": {
            "check_website": "/api/dify/check-website",
            "batch_check": "/api/dify/batch-check",
            "api_info": "/api/dify/api-info"
        },
        "limits": {
            "max_timeout": 60,
            "max_retry_times": 5,
            "max_batch_size": 50,
            "max_concurrent": 10
        },
        "key_info": {
            "name": "API密钥名称",
            "created_at": "2025-06-25T13:57:11.929919",
            "last_used_at": "2025-06-25T14:14:13.044666",
            "usage_count": 5
        }
    }
}
```

## 状态码说明

### 检测状态 (status)
- `standard`: 标准访问成功
- `slow`: 访问成功但响应较慢
- `redirect`: 发生重定向但最终成功
- `ssl_error`: SSL证书错误
- `timeout`: 访问超时
- `connection_error`: 连接错误
- `http_error`: HTTP错误
- `unknown_error`: 未知错误

### HTTP状态码 (status_code)
- `200`: 成功
- `3xx`: 重定向
- `4xx`: 客户端错误
- `5xx`: 服务器错误
- `0`: 连接失败

## 错误处理

### 认证错误
```json
{
    "success": false,
    "error": "API密钥无效",
    "message": "提供的API密钥无效或已过期"
}
```

### 参数错误
```json
{
    "success": false,
    "error": "参数错误",
    "message": "URL参数缺失或格式不正确"
}
```

### 服务器错误
```json
{
    "success": false,
    "error": "检测失败",
    "message": "服务器内部错误: 详细错误信息"
}
```

## 使用限制

- 单次批量检测最多50个网址
- 最大并发数为10
- 超时时间最大60秒
- 重试次数最大5次
- API密钥有使用频率限制

## 示例代码

### Python示例
```python
import requests

api_key = "your_api_key"
base_url = "http://your-domain:5002/api/dify"

# 单个网址检测
response = requests.post(
    f"{base_url}/check-website",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"url": "https://www.example.com"}
)
result = response.json()
print(result)

# 批量检测
response = requests.post(
    f"{base_url}/batch-check",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "urls": ["https://www.example1.com", "https://www.example2.com"],
        "max_concurrent": 2
    }
)
result = response.json()
print(result)
```

### JavaScript示例
```javascript
const apiKey = "your_api_key";
const baseUrl = "http://your-domain:5002/api/dify";

// 单个网址检测
fetch(`${baseUrl}/check-website`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        url: 'https://www.example.com'
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

## 联系支持

如有问题或需要技术支持，请联系系统管理员。
