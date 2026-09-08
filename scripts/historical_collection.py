"""历史精选独立入口；只读冻结输入，不生成 daily issue 或渠道发布事件。"""
from lianxh_exclusions import screen_post, normalized_url
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from isolated_trial import Isolation, forbidden_paths, ROOT
from render_issue_pages import render_item
from trial_selection import evaluation, exact_date, identities, publication_events

CATEGORIES = {'lianxh_posts': '连享会推文', 'papers': '论文阅读', 'tools': '新命令与软件', 'conference_calls': '会议征稿'}

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def validate_collection(data, observed, history):
    """固定历史区间与真实执行时间分开；不调用或放宽日常数量规则。"""
    errors = []
    if data.get('type') != 'historical-collection': errors.append('历史集合类型错误')
    if data.get('human_review') != 'pending' or data.get('release_status') != 'no-release':
        errors.append('历史草稿必须待审核且 no-release')
    if data.get('events') != []: errors.append('草稿不得生成发布事件')
    try:
        start, end = exact_date(data['range_start']), exact_date(data['range_end'])
        checked, added = evaluation(data['checked_at']), evaluation(data['added_at'])
        if start > end or checked > added: errors.append('日期区间或执行时序错误')
    except (KeyError, ValueError, TypeError): return errors + ['日期字段无效']
    observed_by_id = {x['id']: x for x in observed}
    register = data.get('post_register', [])
    if len(observed_by_id) != len(observed): errors.append('观察目录 ID 重复')
    if len({x['id'] for x in register}) != len(register): errors.append('处置登记 ID 重复')
    if {x['id'] for x in register} != set(observed_by_id): errors.append('目录与逐条处置不一致')
    for row in register:
        if not row.get('reason') or row.get('decision') not in {'proposed','deferred','excluded','reuse'}:
            errors.append(row['id']+': 缺少有效处置及原因')
        gate = screen_post(row)
        if gate['action'] == 'excluded' and row.get('decision') != 'excluded':
            errors.append(row['id']+': 前置排除处置不符')
        o = observed_by_id.get(row['id'], {})
        if any(row.get(k) != o.get(k) for k in ('title','url','display_date','author')):
            errors.append(row['id']+': 登记与独立目录不一致')
    register_by_id = {r['id']: r for r in register}
    entry_ids = set()
    selected_posts = set()
    seen = set()
    paper_keys, post_work_keys = set(), set()
    for entry in data.get('entries', []):
        item, category = entry.get('payload', {}), entry.get('category')
        key = item.get('id', '?')
        if key in entry_ids: errors.append(key+': entry ID 重复')
        entry_ids.add(key)
        if category == 'lianxh_posts':
            row, obs = register_by_id.get(key, {}), observed_by_id.get(key, {})
            gate = screen_post(dict(item, content_classification=row.get('content_classification', {})))
            if gate['action'] != 'retain': errors.append(key+': '+gate['reason']); continue
            if not row or not obs: errors.append(key+': entry 缺观察或登记绑定')
            if any(item.get('title') != x.get('title') or normalized_url(item.get('url')) != normalized_url(x.get('url')) for x in (row, obs)):
                errors.append(key+': entry 题名或 URL 与可信输入不符')
            if entry.get('decision') != row.get('decision'): errors.append(key+': entry 处置不符')
            if entry.get('date_kind') == 'page-display' and any(entry.get('source_date') != x.get('display_date') for x in (row, obs)):
                errors.append(key+': entry 页面日期与可信输入不符')
        if category not in CATEGORIES: errors.append(key+': 不支持的分类'); continue
        if not re.fullmatch(r'[a-z0-9-]+', key): errors.append(key+': ID 不安全')
        try:
            day = exact_date(entry['source_date'])
            if not start <= day <= min(end, checked.date()): errors.append(key+': 来源日期越界')
            if evaluation(entry['verified_at']) > checked: errors.append(key+': 核验晚于检查终点')
        except (KeyError, ValueError, TypeError): errors.append(key+': 缺少可靠日精度日期')
        if entry.get('date_kind') not in {'page-display','first-public','substantive-update','release'}:
            errors.append(key+': 发现日或普通更新日不能作为内容日期')
        if not entry.get('date_evidence') or not entry.get('evidence_locator'):
            errors.append(key+': 缺少日期或内容依据')
        if not entry.get('historical_value') or not item.get('page_note'):
            errors.append(key+': 缺少阅读价值或正文')
        keys = identities(item)
        if not keys or keys & seen: errors.append(key+': 成果重复或身份缺失')
        seen.update(keys)
        if category == 'papers':
            if keys & post_work_keys: errors.append(key+': 原论文已有中文解读入口，须关联而非重复摘要')
            paper_keys.update(keys)
        if category == 'lianxh_posts' and item.get('related_work'):
            related = item['related_work'].casefold()
            if related in paper_keys: errors.append(key+': 中文解读与原论文重复摘要')
            post_work_keys.add(related)
        formal = [h for h in history if identities(h) & keys and publication_events(h, 'papers')]
        website = [h for h in formal if any(e.get('kind')=='website' for e in publication_events(h,'papers'))]
        if website and entry.get('decision') != 'reuse': errors.append(key+': 已有正式网站条目须复用')
        if entry.get('decision') == 'reuse' and (not website or not entry.get('existing_website_url')):
            errors.append(key+': 缺少正式网站复用依据')
        if entry.get('decision') not in {'proposed','reuse'}: errors.append(key+': 暂缓条目不得渲染')
        if category == 'lianxh_posts': selected_posts.add(key)
    expected = {x['id'] for x in register if x['decision'] in {'proposed','reuse'}}
    if expected != selected_posts: errors.append('推文拟收录集合与实际条目不同')
    return errors

