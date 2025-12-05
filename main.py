import os
import re
import requests
import webbrowser
import pangu
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from io import BytesIO
from duckduckgo_search import DDGS # 核心搜索库

# ================= ⚙️ 配置区域 =================
# 1. 定义项目根目录 (修复点)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 定义各文件夹路径
EAGLE_LIB_PATH = r"/Users/wangyu/Downloads/插画灵感.library" 
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGOS_DIR = os.path.join(BASE_DIR, "logos")

# 3. 确保文件夹存在
os.makedirs(LOGOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= 🎨 样式定义 =================
S_CONTAINER = 'max-width: 677px; margin: 0 auto; background: #ffffff; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-radius: 6px; overflow: hidden; box-sizing: border-box;'
S_PADDING = 'padding: 20px 15px 40px 15px;'
S_META_WRAPPER = 'padding: 15px 10px 5px 10px; border-bottom: 1px solid #eee; margin-bottom: 30px; text-align: right;'
S_META_P = 'margin: 0 0 4px 0; font-size: 12px; color: #999; text-align: right; line-height: 1.4;'
S_META_BOLD = 'color: #555; font-weight: 600; margin-right: 4px;'
S_H1 = 'display: block; font-size: 24px; font-weight: bold; color: #1658ff; margin-top: 35px; margin-bottom: 20px; line-height: 1.4; letter-spacing: 0.5px;'
S_H2 = 'display: block; font-size: 16px; font-weight: bold; color: #000000; margin-top: 25px; margin-bottom: 10px; line-height: 1.5; border-left: 4px solid #1658ff; padding-left: 10px;'
S_P = 'display: block; font-size: 14px; color: #444; margin-bottom: 15px; text-align: justify; line-height: 1.75; letter-spacing: 0.5px;'
S_HIGHLIGHT = 'font-weight: bold; color: #1658ff;'
S_SOURCE = 'display: block; font-size: 12px; color: #bbb; text-align: right; margin-top: 40px;'

# ================= 🖼️ 图像处理核心 =================

def remove_white_bg_native(img, threshold=245):
    """原生算法去白底"""
    if img.mode != 'RGBA': img = img.convert('RGBA')
    datas = img.getdata()
    new_data = []
    for item in datas:
        # 如果是接近白色，变透明
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    bbox = img.getbbox()
    if bbox: img = img.crop(bbox)
    return img

def resize_logo_normalized(logo_img, max_h, max_w):
    w, h = logo_img.size
    scale = min(max_h/h, max_w/w)
    return logo_img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)

def is_high_quality(img):
    """清晰度门禁：宽度至少 300px"""
    if img.width < 300: return False
    return True

def create_placeholder_logo(name):
    """兜底文字Logo"""
    print(f"   ⚠️ [兜底] 生成文字占位符: {name}")
    size = 500
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=(240, 240, 240))
    text = name[0].upper() if name else "?"
    try:
        font_path = os.path.join(ASSETS_DIR, "Impact.ttf")
        if not os.path.exists(font_path): font_path = os.path.join(ASSETS_DIR, "font.ttf")
        font = ImageFont.truetype(font_path, 300)
    except: font = ImageFont.load_default()
    l, t, r, b = font.getbbox(text)
    draw.text(((size-(r-l))/2-l, (size-(b-t))/2-t), text, font=font, fill=(80, 80, 80))
    return img

# ================= ☁️ Logo 获取 (AI 搜索版) =================

def search_logo_with_ai(keyword):
    """
    使用 DuckDuckGo 模拟 AI 搜索
    搜索词：keyword + "logo png transparent"
    """
    print(f"   🤖 [AI搜索] 正在全网检索: {keyword} logo ...")
    search_term = f"{keyword} logo png transparent"
    
    try:
        with DDGS() as ddgs:
            # 搜索图片，只找 PNG，结果限制前4个
            results = ddgs.images(
                search_term, 
                type_image='transparent', 
                max_results=4
            )
            
            results_list = list(results)
            if not results_list:
                print("   ⚠️ AI 搜索未返回结果")
                return None

            for res in results_list:
                img_url = res.get('image')
                # 简单过滤：不要找 icon 这种小图
                if 'icon' in img_url.lower(): continue
                
                print(f"      ⬇️ 尝试下载: {img_url[:60]}...")
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                    resp = requests.get(img_url, headers=headers, timeout=5)
                    
                    if resp.status_code == 200:
                        img_data = BytesIO(resp.content)
                        try:
                            img = Image.open(img_data)
                        except:
                            continue # 即使报错也继续找下一个
                        
                        if img.format == 'SVG': 
                            print("      ❌ 遇到 SVG 代码，跳过")
                            continue
                            
                        # 检查清晰度
                        if img.width > 300:
                            print(f"      ✅ 捕获高清图! 尺寸: {img.width}x{img.height}")
                            return img
                        else:
                            print(f"      ⚠️ 图片太小 ({img.width}px)，寻找下一张...")
                except:
                    continue

    except Exception as e:
        print(f"   ❌ AI 搜索模块报错: {e}")
    
    return None

