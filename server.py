# -*- coding: utf-8 -*-
import os
import re
import time
import json
import logging
import base64
import requests
import pangu
import shutil
import traceback
from io import BytesIO
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from PIL import Image, ImageDraw, ImageFont
from duckduckgo_search import DDGS

# ================= ⚙️ 配置区域 =================
FEISHU_APP_ID = "" 
FEISHU_APP_SECRET = ""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
LOGOS_DIR = os.path.join(BASE_DIR, 'logos')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

for d in [ASSETS_DIR, LOGOS_DIR, OUTPUT_DIR]:
    if not os.path.exists(d): os.makedirs(d)

FONT_IMPACT_PATH = os.path.join(ASSETS_DIR, 'Impact.ttf')
FONT_NORMAL_PATH = os.path.join(ASSETS_DIR, 'font.ttf')

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= 🧹 清理函数 =================
def clean_output_dir():
    try:
        if os.path.exists(OUTPUT_DIR):
            for filename in os.listdir(OUTPUT_DIR):
                file_path = os.path.join(OUTPUT_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except: pass
    except: pass

# ================= 1. 飞书模块 =================
class FeishuClient:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.token = None
        self.token_expire = 0
    def get_tenant_token(self):
        if not self.app_id or not self.app_secret: return None
        if time.time() < self.token_expire: return self.token
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        try:
            resp = requests.post(url, json={"app_id": self.app_id, "app_secret": self.app_secret})
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("tenant_access_token")
                self.token_expire = time.time() + data.get("expire", 7200) - 60
                return self.token
        except: pass
        return None
    def upload_image(self, file_path):
        token = self.get_tenant_token()
        if not token: return None
        url = "https://open.feishu.cn/open-apis/im/v1/images"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            with open(file_path, 'rb') as f:
                files = {"image": ("cover.jpg", f, "image/jpeg")}
                data = {"image_type": "message"}
                resp = requests.post(url, headers=headers, files=files, data=data)
                if resp.status_code == 200: return resp.json().get("data", {}).get("image_key")
        except: pass
        return None
    def reply_message(self, message_id, content_dict, msg_type="text"):
        token = self.get_tenant_token()
        if not token: return
        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        try:
            requests.post(url, headers=headers, json={"content": json.dumps(content_dict), "msg_type": msg_type})
        except: pass

feishu_client = FeishuClient(FEISHU_APP_ID, FEISHU_APP_SECRET)

# ================= 2. 图像算法 =================

def safe_open_image(img_data):
    try:
        img = Image.open(img_data)
        safe_img = Image.new("RGBA", img.size)
        if img.mode != 'RGBA': img = img.convert('RGBA')
        safe_img.paste(img, (0, 0))
        return safe_img
    except: return None

def remove_white_bg_native(img, threshold=245):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    datas = img.getdata()
    new_data = []
    for item in datas:
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    clean_img = Image.new("RGBA", img.size)
    clean_img.putdata(new_data)
    bbox = clean_img.getbbox()
    return clean_img.crop(bbox) if bbox else clean_img

def resize_logo_normalized(img, max_h, max_w):
    w, h = img.size
    scale = min(max_h/h, max_w/w)
    return img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)

def is_high_quality(img): return img.width >= 200

def search_logo_with_ai(keyword):
    clean_keyword = re.sub(r'[^\w\s\-\.\u4e00-\u9fa5]', '', keyword).strip()
    local_path = os.path.join(LOGOS_DIR, f"{clean_keyword}.png")
    if os.path.exists(local_path):
        try:
            img = safe_open_image(local_path)
            if img and is_high_quality(img): return img
        except: pass
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(f"{clean_keyword} logo png transparent", type_image='transparent', max_results=3))
            for res in results:
                try:
                    resp = requests.get(res['image'], headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                    if resp.status_code == 200:
                        img = safe_open_image(BytesIO(resp.content))
                        if not img: continue
                        if img.width > 200:
                            img = remove_white_bg_native(img)
                            img.save(local_path, "PNG")
                            return img
                except: continue
    except: pass
    try:
        clean_name = re.sub(r'[^\w]', '', clean_keyword).lower()
        url = f"https://logo.clearbit.com/{clean_name}.com?size=600"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            img = safe_open_image(BytesIO(resp.content))
            if img:
                img = remove_white_bg_native(img)
                img.save(local_path, "PNG")
                return img
    except: pass
    return None

# ================= 3. 文本解析 =================

def clean_company_name(text):
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text) 
    text = text.split("：")[0].split(":")[0].strip()
    if " " in text: return text.split(" ")[0]
    return text

