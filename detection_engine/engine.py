from __future__ import annotations
from datetime import datetime, timezone
from collections import defaultdict
from detection_engine.rules import run_all_rules, RuleHit
CATEGORY_META = {'DP-1':{'category':'Misdirection','explanation':''},'DP-2':{'category':'Hidden Costs','explanation':''},'DP-3':{'category':'Confirmshaming','explanation':''},'DP-4':{'category':'Disguised Ads','explanation':''},'DP-5':{'category':'Forced Continuity','explanation':''},'DP-6':{'category':'Urgency / Scarcity','explanation':''}}
SEVERITY_RANK = {'high':3,'medium':2,'low':1}

def _deduplicate(hits):
    seen=set();out=[]
    for h in hits:
        k=(h.category_id,h.evidence[:60].lower().strip())
        if k not in seen: seen.add(k);out.append(h)
    return out
def _overall_risk(f):
    if not f: return 'none'
    h=sum(1 for x in f if x['severity']=='high')
    return 'high' if h>=2 else 'medium' if h==1 or len(f)>=2 else 'low'
def _avg_conf(hits): return round(sum(h.confidence for h in hits)/len(hits),2) if hits else 0.0
def analyse(page):
    rule_hits=run_all_rules(page); ml_hits=[]
    try:
        from detection_engine.classifier import get_classifier
        clf=get_classifier()
        if clf.available:
            snippets=[b['text'] for b in page.buttons if len(b.get('text',''))>5]+[s.strip() for s in page.visible_text.split('.') if 8<len(s.strip())<200][:80]
            for pred in clf.predict(snippets):
                label=str(pred['label']); meta=CATEGORY_META.get(label,{})
                ml_hits.append(RuleHit(category_id=label,category=meta.get('category',label),severity='medium',evidence=f'"{str(pred["text"])[:120]}"',location='ML classifier',rule='ml_classifier',confidence=float(pred['confidence'])))
    except: pass
    all_hits=_deduplicate(rule_hits+ml_hits)
    by_cat=defaultdict(list)
    for h in all_hits: by_cat[str(h.category_id)].append(h)
    findings=[]
    for cat_id,hits in by_cat.items():
        meta=CATEGORY_META.get(cat_id,{})
        sev=max((h.severity for h in hits),key=lambda s:SEVERITY_RANK.get(s,0),default='low')
        findings.append({'id':str(cat_id),'category':meta.get('category',cat_id),'severity':sev,'count':len(hits),'instances':[{
            'evidence':   str(h.evidence),
            'location':   str(h.location),
            'rule':       str(h.rule),
            'confidence': round(float(h.confidence), 2),
            'severity':   str(h.severity),
        } for h in hits[:5]],'explanation':meta.get('explanation','')})
    findings.sort(key=lambda f:(-SEVERITY_RANK.get(f['severity'],0),-f['count']))
    return {'url':page.url,'analysed_at':datetime.now(timezone.utc).isoformat(),'total_found':len(findings),'overall_risk':_overall_risk(findings),'confidence':_avg_conf(all_hits),'categories_checked':6,'findings':findings}
