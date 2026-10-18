const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const script = fs.readFileSync('Presentation/static/event-submit.js', 'utf8');
function setup() {
 const handlers = {}, dialogHandlers = {}, windowHandlers = {};
 const submit = {disabled:false, textContent:'Shrani dogodek'};
 const cancel = {disabled:false, textContent:'Prekliči'};
 const attrs = {};
 const dialog = {querySelectorAll:()=>[submit,cancel],addEventListener:(name,fn)=>dialogHandlers[name]=fn};
 const form = {closest:()=>dialog,append:status=>form.status=status,querySelector:()=>submit,addEventListener:(name,fn)=>handlers[name]=fn,setAttribute:(k,v)=>attrs[k]=v,removeAttribute:k=>delete attrs[k]};
 vm.runInNewContext(script,{document:{querySelector:()=>form,createElement:()=>({setAttribute(){}})},window:{addEventListener:(name,fn)=>windowHandlers[name]=fn}});
 return {handlers,dialogHandlers,windowHandlers,submit,cancel,attrs,form};
}
test('one submission while saving, including keyboard resubmission',()=>{
 const s=setup();let prevented=0;
 s.handlers.submit({submitter:s.submit});
 assert.equal(s.submit.disabled,true);assert.equal(s.cancel.disabled,true);
 assert.equal(s.attrs['aria-busy'],'true');assert.match(s.submit.textContent,/Shranjujem/);
 for(let i=0;i<3;i++)s.handlers.submit({preventDefault:()=>prevented++});
 assert.equal(prevented,3);
 s.dialogHandlers.cancel({preventDefault:()=>prevented++});assert.equal(prevented,4);
 s.windowHandlers.pageshow();assert.equal(s.submit.disabled,false);assert.equal(s.submit.textContent,'Shrani dogodek');
 assert.equal(s.attrs['aria-busy'],undefined);
 s.handlers.submit({submitter:s.submit});assert.equal(s.submit.disabled,true);
});
test('already cancelled submission does not lock form',()=>{
 const s=setup();s.handlers.submit({defaultPrevented:true});assert.equal(s.submit.disabled,false);
});