def parse_info_from_title(title):
    title = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', title).strip()
    info = {"mode": "general", "keywords": []}
    if any(k in title for k in ["收购", "并购", "买下"]):
        info['mode'] = "acquisition"
        split_char = "收购" if "收购" in title else "并购" if "并购" in title else "买下"
        parts = title.split(split_char)
        if len(parts) >= 2:
            info['keywords'] = [clean_company_name(parts[0]), clean_company_name(parts[1])]
            return info
    if any(k in title for k in ["融资", "获投", "完成"]):
        info['mode'] = "finance"
        company_part = re.split(r'(完成|获投|融资|宣布)', title)[0]
        info['keywords'] = [clean_company_name(company_part)]
        # 支持空格，货币单位变为可选
        amt_match = re.search(r'(\d+(?:\.\d+)?\s*(?:亿|万|千万|百万)?\s*(?:美元|人民币|元|B|M)?)', title)
        info['amount'] = amt_match.group(1).strip() if amt_match else ""
        return info
    info['keywords'] = [clean_company_name(title)]
    return info

# ================= 4. 封面绘制 =================
def format_amount(amt):
    if not amt: return "$", "0", ""
    # 默认全部为美元
    sym = "$"
    # 提取数字（支持空格）
    num_match = re.search(r'(\d+(?:\.\d+)?)', amt.replace(' ', ''))
    val = float(num_match.group(1)) if num_match else 0
    mult = 1
    if "亿" in amt: mult = 10**8
    elif "万" in amt: mult = 10**4
    val = val * mult
    # 自动转化为 M/B
    if val >= 10**9: return sym, f"{val/10**9:g}", "B"
    if val >= 10**6: return sym, f"{val/10**6:g}", "M"
    return sym, f"{val:g}", ""

def safe_paste(base, img, pos):
    try: base.paste(img, pos, img)
    except: 
        try: base.paste(img, pos)
        except: pass

def generate_cover_image(info):
    mode = info['mode']
    keywords = info['keywords']
    SCALE = 2
    W, H = 900 * SCALE, 383 * SCALE
    BLUE = (22, 88, 255)
    
    bg_map = {"finance": "bg_finance.jpg", "acquisition": "bg_merge.jpg"}
    bg_path = os.path.join(ASSETS_DIR, bg_map.get(mode, "bg_general.jpg"))
    base = Image.open(bg_path).convert("RGBA").resize((W, H)) if os.path.exists(bg_path) else Image.new("RGBA", (W, H), (255,255,255))
    draw = ImageDraw.Draw(base)
    
    try:
        fx = ImageFont.truetype(FONT_IMPACT_PATH, 40*SCALE)
        fs = ImageFont.truetype(FONT_IMPACT_PATH, 40*SCALE)
        fn = ImageFont.truetype(FONT_IMPACT_PATH, 128*SCALE)
        fu = ImageFont.truetype(FONT_IMPACT_PATH, 40*SCALE)
    except: fn = ImageFont.load_default()
        
    if mode == "finance":
        s, n, u = format_amount(info.get('amount', ''))
        ws, wn, wu = fs.getlength(s), fn.getlength(n), fu.getlength(u)
        total_w = ws + wn + wu + 20*SCALE
        sx, base_y = (W - total_w) / 2, 170 * SCALE
        draw.text((sx, base_y), s, font=fs, fill=BLUE, anchor="ls")
        draw.text((sx+ws+10*SCALE, base_y), n, font=fn, fill=BLUE, anchor="ls")
        draw.text((sx+ws+10*SCALE+wn+10*SCALE, base_y), u, font=fu, fill=BLUE, anchor="ls")
        if keywords:
            l = search_logo_with_ai(keywords[0])
            if l:
                l = resize_logo_normalized(l, 100*SCALE, 400*SCALE)
                pos = (int((W-l.width)/2), int(280*SCALE-l.height/2))
                safe_paste(base, l, pos)
    elif mode == "acquisition" and len(keywords) >= 2:
        GAP = 64 * SCALE
        l1, l2 = search_logo_with_ai(keywords[0]), search_logo_with_ai(keywords[1])
        if l1 and l2:
            l1, l2 = resize_logo_normalized(l1, 130*SCALE, 320*SCALE), resize_logo_normalized(l2, 130*SCALE, 320*SCALE)
            sx = (W - (l1.width + GAP + l2.width)) / 2
            safe_paste(base, l1, (int(sx), int((H-l1.height)/2)))
            draw.text((int(sx + l1.width + GAP/2), int(H/2)), "X", font=fx, fill=(200,200,200), anchor="mm")
            safe_paste(base, l2, (int(sx + l1.width + GAP), int((H-l2.height)/2)))
    else:
        if keywords:
            l = search_logo_with_ai(keywords[0])
            if l:
                l = resize_logo_normalized(l, 150*SCALE, 500*SCALE)
                safe_paste(base, l, (int((W-l.width)/2), int((H-l.height)/2)))

    fn = "cover.jpg"
    base.convert("RGB").save(os.path.join(OUTPUT_DIR, fn), quality=95)
    return fn

