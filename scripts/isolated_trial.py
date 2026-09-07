"""一次隔离草稿入口：显式快照、来源子集、as-of；始终 no-release。"""
from lianxh_exclusions import screen_post, normalized_url
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from build_local_draft import assemble_daily_issue
from editorial_rules import CATEGORIES
from render_issue_pages import render_page, render_item
from render_wechat import render_daily, title_line
from site_config import date_compact, detail_url
from trial_selection import assess, evaluation, identities, selection_errors
from validate_issue import validate_schema, validate_item, validate_wechat, validate_page, validate_public_text
from wechat_format import item_lines, format_url
from coverage_rules import coverage_errors

ROOT = Path(__file__).resolve().parents[1]

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))

class Isolation:
    """每次写入解析真实路径；拒绝禁写树、祖先路径和已有输出覆盖。"""
    def __init__(self, output_root, forbidden):
        if not output_root: raise ValueError('外部输出根必填')
        self.root = Path(output_root).resolve()
        self.forbidden = [Path(p).resolve() for p in forbidden]
        self.check(self.root)
        if self.root.exists():
            raise ValueError('输出根已存在；复渲染须使用新的外部子目录')

    def check(self, path):
        resolved = Path(path).resolve()
        if not resolved.is_relative_to(self.root): raise ValueError('路径越过输出根')
        for banned in self.forbidden:
            if resolved.is_relative_to(banned) or banned.is_relative_to(resolved):
                raise ValueError('输出与禁写树重叠')
        # 拒绝硬链接覆盖；同一进程不接受外部创建的输出文件。
        if resolved.is_file() and resolved.stat().st_nlink > 1:
            raise ValueError('输出文件为硬链接')
        return resolved

    def write(self, rel, data):
        path = self.check(self.root / rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path = self.check(path)
        with path.open('x', encoding='utf-8') as handle: handle.write(data)
        return path

    def json(self, rel, data):
        return self.write(rel, json.dumps(data, ensure_ascii=False, indent=2)+'\n')

def forbidden_paths():
    shared = Path(read(ROOT/'ops-local/runtime-config.json')['shared_root'])
    return [ROOT, shared]

def run(args):
    moment = evaluation(args.as_of)
    snapshot, sources = read(args.snapshot), read(args.sources)
    observed_posts = read(args.observed_posts)
    observed_hash = hashlib.sha256(Path(args.observed_posts).read_bytes()).hexdigest()
    if snapshot.get('observed_posts_sha256') != observed_hash:
        raise ValueError('独立观察目录与冻结快照指纹不一致')
    if not sources or not all(x.get('id') for x in sources): raise ValueError('来源子集必填')
    guard = Isolation(args.output_root, forbidden_paths())
    # 所有输入必须是外部冻结副本，绝不将生产目录当可写状态。
    for path in (args.snapshot, args.sources, args.observed_posts):
        resolved = Path(path).resolve()
        if any(resolved.is_relative_to(p.resolve()) for p in forbidden_paths()):
            raise ValueError('输入须先复制到外部快照')
    if snapshot.get('as_of') != args.as_of: raise ValueError('快照与 as-of 不一致')
    source_ids = {x['id'] for x in sources}
    history = snapshot['history']
    guard.json('candidates/snapshot.json', snapshot)
    guard.json('candidates/sources.json', sources)
    guard.json('candidates/observed-posts.json', observed_posts)
    selected, decisions, seen = [], [], set()
    # 先判重要变更，再判近期重复，避免旧 key 过滤提前丢候选。
    for candidate in snapshot['candidates']:
        payload = candidate.get('payload', {})
        category = {'paper':'papers','tool':'tools','post':'lianxh_posts','resource':'research_resources','conference':'conference_calls'}.get(candidate.get('kind'))
        gate = screen_post(payload) if category == 'lianxh_posts' else {'action':'retain'}
        if gate['action'] != 'retain':
            decisions.append({'id':candidate.get('id'), 'selected':False, 'gate':gate, 'reasons':[gate['reason']]})
            continue
        try:
            reasons = assess(payload, category, history, args.as_of) if category else ['未知类型']
            if not reasons:
                check_payload = dict(payload, priority=candidate['core_or_extended'])
                validate_item(check_payload, category, Path('candidate'), reasons)
                render_item(check_payload, category, False, True)
                if check_payload['priority']=='core': item_lines(category, check_payload, 1)
        except (ValueError, KeyError, TypeError) as exc:
            reasons = ['候选格式或证据异常：' + str(exc)]
        if payload.get('review',{}).get('source_id') not in source_ids: reasons.append('不在显式来源子集')
        if candidate.get('status') != 'eligible': reasons.append(candidate.get('why_selected','未通过编辑核验'))
        keys = identities(payload)
        if keys & seen: reasons.append('同批成果重复')
        if not reasons:
            selected.append(candidate); seen.update(keys)
        decisions.append({'id':candidate.get('id'),'selected':not reasons,'reasons':reasons})
    issue = assemble_daily_issue(moment.date().isoformat(), selected)
    issue['isolated_trial'] = True
    issue['as_of'] = args.as_of
    guard.json('draft/issue.json', issue)
    guard.json('candidates/decisions.json', decisions)
    errors = []
    validate_schema(issue, Path('draft/issue.json'), errors)
    errors += selection_errors(issue, history, args.as_of)
    coverage = snapshot['coverage']
    core_posts = {x['id'] for x in issue['lianxh_posts'] if x['priority']=='core'}
    coverage_problems = coverage_errors(coverage, core_posts, args.as_of, observed_posts, history)
    errors += coverage_problems
    page_rel = 'site/issues/' + date_compact(issue['date']) + '/index.qmd'
    page = guard.write(page_rel, render_page(issue))
    # 完整草稿复用原 renderer；不足 3 条时复用逐条 formatter，校验仍明确失败。
    try:
        text = render_daily(issue)
    except ValueError:
        blocks = [title_line(issue)]
        entries = [(c,i) for c in CATEGORIES for i in issue[c] if i['priority']=='core']
        blocks += ['\n'.join(item_lines(c,i,n)) for n,(c,i) in enumerate(entries,1)]
        blocks += ['——\n'+format_url('🌐 更多内容', detail_url(issue))]
        text = '\n\n'.join(blocks)+'\n'
    guard.write('wechat/'+issue['date']+'.txt', text)
    paths = validate_wechat(issue, guard.root/'wechat', errors)
    page = validate_page(issue, guard.root/'site', errors)
    validate_public_text(issue,page,paths,errors)
    core_ids = [i['id'] for c in CATEGORIES for i in issue[c] if i['priority']=='core']
    extended_ids = [i['id'] for c in CATEGORIES for i in issue[c] if i['priority']=='extended']
    # 外部无 hooks 的最小 Quarto 配置；复制既有 CSS，不执行全站构建。
    guard.write('site/styles.css',(ROOT/'styles.css').read_text(encoding='utf-8'))
    guard.write('site/_quarto.yml','project:\n  type: default\nformat:\n  html:\n    lang: zh\n    toc: true\n    toc-title: 本页目录\n    css: styles.css\n')
    # 真正条目页作为 index；保留日期 QMD 供现有 validator 使用。
    guard.write('site/index.qmd',page.read_text(encoding='utf-8'))
    # Quarto 的 Sass/Deno 缓存也显式隔离，不写用户全局 cache。
    cache = guard.check(guard.root/'checks/runtime')
    cache.mkdir(parents=True,exist_ok=True)
    render_env = dict(os.environ, LOCALAPPDATA=str(cache), APPDATA=str(cache),
                      XDG_CACHE_HOME=str(cache), DENO_DIR=str(cache/'deno'),
                      TEMP=str(cache), TMP=str(cache))
    try:
        render_result = subprocess.run(['quarto','render','index.qmd'],cwd=guard.root/'site',env=render_env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        render_result = subprocess.CompletedProcess([], 1, '', str(exc))
    guard.write('checks/quarto.txt',render_result.stdout+'\n'+render_result.stderr)
    if render_result.returncode: errors.append('外部 Quarto 渲染失败')
    guard.write('README.md','# Task 11 隔离草稿\n\n未发布，待人工审核。'+('这是不完整诊断草稿。' if errors else '')+'\n\n微信尾链仅为目标地址格式预览，不表示本期网页存在。\n\n[网站](site/index.html) · [微信](wechat/'+issue['date']+'.txt) · [唯一事实](draft/issue.json)\n')
    result = {'as_of':args.as_of,'human_review':'pending','release_status':'no-release','A-02':'frozen',
              'content_status':'coverage_unknown' if coverage_problems else ('insufficient' if errors else 'ready_for_review'),
              'observed_posts_sha256':observed_hash,
              'errors':errors,'core_ids':core_ids,'extended_ids':extended_ids,
              'input_sha256':hashlib.sha256(Path(args.snapshot).read_bytes()).hexdigest(),
              'source_sha256':hashlib.sha256(Path(args.sources).read_bytes()).hexdigest()}
    guard.json('run-meta.json',result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('snapshot','sources','observed-posts','as-of','output-root'): parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    result=run(args)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 2 if result['errors'] else 0

if __name__=='__main__': raise SystemExit(main())
