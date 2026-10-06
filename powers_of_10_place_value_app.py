"""Run: python -m pip install streamlit; python -m streamlit run powers_of_10_place_value_app.py"""
import json
import random
import re
from decimal import Decimal, localcontext
import streamlit as st
import streamlit.components.v1 as components


def calculate(text, power):
    text = text.strip()
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
        raise ValueError("Enter a decimal such as 3.141529, 0.008, or -12.5.")
    if len(text.replace('.', '').lstrip('+-')) > 30:
        raise ValueError("Please use at most 30 digits.")
    value = Decimal(text)
    with localcontext() as ctx:
        ctx.prec = 60
        result = value * Decimal(10) ** power
    return format(abs(value), 'f'), format(result, 'f'), value < 0


def random_example():
    st.session_state.number = f"{random.randint(0, 999)}." + ''.join(str(random.randrange(10)) for _ in range(random.randint(2, 8)))
    st.session_state.power = random.choice([i for i in range(-8, 9) if i])


def main():
    st.set_page_config(page_title="What moves when we multiply by 10?", layout="wide")
    st.title("Powers of 10 · What moves?")
    st.write("One calculation, two perspectives. Moving the decimal point is a notation shortcut; sliding the digits shows how their place values change.")
    st.session_state.setdefault('number', '3.141529')
    st.session_state.setdefault('power', 2)
    a, b, c = st.columns([2, 1, 1])
    text = a.text_input('Starting number', key='number')
    power = int(b.number_input('Exponent n in × 10ⁿ', min_value=-12, max_value=12, step=1, key='power'))
    c.button('🎲 Random example', on_click=random_example, use_container_width=True)
    try:
        raw, result, negative = calculate(text, power)
    except ValueError as error:
        st.error(str(error))
        return
    st.subheader(f"{text.strip()} × 10{superscript(power)} = {result}")
    payload = json.dumps(dict(raw=raw, power=power, negative=negative, result=result))
    components.html(HTML.replace('__DATA__', payload), height=690, scrolling=True)
    st.info('The decimal point marks the boundary between ones and tenths. For ×10ⁿ, each digit moves n columns left when n is positive, or |n| columns right when n is negative.')
    st.caption('Hover over a digit or a column for its place value. Blue digits come from the starting number; gray zeros are placeholders. Scroll wide charts horizontally. Negative signs describe the whole number and do not occupy a place-value column.')