# ================= 5. HTML 生成 =================
def image_to_base64(path):
    if not os.path.exists(path): return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def generate_html_file(title, content):
    title = pangu.spacing_text(title)
    FONT = "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif"
    S_ROOT = f"margin: 0 auto; max-width: 677px; background-color: #ffffff; padding: 20px 8px; box-sizing: border-box; font-family: {FONT};"
    C_BLUE = "#1658ff"
    C_TEXT = "#323345"
    C_SIG = "#888888"
    C_META = "#d6d6d6"

    S_SIG_WRAP = "text-align: right; margin-top: 10px; margin-bottom: 30px;"
    S_SIG_ITEM = f"font-size: 14px; color: {C_SIG}; line-height: 1.6; margin: 0; font-weight: 500;"
    S_H1 = f"font-size: 20px; color: {C_BLUE}; font-weight: bold; line-height: 1.4; margin-top: 32px; margin-bottom: 16px; text-align: left;"
    S_H2 = f"font-size: 17px; color: {C_BLUE}; font-weight: bold; line-height: 1.5; margin-top: 24px; margin-bottom: 12px; text-align: left;"
    S_H3 = f"font-size: 14px; color: {C_BLUE}; font-weight: bold; line-height: 1.5; margin-top: 20px; margin-bottom: 8px; text-align: left;"
    S_TXT = f"font-size: 14px; color: {C_TEXT}; line-height: 1.75; text-align: justify; margin: 0;"
    S_BOLD = f"font-size: 14px; color: {C_BLUE}; font-weight: bold;"
    S_META = f"font-size: 12px; color: {C_META}; margin-top: 20px; text-align: right; margin-bottom: 0;"

    lines = content.strip().split('\n')
    header_depths = []
    for line in lines[1:]: 
        m = re.match(r'^(#+)\s', line.strip())
        if m: header_depths.append(len(m.group(1)))
    min_depth = min(header_depths) if header_depths else 0
    
    html_body = f'<section style="{S_H1}">{lines[0]}</section>'
    
    for line in lines[1:]:
        line = line.strip()
        if not line: continue
        line = pangu.spacing_text(line)
        if "来源" in line or "链接" in line or "http" in line:
            html_body += f'<section style="{S_META}">{line}</section>'
            continue
        md_match = re.match(r'^(#+)\s(.*)', line)
        if md_match:
            depth = len(md_match.group(1))
            clean_text = md_match.group(2)
            relative_level = depth - min_depth + 1
            if relative_level == 1: html_body += f'<section style="{S_H1}">{clean_text}</section>'
            elif relative_level == 2: html_body += f'<section style="{S_H2}">{clean_text}</section>'
            else: html_body += f'<section style="{S_H3}">{clean_text}</section>'
            continue
        if "Insights" in line or "核心洞察" in line:
            html_body += f'<section style="{S_H1}">{line}</section>'
            continue
        if len(line) < 24 and not re.search(r'[，。！？、：；]$', line):
            html_body += f'<section style="{S_H1}">{line}</section>'
        else:
            line = re.sub(r'\*\*(.*?)\*\*', f'<span style="{S_BOLD}">\\1</span>', line)
            html_body += f'<section style="{S_TXT}">{line}</section>'

    b64_data = image_to_base64(os.path.join(ASSETS_DIR, 'header.gif'))
    img_tag = f'<img src="data:image/gif;base64,{b64_data}" style="width: 100%; display: block; margin: 0; border-radius: 4px;" alt="Header">' if b64_data else ""

    fn = "news.html"
    with open(os.path.join(OUTPUT_DIR, fn), 'w', encoding='utf-8') as f: f.write(full_html)
    return fn

