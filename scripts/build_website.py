"""验收事实后再生成页面；--check 检查已生成文件是否过期，不写入。"""
import argparse
import json
from pathlib import Path
from build_catalog_pages import public_issues, entries, catalog_outputs, stale_catalog_pages
from render_issue_pages import render_page
from public_history import collections, render_collection, validate_collection
from website_rules import check_website
from validate_issue import validate_schema, validate_history, validate_wechat

ROOT=Path(__file__).resolve().parents[1]
def build(check=False):
    errors=[]; outputs={}
    issues=public_issues()
    for issue in issues:
        source=next(p for p in (ROOT/'content/issues').glob('*.json') if json.loads(p.read_text(encoding='utf-8')).get('issue_id') == issue['issue_id'])
        validate_schema(issue,source,errors)
        if issue.get('issue_type')=='daily':
            if issue.get('website_version') != 3:errors.append('正式日常期次缺少当前网页规则版本')
            errors += check_website(issue,ROOT)
        validate_history(issue,source,ROOT/'content/issues',errors)
        validate_wechat(issue,ROOT/'publish/wechat',errors)
        outputs['issues/'+issue['date'].replace('-','')+'/index.qmd']=render_page(issue)
    for p in (ROOT/'content/issues').glob('*.json'):
        data=json.loads(p.read_text(encoding='utf-8'))
        if data.get('status') == 'demo': outputs['issues/'+data['date'].replace('-','')+'/index.qmd']=render_page(data)
    for slug,data in collections():
        errors += validate_collection(data)
        outputs['history/'+slug+'/index.qmd']=render_collection(data)
    values=entries(issues)
    outputs.update(catalog_outputs(issues, values))
    stale = stale_catalog_pages(outputs)
    if check:
        errors += ['遗留分页文件：' + str(p.relative_to(ROOT)) for p in stale]
    if errors: raise ValueError('\n'.join(sorted(set(errors))))
    for path in stale:
        # 仅删除已确认归本生成器所有的过期分页源文件及其本地 HTML。
        rendered = ROOT / '_site' / path.relative_to(ROOT).with_suffix('.html')
        for target in (path, rendered):
            if not target.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError('生成文件路径越界')
            if target.exists(): target.unlink()
    for name,text in outputs.items():
        p=ROOT/name
        if not p.exists() or p.read_text(encoding='utf-8') != text:
            if check: errors.append('生成文件已过期：'+name)
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
    if errors:raise ValueError('\n'.join(errors))
    print('PASS: 网页内容、历史引用、原短版及生成一致性；'+str(len(values))+' 个唯一索引条目')
    return outputs
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    build(parser.parse_args().check)