def download_logo_clearbit(name):
    """备用方案：Clearbit"""
    clean_name = re.sub(r'[^\w\s\-\.]', '', name).strip().lower()
    clean_name = clean_name.replace(' ', '')
    domains = [f"{clean_name}.com", f"{clean_name}.io", f"{clean_name}.ai", f"{clean_name}.sh"]
    for d in domains:
        try:
            url = f"https://logo.clearbit.com/{d}?size=600"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                print(f"   ✅ Clearbit 命中: {d}")
                return Image.open(BytesIO(resp.content))
        except: pass
    return None

def get_logo(keyword):
    if not keyword: return None
    print(f"\n🔍 任务: 获取 Logo '{keyword}'")
    
    local_path = os.path.join(LOGOS_DIR, f"{keyword}.png")
    
    # 1. 检查本地是否有【高清】缓存
    if os.path.exists(local_path):
        try:
            img = Image.open(local_path)
            if is_high_quality(img):
                print(f"✅ [本地] 发现高清缓存: {local_path}")
                return img
            else:
                print(f"⚠️ [本地] 缓存太模糊 (<300px)，废弃，重新搜索...")
        except: pass

    # 2. AI 网络搜索 (这是主力！)
    img = search_logo_with_ai(keyword)
    
    # 3. 如果 AI 搜不到，试一下 Clearbit (备用)
    if not img:
        print("   ⚠️ AI 搜索未命中，尝试 Clearbit 兜底...")
        img = download_logo_clearbit(keyword)

    # 4. 保存并返回
    if img:
        try:
            # 统一处理：去白底
            img = remove_white_bg_native(img)
            # 保存到本地，供下次使用
            img.save(local_path, "PNG")
            print(f"💾 [保存] 已存入本地库: {local_path}")
            return img
        except Exception as e:
            print(f"❌ 图片处理失败: {e}")

    # 5. 实在找不到，生成文字 Logo
    return create_placeholder_logo(keyword)

# ================= 📝 文本与排版 =================

def clean_company_name(text):
    text = text.split("：")[0].split(":")[0].strip()
    if " " in text: return text.split(" ")[0]
    return text

