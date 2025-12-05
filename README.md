# AutoWeChat - 微信自动化项目

一个基于 Python 的微信自动化工具，使用 Eagle 素材管理软件进行素材管理。

## 项目结构

```
AutoWeChat/
├── assets/          # 存放底图和字体文件
├── output/          # 存放输出结果
├── config.py        # 配置文件（API密钥等）
├── main.py          # 主程序（剪贴板模式）
├── test_eagle.py    # Eagle API 完整测试脚本
├── search_eagle.py  # Eagle 图片搜索专用脚本
├── requirements.txt # Python 依赖包列表
└── README.md        # 项目说明文档
```

## 环境要求

- Python 3.7+
- Eagle 素材管理软件（运行在本地端口 41595）
- requests 库

## 安装依赖

项目使用虚拟环境管理依赖包：

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

## 当前依赖包

- `requests==2.31.0` - HTTP 请求库，用于调用 Eagle API
- `pangu==4.0.6.1` - 中英文混排空格处理库
- `Pillow` - 图像处理库，用于生成封面图

## 配置说明

在 `config.py` 中配置你的 Eagle API 信息：

```python
# Eagle API 配置
EAGLE_API_URL = "http://localhost:41595"  # Eagle 本地服务器地址
EAGLE_TOKEN = "e2f4a7ef-3136-4b9f-9a0e-53f04024dff3"  # 你的 Eagle API Token
```

## 文章格式说明

将要发布的文章内容保存到 `content.txt` 文件中：

### 支持的格式：

1. **完整元数据格式**：
```
类型：融资
公司：腾讯
金额：10亿元
正文：
# 腾讯投资某某公司

文章内容...
```

2. **简化格式**（自动识别）：
```
作者 | 张三
编辑 | 李四

腾讯宣布投资某某公司...

文章内容...
```

程序会自动识别文章类型、公司名称和金额信息。

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 激活虚拟环境

每次使用项目时都需要先激活虚拟环境：

```bash
cd AutoWeChat
source venv/bin/activate
```

### 3. 测试连接

运行完整测试脚本来验证 Eagle API 连接：

```bash
python test_eagle.py
```

### 4. 生成微信文章（剪贴板模式）

运行主程序生成微信文章并复制到剪贴板：

```bash
python main.py
```

主程序功能：
- 📖 读取 `content.txt` 文章内容
- 🔤 使用 `pangu` 自动添加中英文混排空格
- 📝 将 Markdown 转换为带样式的 HTML
- 🌐 保存 HTML 并在浏览器中打开预览
- 🖼️ 生成封面图片并保存到 `output/cover.jpg`
- 🎯 完美适配微信公众号的格式要求

### 5. 搜索图片

使用专用搜索脚本来搜索 Eagle 库中的图片：

```bash
python search_eagle.py
```

默认搜索关键词为 "relace"，如果需要搜索其他关键词，请修改脚本中的关键词参数。

### 2. 获取 Eagle Token

1. 打开 Eagle 软件
2. 进入设置 → 扩展 → 开发者模式
3. 启用 "允许外部应用访问 API"
4. 复制生成的 Token 到 `config.py` 中

## 注意事项

- 确保 Eagle 软件正在运行
- 确保 API 访问已启用
- Token 信息请妥善保管，不要提交到版本控制系统

## 开发计划

- [ ] 微信自动化操作
- [ ] 素材自动整理
- [ ] 批量处理功能

---

如有问题，请检查 Eagle 软件是否正常运行且 API 访问已正确配置。

# AutoWeChat 项目交接文档
1. 项目简介
AutoWeChat 是一个自动化快讯发布工具，旨在通过输入一段文本，自动抓取 Logo、生成封面图（Cover）和排版好的公众号文章（HTML）。
核心特性：
无头运行：脱离本地 Eagle 库，完全基于云端 DuckDuckGo 搜图。
智能排版：自动识别 H1/H2/H3 层级，兼容 Markdown 和自然语言特征。
微信兼容：使用 <section> 架构和 Base64 图片嵌入，确保样式在公众号后台 100% 还原。
2. 核心架构
框架: Flask (Python)
图像引擎: Pillow (PIL)
搜图引擎: duckduckgo_search + Clearbit
入口: server.py (集成了 Web UI 和 API)
端口: 8080
3. 文件结构
code
Text
AutoWeChat/
├── assets/          # 核心素材 (严禁删除)
│   ├── header.gif   # 公众号顶部动图
│   ├── bg_finance.jpg # 融资底图
│   ├── bg_merge.jpg   # 收购底图
│   ├── Impact.ttf   # 数字字体
│   └── font.ttf     # 备用字体
├── logos/           # Logo 缓存池 (自动管理)
├── output/          # 生成结果 (每次运行会自动清空)
└── server.py        # 主程序
4. 负责人用户画像 (重要!)
身份：项目负责人 (Boss)。
偏好：不喜欢看代码细节，只看结果。
要求：
视觉强迫症：对齐、字号、颜色必须严格符合 VI。
稳定性：不能报错，不能生成垃圾文件。
易用性：必须有傻瓜式 Web 界面或机器人接口。
5. 部署与运行
安装依赖:
pip install flask pillow requests pangu duckduckgo_search
启动服务:
python server.py
访问:
浏览器打开 http://localhost:8080/
6. 飞书机器人配置 (可选)
在 server.py 顶部填入 FEISHU_APP_ID 和 FEISHU_APP_SECRET，并将飞书后台的“消息卡片回调地址”设置为 http://服务器IP:8080/api/feishu。