# ================= 6. 路由与UI =================
@app.route('/')
def home():
    """自带的 Web 界面"""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>AutoWeChat 自动化排版工具</title>
        <style>
            body { font-family: -apple-system, sans-serif; background: #f5f7fa; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
            .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); width: 600px; }
            h1 { color: #1658ff; margin-bottom: 20px; text-align: center; }
            textarea { width: 100%; height: 200px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; margin-bottom: 20px; box-sizing: border-box; }
            .hint { font-size: 12px; color: #999; margin-bottom: 10px; }
            button { width: 100%; background: #1658ff; color: white; border: none; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; }
            button:hover { background: #0042d9; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            #result { margin-top: 20px; display: none; }
            .link-box { background: #f0f7ff; padding: 15px; border-radius: 8px; border: 1px solid #cce4ff; margin-bottom: 10px; word-break: break-all; }
            a { color: #1658ff; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 AutoWeChat 排版助手</h1>
            <p class="hint">输入快讯文本（支持 Markdown # 标题）：</p>
            <textarea id="input-text" placeholder="在此粘贴快讯内容..."></textarea>
            
            <p class="hint">手动指定 Logo (可选，用逗号分隔，如: OpenAI, Microsoft)：</p>
            <textarea id="input-kw" style="height: 50px;" placeholder="一般留空，让 AI 自动识别"></textarea>
            
            <button id="btn" onclick="submit()">🚀 立即生成</button>
            
            <div id="result">
                <div class="link-box">🖼 封面图: <a id="cover-link" target="_blank" href="#">点击查看</a></div>
                <div class="link-box">📄 排版文: <a id="html-link" target="_blank" href="#">点击预览 & 复制</a></div>
            </div>
        </div>
        <script>
            async function submit() {
                const btn = document.getElementById('btn');
                const text = document.getElementById('input-text').value;
                const kwStr = document.getElementById('input-kw').value;
                
                if(!text) return alert("请输入内容");
                
                btn.disabled = true;
                btn.innerText = "⏳ 正在搜图与排版...";
                
                const keywords = kwStr ? kwStr.split(/[,，]/).map(s => s.trim()).filter(s => s) : [];
                
                try {
                    const res = await fetch('/api/process', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ text, keywords })
                    });
                    const data = await res.json();
                    
                    if(data.html_url) {
                        document.getElementById('cover-link').href = data.cover_url;
                        document.getElementById('html-link').href = data.html_url;
                        document.getElementById('result').style.display = 'block';
                        btn.innerText = "✅ 生成成功 (点击下方链接)";
                    } else {
                        alert("生成失败: " + JSON.stringify(data));
                        btn.innerText = "❌ 重试";
                    }
                } catch(e) {
                    alert("网络错误: " + e);
                    btn.innerText = "❌ 重试";
                }
                btn.disabled = false;
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/output/<path:filename>')
def get_file(filename): return send_from_directory(OUTPUT_DIR, filename)

@app.route('/api/process', methods=['POST'])
def manual_test():
    clean_output_dir()
    try:
        data = request.json
        text = data.get('text', '')
        manual_keywords = data.get('keywords', [])
        title = text.split('\n')[0]
        info = parse_info_from_title(title)
        if manual_keywords:
            info['keywords'] = manual_keywords
            info['mode'] = "acquisition" if len(manual_keywords) >= 2 else "general"

        host = request.host_url.rstrip('/')
        cover = generate_cover_image(info)
        html = generate_html_file(title, text)
        return jsonify({"cover_url": f"{host}/output/{cover}", "html_url": f"{host}/output/{html}"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)}), 500

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = 23456
    
    print("🚀 AutoWeChat V4.0 (Web UI Ready)")
    print(f"📡 服务运行中，可通过以下地址访问：")
    print(f"   - 本机访问: http://127.0.0.1:{port}/")
    print(f"   - 局域网访问: http://{local_ip}:{port}/")
    print(f"   - 所有接口: http://0.0.0.0:{port}/")
    
    app.run(host='0.0.0.0', port=port, debug=False)