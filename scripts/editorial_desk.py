"""连续编辑台账：私有事件为真源，当前视图可重建；不自动判断学术质量或发布。"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, os
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from issue_dates import review_date, item_evaluation_date
from conference_policy import conference_window, conference_publication_kind

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

def publication_moment(issue, publication, item=None):
    """Use actual online evidence for backfills; leave ordinary history unchanged."""
    if item and 'website_addition' in item:
        # 原期次 proof 只证明原页面，不能把后来新增会议倒记为旧日已发布。
        return None, 'website-addition-needs-separate-publication-proof'
    if 'backfill' not in issue:
        return issue['date'], 'historical-issue-date'
    actual_day = review_date(issue)
    if publication.get('status') != 'published' or not publication.get('commit'):
        return None, 'unverified-backfill'
    if any(publication.get(field) is not None and publication[field] != issue['date'] for field in ('date', 'issue_date')):
        return None, 'mismatched-issue-proof'
    for field in ('published_at', 'verified_at'):
        value = publication.get(field)
        if not isinstance(value, str):
            continue
        try:
            moment = datetime.fromisoformat(value)
            if moment.tzinfo is None or moment.astimezone(TZ).date() < actual_day:
                continue
            if moment > datetime.now(TZ):
                continue
        except ValueError:
            continue
        return moment.astimezone(TZ).isoformat(), 'actual-publication' if field == 'published_at' else 'actual-online-verification'
    return None, 'unverified-backfill'

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
            elif e['kind']=='observation':
                # HTTP 成功、部分筛选和未映射线索均可留痕；不冒充完整覆盖。
                row = state['sources'].setdefault(e['source_id'], {})
                row['last_observation'] = e
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
                for field in ('gap','next_action','owner'):
                    if field in e:state['candidates'][e['key']][field]=e[field]
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
            published_at, timestamp_basis = publication_moment(issue, publication)
            candidate_at = review_date(issue).isoformat() if 'backfill' in issue else day
            for category in CATEGORIES:
                for item in issue.get(category,[]):
                    item_at=item_evaluation_date(issue,item).isoformat() if 'website_addition' in item else candidate_at
                    item_published_at,item_timestamp_basis=publication_moment(issue,publication,item)
                    first=item.get('first_discovered_date',item.get('added_date',item_at)) if 'website_addition' in item else item.get('added_date',candidate_at)
                    key=identity(item,category)
                    self.emit(dict(kind='candidate',at=item_at,order=0,key=key,candidate=dict(id=item['id'],category=category,payload=item,status='needs-review',first_discovered=first,provenance=str(p.relative_to(self.root)))))
                    if item_published_at is not None:
                        event = dict(kind='publication',at=item_published_at,order=2,key=key,issue_date=day,website_record=True,live_verified=publication.get('status')=='published',commit=publication.get('commit'),wechat_generated=item.get('priority')=='core' and (self.root/'publish/wechat'/f'{day}.txt').exists(),wechat_sent='unknown')
                        if 'backfill' in issue:
                            event['timestamp_basis'] = item_timestamp_basis
                        self.emit(event)
            for category, field in [('journal','journal_checks'),('working-paper','working_paper_checks')]:
                for row in issue.get('paper_review',{}).get(field,[]):
                    effective=row.get('fallback',row) if row.get('status')=='access-failed' else row
                    # 保留原日期、原候选与原出处；导入旧成功记录不表示重新核验。
                    # 有界轮查或显式未完成只保留尝试，不能推进整段成功终点。
                    complete = effective['status'] in ('found','no-eligible') and bool(effective.get('complete',True) and effective.get('exhaustive',True))
                    self.emit(dict(kind='check',at=effective['checked_at'],source_id=category+':'+slug(row['source']),status=effective['status'],complete=complete,window_start=effective['window_start'],window_end=effective['window_end'],candidate_ids=effective['candidate_ids'],evidence_url=effective['evidence_url'],reason=effective['reason'],provenance='historical-record',original_failure=row if row.get('status')=='access-failed' else None))
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

    def plan(self,day,output_path=None):
        today=date.fromisoformat(day);s=self.rebuild();tasks=[]
        registry=self.registry()
        source_ids={row['id'] for row in registry}
        legacy=read(self.root/'config/source-registry.yml').get('conference_sources',[])
        def candidate_sources(candidate):
            payload=candidate['payload'];review=payload.get('review',{})
            matched=set()
            for source_id in (candidate.get('source_id'),payload.get('source_id'),review.get('source_id')):
                if source_id in source_ids:matched.add(source_id)
                elif source_id and 'conference:'+source_id in source_ids:matched.add('conference:'+source_id)
            urls={payload.get(k) for k in ('official_url','source_url')}|{review.get('source_url')}
            urls.discard(None)
            matched.update(row['id'] for row in registry if row['category'] in ('conferences','conference_calls') and row['url'] in urls)
            matched.update(row['editorial_source_id'] for row in legacy if row.get('editorial_source_id') in source_ids
                           and (row.get('official_entry') in urls or row.get('original_official_entry') in urls))
            return matched
        conference_queue=[]
        active_sources=set()
        for key,c in s['candidates'].items():
            if c.get('category')!='conference_calls' or c.get('status') in ('excluded','expired'):continue
            window=conference_window(c['payload'],day)
            if (c.get('status')!='published' and window['actionable'] is not False) or window['actionable'] is True or c.get('follow_up_needed') is True:
                # 已刊仍开放者也须跟踪正式变更；精确已登记 ID/URL/映射，不按标题或域名猜品牌。
                active_sources.update(candidate_sources(c))
            if c.get('status')=='published':
                # 已刊身份不重新成为普通候选；只提示有真实发布事实的提醒比较。
                facts=[p for p in s['publications'] if p['key']==key]
                reminded=any(p.get('publication_type')=='deadline-reminder' or p.get('payload_snapshot',{}).get('reminder') is True for p in facts)
                if not facts or reminded or conference_publication_kind(c['payload'])!='initial' or not (window['actionable'] is True and 0 < window['days_remaining'] <= 5):continue
                first_days=[]
                for fact in facts:
                    if fact.get('publication_scope')=='website-supplement':
                        actual_day=None
                        for field in ('website_first_published_at','at'):
                            try:
                                actual=datetime.fromisoformat(fact[field])
                                if actual.tzinfo is None:continue
                                actual_day=actual.astimezone(TZ).date();break
                            except (KeyError,TypeError,ValueError):continue
                        first_days.append(actual_day)
                    else:
                        # 普通旧记录保留原口径；网站补充不能退回承载页日期。
                        first_days.append(date.fromisoformat(fact.get('issue_date',fact['at'][:10])))
                if any(day is None for day in first_days):continue
                first=min(first_days)
                initial=conference_window(c['payload'],first.isoformat())
                if initial['days_remaining'] is not None and initial['days_remaining']<=5:continue
                action='compare-one-reminder'
            elif window['actionable'] is False:
                action='resolve-expiry-or-status-change'
            else:
                action='review-candidate'
            conference_queue.append(dict(key=key,id=c['id'],source_id=c.get('source_id'),title=c['payload']['title'],
                source_ids=sorted(candidate_sources(c)),
                candidate_status=c.get('status'),action=action,**window,
                owner=c.get('owner') or c.get('decision',{}).get('reviewed_by'),
                unresolved=c.get('status') not in ('ready','published'),
                candidate_next_action=c.get('next_action') or c.get('decision',{}).get('next_action')))
        for src in registry:
            source_state=s['sources'].get(src['id'],{})
            last=source_state.get('last_success')
            observed=source_state.get('last_observation')
            age=(today-date.fromisoformat(last['window_end'])).days if last else None
            due=age is None or age<0 or age>=src['interval_days']
            action='check' if due else 'reuse'
            if src['category'] in ('conferences','conference_calls'):
                weekdays=src.get('review_weekdays',['mon','thu'])
                full=today.strftime('%a').lower() in weekdays
                incremental=bool(src.get('daily_incremental') or src['id'] in active_sources)
                # 一次实际完整筛选可完成当日轮查；有界观察仍保留待办。
                checked_today=bool(last and last['at'][:10]==day and last['window_end']==day)
                due=(full or incremental) and not checked_today
                action=('full-review' if full else 'incremental-follow-up') if due else ('reuse' if checked_today else 'scheduled-full-review')
            tasks.append(dict(source_id=src['id'],category=src['category'],url=src['url'],due=due,last_success=last['at'] if last else None,action=action,priority=src.get('priority','standard'),entry_status=src.get('entry_status','unverified'),
                last_observation=observed['at'] if observed else None,
                observation_stage=observed.get('stage') if observed else None,
                next_action=observed.get('next_action') if observed else None))
        pool=[]
        for key,c in s['candidates'].items():
            if c['status'] in ('published','excluded','expired'):continue
            parts=c.get('metadata',{}).get('published-online',{}).get('date-parts',[[]])[0]
            age=(today-date(*parts)).days if len(parts)==3 else None
            category=c.get('category','papers')
            window=conference_window(c['payload'],day) if category=='conference_calls' else None
            pool.append(dict(key=key,id=c['id'],category=category,title=c['payload']['title'],status=c['status'],age_days=age,
                eligible_window=window['actionable'] if window else age is not None and 0<=age<=30,
                **({'conference_window':window} if window else {})))
        priority={'lianxh_posts':0,'conference_calls':1,'papers':2,'tools':2,'research_resources':2}
        pool.sort(key=lambda row:(priority.get(row['category'],3),row['id']))
        conference_queue.sort(key=lambda row:(row['days_remaining'] is None,row['days_remaining'] if row['days_remaining'] is not None else 99999,row['id']))
        ct=[t for t in tasks if t['category'] in ('conferences','conference_calls')]
        summary=dict(due_sources=sum(t['due'] for t in ct),source_stage_counts={stage:sum((t['observation_stage'] or 'not-observed')==stage for t in ct) for stage in sorted({t['observation_stage'] or 'not-observed' for t in ct})},
            unresolved_soon_deadline=sum(row['unresolved'] and row['days_remaining'] is not None and 0<=row['days_remaining']<=5 for row in conference_queue),
            unresolved_unknown=sum(row['unresolved'] and row['actionable'] is None for row in conference_queue))
        result=dict(date=day,tasks=tasks,candidates=pool,conference_summary=summary,conference_action_queue=conference_queue,
            note='候选未核验不等于合格；会议按有效投稿/报名窗口比较，不套用公告14/30天窗口；此计划不自动选稿，统一audit/build仍为shadow')
        write(Path(output_path) if output_path else self.root/'ops-local/runs'/day/'editorial-plan.json',result)
        return result

    def observe(self,e):
        """Retain real raw/partial observations without fabricated candidates or coverage."""
        required=('source_id','at','stage','evidence_path','reason','next_action')
        if any(not e.get(k) for k in required):raise ValueError('观察记录字段不全')
        if e['source_id'] not in {r['id'] for r in self.registry()}:raise ValueError('来源未登记')
        if e['stage'] not in ('fetched','awaiting-screen','partial-screen','unmapped-findings','access-failed'):raise ValueError('非法观察阶段')
        if e.get('complete',False) is not False:raise ValueError('观察不能宣称完整覆盖')
        if 'candidate_ids' in e or e.get('status') in ('found','no-eligible'):raise ValueError('观察不代填候选或无合格结论')
        observed=datetime.fromisoformat(e['at'])
        if observed.tzinfo is None or observed>datetime.now(TZ):raise ValueError('观察时点须有真实时区且不能为未来')
        path=(self.root/e['evidence_path']).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():raise ValueError('缺少项目内实际观察证据')
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if e.get('sha256') and e['sha256']!=sha:raise ValueError('观察证据指纹不一致')
        self.emit(dict(e,kind='observation',complete=False,sha256=sha));return self.rebuild()

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
            self.observe(dict(source_id=source_id,at=datetime.now(TZ).isoformat(),stage='awaiting-screen',
                evidence_path=result['evidence_path'],sha256=result['sha256'],reason='已抓取原始页面，尚未完成编辑筛选',next_action='读取实际通知并登记线索；按真实边界记录筛选覆盖'))
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
        first=record.get('first_discovered',day)
        if date.fromisoformat(first)>date.fromisoformat(day):raise ValueError('首次发现不能晚于本次登记')
        if first!=day:
            old_path=(self.root/record.get('first_discovered_evidence_path','')).resolve()
            if not old_path.is_relative_to(self.root.resolve()) or not old_path.is_file() or not record.get('first_discovered_basis'):
                raise ValueError('保留较早发现日期须有历史证据和日期依据')
            if hashlib.sha256(old_path.read_bytes()).hexdigest()!=record.get('first_discovered_evidence_sha256'):
                raise ValueError('首次发现历史证据指纹不一致')
        retained={k:record[k] for k in ('first_discovered_evidence_path','first_discovered_evidence_sha256','first_discovered_basis','next_action','owner','gap') if k in record}
        self.emit(dict(kind='candidate',at=record['at'],key=key,candidate=dict(id=payload['id'],category=category,payload=payload,status='needs-review',first_discovered=first,source_id=record['source_id'],provenance=record['evidence_path'],**retained)))
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
        decision=dict(record,kind='decision',order=1)
        if record['status']=='ready':
            decision.setdefault('gap',None)
            decision.setdefault('next_action','审核合格，待编辑比较与编排')
            decision.setdefault('owner',record['reviewed_by'])
        self.emit(decision);return self.rebuild()

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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['migrate','plan','record','observe','fetch','decide','ingest','audit','build']);p.add_argument('--date',default=datetime.now(TZ).date().isoformat());p.add_argument('--input',type=Path);p.add_argument('--source');p.add_argument('--review',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();desk=Desk()
    if a.command=='migrate':s=desk.migrate();result={k:len(v) for k,v in s.items()}
    elif a.command=='plan':result=desk.plan(a.date,a.output);result=dict(date=a.date,due=sum(t['due'] for t in result['tasks']),candidates=len(result['candidates']),conference_summary=result['conference_summary'])
    elif a.command=='fetch':result=desk.fetch(a.source,a.date)
    elif a.command=='ingest':
        if not a.input:p.error('--input required')
        result=desk.ingest(read(a.input))
    elif a.command in ('record','observe','decide'):
        if not a.input:p.error('--input required')
        result=getattr(desk,'check' if a.command=='record' else a.command)(read(a.input));result={k:len(v) for k,v in result.items()}
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
