"""连续编辑台账：私有事件为真源，当前视图可重建；不自动判断学术质量或发布。"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, os
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ('lianxh_posts', 'papers', 'tools', 'research_resources', 'conference_calls')
TZ = timezone(timedelta(hours=8))

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def write(p, data):
    # 先写临时文件，再原子替换，避免中断留下半份 JSON。
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    tmp.replace(p)

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def identity(item, category='papers'):
    # 不从全段文本提取 DOI：参考文献和轮查候选不是已发布成果。
    doi = item.get('doi_url', '').lower().removeprefix('https://doi.org/')
    if doi:
        if 'arxiv.' in doi: doi = re.sub(r'v\d+$', '', doi)
        return 'doi:'+doi
    if category == 'tools':
        return 'software:'+item.get('ecosystem','unknown').lower()+':'+item.get('name',item['id']).lower()
    if category == 'conference_calls': return 'event:'+item.get('event_id',item['id'])
    return category+':'+item['id']

@contextmanager
def command_lock(root):
    # 操作系统文件锁在崩溃后自动释放，不以遗留 lock 文件判断仍在执行。
    p=Path(root)/'ops-local/editorial/.lock';p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a+b') as handle:
        handle.seek(0,2)
        if handle.tell()==0:handle.write(b'0');handle.flush()
        handle.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:yield
        finally:
            handle.seek(0)
            if os.name=='nt':msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(handle,fcntl.LOCK_UN)

class Desk:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.base = self.root/'ops-local/editorial'
        self.events = self.base/'events'

    def emit(self, event):
        # 相同历史事实只存一次；事件写成功后才重建当前状态。
        raw = json.dumps(event, ensure_ascii=False, sort_keys=True).encode()
        key = hashlib.sha256(raw).hexdigest()
        p = self.events/(key+'.json')
        if not p.exists(): write(p,event)
        return key

    def rebuild(self):
        state = dict(sources={},candidates={},publications=[])
        events = [read(p) for p in sorted(self.events.glob('*.json'))]
        for e in sorted(events,key=lambda e:(e['at'],e.get('order',0))):
            if e['kind']=='check':
                row = state['sources'].setdefault(e['source_id'],{})
                row['last_attempt']=e
                # 失败、仅快照或分页不完整均不能推进成功覆盖。
                if e['status'] in ('found','no-eligible') and e.get('complete'):
                    row['last_success']=e
            elif e['kind']=='candidate':
                old=state['candidates'].get(e['key'],{})
                incoming=dict(e['candidate'])
                if old.get('first_discovered'):
                    incoming['first_discovered']=min(old['first_discovered'],incoming.get('first_discovered',old['first_discovered']))
                if old.get('payload',{}).get('page_note') and not incoming.get('payload',{}).get('page_note'):
                    incoming['payload']=old['payload']
                state['candidates'][e['key']]={**old,**incoming}
            elif e['kind']=='decision':
                if e['key'] not in state['candidates']: raise ValueError('候选不存在')
                state['candidates'][e['key']].update(status=e['status'],decision=e)
            elif e['kind']=='publication':
                state['publications'].append(e)
                if e['key'] in state['candidates']:
                    state['candidates'][e['key']].update(status='published')
        # 后来的候选重导入不能把已发布事实变回待选。
        for e in state['publications']:
            if e['key'] in state['candidates']:state['candidates'][e['key']]['status']='published'
        write(self.base/'state.json',state)
        return state

    def migrate(self):
        for p in sorted((self.root/'content/issues').glob('*.json')):
            issue=read(p)
            if issue.get('status')!='published':continue
            day=issue['date']; proof=self.root/'ops-local/runs'/day/'publication.json'
            publication=read(proof) if proof.exists() else {}
            for category in CATEGORIES:
                for item in issue.get(category,[]):
                    key=identity(item,category)
                    self.emit(dict(kind='candidate',at=day,order=0,key=key,candidate=dict(id=item['id'],category=category,payload=item,status='needs-review',first_discovered=item.get('added_date',day),provenance=str(p.relative_to(self.root)))))
                    self.emit(dict(kind='publication',at=day,order=2,key=key,issue_date=day,website_record=True,live_verified=publication.get('status')=='published',commit=publication.get('commit'),wechat_generated=item.get('priority')=='core' and (self.root/'publish/wechat'/f'{day}.txt').exists(),wechat_sent='unknown'))
            for category, field in [('journal','journal_checks'),('working-paper','working_paper_checks')]:
                for row in issue.get('paper_review',{}).get(field,[]):
                    effective=row.get('fallback',row) if row.get('status')=='access-failed' else row
                    # 保留原日期、原候选与原出处；导入旧成功记录不表示重新核验。
                    self.emit(dict(kind='check',at=effective['checked_at'],source_id=category+':'+slug(row['source']),status=effective['status'],complete=effective['status'] in ('found','no-eligible'),window_start=effective['window_start'],window_end=effective['window_end'],candidate_ids=effective['candidate_ids'],evidence_url=effective['evidence_url'],reason=effective['reason'],provenance='historical-record',original_failure=row if row.get('status')=='access-failed' else None))
        # 未采用候选只从真实缓存元数据导入，绝不直接升为合格。
        for p in sorted((self.root/'ops-local/runs').glob('*/journals/*.json')):
            data=read(p)
            if not isinstance(data,dict):continue
            for m in data.get('message',{}).get('items',[]):
                if m.get('type')!='journal-article' or not m.get('DOI'):continue
                payload=dict(id='candidate-'+slug(m['DOI']),doi_url='https://doi.org/'+m['DOI'],title=m.get('title',[''])[0])
                key=identity(payload)
                self.emit(dict(kind='candidate',at=p.parents[1].name,order=0,key=key,candidate=dict(id=payload['id'],category='papers',payload=payload,metadata=m,status='needs-review',first_discovered=p.parents[1].name,provenance=str(p.relative_to(self.root)))))
        return self.rebuild()

    def registry(self):
        return read(self.root/'config/source-registry.yml')['editorial_sources']

    def plan(self,day):
        today=date.fromisoformat(day);s=self.rebuild();tasks=[]
        for src in self.registry():
            last=s['sources'].get(src['id'],{}).get('last_success')
            age=(today-date.fromisoformat(last['window_end'])).days if last else None
            due=age is None or age<0 or age>=src['interval_days']
            tasks.append(dict(source_id=src['id'],category=src['category'],url=src['url'],due=due,last_success=last['at'] if last else None,action='check' if due else 'reuse',priority=src.get('priority','standard'),entry_status=src.get('entry_status','unverified')))
        pool=[]
        for key,c in s['candidates'].items():
            if c['status'] in ('published','excluded','expired'):continue
            parts=c.get('metadata',{}).get('published-online',{}).get('date-parts',[[]])[0]
            age=(today-date(*parts)).days if len(parts)==3 else None
            pool.append(dict(key=key,id=c['id'],title=c['payload']['title'],status=c['status'],age_days=age,eligible_window=age is not None and 0<=age<=30))
        result=dict(date=day,tasks=tasks,candidates=pool,note='候选未核验不等于合格；超过14天须有遗漏理由，超过30天不作为普通新闻')
        write(self.root/'ops-local/runs'/day/'editorial-plan.json',result)
        return result

    def check(self,e):
        required=('source_id','at','status','complete','window_start','window_end','candidate_ids','reason','evidence_path')
        if any(k not in e for k in required):raise ValueError('检查记录字段不全')
        if e['source_id'] not in {r['id'] for r in self.registry()}:raise ValueError('来源未登记')
        if e['status'] not in ('found','no-eligible','access-failed','not-searched'):raise ValueError('非法状态')
        start=date.fromisoformat(e['window_start']);end=date.fromisoformat(e['window_end'])
        checked=date.fromisoformat(e['at'][:10])
        if not start<=end<=checked<=datetime.now(TZ).date():raise ValueError('无效覆盖日期')
        path=(self.root/e['evidence_path']).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():raise ValueError('缺少项目内实际证据文件')
        if not isinstance(e['candidate_ids'],list) or not e['reason']:raise ValueError('缺少候选或说明')
        if e['status']=='found' and not e['candidate_ids']:raise ValueError('found 必须有候选')
        if e['status']=='no-eligible' and e['candidate_ids']:raise ValueError('无合格记录须将被排除候选放 screened_ids，并说明原因')
        if e['status'] in ('access-failed','not-searched') and e['complete']:raise ValueError('失败不能推进覆盖')
        self.emit(dict(e,kind='check'));return self.rebuild()

    def fetch(self,source_id,day):
        # 只抓取原始证据，网页200不自动变成已完成编辑筛选。
        src=next(r for r in self.registry() if r['id']==source_id)
        stamp=datetime.now(TZ).strftime('%Y%m%d-%H%M%S-%f')
        p=self.root/'ops-local/runs'/day/'sources'/f'{slug(source_id)}-{stamp}.html'
        p.parent.mkdir(parents=True,exist_ok=True)
        try:
            with urlopen(Request(src['url'],headers={'User-Agent':'LianxhBrief/1.0'}),timeout=30) as response:
                raw=response.read(8_000_001)
                if len(raw)>8_000_000:raise ValueError('页面超过8MB，未宣称完整覆盖')
                p.write_bytes(raw)
            result=dict(source_id=source_id,status='awaiting-screen',evidence_path=str(p.relative_to(self.root)),sha256=hashlib.sha256(raw).hexdigest())
        except Exception as exc:
            p.write_text(str(exc),encoding='utf-8')
            self.check(dict(source_id=source_id,at=datetime.now(TZ).isoformat(),status='access-failed',complete=False,window_start=day,window_end=day,candidate_ids=[],reason=str(exc),evidence_path=str(p.relative_to(self.root))))
            result=dict(source_id=source_id,status='access-failed',evidence_path=str(p.relative_to(self.root)))
        write(p.with_suffix('.json'),result);return result

    def ingest(self,record):
        category=record.get('category')
        payload=record.get('payload',{})
        if category not in CATEGORIES or not payload.get('id') or not payload.get('title'):
            raise ValueError('新增候选缺少category、id或title')
        path=(self.root/record.get('evidence_path','')).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():raise ValueError('缺少候选原始证据')
        if not record.get('source_id') in {r['id'] for r in self.registry()}:raise ValueError('未知来源')
        key=identity(payload,category)
        old=self.rebuild()['candidates'].get(key)
        if old:return {'key':key,'status':old['status'],'action':'already-known; use decide for reviewed changes'}
        day=record['at'][:10]
        if date.fromisoformat(day)>datetime.now(TZ).date():raise ValueError('发现日期不能为未来')
        self.emit(dict(kind='candidate',at=record['at'],key=key,candidate=dict(id=payload['id'],category=category,payload=payload,status='needs-review',first_discovered=day,source_id=record['source_id'],provenance=record['evidence_path'])))
        self.rebuild();return {'key':key,'status':'needs-review'}

    def decide(self,record):
        s=self.rebuild();key=record['key']
        if key not in s['candidates']:raise ValueError('候选不存在')
        if record['status'] not in ('ready','deferred','excluded','expired'):raise ValueError('非法候选状态')
        if not record.get('reason') or not record.get('reviewed_by'):raise ValueError('缺少审核依据')
        payload=record.get('payload')
        if record['status']=='ready':
            if not isinstance(payload,dict):raise ValueError('合格候选须提供完整payload')
            if identity(payload,s['candidates'][key]['category'])!=key:raise ValueError('成果身份不一致')
            from validate_issue import validate_item
            errors=[];validate_item(payload,s['candidates'][key]['category'],Path('candidate'),errors)
            if errors:raise ValueError('\n'.join(errors))
            self.emit(dict(kind='candidate',at=record['at'],order=0,key=key,candidate={**s['candidates'][key],'payload':payload}))
        self.emit(dict(record,kind='decision',order=1));return self.rebuild()

    def audit(self,day,issue,review):
        plan=self.plan(day);errors=[]
        if review.get('date')!=day or issue.get('date')!=day:errors.append('审核目标日期不一致')
        for t in plan['tasks']:
            if t['due']:errors.append('缺少有效覆盖：'+t['source_id'])
        comparisons=review.get('priority_comparison')
        if not review.get('reviewed_by') or not isinstance(comparisons,list) or not comparisons:
            errors.append('缺少重要期刊候选比较')
        elif any(not isinstance(x,dict) or not x.get('key') or not x.get('reason') or x.get('decision') not in ('select','defer','exclude') for x in comparisons):
            errors.append('候选比较必须逐项给出key、decision和reason')
        else:
            pool=self.rebuild()['candidates']
            if any(x['key'] not in pool for x in comparisons):errors.append('比较记录引用未知候选')
        items=[(c,x) for c in CATEGORIES for x in issue.get(c,[])]
        state=self.rebuild()
        for category,item in items:
            key=identity(item,category);candidate=state['candidates'].get(key)
            if not candidate or candidate['status']!='ready':errors.append('候选尚未审核合格：'+item['id'])
            elif {k:v for k,v in item.items() if k!='priority'}!={k:v for k,v in candidate['payload'].items() if k!='priority'}:
                errors.append('当期内容与审核payload不一致：'+item['id'])
            if any(p['key']==key for p in state['publications']):errors.append('已有发布记录，须人工核验更新例外：'+item['id'])
        if not items:errors.append('没有当期条目')
        if items and all(c=='papers' for c,x in items) and not review.get('all_papers_reason'):errors.append('全论文期次缺少额外复核')
        result=dict(date=day,errors=errors,passed=not errors,review=review)
        write(self.root/'ops-local/runs'/day/'editorial-audit.json',result)
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['migrate','plan','record','fetch','decide','ingest','audit','build']);p.add_argument('--date',default=datetime.now(TZ).date().isoformat());p.add_argument('--input',type=Path);p.add_argument('--source');p.add_argument('--review',type=Path)
    a=p.parse_args();desk=Desk()
    if a.command=='migrate':s=desk.migrate();result={k:len(v) for k,v in s.items()}
    elif a.command=='plan':result=desk.plan(a.date);result=dict(date=a.date,due=sum(t['due'] for t in result['tasks']),candidates=len(result['candidates']))
    elif a.command=='fetch':result=desk.fetch(a.source,a.date)
    elif a.command=='ingest':
        if not a.input:p.error('--input required')
        result=desk.ingest(read(a.input))
    elif a.command in ('record','decide'):
        if not a.input:p.error('--input required')
        result=getattr(desk,'check' if a.command=='record' else 'decide')(read(a.input));result={k:len(v) for k,v in result.items()}
    else:
        if not a.input or not a.review:p.error('--input issue.json --review review.json required')
        issue=read(a.input);result=desk.audit(a.date,issue,read(a.review))
        if a.command=='build' and result['passed']:
            from validate_issue import validate_schema,validate_history
            from render_wechat import render_daily
            errors=[];validate_schema(issue,a.input,errors);validate_history(issue,a.input,ROOT/'content/issues',errors)
            if errors:raise ValueError('\n'.join(errors))
            out=ROOT/'ops-local/runs'/a.date;write(out/'draft.json',issue);(out/(a.date+'.txt')).write_text(render_daily(issue),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result.get('errors') else 0

if __name__=='__main__':
    with command_lock(ROOT):sys.exit(main())
