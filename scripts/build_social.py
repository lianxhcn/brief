"""Build local editorial packages from a reviewed daily issue; never post online."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from website_citations import bibliography_metadata, format_myapa
from site_config import detail_url

ROOT = Path(__file__).resolve().parents[1]

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def text(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + '\n', encoding='utf-8')

def wrap(value, font, width):
    lines = []
    for paragraph in value.split('\n'):
        line = ''
        for char in paragraph:
            if font.getlength(line + char) > width:
                lines.append(line)
                line = char
            else:
                line += char
        lines.append(line)
    return lines

def card(path, title, body, source, date, number):
    im = Image.new('RGB', (1080, 1440), '#f7f3ea')
    d = ImageDraw.Draw(im)
    fontpath = 'C:/Windows/Fonts/msyh.ttc'
    boldpath = 'C:/Windows/Fonts/msyhbd.ttc'
    small = ImageFont.truetype(fontpath, 27)
    d.rectangle((0, 0, 1080, 18), fill='#247568')
    d.text((76, 64), '连享会 · 研究与方法', font=small, fill='#247568')
    d.text((76, 116), date.replace('-', '.') + f'  /  {number:02d}', font=small, fill='#5f6865')
    titlefont = ImageFont.truetype(boldpath, 55)
    titlelines = wrap(title, titlefont, 928)
    y = 220
    for line in titlelines:
        d.text((76, y), line, font=titlefont, fill='#172f2b')
        y += 80
    y += 36
    for size in range(37, 25, -1):
        bodyfont = ImageFont.truetype(fontpath, size)
        bodylines = wrap(body.replace('`', ''), bodyfont, 928)
        if y + len(bodylines) * (size + 22) <= 1190:
            break
    else:
        raise ValueError('Card text exceeds safe area: ' + title)
    for line in bodylines:
        d.text((76, y), line, font=bodyfont, fill='#34433e')
        y += size + 22
    for i, line in enumerate(wrap(source, small, 928)):
        if 1240 + i * 38 > 1340:
            raise ValueError('Source exceeds safe area')
        d.text((76, 1240 + i * 38), line, font=small, fill='#5f6865')
    d.line((76, 1370, 1004, 1370), fill='#b7c9bf', width=2)
    d.text((76, 1380), '学术研究  /  方法边界  /  实用工具', font=small, fill='#247568')
    im.save(path)

def build(date, output):
    issuepath = ROOT / 'content/issues' / (date + '.json')
    issue = json.loads(issuepath.read_text(encoding='utf-8'))
    if issue['date'] != date or issue.get('status') != 'published':
        raise ValueError('Expected matching published issue')
    stamp = date.replace('-', '')
    paths = [output/'weibo'/f'{stamp}.md', output/'zhihu'/f'{stamp}.md', output/'xiaohongshu'/stamp]
    if any(p.exists() for p in paths):
        raise FileExistsError('Existing package: review before replacing')
    entries = [(category, item) for category in ('lianxh_posts', 'papers', 'tools', 'research_resources', 'conference_calls') for item in issue.get(category, [])]
    entries = [(c, i) for c, i in entries if i.get('page_note')]
    labels = {'papers':'论文', 'tools':'工具', 'research_resources':'研究资源', 'lianxh_posts':'连享会', 'conference_calls':'会议'}
    weibo = [issue['title'], '> <' + detail_url(issue) + '>']
    zhihu = [f'# {issue["title"]}', f'本期整理 {len(entries)} 条研究与工具资料，保留原始来源和方法适用边界。']
    for category, item in entries:
        url = item.get('source_url') or item.get('homepage_url') or item.get('url')
        if not url:
            raise ValueError('Missing source: ' + item['id'])
        source_date = item.get('published_date') or item.get('release_date') or 'unknown'
        if category == 'papers':
            state = {'published':'正式发表', 'forthcoming':'forthcoming', 'working-paper':'工作论文'}.get(item.get('publication_status'), '状态未标明')
            if item.get('pdf_version'):
                state += ' / ' + item['pdf_version']
        elif category == 'tools':
            state = ' / '.join(str(item[k]) for k in ('ecosystem', 'name', 'version') if item.get(k))
        else:
            state = labels[category]
        provenance = f'来源日期：{source_date}；{state}'
        weibo += [f'[{labels[category]}] **{item["title"]}**', item['page_note'], provenance, f'来源：<{url}>']
        zhihu += [f'## {item["title"]}']
        if category == 'papers':
            citation = format_myapa(bibliography_metadata(item))
            citation = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](<\1>)', citation)
            zhihu += [html.unescape(re.sub('<[^>]+>', '', citation.replace('(<https', '(\x01https'))).replace('(\x01https', '(<https')]
        zhihu += [item['page_note'], provenance, f'来源：<{url}>', '标签：' + ' · '.join(item.get('catalog', {}).get('tags', []))]
    text(paths[0], '\n\n'.join(weibo))
    text(paths[1], '\n\n'.join(zhihu))
    # Prefer core items and keep both papers and tools; record actual IDs rather than invented scores.
    papers = [i for c,i in entries if c == 'papers']
    tools = [i for c,i in entries if c == 'tools']
    papers.sort(key=lambda i: i.get('priority') != 'core')
    tools.sort(key=lambda i: i.get('priority') != 'core')
    chosen = papers[:3] + tools[:2]
    if len(chosen) < 5:
        chosen += [i for c,i in entries if i not in chosen][:5-len(chosen)]
    category_by_id = {i['id']: c for c, i in entries}
    folder = paths[2]
    folder.mkdir(parents=True)
    cards = [{'title':'今日研究与方法', 'body':'\n\n'.join(i['title'] for i in chosen), 'source':'研究方法 · 论文发现 · 实用工具', 'label':'导读'}]
    post = [f'# 研究方法与工具札记 | {date.replace("-", ".")}', '从本期快讯中精选几条研究问题与实用工具，保留结论的适用边界。']
    sources = ['# 编辑核对来源', '仅供编辑核对，不上传为小红书正文或卡片。']
    for item in chosen:
        b = item.get('bibliography', {})
        source = '来源：' + (b.get('source') or item.get('journal') or item.get('ecosystem') or '官方项目文档')
        cards.append({'title':item['title'], 'body':item['page_note'], 'source':source, 'label':labels[category_by_id[item['id']]]})
        post += [f'## {item["title"]}', item['page_note'], source]
        sources += [f'## {item["title"]}', item.get('source_url') or item.get('homepage_url') or item.get('url')]
    text(folder/'post.md', '\n\n'.join(post + ['#学术研究 #研究方法 #实证研究']))
    text(folder/'sources.md', '\n\n'.join(sources))
    dump(folder/'selection.json', {'issue_date':date, 'count':len(chosen), 'selected_ids':[i['id'] for i in chosen], 'category_counts':{c:sum(category_by_id[i['id']] == c for i in chosen) for c in labels}, 'rule':'论文与工具优先、core优先；不足时从其余已审核条目补充，记录实际构成；无虚构语义评分', 'review':'核对正式期次说明及适用边界；卡片须目视检查'})
    dump(folder/'card-text.json', cards)
    for n, value in enumerate(cards):
        card(folder/('cover.png' if n == 0 else f'item-{n:02d}.png'), value['title'], value['body'], value['source'], date, n)
    files = [paths[0], paths[1]] + sorted(folder.iterdir())
    manifest = {'date':date, 'generated_at':datetime.now(timezone(timedelta(hours=8))).isoformat(), 'source_sha256':hashlib.sha256(issuepath.read_bytes()).hexdigest(), 'status':'generated-awaiting-visual-review', 'platform_posted':False, 'files':[{'path':str(p.relative_to(output)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    dump(ROOT/'ops-local/runs'/date/'social-package.json', manifest)
    print(date, len(files), 'files', output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.date, args.output)
