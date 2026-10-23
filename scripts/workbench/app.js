'use strict';

const $ = (selector) => document.querySelector(selector);
const names = {overview:'开发总览',goals:'目标与阶段',evaluation:'求解器评价',evidence:'任务与证据',learning:'开发伴学',delivery:'版本与交付'};
const english = {overview:'PROJECT OVERVIEW',goals:'GOALS & MILESTONES',evaluation:'SOLVER EVALUATION',evidence:'TASKS & EVIDENCE',learning:'LEARN WITH THE CODE',delivery:'VERSIONS & DELIVERY'};
const view = {evaluation:'dimensions', capability:'all', taskQuery:'', taskFilter:'all', taskLimit:35, lessonQuery:'', lessonOrder:'development'};
let state = null;
let busy = false;
let changes = [];
let selectedDocument = null;
let rawReader = false;
let selection = null;
let contextEvidence = '';
const documentCache = new Map();

function esc(value) {return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function clean(value) {return String(value ?? '').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[*`]/g,'');}
function shortHash(value) {return value ? String(value).slice(0,7) : '未登记';}
function when(value) {return value ? new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date(value)) : '未登记';}
function route() {return Object.hasOwn(names,location.hash.slice(1)) ? location.hash.slice(1) : 'overview';}
function chip(text,tone='muted') {return '<span class="chip '+esc(tone)+'">'+esc(text)+'</span>';}
function reviewed(item) {return item.needs_review ? chip('来源变化 · 待复核','stale') : '';}
function sourceButton(path,label) {return '<button class="source-link" data-doc="'+esc(path)+'">'+esc(label || path)+' ↗</button>';}
function sourceChips(paths) {return '<div class="source-chips">'+[...new Set(paths || [])].map(path=>'<button data-doc="'+esc(path)+'">'+esc(path.split('/').pop())+' ↗</button>').join('')+'</div>';}
function askButton(kind,id,label='与 Codex 讨论',className='button small') {return '<button class="'+className+'" data-ask="'+esc(kind)+'" data-id="'+esc(id)+'">'+esc(label)+'</button>';}
function header(page,description) {return '<div class="page-heading"><div><span class="eyebrow">'+english[page]+'</span><h1>'+names[page]+'</h1><p class="subtitle">'+esc(description)+'</p></div>'+askButton('page',page,'生成讨论上下文','button primary page-action')+'</div>';}
function section(title,note='',button='') {return '<div class="section-heading"><h2>'+esc(title)+'</h2><span>'+esc(note)+'</span>'+button+'</div>';}
function metric(label,value,note) {return '<div class="panel metric"><span class="metric-label">'+esc(label)+'</span><strong class="metric-value">'+esc(value)+'</strong><span class="metric-note">'+esc(note)+'</span></div>';}
function notice() {
  if(!state.warnings.length) return '';
  return '<div class="notice">有 '+state.warnings.length+' 项已登记来源发生变化或缺失。相关初始判断需重新核对，详情可在版本页查看。'+sourceChips(state.warnings.map(x=>x.path))+'</div>';
}
function unitFlow() {
  return '<div class="panel flow">'+state.units.map(unit=>'<div class="flow-step '+esc(unit.tone)+'"><span class="step-letter">'+unit.id+'</span><h3>'+esc(unit.title)+'</h3>'+chip(unit.status,unit.tone)+'<p>'+esc(unit.milestone)+' · '+(unit.needs_review?'来源待复核':'按已记录边界')+'</p>'+askButton('unit',unit.id,'查看依据与缺口','link-button')+'</div>').join('')+'</div>';
}
function pageOverview() {
  const unitC = state.units.find(x=>x.id==='C');
  const stage = clean(state.profile['Phase 9']) || '状态未读取';
  const hold = unitC.needs_review;
  const lessonCount=state.lessons.length;
  return header('overview','在一个地方看清当前能力、目标覆盖与下一道证据门槛。')+notice()+
    '<div class="grid four">'+metric('当前项目定位','教学型参考求解器','代码 '+state.version+' · 科研能力逐项评价')+metric('工程阶段','Phase 9',stage)+metric('研究推进',hold?'C · 待复核':'C · HOLD','A / B 已验收；D / E 未启动 · '+state.snapshot_date+' 整理')+metric('开发伴学',lessonCount+' 篇资料','按实际代码基线核对，支持主题学习')+'</div>'+
    '<div class="hold-panel"><div class="hold-main">'+chip(hold?'来源变化 · 请核对原记录':'当前研究门槛 · HOLD','hold')+'<h2>先补齐应用证据，再讨论增量机制。</h2><p>'+esc(unitC.description)+' 当前记录是签发前就绪性判断，真实应用假设与原研究问题保持开放。</p></div><div class="hold-side"><strong>尚缺的联合证据</strong><ul><li>同域、完整且可核验的应用精确定价</li><li>真实 root-CG 对偶与状态轨迹</li><li>强冷 / 直接动态对照及完整成本依据</li></ul><button class="link-button" data-doc="docs/bounded_goal_outcome_20261020.md">阅读停止记录与门槛依据 ↗</button></div></div>'+
    section('有界推进 · A — E','最多五项；当前到达预设停止点')+unitFlow()+
    '<div class="grid two">'+
      '<section class="panel pad">'+section('八维评价概览','','<a class="link-button" href="#evaluation">进入完整评价 →</a>')+state.dimensions.map(d=>'<div class="dimension-mini"><span>'+esc(d.name)+'</span>'+chip(d.needs_review?'待复核':d.status,d.needs_review?'stale':d.tone)+'</div>').join('')+'</section>'+
      '<section class="panel pad">'+section('最近变化与待决策')+(changes.length ? '<div class="notice fresh">'+changes.map(esc).join('<br>')+'</div>' : '<p class="subtle">本次读取未发现与上次浏览相比的新增变化。首次浏览从当前快照开始记录。</p>')+
      '<div class="list-row"><strong>研究下一步</strong><small>原 5 联合证据仍缺；恢复执行须先明确有限核验方案及相应授权。</small></div><div class="list-row"><strong>已有记录与本轮运行分别展示</strong><small>历史测试结果见原报告；刷新工作台只读取资料，不运行测试。</small></div><div class="list-row"><strong>本地 Git</strong><small>'+esc(state.git.branch || '未知分支')+' · '+shortHash(state.git.head)+' · 缓存远端 ahead '+esc(state.git.ahead ?? '未知')+' / behind '+esc(state.git.behind ?? '未知')+'</small></div>'+askButton('unit','C','解释当前门槛','button small')+'</section>'+
    '</div>'+
    section('原目标始终可见','目标完成依据验收条件，不按任务数量折算')+'<div class="panel pad"><ul class="boundary-list">'+state.boundaries.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'+sourceChips(['.silo-dos/project_profile.md','docs/seven_step_completion_plan_20261020.md'])+'</div>';
}

function pageGoals() {
  const stale=state.warnings.some(x=>['.silo-dos/project_profile.md','docs/bounded_goal_outcome_20261020.md'].includes(x.path));
  return header('goals','原研究里程碑、工程阶段和当前合同各有自己的完成线。')+notice()+unitFlow()+
    section('原三阶段 · 七个研究里程碑','当前映射整理于 '+state.snapshot_date+(stale?' · 来源待复核':''))+
    '<div class="detail-grid"><div class="route-line">'+state.milestones.map(m=>'<div class="milestone-row '+(m.status==='HOLD'?'hold':m.status==='未启动'?'muted':'')+'"><div class="row-title"><h3><span class="kicker">'+esc(m.id)+'</span>　'+esc(m.title)+'</h3>'+chip(stale?'待复核':m.status,stale?'stale':m.status==='HOLD'?'hold':m.status==='未启动'?'muted':'good')+'</div><p>'+esc(m.detail)+'</p></div>').join('')+'</div><div class="panel pad"><h2>结束边界</h2><ul class="boundary-list">'+state.boundaries.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'+sourceChips(['docs/seven_step_completion_plan_20261020.md','docs/bounded_goal_outcome_20261020.md'])+'<div class="section-heading"><h2>单元 C 的结束线</h2></div><p class="subtle">C 为 HOLD 已结束本轮自动推进；原 5 仍未通过，原 6 / 7 保持未完成。新增工作应明确对原计划和预算的影响。</p>'+askButton('unit','C','整理需要决定的问题')+'</div></div>'+
    section('运行预算与终态','预算来自固定计划；尚未运行时保留该状态')+'<div class="panel table-wrap"><table><thead><tr><th>工作单元</th><th>执行上限</th><th>已记录终态</th></tr></thead><tbody>'+state.budgets.map(b=>'<tr><td>'+esc(b.name)+'</td><td>'+esc(b.limit)+'</td><td>'+esc(b.state)+sourceButton(b.source,'预算依据')+'</td></tr>').join('')+'</tbody></table><div class="budget-note">负面结果、超限与暂停均需保留；预算限制本轮工作，研究完成标准保持原样。</div></div>'+
    section('工程路线 · ROADMAP','完成状态限于各阶段已批准的保守范围')+'<div class="phase-list">'+state.phases.map(p=>'<div class="phase-item"><span class="mono">PHASE '+p.number+'</span><div><strong>'+esc(p.title)+'</strong><p>'+esc(p.number===9?clean(state.profile['Phase 9'] || '状态以当前摘要为准'):p.status)+'</p></div></div>').join('')+'<div class="phase-item"><span class="mono">PHASE 10</span><div><strong>未来阶段</strong><p>'+esc(clean(state.profile['Phase 10'] || '未登记'))+'</p></div></div></div>'+sourceChips(['ROADMAP.md','.silo-dos/project_profile.md']);
}

function pageEvaluation() {
  const options='<option value="all">全部能力</option>'+state.capabilities.map(c=>'<option value="'+esc(c.id)+'"'+(view.capability===c.id?' selected':'')+'>'+esc(c.name)+'</option>').join('');
  const cards=state.dimensions.map(d=>'<section class="panel dimension-card"><div class="panel-heading"><h3>'+esc(d.name)+'</h3>'+chip(d.needs_review?'待复核':d.status,d.needs_review?'stale':d.tone)+'</div><span class="subtle">'+esc(d.question)+'</span><p>'+esc(d.conclusion)+'</p><div class="criterion"><strong>仍缺什么</strong><br>'+esc(d.gap)+'<br><br><strong>通过标准</strong><br>'+esc(d.criterion)+'</div>'+sourceChips(d.sources)+askButton('dimension',d.id,'展开依据并讨论','link-button')+'</section>').join('');
  const caps=state.capabilities.filter(c=>view.capability==='all'||view.capability===c.id);
  const rows=caps.map(c=>'<tr><td><span class="matrix-title">'+esc(c.name)+'</span><div class="maturity" aria-label="建议成熟度：'+esc(c.level)+'">'+[0,1,2,3].map(n=>'<span class="'+(n<=c.maturity?'on':'')+'"></span>').join('')+'</div><small>'+esc(c.needs_review?'来源变化，等级待复核':c.level)+'</small></td><td>'+esc(c.scope)+'</td><td>'+esc(c.limit)+sourceChips(c.sources)+'</td><td>'+reviewed(c)+askButton('capability',c.id,'查看档案','button small')+'</td></tr>').join('');
  const matrix='<div class="toolbar"><select id="capability-filter" aria-label="选择评价能力">'+options+'</select><span class="subtle">能力等级为初始整理，按支持域与原证据解读。</span></div><div class="panel table-wrap"><table><thead><tr><th>能力与建议定位</th><th>实际支持范围</th><th>局限与证据</th><th>操作</th></tr></thead><tbody>'+rows+'</tbody></table><div class="matrix-legend"><span>01 原理演示</span><span>02 经核验的参考实现</span><span>03 代表性问题验证</span><span>04 指定环境可靠使用</span></div></div>';
  const performance='<div class="panel pad"><div class="panel-heading"><h2>规模与性能基准</h2>'+chip('尚无完整评价','muted')+'</div><p class="subtle">现有小实例核验与测试运行时间保留在报告中。规模、竞争力和端到端收益需要独立计算基准。</p><div class="table-wrap"><table><thead><tr><th>需要冻结</th><th>需要报告</th><th>当前证据</th></tr></thead><tbody><tr><td>实例身份、模型、硬件与环境</td><td>成功求解数量、失败、超时与输出核验</td><td>未形成完整规模基准</td></tr><tr><td>强基线、配置与同等预算</td><td>端到端耗时、峰值内存与最优性差距</td><td>未评价</td></tr><tr><td>维护机制、初始化与回退策略</td><td>建立、定位、核验、恢复、重建和 RMP 成本</td><td>E 未启动</td></tr></tbody></table></div>'+sourceChips(['docs/seven_step_completion_plan_20261020.md','.silo-dos/project_profile.md'])+'</div>';
  return header('evaluation','按八个维度观察能力与证据；每项结论都保留适用范围。')+notice()+'<div class="notice fresh">'+esc(state.assessment_note)+'</div><div class="tab-buttons" role="group" aria-label="评价视图">'+[['dimensions','八维评价'],['capabilities','能力成熟度'],['performance','计算基准']].map(([id,label])=>'<button data-eval-tab="'+id+'" aria-pressed="'+(view.evaluation===id)+'" class="'+(view.evaluation===id?'active':'')+'">'+label+'</button>').join('')+'</div>'+(view.evaluation==='dimensions'?'<div class="grid two">'+cards+'</div>':view.evaluation==='capabilities'?matrix:performance);
}

function filteredTasks() {
  const query=view.taskQuery.toLowerCase();
  return state.tasks.filter(t=>(t.id+' '+t.title).toLowerCase().includes(query)&&(view.taskFilter==='all'||(view.taskFilter==='report'?t.report:!t.report)));
}
function taskResults() {
  const items=filteredTasks();
  if(!items.length) return '<div class="panel empty">没有匹配的任务。可尝试任务编号、日期或关键词。</div>';
  return '<div class="panel table-wrap"><table><thead><tr><th>合同与任务</th><th>记录状态</th><th>来源</th><th>讨论</th></tr></thead><tbody>'+items.slice(0,view.taskLimit).map(t=>'<tr><td><span class="matrix-title">'+esc(t.title)+'</span><small class="mono">'+esc(t.id)+'</small></td><td>'+chip(t.report?'有同名报告':'无同名报告',t.report?'good':'muted')+'<small>存在报告仅表示有记录</small></td><td>'+sourceButton(t.path,'阅读合同')+(t.report?sourceButton(t.report,'阅读执行报告'):'')+'</td><td>'+askButton('task',t.id,'核查此任务','button small')+'</td></tr>').join('')+'</tbody></table></div><div class="section-heading"><span>显示 '+Math.min(view.taskLimit,items.length)+' / '+items.length+' 项</span>'+(items.length>view.taskLimit?'<button class="button small" id="more-tasks">显示更多记录</button>':'')+'</div>';
}
function pageEvidence() {
  return header('evidence','沿合同、执行记录和验收决定追溯；报告存在与验收通过分别判断。')+
    '<div class="grid three">'+metric('任务合同',String(state.tasks.length),'按完整路径区分任务身份')+metric('同名执行报告',String(state.tasks.filter(t=>t.report).length),'资料清点，不表示成功或验收')+metric('状态与验收入口','当前项目摘要','历史建议须结合当前来源判断')+'</div>'+section('合同与报告','','<button class="link-button" data-doc=".silo-dos/project_profile.md">当前状态依据 ↗</button>')+
    '<div class="toolbar"><input id="task-search" class="input search" placeholder="搜索任务编号、日期、标题…" aria-label="搜索任务" value="'+esc(view.taskQuery)+'"><select id="task-filter" aria-label="筛选记录状态"><option value="all">全部记录</option><option value="report"'+(view.taskFilter==='report'?' selected':'')+'>有同名报告</option><option value="missing"'+(view.taskFilter==='missing'?' selected':'')+'>无同名报告</option></select></div><div id="task-results">'+taskResults()+'</div>'+sourceChips(['tasks/README.md','docs/bounded_goal_outcome_20261020.md']);
}

function lessonResults() {
  let lessons=state.lessons.filter(l=>(l.lesson_id+' '+l.title+' '+l.topic).toLowerCase().includes(view.lessonQuery.toLowerCase()));
  if(view.lessonOrder==='topic') lessons=lessons.slice().sort((a,b)=>a.topic.localeCompare(b.topic));
  if(!lessons.length) return '<div class="panel empty">没有匹配篇目。可尝试“对偶”“定价”“CG”或 L0001。</div>';
  return '<div class="grid three">'+lessons.map(l=>'<section class="panel lesson-card"><div class="panel-heading"><span class="lesson-id">'+esc(l.lesson_id)+'</span>'+chip(l.status==='checked'?'按记录已核对':l.status || '待核对',l.status==='checked'?'good':'muted')+'</div><h3>'+esc(l.title)+'</h3><div class="lesson-meta">讲解版本 '+esc(l.version || '未登记')+' · 核验日期 '+esc(l.verified_on || '未登记')+'<br>代码基线 <span class="mono">'+shortHash(l.verified_code)+'</span><br>'+esc(l.topic || '')+'</div><div class="lesson-actions"><button class="button small primary" data-doc="'+esc(l.path)+'">开始阅读</button>'+(l.exercises?'<button class="button small" data-doc="'+esc(l.path.replace('README.md','exercises.md'))+'">练习</button>':'')+(l.solutions?'<button class="button small" data-doc="'+esc(l.path.replace('README.md','solutions.md'))+'">解答</button>':'')+'</div>'+askButton('lesson',l.lesson_id,'请 Codex 讲解这一篇','source-link')+'</section>').join('')+'</div>';
}
function pageLearning() {
  return header('learning','沿“手算 → 推导 → 代码 → 核验 → 练习”学习，正文始终来自 learning。')+
    '<div class="notice fresh">当前有 '+state.lessons.length+' 篇伴学资料。checked 表示按所记录基线核对，篇目数量不用于计算求解器成熟度。</div><div class="toolbar"><input id="lesson-search" class="input search" placeholder="搜索主题、标题或篇目 ID…" aria-label="搜索伴学资料" value="'+esc(view.lessonQuery)+'"><select id="lesson-order" aria-label="学习资料排序"><option value="development">按开发顺序</option><option value="topic"'+(view.lessonOrder==='topic'?' selected':'')+'>按主题分组排序</option></select><button class="button small" data-doc="learning/CATALOG.md">查看学习路线</button></div><div id="lesson-results">'+lessonResults()+'</div>';
}

function pageDelivery() {
  return header('delivery','代码、流程、教学与研究基线分别追溯，共享一个正式源码内核。')+notice()+
    '<div class="grid four">'+metric('代码版本',state.version,'开发中 · Unreleased')+metric('当前分支',state.git.branch || '不可用',shortHash(state.git.head))+metric('缓存远端差异','↑ '+(state.git.ahead ?? '?')+'　↓ '+(state.git.behind ?? '?'),'只读本地引用；未 fetch')+metric('工作台整理日期',state.snapshot_date,'来源变动时提示重新核对')+'</div>'+section('交付准备')+'<div class="grid two">'+state.delivery.map(d=>'<section class="panel readiness"><div class="panel-heading"><h3>'+esc(d.name)+'</h3>'+chip(d.needs_review?'待复核':d.status,d.needs_review?'stale':d.tone)+'</div><p>'+esc(d.detail)+'</p>'+sourceChips(d.sources)+askButton('delivery',d.id,'核查交付条件','link-button')+'</section>').join('')+'</div>'+
    section('最近代码与文档提交','读取当前本地 Git 日志')+'<div class="grid two"><div class="panel pad">'+(state.git.recent.length?state.git.recent.map(c=>'<div class="commit-row"><span class="mono">'+esc(c.hash)+'</span><div>'+esc(c.subject)+'<small>'+esc(c.date)+'</small></div></div>').join(''):'<p class="subtle">Git 日志不可用。</p>')+'</div><div class="panel pad"><h2>工作副本与同步依据</h2><p class="subtle">'+esc(state.git.remote_basis)+'<br>核对时间 '+when(state.git.checked_at)+'</p><pre class="source-raw">'+esc(state.git.working_tree===null?'Git 状态不可用':state.git.working_tree || '工作副本干净')+'</pre>'+sourceChips(['docs/development_layout.md','.silo-dos/remote_sync_proof.md'])+'</div></div>'+
    section('来源新鲜度','SHA-256 与首版整理基线逐项比较')+'<div class="panel table-wrap"><table><thead><tr><th>来源文件</th><th>当前状态</th><th>当前摘要</th></tr></thead><tbody>'+state.sources.map(s=>'<tr><td>'+sourceButton(s.path)+'</td><td>'+chip(s.state==='available'?'与整理基线一致':s.state==='changed'?'已变化 · 待复核':'缺失',s.state==='available'?'good':'stale')+'</td><td class="mono">'+esc(s.sha256? s.sha256.slice(0,16)+'…':s.error)+'</td></tr>').join('')+'</tbody></table></div>';
}

const pages={overview:pageOverview,goals:pageGoals,evaluation:pageEvaluation,evidence:pageEvidence,learning:pageLearning,delivery:pageDelivery};
function render() {
  if(!state) return;
  const page=route();
  $('#loading').hidden=true;
  $('#app').innerHTML=pages[page]();
  $('#breadcrumb').textContent=names[page];
  document.title=names[page]+' · SILO 开发工作台';
  document.querySelectorAll('[data-page]').forEach(a=>{a.classList.toggle('active',a.dataset.page===page); if(a.dataset.page===page)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('#sidebar-version').textContent='SILO '+state.version+' · 开发中';
  $('#updated').textContent='资料读取 '+when(state.generated_at)+'（北京时间）';
}
function toast(text) {$('#toast').textContent=text;$('#toast').classList.add('show');setTimeout(()=>$('#toast').classList.remove('show'),3200);}
async function refresh(manual=false) {
  if(busy)return;
  busy=true;$('#refresh').disabled=true;
  try {
    const response=await fetch('/api/state',{cache:'no-store'});
    if(!response.ok) throw new Error('资料读取失败：HTTP '+response.status);
    const next=await response.json();
    const key='silo-workbench:'+next.repository;
    const detected=[];
    try {
      const previous=JSON.parse(localStorage.getItem(key) || 'null');
      if(previous) {
        if(previous.head!==next.git.head)detected.push('本地提交已从 '+shortHash(previous.head)+' 更新为 '+shortHash(next.git.head)+'。');
        next.sources.forEach(s=>{if(previous.hashes[s.path]!==s.sha256)detected.push('来源有变化：'+s.path);});
        if(previous.lessons!==next.lessons.length)detected.push('伴学目录现有 '+next.lessons.length+' 篇。');
        if(previous.tasks!==next.tasks.length)detected.push('任务目录现有 '+next.tasks.length+' 份合同。');
      }
      localStorage.setItem(key,JSON.stringify({head:next.git.head,hashes:Object.fromEntries(next.sources.map(s=>[s.path,s.sha256])),lessons:next.lessons.length,tasks:next.tasks.length}));
    } catch { /* Browser storage may be disabled; the live view still works. */ }
    changes=[...new Set([...changes,...detected])].slice(-10);
    state=next;documentCache.clear();render();
    if(manual)toast('已重新读取仓库资料；未运行测试。');
  } catch(error) {
    if(state){toast(error.message+'，暂保留上次资料。');$('#updated').textContent='读取失败 · 保留 '+when(state.generated_at)+' 的资料';}
    else $('#loading').textContent=error.message+'。请检查服务后点击“刷新数据”。';
  } finally {busy=false;$('#refresh').disabled=false;}
}

function normalizePath(base,path) {
  const parts=(path.startsWith('/')?path.slice(1):base.split('/').slice(0,-1).join('/')+'/'+path).split('/');
  const result=[];
  for(const part of parts){if(!part||part==='.')continue;if(part==='..')result.pop();else result.push(part);}
  return result.join('/');
}
function inline(text,base) {
  return esc(text).replace(/\[([^\]]+)\]\(([^)]+)\)/g,(_,label,target)=>{
    if(/^https?:\/\//i.test(target))return '<a href="'+target+'" target="_blank" rel="noopener noreferrer">'+label+' ↗</a>';
    if(target.startsWith('#'))return label;
    if(/^[a-z][a-z0-9+.-]*:/i.test(target))return label;
    const path=normalizePath(base,target.split('#')[0]);
    return '<button class="link-button" data-doc="'+esc(path)+'">'+label+'</button>';
  }).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
}
function markdown(text,path) {
  const lines=text.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/,'').split(/\r?\n/);
  let output='',i=0;
  const fence=/^\s*(`{3,}|~{3,})/;
  while(i<lines.length) {
    const line=lines[i];
    if(fence.test(line)) {
      const marker=line.trim()[0];const block=[];i++;
      while(i<lines.length&&!lines[i].trim().startsWith(marker.repeat(3)))block.push(lines[i++]);
      output+='<pre><code>'+esc(block.join('\n'))+'</code></pre>';i++;continue;
    }
    if(line.trim()==='\\[' || line.trim()==='$$') {
      const end=line.trim()==='\\['?'\\]':'$$';const block=[];i++;
      while(i<lines.length&&lines[i].trim()!==end)block.push(lines[i++]);
      output+='<div class="math-source" aria-label="公式 TeX 原文">'+esc(block.join('\n'))+'</div>';i++;continue;
    }
    if(/^\s*\|/.test(line)&&i+1<lines.length&&/^\s*\|?\s*:?-{3}/.test(lines[i+1])) {
      const cells=s=>s.trim().replace(/^\||\|$/g,'').split('|').map(x=>x.trim());
      output+='<div class="table-wrap"><table><thead><tr>'+cells(line).map(c=>'<th>'+inline(c,path)+'</th>').join('')+'</tr></thead><tbody>';i+=2;
      while(i<lines.length&&/^\s*\|/.test(lines[i])){output+='<tr>'+cells(lines[i++]).map(c=>'<td>'+inline(c,path)+'</td>').join('')+'</tr>';}
      output+='</tbody></table></div>';continue;
    }
    const heading=line.match(/^(#{1,6})\s+(.+)/);
    if(heading){output+='<h'+heading[1].length+'>'+inline(heading[2],path)+'</h'+heading[1].length+'>';i++;continue;}
    if(/^\s*[-*]\s+/.test(line)||/^\s*\d+\.\s+/.test(line)) {
      const ordered=/^\s*\d+\.\s+/.test(line);const tag=ordered?'ol':'ul';output+='<'+tag+'>';
      while(i<lines.length&&(/^\s*[-*]\s+/.test(lines[i])||/^\s*\d+\.\s+/.test(lines[i])))output+='<li>'+inline(lines[i++].replace(/^\s*(?:[-*]|\d+\.)\s+/,''),path)+'</li>';
      output+='</'+tag+'>';continue;
    }
    if(/^>\s?/.test(line)){output+='<blockquote>'+inline(line.replace(/^>\s?/,''),path)+'</blockquote>';i++;continue;}
    if(!line.trim()){i++;continue;}
    if(/^<!--/.test(line)){while(i<lines.length&&!lines[i].includes('-->'))i++;i++;continue;}
    const paragraph=[line];i++;
    while(i<lines.length&&lines[i].trim()&&!/^#{1,6}\s/.test(lines[i])&&!fence.test(lines[i])&&!/^\s*\|/.test(lines[i])&&!/^\s*[-*]\s+/.test(lines[i])&&!/^\s*\d+\.\s+/.test(lines[i])&&!['\\[','$$'].includes(lines[i].trim()))paragraph.push(lines[i++]);
    output+='<p>'+inline(paragraph.join('\n'),path).replace(/\n/g,'<br>')+'</p>';
  }
  return output;
}
async function getDocument(path) {
  if(documentCache.has(path))return documentCache.get(path);
  const response=await fetch('/api/document?path='+encodeURIComponent(path),{cache:'no-store'});
  const result=await response.json();if(!response.ok)throw new Error(result.error || '无法读取资料');
  documentCache.set(path,result);return result;
}
function renderReader() {
  const doc=selectedDocument;if(!doc)return;
  $('#reader-title').textContent=doc.path;
  $('#reader-meta').textContent='SHA-256 '+doc.sha256.slice(0,12)+' · 公式保留 TeX 原文';
  $('#reader-mode').textContent=rawReader?'阅读视图':'查看原文';
  $('#reader-body').innerHTML=rawReader||!doc.path.endsWith('.md')?'<pre class="source-raw">'+doc.text.split('\n').map((line,i)=>'<span class="line"><span class="line-number">'+(i+1)+'</span>'+esc(line)+'</span>').join('')+'</pre>':markdown(doc.text,doc.path);
  $('#reader').scrollTop=0;
}
async function openDocument(path) {
  try{selectedDocument=await getDocument(path);rawReader=!path.endsWith('.md');renderReader();if(!$('#reader').open)$('#reader').showModal();}
  catch(error){toast('无法打开来源：'+error.message);}
}
function selectObject(kind,id) {
  if(kind==='unit')return state.units.find(x=>x.id===id);
  if(kind==='dimension')return state.dimensions.find(x=>x.id===id);
  if(kind==='capability')return state.capabilities.find(x=>x.id===id);
  if(kind==='delivery')return state.delivery.find(x=>x.id===id);
  if(kind==='lesson'){const l=state.lessons.find(x=>x.lesson_id===id);return {...l,sources:[l.path],description:'教学篇目 '+l.lesson_id+'，讲解版本 '+l.version+'，verified_code='+l.verified_code};}
  if(kind==='task'){const t=state.tasks.find(x=>x.id===id);return {...t,sources:[t.path,...(t.report?[t.report]:[])],description:t.report?'存在同名报告；成功与验收须读依据。':'未找到同名报告；不据此推断任务状态。'};}
  if(kind==='document')return {title:id,sources:[id]};
  const sources=id==='learning'?['learning/CATALOG.md','learning/README.md']:id==='evaluation'?['.silo-dos/project_profile.md','docs/correctness_baseline.md']:['.silo-dos/project_profile.md','docs/bounded_goal_outcome_20261020.md'];
  return {title:names[id] || id,description:'当前页面讨论',sources};
}
function updateContext() {
  if(!selection)return;
  const item=selection;
  const fields=['status','level','scope','description','conclusion','gap','criterion','limit','exit','detail','verified_code'];
  const summary=fields.filter(k=>item[k]).map(k=>k+': '+item[k]).join('\n');
  $('#context-text').value='SILO 开发讨论上下文\n\n问题：'+($('#question').value.trim() || '请解释当前对象，核查证据及仍未解决的义务。')+'\n对象：'+(item.name || item.title || item.id)+'\n仓库：'+state.repository+'\n代码 HEAD：'+state.git.head+'\n资料读取：'+state.generated_at+'\n初始判断整理日期：'+state.snapshot_date+'\n\n'+summary+'\n'+(item.needs_review?'注意：来源相对整理基线已变化，结论需复核。\n':'')+'\n来源原文节选（节选未覆盖完整文档，请按需要继续读取原文件）：\n'+contextEvidence+'\n\n讨论边界：\n'+state.boundaries.map(x=>'- '+x).join('\n')+'\n- 此包用于解释/核查/规划，不自动授权执行任务、修改阶段或推送。\n- 原始来源优先；分别判断数学正确性、原目标覆盖与外部贡献。';
}
async function openContext(kind,id) {
  const item=selectObject(kind,id);if(!item)return;
  selection=item;contextEvidence='正在读取来源…';$('#question').value='';updateContext();
  if(!$('#context').open)$('#context').showModal();
  const excerpts=await Promise.all((item.sources || []).slice(0,4).map(async path=>{
    try{
      const doc=await getDocument(path);const allLines=doc.text.split('\n');
      const anchors=kind==='unit'&&id==='C'?['## C Readiness','## 3. C的准确裁决','### C：']:[];
      const found=allLines.findIndex(line=>anchors.some(anchor=>line.startsWith(anchor)));
      const start=found<0?0:found;const lines=allLines.slice(start,start+45);
      return path+'\nSHA-256: '+doc.sha256+'\n'+lines.map((line,i)=>(start+i+1)+': '+line).join('\n');
    }
    catch(error){return path+'\n来源读取失败：'+error.message;}
  }));
  if(selection!==item)return;
  contextEvidence=excerpts.join('\n\n');updateContext();
}

document.addEventListener('click',async event=>{
  const target=event.target.closest('button');if(!target)return;
  if(target.dataset.close){document.getElementById(target.dataset.close).close();return;}
  if(target.dataset.doc){await openDocument(target.dataset.doc);return;}
  if(target.dataset.ask){await openContext(target.dataset.ask,target.dataset.id);return;}
  if(target.dataset.evalTab){view.evaluation=target.dataset.evalTab;render();return;}
  if(target.id==='more-tasks'){view.taskLimit+=35;$('#task-results').innerHTML=taskResults();}
});
document.addEventListener('input',event=>{
  if(event.target.id==='task-search'){view.taskQuery=event.target.value;view.taskLimit=35;$('#task-results').innerHTML=taskResults();}
  if(event.target.id==='lesson-search'){view.lessonQuery=event.target.value;$('#lesson-results').innerHTML=lessonResults();}
});
document.addEventListener('change',event=>{
  if(event.target.id==='task-filter'){view.taskFilter=event.target.value;view.taskLimit=35;$('#task-results').innerHTML=taskResults();}
  if(event.target.id==='lesson-order'){view.lessonOrder=event.target.value;$('#lesson-results').innerHTML=lessonResults();}
  if(event.target.id==='capability-filter'){view.capability=event.target.value;render();}
});
$('#reader-mode').addEventListener('click',()=>{rawReader=!rawReader;renderReader();});
$('#reader-context').addEventListener('click',()=>openContext('document',selectedDocument.path));
$('#question').addEventListener('input',updateContext);
$('#copy-context').addEventListener('click',async()=>{
  try {await navigator.clipboard.writeText($('#context-text').value);toast('上下文包已复制，可粘贴到 Codex。');}
  catch {$('#context-text').focus();$('#context-text').select();toast('浏览器未允许自动复制；已选中文本，请按 Ctrl+C。');}
});
$('#refresh').addEventListener('click',()=>refresh(true));
window.addEventListener('hashchange',()=>{render();window.scrollTo({top:0});});
setInterval(()=>{if(!document.hidden&&!$('#reader').open&&!$('#context').open&&!['INPUT','SELECT'].includes(document.activeElement.tagName))refresh();},60000);
refresh();
