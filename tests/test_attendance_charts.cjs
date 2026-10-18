const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('Presentation/static/app.js','utf8');
const script = source.slice(source.indexOf('function attendanceChartScale('),source.indexOf('\ndrawAttendanceCharts();'));
function setup(matrix, labels=['1. okt.','8. okt.']) {
 const text=[], points=[];
 const ctx={scale(){},beginPath(){},moveTo(){},lineTo(){},stroke(){},fill(){},arc(x,y){points.push([x,y]);},fillText(value,x){text.push({value,x});}};
 const canvas={dataset:{attendanceChart:'all'},parentElement:{clientWidth:700},style:{},getContext:()=>ctx};
 const data={labels,columns:[0,1],voices:matrix.map(()=>'Alt')};
 const sandbox={document:{querySelector:()=>({textContent:JSON.stringify(data)}),querySelectorAll:()=>[canvas],documentElement:{dataset:{theme:'light'}}},window:{devicePixelRatio:1},currentAttendanceMatrix:()=>matrix,attendanceStates:['present','absent','excused','unentered'].map(name=>({name}))};
 vm.createContext(sandbox);vm.runInContext(script,sandbox);
 return {sandbox,text,points,canvas};
}
test('nice integer ticks include peak with at most six intervals',()=>{
 const {sandbox}=setup([]);
 for(const maximum of [0,1,2,4,7,10,13,23,41,100,150]){
  const scale=sandbox.attendanceChartScale(maximum);
  assert.ok(scale.max>=maximum);assert.ok(scale.step>=1);assert.ok(Number.isInteger(scale.step));
  assert.ok(scale.max/scale.step<=6);assert.ok(scale.max>0);
 }
});
test('total chart scales to largest displayed status count, not membership',()=>{
 const states=['present','absent','excused','unentered'];
 const matrix=Array.from({length:40},(_,i)=>[states[Math.floor(i/10)],states[Math.floor(i/10)]]);
 const {sandbox,text,points}=setup(matrix);sandbox.drawAttendanceCharts();
 assert.deepEqual(text.filter(item=>item.x===7).map(item=>item.value),[0,2,4,6,8,10]);
 assert.ok(points.every(([x,y])=>Number.isFinite(x)&&Number.isFinite(y)));
});
test('no past dates produces no plot',()=>{
 const {sandbox,text}=setup([],[]);sandbox.drawAttendanceCharts();assert.equal(text.length,0);
});
