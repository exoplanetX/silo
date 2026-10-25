'use strict';

/* Bounded TeX-to-MathML reader for the notation actually used in L0016.
 * This is a text parser, with no HTML, macro expansion, eval or network access. */
(function () {
  const escape = value => String(value).replace(/[&<>"']/g, c =>
    ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const symbols = {
    alpha:'α', beta:'β', gamma:'γ', delta:'δ', theta:'θ', lambda:'λ', mu:'μ',
    pi:'π', rho:'ρ', sigma:'σ', omega:'ω', ell:'ℓ', epsilon:'ε', tau:'τ',
    Sigma:'Σ', Delta:'Δ', sum:'∑', prod:'∏', infty:'∞',
    leq:'≤', le:'≤', geq:'≥', ge:'≥', neq:'≠', in:'∈', notin:'∉',
    times:'×', cdot:'·', pm:'±', to:'→', implies:'⇒', forall:'∀',
    approx:'≈', partial:'∂', nabla:'∇', vert:'|',
  };
  const operators = new Set(['min','max','sin','cos','log','det','exp']);
  const element = (name, content, attributes='') =>
    '<' + name + attributes + '>' + content + '</' + name + '>';
  const row = children => element('mrow', children.join(''));

  class Parser {
    constructor(source) {
      if (source.length > 4096) throw new Error('公式超过本地阅读长度限制');
      this.tokens = source.match(/\\[A-Za-z]+|\\.|[0-9]+(?:\.[0-9]+)?|[^\s]/gu) || [];
      this.position = 0;
      this.depth = 0;
    }
    take() { return this.tokens[this.position++]; }
    peek() { return this.tokens[this.position]; }
    group() {
      if (this.peek() !== '{') return this.atom();
      this.take();
      if (++this.depth > 32) throw new Error('公式嵌套过深');
      const result = this.sequence(new Set(['}']));
      if (this.take() !== '}') throw new Error('分组没有闭合');
      this.depth--;
      return result;
    }
    literalGroup() {
      if (this.take() !== '{') throw new Error('需要带花括号的名称');
      const text = [];
      while (this.peek() && this.peek() !== '}') text.push(this.take());
      if (this.take() !== '}') throw new Error('名称没有闭合');
      return text.join('');
    }
    matrix() {
      const name = this.literalGroup();
      if (!['pmatrix','bmatrix','matrix','vmatrix'].includes(name)) {
        throw new Error('暂未支持的环境 ' + name);
      }
      const rows = [];
      let cells = [];
      while (this.peek() && this.peek() !== '\\end') {
        cells.push(element('mtd', this.sequence(new Set(['&', '\\\\', '\\end']))));
        if (this.peek() === '&') { this.take(); continue; }
        rows.push(element('mtr', cells.join('')));
        cells = [];
        if (this.peek() === '\\\\') this.take();
      }
      if (this.take() !== '\\end' || this.literalGroup() !== name) {
        throw new Error('矩阵环境没有正确闭合');
      }
      const table = element('mtable', rows.join(''));
      const brackets = {pmatrix:['(',')'], bmatrix:['[',']'], vmatrix:['|','|']};
      if (!brackets[name]) return table;
      return row([element('mo', brackets[name][0], ' stretchy="true"'), table,
        element('mo', brackets[name][1], ' stretchy="true"')]);
    }
    atom() {
      const token = this.take();
      if (!token) throw new Error('公式缺少操作数');
      if (token === '{') { this.position--; return this.group(); }
      if (['}', '_', '^', '&', '\\\\'].includes(token)) throw new Error('意外的分隔符');
      if (/^\d/.test(token)) return element('mn', escape(token));
      if (token === '\\begin') return this.matrix();
      if (token === '\\frac' || token === '\\dfrac' || token === '\\tfrac') {
        return element('mfrac', this.group() + this.group());
      }
      if (token === '\\sqrt') return element('msqrt', this.group());
      if (['\\text','\\mathrm','\\mathbf','\\operatorname'].includes(token)) {
        return element(token === '\\text' ? 'mtext' : 'mi', escape(this.literalGroup()),
          ' mathvariant="' + (token === '\\mathbf' ? 'bold' : 'normal') + '"');
      }
      if (['\\left','\\right'].includes(token)) {
        const bracket = this.take();
        return bracket === '.' ? '' : element('mo', escape(bracket), ' stretchy="true"');
      }
      if (['\\quad','\\qquad','\\,','\\;','\\:','\\!','\\ '].includes(token)) {
        return '<mspace width="' + (token === '\\qquad' ? '1.4' : '.4') + 'em"/>';
      }
      if (token.startsWith('\\')) {
        const name = token.slice(1);
        if (operators.has(name)) return element('mo', name, ' movablelimits="true"');
        if (symbols[name]) {
          return element(/^[α-ωℓ]$/u.test(symbols[name]) ? 'mi' : 'mo', symbols[name]);
        }
        if (['{','}','|','%','_'].includes(name)) return element('mo', escape(name));
        throw new Error('暂未支持的语法 ' + token);
      }
      return element(/^[\p{L}]$/u.test(token) ? 'mi' : 'mo', escape(token));
    }
    scripted() {
      let base = this.atom();
      let sub = null, sup = null;
      while (this.peek() === '_' || this.peek() === '^' || this.peek() === "'") {
        const script = this.take();
        if (script === "'") {
          sup = row([sup || '', element('mo', '′')]);
        } else if (script === '_') {
          if (sub !== null) throw new Error('下标重复');
          sub = this.group();
        } else {
          if (sup !== null) throw new Error('上标重复');
          sup = this.group();
        }
      }
      if (sub !== null && sup !== null) base = element('msubsup', base + sub + sup);
      else if (sub !== null) base = element('msub', base + sub);
      else if (sup !== null) base = element('msup', base + sup);
      return base;
    }
    sequence(stops=new Set()) {
      const children = [];
      while (this.peek() && !stops.has(this.peek())) {
        if (this.peek() === '/') {
          this.take();
          if (!children.length) throw new Error('分式缺少分子');
          children.push(element('mfrac', children.pop() + this.scripted()));
        } else children.push(this.scripted());
      }
      return row(children);
    }
    parse() {
      const result = this.sequence();
      if (this.position !== this.tokens.length) throw new Error('公式未完整读取');
      return result;
    }
  }
  function render(source, display=false) {
    try {
      const body = new Parser(source).parse();
      return '<math xmlns="http://www.w3.org/1998/Math/MathML" display="' +
        (display ? 'block' : 'inline') + '" aria-label="' + escape(source) +
        '"><semantics>' + body + '<annotation encoding="application/x-tex">' +
        escape(source) + '</annotation></semantics></math>';
    } catch (error) {
      return '<span class="math-fallback" role="note">公式原文（' + escape(error.message) +
        '）：<code>' + escape(source) + '</code></span>';
    }
  }
  const api = {render};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.SiloMath = api;
})();
