import {createRequire} from 'module';
const require=createRequire('/Users/ozlevy/Projects/whats-mac/server/package.json');
const {chromium}=require('playwright-core');
const b=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const p=await b.newPage({viewport:{width:1080,height:1920}});
const items={
 cap:`<div style="position:absolute;top:140px;width:1080px;text-align:center;font:500 36px Geist,Helvetica;color:rgba(255,255,255,.85);letter-spacing:2px">UN General Assembly · Sept 22, 2026</div>`,
 si:`<div style="position:absolute;top:1330px;width:1080px;text-align:center;font:400 380px 'Instrument Serif',Georgia;color:#FFB938;text-shadow:0 0 60px rgba(255,185,56,.5)">SI</div>`,
 rew:`<div style="position:absolute;top:120px;left:80px;font:700 70px Helvetica;color:#fff;text-shadow:3px 0 #f0f,-3px 0 #0ff">◀◀ REW</div>`};
for(const[k,v] of Object.entries(items)){
 await p.setContent(`<style>@font-face{font-family:'Instrument Serif';src:url('file:///Users/ozlevy/Projects/humanbrowser/app/assets/fonts/InstrumentSerif-Regular.ttf')}html,body{margin:0;background:transparent}</style>${v}`);
 await p.waitForTimeout(300);
 await p.screenshot({path:`/tmp/supercut/v3/ov_${k}.png`,omitBackground:true});}
await b.close();