def superscript(n):
    return str(n).translate(str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻'))


HTML = r'''<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;color:#17243b;font-family:system-ui,sans-serif;background:#fff}button{background:#17243b;color:white;border:0;border-radius:8px;padding:10px 16px;cursor:pointer}button.secondary{background:#eef2f7;color:#17243b}.toolbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:8px 0 16px}input{flex:1;min-width:150px;accent-color:#176bba}.cards{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{min-width:0;border:1px solid #dce3ec;border-radius:16px;padding:20px}h2{font-size:20px;margin:0 0 8px}.sub{font-size:14px;color:#536276;min-height:64px;line-height:1.5}.scroll{overflow-x:auto;background:#f5f8fc;border-radius:10px;padding:12px 0}.stage{position:relative;height:215px}.cell{position:absolute;top:10px;width:64px;height:160px;border-left:1px solid #d5dce6;text-align:center}.label{font-size:11px;padding:8px 3px;height:70px;color:#536276}.token{position:absolute;top:99px;width:64px;text-align:center;font:700 32px ui-monospace,monospace;color:#176bba;cursor:help}.zero{color:#98a4b4}.boundary{position:absolute;top:77px;height:80px;border-left:3px solid #c13e51}.dot{position:absolute;top:100px;width:20px;font:800 32px ui-monospace,monospace;color:#c13e51;text-align:center}.note{font-size:14px;line-height:1.5;margin-top:14px}.equation{font-weight:700;margin-top:14px}.badge{font-size:13px;background:#eef2f7;border-radius:6px;padding:5px 8px}#tip{position:fixed;z-index:20;pointer-events:none;background:#17243b;color:white;padding:9px 12px;border-radius:8px;font-size:13px;max-width:280px;display:none}@media(max-width:700px){.cards{grid-template-columns:1fr}.sub{min-height:0;margin-bottom:15px}}
</style></head><body>
<div class="toolbar"><button id="play">▶ Animate both</button><button class="secondary" id="reset">↺ Reset</button><label for="progress">Progress</label><input id="progress" type="range" min="0" max="1" step="0.001" value="0"><span id="status" class="badge">Starting number</span></div>
<div class="cards"><section class="card"><h2>1 · Moving decimal point</h2><div class="sub">The digits stay in the same positions on the screen. The point moves through them, changing how we read their places.</div><div class="scroll"><div id="point" class="stage"></div></div><div class="note" id="pointNote"></div><div class="equation" id="pointRead"></div></section>
<section class="card"><h2>2 · Sliding digits</h2><div class="sub">The place-value columns and decimal boundary stay fixed. Every digit slides into a place with a different value.</div><div class="scroll"><div id="digits" class="stage"></div></div><div class="note" id="digitNote"></div><div class="equation" id="digitRead"></div></section></div><div id="tip" role="tooltip"></div>
<script>
const D=__DATA__, W=64, padding=32;
const [whole,frac='']=D.raw.split('.');
const original=(whole+frac).split('').map((d,i)=>({d,exp:whole.length-i-1}));
const hi=Math.max(whole.length-1,whole.length-1+D.power,0)+1;
const lo=Math.min(-frac.length,-frac.length+D.power,-1)-1;
const count=hi-lo+1, width=count*W+padding*2;
let t=0, frame=null;
function place(e){const names={0:'ones',1:'tens',2:'hundreds',3:'thousands',4:'ten thousands',5:'hundred thousands',6:'millions',7:'ten millions',8:'hundred millions',9:'billions','-1':'tenths','-2':'hundredths','-3':'thousandths','-4':'ten-thousandths','-5':'hundred-thousandths','-6':'millionths','-7':'ten-millionths','-8':'hundred-millionths','-9':'billionths'};return names[e]||'10^'+e+' place';}
function x(e){return padding+(hi-e)*W}
function element(parent,cls,text){const e=document.createElement('div');e.className=cls;e.textContent=text||'';parent.appendChild(e);return e}
const point=document.getElementById('point'), grid=document.getElementById('digits');
point.style.width=grid.style.width=width+'px';
const headers=[];
for(let e=hi;e>=lo;e--){
 for(const parent of [point,grid]){const cell=element(parent,'cell');cell.style.left=x(e)+'px';const label=element(cell,'label');headers.push({label,exp:e,moving:parent===point});}
}
const fixed=element(grid,'boundary');fixed.style.left=(x(0)+W)+'px';fixed.title='Fixed boundary between ones and tenths';
const dotFixed=element(grid,'dot','.');dotFixed.style.left=(x(0)+W-10)+'px';dotFixed.dataset.tip='Fixed decimal point: ones | tenths';
const dotMoving=element(point,'dot','.');dotMoving.dataset.tip='Decimal point: boundary between ones and tenths';
const leftTokens=[],rightTokens=[];
for(const o of original){const a=element(point,'token',o.d),b=element(grid,'token',o.d);a.style.left=x(o.exp)+'px';leftTokens.push({...o,node:a});rightTokens.push({...o,node:b});}
const zerosA=[],zerosB=[];
for(let e=hi;e>=lo;e--){const a=element(point,'token zero','0'),b=element(grid,'token zero','0');a.style.left=b.style.left=x(e)+'px';zerosA.push({exp:e,node:a});zerosB.push({exp:e,node:b});}
function update(v){
 t=v;document.getElementById('progress').value=t;
 const shift=D.power*t, settled=t===0||t===1, n=t===1?D.power:0;
 dotMoving.style.left=(x(0)+W-10+shift*W)+'px';
 for(const h of headers){const exp=h.exp+(h.moving?n:0);h.label.textContent=(h.moving&&!settled)?'':place(exp);h.label.parentElement.dataset.tip=(h.moving&&!settled)?'Between places during animation':place(exp)+' · 10^'+exp;}
 for(const o of rightTokens){o.node.style.left=(x(o.exp)-shift*W)+'px';o.node.dataset.tip=settled?'Digit '+o.d+' · '+place(o.exp+n)+' · '+o.d+' × 10^'+(o.exp+n):'Digit '+o.d+' · '+place(o.exp)+' → '+place(o.exp+D.power);}
 for(const o of leftTokens)o.node.dataset.tip=settled?'Digit '+o.d+' · '+place(o.exp+n)+' · '+o.d+' × 10^'+(o.exp+n):'Digit '+o.d+' · '+place(o.exp)+' → '+place(o.exp+D.power);
 const max=Math.max(0,whole.length-1+n),min=Math.min(-1,-frac.length+n);
 for(const o of zerosA){const exp=o.exp+n;const visible=settled&&exp<=max&&exp>=min&&!original.some(d=>d.exp===o.exp);o.node.hidden=!visible;o.node.dataset.tip='Placeholder zero · '+place(exp);}
 for(const o of zerosB){const visible=settled&&o.exp<=max&&o.exp>=min&&!original.some(d=>d.exp+n===o.exp);o.node.hidden=!visible;o.node.dataset.tip='Placeholder zero · '+place(o.exp);}
 const read=settled?(t===1?D.result:(D.negative?'-':'')+D.raw):'Digits are moving between places…';
 document.getElementById('pointRead').textContent=read;document.getElementById('digitRead').textContent=read;
 document.getElementById('status').textContent=t===0?'Starting number':t===1?'Result':Math.round(t*100)+'%';
}
const steps=Math.abs(D.power),pointDirection=D.power>0?'right':'left',digitDirection=D.power>0?'left':'right';
document.getElementById('pointNote').textContent=D.power===0?'×10⁰ = ×1: nothing moves.':'The point moves '+steps+' place'+(steps===1?'':'s')+' '+pointDirection+'.';
document.getElementById('digitNote').textContent=D.power===0?'×10⁰ = ×1: every digit keeps its place.':'The digits move '+steps+' column'+(steps===1?'':'s')+' '+digitDirection+'. Each place is worth '+(D.power>0?'10^'+steps+' times as much.':'1/10^'+steps+' as much.');
function stop(){if(frame!==null)cancelAnimationFrame(frame);frame=null;document.getElementById('play').textContent='▶ Animate both';}
document.getElementById('play').onclick=()=>{if(frame!==null){stop();return}if(t===1)update(0);const start=t,begin=performance.now(),duration=Math.max(1200,steps*350);document.getElementById('play').textContent='⏸ Pause';function tick(now){const u=Math.min(1,(now-begin)/duration);update(start+(1-start)*(u*u*(3-2*u)));if(u<1)frame=requestAnimationFrame(tick);else stop()}frame=requestAnimationFrame(tick)};
document.getElementById('reset').onclick=()=>{stop();update(0)};
document.getElementById('progress').oninput=e=>{stop();update(Number(e.target.value))};
const tip=document.getElementById('tip');document.addEventListener('pointermove',e=>{const target=e.target.closest('[data-tip]');if(!target){tip.style.display='none';return}tip.textContent=target.dataset.tip;tip.style.display='block';tip.style.left=Math.max(4,Math.min(e.clientX+12,innerWidth-tip.offsetWidth-8))+'px';tip.style.top=Math.max(4,Math.min(e.clientY+16,innerHeight-tip.offsetHeight-8))+'px'});document.addEventListener('pointerleave',()=>tip.style.display='none');
update(0);
</script></body></html>'''

if __name__ == '__main__':
    main()