def carry_followups(rows, history, checked_at):
    """推进终点不丢候选；只有真实正式短版事件能够更新短版状态。"""
    moment = evaluation(checked_at)
    result = copy.deepcopy(rows)
    if len({x['id'] for x in result}) != len(result): raise ValueError('后续 ID 重复')
    for row in result:
        if screen_post(row)['action'] == 'excluded':
            raise ValueError(row['id']+': 排除项须先登记，不得进入后续队列')
        events = []
        for old in history:
            if identities(row) & identities(old):
                events += [e for e in publication_events(old, 'lianxh_posts')
                           if exact_date(e['date']) <= moment.date()]
        row['last_checked_at'] = checked_at
        if events:
            row['wechat_short_status'] = 'confirmed-formal-short'
            row['wechat_short_evidence'] = events
        # 不推断 sent；不把历史网站拟案当短版排队，也不删除质量暂缓记录。
    return result

def render_collection(data):
    title = f"历史精选：{data['range_start'].replace('-', '.')}–{data['range_end'].replace('-', '.')}"
    lines = ['---', 'title: '+json.dumps(title,ensure_ascii=False), 'lang: zh-CN', 'body-classes: issue-page',
             'search: false', 'sitemap: false', 'toc: true', 'toc-depth: 2',
             'header-includes: |', '  <meta name="robots" content="noindex,nofollow">', '---', '',
             '**待人工审核 · 历史网站草稿 · no-release**', '',
             '这是按来源日期整理的阅读集合。实际补录时间：'+data['added_at']+
             '。各条日期为来源日期，不代表当天已发布快讯或已发送微信群。', '']
    for category, label in CATEGORIES.items():
        entries = sorted([e for e in data['entries'] if e['category']==category],
                         key=lambda e:(e['source_date'],e['payload']['id']), reverse=True)
        if not entries: continue
        lines += ['## '+label, '']
        previous = None
        for entry in entries:
            if entry['source_date'] != previous:
                previous = entry['source_date']; lines += ['### '+previous, '']
            block = render_item(entry['payload'],category,False,True)
            if category == 'lianxh_posts':
                author = next(r['author'] for r in data['post_register'] if r['id']==entry['payload']['id'])
                block[4:4] = ['作者：'+author+' · 来源显示日期：'+entry['source_date'], '']
            lines += block
            if entry['payload'].get('related_work') in {'arxiv:2608.31059','arxiv:2608.26837','arxiv:2608.27364'}:
                lines += ['[阅读关联原论文](https://arxiv.org/abs/'+entry['payload']['related_work'].split(':')[1]+')', '']
            if entry['decision']=='reuse':
                lines += ['[查看已有正式网站条目]('+entry['existing_website_url']+')', '']
    return '\n'.join(lines)+'\n'

def run(args):
    guard = Isolation(args.output_root, forbidden_paths())
    for p in (args.collection,args.observed,args.history):
        if any(Path(p).resolve().is_relative_to(b.resolve()) for b in forbidden_paths()):
            raise ValueError('必须使用仓库外冻结输入')
    data, observed, history = read(args.collection), read(args.observed), read(args.history)
    if data.get('observed_sha256') != hashlib.sha256(Path(args.observed).read_bytes()).hexdigest():
        raise ValueError('观察目录指纹不一致')
    errors = validate_collection(data,observed,history)
    if errors: raise ValueError('; '.join(errors))
    guard.write('index.qmd',render_collection(data))
    guard.write('styles.css',(ROOT/'styles.css').read_text(encoding='utf-8'))
    guard.write('_quarto.yml','project:\n  type: default\nformat:\n  html:\n    css: styles.css\n    toc: true\n')
    # 长 Windows 交接路径可显式提供全新仓库外缓存根，仍受隔离检查。
    runtime = Isolation(args.runtime_root, forbidden_paths()) if getattr(args, 'runtime_root', None) else guard
    env = os.environ.copy()
    for name in ('LOCALAPPDATA','APPDATA','XDG_CACHE_HOME','DENO_DIR','TEMP','TMP'):
        p=runtime.check(runtime.root/'runtime'/name); p.mkdir(parents=True,exist_ok=True); env[name]=str(p)
    env['PYTHONDONTWRITEBYTECODE']='1'
    proc=subprocess.run([shutil.which('quarto') or r'C:\Program Files\Quarto\bin\quarto.exe',
                         'render','index.qmd','--to','html'],cwd=guard.root,env=env,
                        capture_output=True,text=True,encoding='utf-8',timeout=120)
    guard.write('render.log',proc.stdout+proc.stderr)
    guard.json('build-status.json',{'technical_status':'passed' if proc.returncode==0 else 'failed',
               'human_review':'pending','release_status':'no-release','A-02':'frozen','entries':len(data['entries'])})
    return proc.returncode

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('collection','observed','history','output-root'): parser.add_argument('--'+name,required=True)
    parser.add_argument('--runtime-root', help='可选的全新仓库外短缓存路径')
    raise SystemExit(run(parser.parse_args()))