def parse_content_text(raw_text):
    info = {"type": "通用", "amount": "", "company": "", "buyer": "", "target": "", "body_html": "", "title": ""}
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    if not lines: return info
    
    info['title'] = lines[0]
    title = info['title']
    
    if any(k in title for k in ["收购", "并购", "买下"]):
        info['type'] = "收购"
        split_char = "收购" if "收购" in title else "并购" if "并购" in title else "买下"
        parts = title.split(split_char)
        if len(parts) >= 2:
            info['buyer'] = clean_company_name(parts[0])
            info['target'] = clean_company_name(parts[1])
    elif any(k in title for k in ["融资", "获投", "完成"]):
        info['type'] = "融资"
        amt_match = re.search(r'(\d+(?:\.\d+)?(?:亿|万|千万|百万)?(?:美元|人民币|元|B|M))', title)
        if amt_match: info['amount'] = amt_match.group(1)
        company_part = re.split(r'(完成|获投|融资|宣布)', title)[0]
        info['company'] = clean_company_name(company_part)
    else:
        info['type'] = "通用"
        info['company'] = clean_company_name(title.split(" ")[0])

    print(f"🤖 智能分类: [{info['type']}] | 主体: {info.get('company') or (info.get('buyer') + ' & ' + info.get('target'))}")

    body_parts = []
    H1_KEYS = ["核心洞察", "Core Insights", "关键要点", "深度分析"]
    for line in lines[1:]:
        line = pangu.spacing_text(line)
        line = re.sub(r'\*\*(.*?)\*\*', f'<span style="{S_HIGHLIGHT}">\\1</span>', line)
        if line.startswith("# "): body_parts.append(f'<p style="{S_H1}">{line[2:].strip()}</p>')
        elif line.startswith("## "): body_parts.append(f'<p style="{S_H2}">{line[3:].strip()}</p>')
        elif line in H1_KEYS: body_parts.append(f'<p style="{S_H1}">{line}</p>')
        elif "来源" in line: body_parts.append(f'<p style="{S_SOURCE}">{line}</p>')
        else: body_parts.append(f'<p style="{S_P}">{line}</p>')

    js = """<script>function copyToWeChat(){const r=document.createRange();r.selectNodeContents(document.getElementById('wechat-content'));window.getSelection().removeAllRanges();window.getSelection().addRange(r);document.execCommand('copy');alert('✅ 已复制！');}</script>"""
    info['body_html'] = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body style='background:#f2f2f2;padding:20px;font-family:-apple-system;'><div style='text-align:center;margin-bottom:20px;'><button onclick='copyToWeChat()' style='background:#1658ff;color:white;border:none;padding:12px 25px;border-radius:6px;cursor:pointer;font-weight:bold;'>📋 复制到公众号</button></div><div id='wechat-content' style='{S_CONTAINER}'><div style='width:100%;background:#f8f8f8;text-align:center;min-height:100px;'><img src='header.gif' style='width:100%;display:block;'></div><div style='{S_META_WRAPPER}'><p style='{S_META_P}'><span style='{S_META_BOLD}'>作者</span> | INP Family</p></div><div style='{S_PADDING}'>{''.join(body_parts)}</div></div>{js}</body></html>"""
    return info

# ================= 🎨 绘制封面 =================

def format_amount(amt):
    if not amt: return "$", "0", ""
    sym = "¥" if "元" in amt or "人民币" in amt else "$"
    num_match = re.search(r'(\d+(?:\.\d+)?)', amt)
    val = float(num_match.group(1)) if num_match else 0
    mult = 1
    if "亿" in amt: mult = 10**8
    elif "万" in amt: mult = 10**4
    val = val * mult
    if val >= 10**9: return sym, f"{val/10**9:g}", "B"
    if val >= 10**6: return sym, f"{val/10**6:g}", "M"
    return sym, f"{val:g}", ""

def generate_cover(info):
    SCALE = 2
    W, H = 900*SCALE, 383*SCALE
    BLUE = (22, 88, 255)
    
    mode = info['type']
    bg_map = {"融资": "bg_finance.jpg", "收购": "bg_merge.jpg"}
    bg_name = bg_map.get(mode, "bg_general.jpg")
    bg_path = os.path.join(ASSETS_DIR, bg_name)
    
    if os.path.exists(bg_path): base = Image.open(bg_path).convert("RGBA").resize((W, H))
    else: base = Image.new("RGBA", (W, H), (255,255,255))
    
    draw = ImageDraw.Draw(base)
    
    if mode == "融资":
        s, n, u = format_amount(info['amount'])
        try:
            font_path = os.path.join(ASSETS_DIR, "Impact.ttf")
            fs, fn, fu = ImageFont.truetype(font_path, 40*SCALE), ImageFont.truetype(font_path, 128*SCALE), ImageFont.truetype(font_path, 40*SCALE)
        except: fn = ImageFont.load_default()
        
        ws, wn, wu = fs.getlength(s), fn.getlength(n), fu.getlength(u)
        base_y, total_w = 170*SCALE, ws + wn + wu + 20*SCALE
        sx = (W - total_w)/2
        
        draw.text((sx, base_y), s, font=fs, fill=BLUE, anchor="ls")
        draw.text((sx+ws+10*SCALE, base_y), n, font=fn, fill=BLUE, anchor="ls")
        draw.text((sx+ws+10*SCALE+wn+10*SCALE, base_y), u, font=fu, fill=BLUE, anchor="ls")
        
        l = get_logo(info['company'])
        l = resize_logo_normalized(l, 100*SCALE, 400*SCALE)
        base.paste(l, (int((W-l.width)/2), int(280*SCALE-l.height/2)), l)
                
    elif mode == "收购":
        GAP = 64*SCALE
        l1, l2 = get_logo(info.get('buyer')), get_logo(info.get('target'))
        
        l1, l2 = resize_logo_normalized(l1, 130*SCALE, 320*SCALE), resize_logo_normalized(l2, 130*SCALE, 320*SCALE)
        tw = l1.width + GAP + l2.width
        sx, sy = (W - tw)/2, (H - l1.height)/2
        
        base.paste(l1, (int(sx), int(sy)), l1)
        try:
            fx = ImageFont.truetype(os.path.join(ASSETS_DIR, "Impact.ttf"), 40*SCALE)
            draw.text((int(sx + l1.width + GAP/2), int(sy + l1.height/2)), "X", font=fx, fill=(200,200,200), anchor="mm")
        except: pass
        base.paste(l2, (int(sx+l1.width+GAP), int((H-l2.height)/2)), l2)
            
    else:
        l = get_logo(info.get('company'))
        l = resize_logo_normalized(l, 150*SCALE, 500*SCALE)
        base.paste(l, (int((W-l.width)/2), int((H-l.height)/2)), l)
            
    final = os.path.join(OUTPUT_DIR, "cover.jpg")
    base.convert("RGB").save(final)
    return final

def main():
    print("🚀 启动自动化排版 (AI Search V6.1)...")
    txt_path = os.path.join(BASE_DIR, "content.txt")
    if not os.path.exists(txt_path): 
        print(f"❌ 找不到 content.txt，请在 {BASE_DIR} 下创建文件。")
        return
        
    with open(txt_path, "r", encoding="utf-8") as f: content = f.read()
    info = parse_content_text(content)
    html_path = os.path.join(OUTPUT_DIR, "preview.html")
    with open(html_path, "w", encoding="utf-8") as f: f.write(info['body_html'])
    cover_path = generate_cover(info)
    print(f"\n🎉 成功！\nHTML: {html_path}\nCover: {cover_path}")
    webbrowser.open('file://' + html_path)
    os.system(f"open {cover_path}")

if __name__ == "__main__":
    main()