'use strict';

/* Fixed teaching algebra only. The model data and eta inputs come from L0016. */
(function () {
  const escape = value => String(value).replace(/[&<>"']/g, c =>
    ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const gcd = (a,b) => b === 0n ? (a < 0n ? -a : a) : gcd(b,a % b);
  function fraction(value) {
    if (value && typeof value.n === 'bigint') return value;
    const text = String(value);
    if (!/^-?\d+(?:\/\d+)?$/.test(text) || text.length > 50) {
      throw new Error('Only small rational teaching data are accepted');
    }
    const [n,d='1'] = text.split('/');
    return rational(BigInt(n),BigInt(d));
  }
  function rational(n,d) {
    if (d === 0n) throw new Error('Zero teaching denominator');
    if (d < 0n) {n=-n;d=-d;}
    const divisor=gcd(n,d);
    return {n:n/divisor,d:d/divisor};
  }
  const add=(x,y)=>{x=fraction(x);y=fraction(y);return rational(x.n*y.d+y.n*x.d,x.d*y.d);};
  const neg=x=>{x=fraction(x);return rational(-x.n,x.d);};
  const sub=(x,y)=>add(x,neg(y));
  const mul=(x,y)=>{x=fraction(x);y=fraction(y);return rational(x.n*y.n,x.d*y.d);};
  const div=(x,y)=>{x=fraction(x);y=fraction(y);return rational(x.n*y.d,x.d*y.n);};
  const leq=(x,y)=>sub(x,y).n<=0n;
  const string=x=>{x=fraction(x);return x.d===1n?String(x.n):String(x.n)+'/'+String(x.d);};
  const vector=v=>'('+v.map(string).join(', ')+')';
  const transpose=a=>a[0].map((_,j)=>a.map(row=>row[j]));
  const mv=(a,v)=>a.map(row=>row.reduce((sum,x,j)=>add(sum,mul(x,v[j])),fraction(0)));
  function solve2(a,b) {
    const [[p,q],[r,s]]=a;
    const determinant=sub(mul(p,s),mul(q,r));
    return [div(sub(mul(s,b[0]),mul(q,b[1])),determinant),
      div(sub(mul(p,b[1]),mul(r,b[0])),determinant)];
  }
  const mm=(a,b)=>a.map(row=>transpose(b).map(column=>
    row.reduce((sum,x,j)=>add(sum,mul(x,column[j])),fraction(0))));
  function etaCalculation(data, transposed=false, wrong=false) {
    const basis=mm(data.e1,data.e2);
    const rhs=transposed?data.transpose_rhs:data.ordinary_rhs;
    let order=transposed?[transpose(data.e2),transpose(data.e1)]:[data.e1,data.e2];
    if(wrong)order=order.slice().reverse();
    const middle=solve2(order[0],rhs), answer=solve2(order[1],middle);
    const original=transposed?transpose(basis):basis;
    const product=mv(original,answer);
    return {basis:basis.map(row=>row.map(string)), rhs:rhs.map(string),
      middle:middle.map(string), answer:answer.map(string),
      product:product.map(string), residual:product.map((x,i)=>string(sub(x,rhs[i])))};
  }
  function previousPoint(scenarios,index) {
    if(index===0)return null;
    const point=scenarios[index-1].point.map(fraction), current=scenarios[index];
    const reasons=[];
    if(!leq(add(add(point[0],point[1]),point[2]),current.rhs))reasons.push('违反当前主行');
    if(!leq(point[1],current.y_upper))reasons.push('违反新的 y 上界');
    if(current.x_row_upper!==null&&!leq(point[0],current.x_row_upper))reasons.push('违反新增 x 行');
    return {feasible:reasons.length===0,reasons};
  }
  const math=(source,display=false)=>window.SiloMath.render(source,display);
  const matrixTex=a=>'\\begin{pmatrix}'+a.map(row=>row.join('&')).join('\\\\')+'\\end{pmatrix}';
  const vectorTex=v=>'\\begin{pmatrix}'+v.join('\\\\')+'\\end{pmatrix}';
  function scenarioHTML(outline,index) {
    const item=outline.scenarios[index],previous=previousPoint(outline.scenarios,index);
    const strategies=[
      '先建立当前模型、基与数值分解，再核验原空间可行性和最优性。',
      '若基矩阵、坐标和尺度不变，可复用 LU/eta；解新右端，重算基本值，必要时进行对偶推进。',
      '界变化可能改变 offset、补界行或标准化；先检查身份，再决定复用，更新恢复关系与当前结果。',
      '追加行改变维度：可尝试语义基扩展，数值因子需要重新构造，随后核对完整状态。',
      '旧点配 z=0 仍可行；基矩阵不变时可复用分解，对新列定价并重建最优性依据。',
    ];
    const activeZ=item.z_upper!==null;
    let constraints='x+y'+(activeZ?'+z':'')+'\\leq '+item.rhs+
      ',\\quad 0\\leq x\\leq 2,\\quad 0\\leq y\\leq '+item.y_upper;
    if(item.x_row_upper!==null)constraints+=',\\quad x\\leq '+item.x_row_upper;
    if(activeZ)constraints+=',\\quad 0\\leq z\\leq '+item.z_upper;
    return '<div class="demo-heading"><div><span class="eyebrow">MODEL CONTINUITY</span>'+
      '<h3>同一个模型，连续修改四次</h3></div><span class="chip good">固定小例 · 精确有理数</span></div>'+
      '<div class="scenario-tabs" role="group" aria-label="选择连续模型状态">'+outline.scenarios.map((s,i)=>
        '<button class="button small '+(index===i?'primary':'')+'" data-scenario="'+i+
        '" aria-pressed="'+(index===i)+'">'+s.id+'</button>').join('')+'</div>'+
      '<div class="scenario-current"><strong>'+escape(item.id+' · '+item.edit)+'</strong>'+
      math('\\min\\ 3-x-2y'+(activeZ?'-3z':''),true)+math(constraints,true)+'</div>'+
      '<div class="demo-grid"><div><span class="field-label">当前一组最优点</span>'+
      math('(x,y,z)='+vector(item.point),true)+'</div><div><span class="field-label">当前最优目标</span>'+
      '<strong class="demo-value">'+math(item.objective)+'</strong></div></div>'+
      '<div class="scenario-reason"><strong>上一步最优点是否仍可行？</strong><p>'+
      (previous?(previous.feasible?'仍可行。S3 的点保留 z=0，满足新模型；新列可能改善目标。':
        '已不可行：'+escape(previous.reasons.join('；'))+'。'):'S0 是初始模型，尚无前一步答案。')+
      '</p><strong>哪些对象可复用，哪些必须重算？</strong><p>'+strategies[index]+'</p></div>'+
      '<div class="demo-controls"><button class="button small" data-scenario="'+Math.max(0,index-1)+'"'+
      (index===0?' disabled':'')+'>上一步</button><span>状态 '+index+' / 4 · 修改逐项累积</span>'+
      '<button class="button small" data-scenario="'+Math.min(4,index+1)+'"'+(index===4?' disabled':'')+
      '>下一步</button></div><p class="demo-note">'+escape(outline.scenario_note)+
      ' 本演示不推断真实算法采用的换基轨迹。</p>';
  }
  function etaHTML(data,transposed=false,wrong=false) {
    const result=etaCalculation(data,transposed,wrong);
    const order=transposed?(wrong?['E_1^{-T}','E_2^{-T}']:['E_2^{-T}','E_1^{-T}']):
      (wrong?['E_2^{-1}','E_1^{-1}']:['E_1^{-1}','E_2^{-1}']);
    return '<div class="demo-heading"><div><span class="eyebrow">ETA UPDATE ORDER</span>'+
      '<h3>两次不交换更新：顺序为何重要</h3></div><span class="chip '+(wrong?'stale':'good')+'">'+
      (wrong?'错误顺序对照':'正确顺序')+'</span></div>'+
      '<div class="toolbar"><label>方程 <select id="eta-mode" aria-label="eta 求解模式">'+
      '<option value="ordinary"'+(!transposed?' selected':'')+'>普通求解 B₂t=b</option>'+
      '<option value="transpose"'+(transposed?' selected':'')+'>转置求解 B₂ᵀt=b</option></select></label>'+
      '<label class="check-label"><input type="checkbox" id="eta-wrong"'+(wrong?' checked':'')+
      '>对照错误顺序</label></div>'+
      '<div class="eta-matrices">'+math('E_1='+matrixTex(data.e1),true)+
      math('E_2='+matrixTex(data.e2),true)+math('B_2=E_1E_2='+matrixTex(result.basis),true)+'</div>'+
      '<div class="eta-steps"><div><span>右端 b</span>'+math(vectorTex(result.rhs),true)+'</div>'+
      '<div><span>① 应用 '+math(order[0])+'</span>'+math(vectorTex(result.middle),true)+'</div>'+
      '<div><span>② 应用 '+math(order[1])+'</span>'+math('t='+vectorTex(result.answer),true)+'</div></div>'+
      '<div class="eta-residual '+(wrong?'wrong':'')+'"><strong>'+
      (wrong?'错误结果：不满足原方程':'代回当前方程检查')+'</strong>'+
      math((transposed?'B_2^T':'B_2')+'t-b='+vectorTex(result.residual),true)+'</div>'+
      '<p class="demo-note">数据读取 L0016-E03；中间向量和残差由固定 2×2 有理运算产生。'+
      '普通与转置求解分别遵守各自顺序，不调用 solver。</p>';
  }
  function hero(data,h) {
    const meta=data.metadata;
    return '<div class="lesson-hero"><a class="link-button" href="#learning">← 返回伴学目录</a>'+
      '<span class="eyebrow">L0016 / RELIABLE SOLVER</span><h1>'+h.esc(data.outline.title)+'</h1>'+
      '<p>从原问题、数值状态、终止依据到计算成本，沿八个单元理解可靠求解器的实现。</p>'+
      '<div class="lesson-identity"><span>讲解 v'+h.esc(meta.version)+'</span><span>实际核对 '+
      h.esc(meta.verified_on)+'</span><span>代码 <code>'+h.esc(meta.verified_code)+'</code></span>'+
      '<span>'+h.esc(meta.status)+'</span></div></div>';
  }
  function render(data,view,h) {
    const base='#learning/L0016';
    const nav='<aside class="lesson-nav" aria-label="八单元导航"><a href="'+base+
      '" class="lesson-nav-top">专题概览与全文</a>'+data.outline.modules.map(m=>'<a href="'+base+'/'+m.id+
      '" class="'+(view.unit===m.id?'active':'')+'"><span>'+m.id+'</span>'+h.esc(m.heading.slice(4))+
      '</a>').join('')+'<a href="#evaluation">关联：八维评价 →</a></aside>';
    const tabs='<div class="tab-buttons lesson-tabs" role="group" aria-label="专题阅读视图">'+
      [['body','完整正文'],['exercises','练习'],['solutions','解答']].map(([id,label])=>
        '<button data-lesson-tab="'+id+'" class="'+(view.tab===id?'active':'')+
        '" aria-pressed="'+(view.tab===id)+'">'+label+'</button>').join('')+'</div>';
    let content;
    if(view.tab==='solutions') {
      content='<div class="notice">按题号主动展开解答，建议先完成对应练习。</div>'+
        data.documents.solutions.text.split(/(?=^## L0016-E)/m).slice(1).map(part=>{
          const line=part.split('\n')[0].replace(/^## /,'').trim();
          return '<details class="answer"><summary>'+h.esc(line)+' · 展开解答</summary><div class="prose">'+
            h.markdown(part.split('\n').slice(1).join('\n'),data.documents.solutions.path)+'</div></details>';
        }).join('');
    } else {
      let body=h.markdown(data.documents[view.tab].text,data.documents[view.tab].path);
      if(view.tab==='body') {
        body=body.replace(/(<h2 id="lesson-section-3">[^<]+<\/h2>)/,
          '$1<section class="panel teaching-demo" id="scenario-demo">'+
          scenarioHTML(data.outline,view.scenario)+'</section>');
        body=body.replace(/(<h3 id="unit-R03">[^<]+<\/h3>)/,
          '$1<section class="panel teaching-demo" id="eta-demo">'+
          etaHTML(data.eta,view.transpose,view.wrong)+'</section>');
      }
      content='<article class="prose lesson-prose">'+body+'</article>';
    }
    let related='';
    if(view.unit) {
      const unit=data.outline.modules.find(m=>m.id===view.unit);
      const paths=unit.related_lessons.map(id=>h.lessons.find(l=>l.lesson_id===id)?.path).filter(Boolean);
      related='<div class="lesson-related"><strong>'+h.esc(unit.heading)+' · 继续深读</strong>'+
        h.sourceChips(paths)+'</div>';
    }
    return hero(data,h)+tabs+'<div class="lesson-layout">'+nav+'<div class="lesson-content">'+related+
      content+
      '<section class="lesson-sources"><h2>规范正文与代码来源</h2>'+
      h.sourceChips(Object.values(data.documents).map(doc=>doc.path))+
      '<p class="subtle">网页只读展示规范文件；打开日期不改变教学核对日期。原文模式可查看完整来源。</p>'+
      '</section></div></div>';
  }
  const api={etaCalculation,previousPoint,scenarioHTML,etaHTML,render};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof window!=='undefined')window.SiloReliability=api;
})();
