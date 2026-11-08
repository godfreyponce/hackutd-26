import{A as e,C as t,D as n,E as r,F as i,M as a,N as o,O as s,P as c,S as l,T as u,_ as d,a as f,b as p,c as m,d as h,f as g,g as _,h as v,i as y,j as b,k as x,l as S,m as C,n as w,o as T,p as E,r as D,s as ee,t as te,u as O,v as ne,w as re,x as ie,y as ae}from"./index-CBxATNs6.js";var oe=0,se=1,ce=2,le=0,ue=1,de=2,fe=1.25,pe=65535,me=2**-24,he=Symbol(`SKIP_GENERATION`);function ge(e){return e.index?e.index.count:e.attributes.position.count}function _e(e){return ge(e)/3}function ve(e,t=ArrayBuffer){return e>65535?new Uint32Array(new t(4*e)):new Uint16Array(new t(2*e))}function ye(e,t){if(!e.index){let n=e.attributes.position.count,r=ve(n,t.useSharedArrayBuffer?SharedArrayBuffer:ArrayBuffer);e.setIndex(new D(r,1));for(let e=0;e<n;e++)r[e]=e}}function be(e,t){let n=_e(e),r=t||e.drawRange,i=r.start/3,a=(r.start+r.count)/3,o=Math.max(0,i),s=Math.min(n,a)-o;return[{offset:Math.floor(o),count:Math.floor(s)}]}function xe(e,t){if(!e.groups||!e.groups.length)return be(e,t);let n=[],r=new Set,i=t||e.drawRange,a=i.start/3,o=(i.start+i.count)/3;for(let t of e.groups){let e=t.start/3,n=(t.start+t.count)/3;r.add(Math.max(a,e)),r.add(Math.min(o,n))}let s=Array.from(r.values()).sort((e,t)=>e-t);for(let e=0;e<s.length-1;e++){let t=s[e],r=s[e+1];n.push({offset:Math.floor(t),count:Math.floor(r-t)})}return n}function Se(e,t){let n=_e(e),r=xe(e,t).sort((e,t)=>e.offset-t.offset),i=r[r.length-1];i.count=Math.min(n-i.offset,i.count);let a=0;return r.forEach(({count:e})=>a+=e),n!==a}function Ce(e,t,n,r,i){let a=1/0,o=1/0,s=1/0,c=-1/0,l=-1/0,u=-1/0,d=1/0,f=1/0,p=1/0,m=-1/0,h=-1/0,g=-1/0;for(let r=t*6,i=(t+n)*6;r<i;r+=6){let t=e[r+0],n=e[r+1],i=t-n,_=t+n;i<a&&(a=i),_>c&&(c=_),t<d&&(d=t),t>m&&(m=t);let v=e[r+2],y=e[r+3],b=v-y,x=v+y;b<o&&(o=b),x>l&&(l=x),v<f&&(f=v),v>h&&(h=v);let S=e[r+4],C=e[r+5],w=S-C,T=S+C;w<s&&(s=w),T>u&&(u=T),S<p&&(p=S),S>g&&(g=S)}r[0]=a,r[1]=o,r[2]=s,r[3]=c,r[4]=l,r[5]=u,i[0]=d,i[1]=f,i[2]=p,i[3]=m,i[4]=h,i[5]=g}function we(e,t=null,n=null,r=null){let i=e.attributes.position,a=e.index?e.index.array:null,o=_e(e),s=i.normalized,c;t===null?(c=new Float32Array(o*6),n=0,r=o):(c=t,n||=0,r||=o);let l=i.array,u=i.offset||0,d=3;i.isInterleavedBufferAttribute&&(d=i.data.stride);let f=[`getX`,`getY`,`getZ`];for(let e=n;e<n+r;e++){let t=e*3,n=e*6,r=t+0,o=t+1,p=t+2;a&&(r=a[r],o=a[o],p=a[p]),s||(r=r*d+u,o=o*d+u,p=p*d+u);for(let e=0;e<3;e++){let t,a,u;s?(t=i[f[e]](r),a=i[f[e]](o),u=i[f[e]](p)):(t=l[r+e],a=l[o+e],u=l[p+e]);let d=t;a<d&&(d=a),u<d&&(d=u);let m=t;a>m&&(m=a),u>m&&(m=u);let h=(m-d)/2,g=e*2;c[n+g+0]=d+h,c[n+g+1]=h+(Math.abs(d)+h)*me}}return c}function k(e,t,n){return n.min.x=t[e],n.min.y=t[e+1],n.min.z=t[e+2],n.max.x=t[e+3],n.max.y=t[e+4],n.max.z=t[e+5],n}function Te(e){let t=-1,n=-1/0;for(let r=0;r<3;r++){let i=e[r+3]-e[r];i>n&&(n=i,t=r)}return t}function Ee(e,t){t.set(e)}function De(e,t,n){let r,i;for(let a=0;a<3;a++){let o=a+3;r=e[a],i=t[a],n[a]=r<i?r:i,r=e[o],i=t[o],n[o]=r>i?r:i}}function Oe(e,t,n){for(let r=0;r<3;r++){let i=t[e+2*r],a=t[e+2*r+1],o=i-a,s=i+a;o<n[r]&&(n[r]=o),s>n[r+3]&&(n[r+3]=s)}}function ke(e){let t=e[3]-e[0],n=e[4]-e[1],r=e[5]-e[2];return 2*(t*n+n*r+r*t)}var Ae=32,je=(e,t)=>e.candidate-t.candidate,A=Array(Ae).fill().map(()=>({count:0,bounds:new Float32Array(6),rightCacheBounds:new Float32Array(6),leftCacheBounds:new Float32Array(6),candidate:0})),Me=new Float32Array(6);function Ne(e,t,n,r,i,a){let o=-1,s=0;if(a===0)o=Te(t),o!==-1&&(s=(t[o]+t[o+3])/2);else if(a===1)o=Te(e),o!==-1&&(s=Pe(n,r,i,o));else if(a===2){let a=ke(e),c=fe*i,l=r*6,u=(r+i)*6;for(let e=0;e<3;e++){let r=t[e],d=(t[e+3]-r)/Ae;if(i<Ae/4){let t=[...A];t.length=i;let r=0;for(let i=l;i<u;i+=6,r++){let a=t[r];a.candidate=n[i+2*e],a.count=0;let{bounds:o,leftCacheBounds:s,rightCacheBounds:c}=a;for(let e=0;e<3;e++)c[e]=1/0,c[e+3]=-1/0,s[e]=1/0,s[e+3]=-1/0,o[e]=1/0,o[e+3]=-1/0;Oe(i,n,o)}t.sort(je);let d=i;for(let e=0;e<d;e++){let n=t[e];for(;e+1<d&&t[e+1].candidate===n.candidate;)t.splice(e+1,1),d--}for(let r=l;r<u;r+=6){let i=n[r+2*e];for(let e=0;e<d;e++){let a=t[e];i>=a.candidate?Oe(r,n,a.rightCacheBounds):(Oe(r,n,a.leftCacheBounds),a.count++)}}for(let n=0;n<d;n++){let r=t[n],l=r.count,u=i-r.count,d=r.leftCacheBounds,f=r.rightCacheBounds,p=0;l!==0&&(p=ke(d)/a);let m=0;u!==0&&(m=ke(f)/a);let h=1+fe*(p*l+m*u);h<c&&(o=e,c=h,s=r.candidate)}}else{for(let e=0;e<Ae;e++){let t=A[e];t.count=0,t.candidate=r+d+e*d;let n=t.bounds;for(let e=0;e<3;e++)n[e]=1/0,n[e+3]=-1/0}for(let t=l;t<u;t+=6){let i=~~((n[t+2*e]-r)/d);i>=Ae&&(i=31);let a=A[i];a.count++,Oe(t,n,a.bounds)}let t=A[31];Ee(t.bounds,t.rightCacheBounds);for(let e=30;e>=0;e--){let t=A[e],n=A[e+1];De(t.bounds,n.rightCacheBounds,t.rightCacheBounds)}let f=0;for(let t=0;t<31;t++){let n=A[t],r=n.count,l=n.bounds,u=A[t+1].rightCacheBounds;r!==0&&(f===0?Ee(l,Me):De(l,Me,Me)),f+=r;let d=0,p=0;f!==0&&(d=ke(Me)/a);let m=i-f;m!==0&&(p=ke(u)/a);let h=1+fe*(d*f+p*m);h<c&&(o=e,c=h,s=n.candidate)}}}}else console.warn(`MeshBVH: Invalid build strategy value ${a} used.`);return{axis:o,pos:s}}function Pe(e,t,n,r){let i=0;for(let a=t,o=t+n;a<o;a++)i+=e[a*6+r*2];return i/n}var Fe=class{constructor(){this.boundingData=new Float32Array(6)}};function Ie(e,t,n,r,i,a){let o=r,s=r+i-1,c=a.pos,l=a.axis*2;for(;;){for(;o<=s&&n[o*6+l]<c;)o++;for(;o<=s&&n[s*6+l]>=c;)s--;if(o<s){for(let e=0;e<3;e++){let n=t[o*3+e];t[o*3+e]=t[s*3+e],t[s*3+e]=n}for(let e=0;e<6;e++){let t=n[o*6+e];n[o*6+e]=n[s*6+e],n[s*6+e]=t}o++,s--}else return o}}function Le(e,t,n,r,i,a){let o=r,s=r+i-1,c=a.pos,l=a.axis*2;for(;;){for(;o<=s&&n[o*6+l]<c;)o++;for(;o<=s&&n[s*6+l]>=c;)s--;if(o<s){let t=e[o];e[o]=e[s],e[s]=t;for(let e=0;e<6;e++){let t=n[o*6+e];n[o*6+e]=n[s*6+e],n[s*6+e]=t}o++,s--}else return o}}function j(e,t){return t[e+15]===65535}function M(e,t){return t[e+6]}function N(e,t){return t[e+14]}function P(e){return e+8}function F(e,t){return t[e+6]}function Re(e,t){return t[e+7]}function I(e){return e}var ze,Be,Ve,He,Ue=2**32;function We(e){return`count`in e?1:1+We(e.left)+We(e.right)}function Ge(e,t,n){return ze=new Float32Array(n),Be=new Uint32Array(n),Ve=new Uint16Array(n),He=new Uint8Array(n),Ke(e,t)}function Ke(e,t){let n=e/4,r=e/2,i=`count`in t,a=t.boundingData;for(let e=0;e<6;e++)ze[n+e]=a[e];if(i){if(t.buffer){let r=t.buffer;He.set(new Uint8Array(r),e);for(let t=e,i=e+r.byteLength;t<i;t+=32)j(t/2,Ve)||(Be[t/4+6]+=n);return e+r.byteLength}{let i=t.offset,a=t.count;return Be[n+6]=i,Ve[r+14]=a,Ve[r+15]=pe,e+32}}{let r=t.left,i=t.right,a=t.splitAxis,o;if(o=Ke(e+32,r),o/4>Ue)throw Error(`MeshBVH: Cannot store child pointer greater than 32 bits.`);return Be[n+6]=o/4,o=Ke(o,i),Be[n+7]=a,o}}function qe(e,t){let n=(e.index?e.index.count:e.attributes.position.count)/3,r=n>2**16,i=r?4:2,a=t?new SharedArrayBuffer(n*i):new ArrayBuffer(n*i),o=r?new Uint32Array(a):new Uint16Array(a);for(let e=0,t=o.length;e<t;e++)o[e]=e;return o}function Je(e,t,n,r,i){let{maxDepth:a,verbose:o,maxLeafTris:s,strategy:c,onProgress:l,indirect:u}=i,d=e._indirectBuffer,f=e.geometry,p=f.index?f.index.array:null,m=u?Le:Ie,h=_e(f),g=new Float32Array(6),_=!1,v=new Fe;return Ce(t,n,r,v.boundingData,g),b(v,n,r,g),v;function y(e){l&&l(e/h)}function b(e,n,r,i=null,l=0){if(!_&&l>=a&&(_=!0,o&&(console.warn(`MeshBVH: Max depth of ${a} reached when generating BVH. Consider increasing maxDepth.`),console.warn(f))),r<=s||l>=a)return y(n+r),e.offset=n,e.count=r,e;let u=Ne(e.boundingData,i,t,n,r,c);if(u.axis===-1)return y(n+r),e.offset=n,e.count=r,e;let h=m(d,p,t,n,r,u);if(h===n||h===n+r)y(n+r),e.offset=n,e.count=r;else{e.splitAxis=u.axis;let i=new Fe,a=n,o=h-n;e.left=i,Ce(t,a,o,i.boundingData,g),b(i,a,o,g,l+1);let s=new Fe,c=h,d=r-o;e.right=s,Ce(t,c,d,s.boundingData,g),b(s,c,d,g,l+1)}return e}}function Ye(e,t){let n=e.geometry;t.indirect&&(e._indirectBuffer=qe(n,t.useSharedArrayBuffer),Se(n,t.range)&&!t.verbose&&console.warn(`MeshBVH: Provided geometry contains groups or a range that do not fully span the vertex contents while using the "indirect" option. BVH may incorrectly report intersections on unrendered portions of the geometry.`)),e._indirectBuffer||ye(n,t);let r=t.useSharedArrayBuffer?SharedArrayBuffer:ArrayBuffer,i=we(n);e._roots=(t.indirect?be(n,t.range):xe(n,t.range)).map(n=>{let a=Je(e,i,n.offset,n.count,t),o=We(a),s=new r(32*o);return Ge(0,a,s),s})}var L=class{constructor(){this.min=1/0,this.max=-1/0}setFromPointsField(e,t){let n=1/0,r=-1/0;for(let i=0,a=e.length;i<a;i++){let a=e[i][t];n=a<n?a:n,r=a>r?a:r}this.min=n,this.max=r}setFromPoints(e,t){let n=1/0,r=-1/0;for(let i=0,a=t.length;i<a;i++){let a=t[i],o=e.dot(a);n=o<n?o:n,r=o>r?o:r}this.min=n,this.max=r}isSeparated(e){return this.min>e.max||e.min>this.max}};L.prototype.setFromBox=(function(){let e=new o;return function(t,n){let r=n.min,i=n.max,a=1/0,o=-1/0;for(let n=0;n<=1;n++)for(let s=0;s<=1;s++)for(let c=0;c<=1;c++){e.x=r.x*n+i.x*(1-n),e.y=r.y*s+i.y*(1-s),e.z=r.z*c+i.z*(1-c);let l=t.dot(e);a=Math.min(l,a),o=Math.max(l,o)}this.min=a,this.max=o}})(),(function(){let e=new L;return function(t,n){let r=t.points,i=t.satAxes,a=t.satBounds,o=n.points,s=n.satAxes,c=n.satBounds;for(let t=0;t<3;t++){let n=a[t],r=i[t];if(e.setFromPoints(r,o),n.isSeparated(e))return!1}for(let t=0;t<3;t++){let n=c[t],i=s[t];if(e.setFromPoints(i,r),n.isSeparated(e))return!1}}})();var Xe=(function(){let e=new o,t=new o,n=new o;return function(r,i,a){let o=r.start,s=e,c=i.start,l=t;n.subVectors(o,c),e.subVectors(r.end,r.start),t.subVectors(i.end,i.start);let u=n.dot(l),d=l.dot(s),f=l.dot(l),p=n.dot(s),m=s.dot(s)*f-d*d,h,g;h=m===0?0:(u*d-p*f)/m,g=(u+h*d)/f,a.x=h,a.y=g}})(),Ze=(function(){let e=new a,t=new o,n=new o;return function(r,i,a,o){Xe(r,i,e);let s=e.x,c=e.y;if(s>=0&&s<=1&&c>=0&&c<=1)r.at(s,a),i.at(c,o);else if(s>=0&&s<=1)c<0?i.at(0,o):i.at(1,o),r.closestPointToPoint(o,!0,a);else if(c>=0&&c<=1)s<0?r.at(0,a):r.at(1,a),i.closestPointToPoint(a,!0,o);else{let e;e=s<0?r.start:r.end;let l;l=c<0?i.start:i.end;let u=t,d=n;if(r.closestPointToPoint(l,!0,t),i.closestPointToPoint(e,!0,n),u.distanceToSquared(l)<=d.distanceToSquared(e)){a.copy(u),o.copy(l);return}a.copy(e),o.copy(d);return}}})(),Qe=(function(){let e=new o,t=new o,n=new ne,r=new O;return function(i,a){let{radius:o,center:s}=i,{a:c,b:l,c:u}=a;if(r.start=c,r.end=l,r.closestPointToPoint(s,!0,e).distanceTo(s)<=o||(r.start=c,r.end=u,r.closestPointToPoint(s,!0,e).distanceTo(s)<=o)||(r.start=l,r.end=u,r.closestPointToPoint(s,!0,e).distanceTo(s)<=o))return!0;let d=a.getPlane(n);if(Math.abs(d.distanceToPoint(s))<=o){let e=d.projectPoint(s,t);if(a.containsPoint(e))return!0}return!1}})(),$e=1e-15;function et(e){return Math.abs(e)<$e}var R=class extends s{constructor(...e){super(...e),this.isExtendedTriangle=!0,this.satAxes=[,,,,].fill().map(()=>new o),this.satBounds=[,,,,].fill().map(()=>new L),this.points=[this.a,this.b,this.c],this.sphere=new n,this.plane=new ne,this.needsUpdate=!0}intersectsSphere(e){return Qe(e,this)}update(){let e=this.a,t=this.b,n=this.c,r=this.points,i=this.satAxes,a=this.satBounds,o=i[0],s=a[0];this.getNormal(o),s.setFromPoints(o,r);let c=i[1],l=a[1];c.subVectors(e,t),l.setFromPoints(c,r);let u=i[2],d=a[2];u.subVectors(t,n),d.setFromPoints(u,r);let f=i[3],p=a[3];f.subVectors(n,e),p.setFromPoints(f,r),this.sphere.setFromPoints(this.points),this.plane.setFromNormalAndCoplanarPoint(o,e),this.needsUpdate=!1}};R.prototype.closestPointToSegment=(function(){let e=new o,t=new o,n=new O;return function(r,i=null,a=null){let{start:o,end:s}=r,c=this.points,l,u=1/0;for(let o=0;o<3;o++){let s=(o+1)%3;n.start.copy(c[o]),n.end.copy(c[s]),Ze(n,r,e,t),l=e.distanceToSquared(t),l<u&&(u=l,i&&i.copy(e),a&&a.copy(t))}return this.closestPointToPoint(o,e),l=o.distanceToSquared(e),l<u&&(u=l,i&&i.copy(e),a&&a.copy(o)),this.closestPointToPoint(s,e),l=s.distanceToSquared(e),l<u&&(u=l,i&&i.copy(e),a&&a.copy(s)),Math.sqrt(u)}})(),R.prototype.intersectsTriangle=(function(){let e=new R,t=[,,,],n=[,,,],r=new L,i=new L,a=new o,s=new o,c=new o,l=new o,u=new o,d=new O,f=new O,p=new O,m=new o;function h(e,t,n){let r=e.points,i=0,a=-1;for(let e=0;e<3;e++){let{start:o,end:c}=d;o.copy(r[e]),c.copy(r[(e+1)%3]),d.delta(s);let l=et(t.distanceToPoint(o));if(et(t.normal.dot(s))&&l){n.copy(d),i=2;break}let u=t.intersectLine(d,m);if(!u&&l&&m.copy(o),(u||l)&&!et(m.distanceTo(c))){if(i<=1)(i===1?n.start:n.end).copy(m),l&&(a=i);else if(i>=2){(a===1?n.start:n.end).copy(m),i=2;break}if(i++,i===2&&a===-1)break}}return i}return function(o,s=null,d=!1){this.needsUpdate&&this.update(),o.isExtendedTriangle?o.needsUpdate&&o.update():(e.copy(o),e.update(),o=e);let m=this.plane,g=o.plane;if(Math.abs(m.normal.dot(g.normal))>1-1e-10){let e=this.satBounds,c=this.satAxes;n[0]=o.a,n[1]=o.b,n[2]=o.c;for(let t=0;t<4;t++){let i=e[t],a=c[t];if(r.setFromPoints(a,n),i.isSeparated(r))return!1}let l=o.satBounds,u=o.satAxes;t[0]=this.a,t[1]=this.b,t[2]=this.c;for(let e=0;e<4;e++){let n=l[e],i=u[e];if(r.setFromPoints(i,t),n.isSeparated(r))return!1}for(let e=0;e<4;e++){let o=c[e];for(let e=0;e<4;e++){let s=u[e];if(a.crossVectors(o,s),r.setFromPoints(a,t),i.setFromPoints(a,n),r.isSeparated(i))return!1}}return s&&(d||console.warn(`ExtendedTriangle.intersectsTriangle: Triangles are coplanar which does not support an output edge. Setting edge to 0, 0, 0.`),s.start.set(0,0,0),s.end.set(0,0,0)),!0}{let e=h(this,g,f);if(e===1&&o.containsPoint(f.end))return s&&(s.start.copy(f.end),s.end.copy(f.end)),!0;if(e!==2)return!1;let t=h(o,m,p);if(t===1&&this.containsPoint(p.end))return s&&(s.start.copy(p.end),s.end.copy(p.end)),!0;if(t!==2)return!1;if(f.delta(c),p.delta(l),c.dot(l)<0){let e=p.start;p.start=p.end,p.end=e}let n=f.start.dot(c),r=f.end.dot(c),i=p.start.dot(c),a=p.end.dot(c);return n!==a&&i!==r&&r<i==n<a?!1:(s&&(u.subVectors(f.start,p.start),u.dot(c)>0?s.start.copy(f.start):s.start.copy(p.start),u.subVectors(f.end,p.end),u.dot(c)<0?s.end.copy(f.end):s.end.copy(p.end)),!0)}}})(),R.prototype.distanceToPoint=(function(){let e=new o;return function(t){return this.closestPointToPoint(t,e),t.distanceTo(e)}})(),R.prototype.distanceToTriangle=(function(){let e=new o,t=new o,n=[`a`,`b`,`c`],r=new O,i=new O;return function(a,o=null,s=null){let c=o||s?r:null;if(this.intersectsTriangle(a,c))return(o||s)&&(o&&c.getCenter(o),s&&c.getCenter(s)),0;let l=1/0;for(let t=0;t<3;t++){let r,i=n[t],c=a[i];this.closestPointToPoint(c,e),r=c.distanceToSquared(e),r<l&&(l=r,o&&o.copy(e),s&&s.copy(c));let u=this[i];a.closestPointToPoint(u,e),r=u.distanceToSquared(e),r<l&&(l=r,o&&o.copy(u),s&&s.copy(e))}for(let c=0;c<3;c++){let u=n[c],d=n[(c+1)%3];r.set(this[u],this[d]);for(let c=0;c<3;c++){let u=n[c],d=n[(c+1)%3];i.set(a[u],a[d]),Ze(r,i,e,t);let f=e.distanceToSquared(t);f<l&&(l=f,o&&o.copy(e),s&&s.copy(t))}}return Math.sqrt(l)}})();var z=class{constructor(e,t,n){this.isOrientedBox=!0,this.min=new o,this.max=new o,this.matrix=new E,this.invMatrix=new E,this.points=Array(8).fill().map(()=>new o),this.satAxes=[,,,].fill().map(()=>new o),this.satBounds=[,,,].fill().map(()=>new L),this.alignedSatBounds=[,,,].fill().map(()=>new L),this.needsUpdate=!1,e&&this.min.copy(e),t&&this.max.copy(t),n&&this.matrix.copy(n)}set(e,t,n){this.min.copy(e),this.max.copy(t),this.matrix.copy(n),this.needsUpdate=!0}copy(e){this.min.copy(e.min),this.max.copy(e.max),this.matrix.copy(e.matrix),this.needsUpdate=!0}};z.prototype.update=(function(){return function(){let e=this.matrix,t=this.min,n=this.max,r=this.points;for(let i=0;i<=1;i++)for(let a=0;a<=1;a++)for(let o=0;o<=1;o++){let s=r[1*i|2*a|4*o];s.x=i?n.x:t.x,s.y=a?n.y:t.y,s.z=o?n.z:t.z,s.applyMatrix4(e)}let i=this.satBounds,a=this.satAxes,o=r[0];for(let e=0;e<3;e++){let t=a[e],n=i[e],s=r[1<<e];t.subVectors(o,s),n.setFromPoints(t,r)}let s=this.alignedSatBounds;s[0].setFromPointsField(r,`x`),s[1].setFromPointsField(r,`y`),s[2].setFromPointsField(r,`z`),this.invMatrix.copy(this.matrix).invert(),this.needsUpdate=!1}})(),z.prototype.intersectsBox=(function(){let e=new L;return function(t){this.needsUpdate&&this.update();let n=t.min,r=t.max,i=this.satBounds,a=this.satAxes,o=this.alignedSatBounds;if(e.min=n.x,e.max=r.x,o[0].isSeparated(e)||(e.min=n.y,e.max=r.y,o[1].isSeparated(e))||(e.min=n.z,e.max=r.z,o[2].isSeparated(e)))return!1;for(let n=0;n<3;n++){let r=a[n],o=i[n];if(e.setFromBox(r,t),o.isSeparated(e))return!1}return!0}})(),z.prototype.intersectsTriangle=(function(){let e=new R,t=[,,,],n=new L,r=new L,i=new o;return function(a){this.needsUpdate&&this.update(),a.isExtendedTriangle?a.needsUpdate&&a.update():(e.copy(a),e.update(),a=e);let o=this.satBounds,s=this.satAxes;t[0]=a.a,t[1]=a.b,t[2]=a.c;for(let e=0;e<3;e++){let r=o[e],i=s[e];if(n.setFromPoints(i,t),r.isSeparated(n))return!1}let c=a.satBounds,l=a.satAxes,u=this.points;for(let e=0;e<3;e++){let t=c[e],r=l[e];if(n.setFromPoints(r,u),t.isSeparated(n))return!1}for(let e=0;e<3;e++){let a=s[e];for(let e=0;e<4;e++){let o=l[e];if(i.crossVectors(a,o),n.setFromPoints(i,t),r.setFromPoints(i,u),n.isSeparated(r))return!1}}return!0}})(),z.prototype.closestPointToPoint=(function(){return function(e,t){return this.needsUpdate&&this.update(),t.copy(e).applyMatrix4(this.invMatrix).clamp(this.min,this.max).applyMatrix4(this.matrix),t}})(),z.prototype.distanceToPoint=(function(){let e=new o;return function(t){return this.closestPointToPoint(t,e),t.distanceTo(e)}})(),z.prototype.distanceToBox=(function(){let e=[`x`,`y`,`z`],t=Array(12).fill().map(()=>new O),n=Array(12).fill().map(()=>new O),r=new o,i=new o;return function(a,o=0,s=null,c=null){if(this.needsUpdate&&this.update(),this.intersectsBox(a))return(s||c)&&(a.getCenter(i),this.closestPointToPoint(i,r),a.closestPointToPoint(r,i),s&&s.copy(r),c&&c.copy(i)),0;let l=o*o,u=a.min,d=a.max,f=this.points,p=1/0;for(let e=0;e<8;e++){let t=f[e];i.copy(t).clamp(u,d);let n=t.distanceToSquared(i);if(n<p&&(p=n,s&&s.copy(t),c&&c.copy(i),n<l))return Math.sqrt(n)}let m=0;for(let r=0;r<3;r++)for(let i=0;i<=1;i++)for(let a=0;a<=1;a++){let o=(r+1)%3,s=(r+2)%3,c=i<<o|a<<s,l=1<<r|i<<o|a<<s,p=f[c],h=f[l];t[m].set(p,h);let g=e[r],_=e[o],v=e[s],y=n[m],b=y.start,x=y.end;b[g]=u[g],b[_]=i?u[_]:d[_],b[v]=a?u[v]:d[_],x[g]=d[g],x[_]=i?u[_]:d[_],x[v]=a?u[v]:d[_],m++}for(let e=0;e<=1;e++)for(let t=0;t<=1;t++)for(let n=0;n<=1;n++){i.x=e?d.x:u.x,i.y=t?d.y:u.y,i.z=n?d.z:u.z,this.closestPointToPoint(i,r);let a=i.distanceToSquared(r);if(a<p&&(p=a,s&&s.copy(r),c&&c.copy(i),a<l))return Math.sqrt(a)}for(let e=0;e<12;e++){let a=t[e];for(let e=0;e<12;e++){let t=n[e];Ze(a,t,r,i);let o=r.distanceToSquared(i);if(o<p&&(p=o,s&&s.copy(r),c&&c.copy(i),o<l))return Math.sqrt(o)}}return Math.sqrt(p)}})();var tt=class{constructor(e){this._getNewPrimitive=e,this._primitives=[]}getPrimitive(){let e=this._primitives;return e.length===0?this._getNewPrimitive():e.pop()}releasePrimitive(e){this._primitives.push(e)}},B=new class extends tt{constructor(){super(()=>new R)}},V=new class{constructor(){this.float32Array=null,this.uint16Array=null,this.uint32Array=null;let e=[],t=null;this.setBuffer=n=>{t&&e.push(t),t=n,this.float32Array=new Float32Array(n),this.uint16Array=new Uint16Array(n),this.uint32Array=new Uint32Array(n)},this.clearBuffer=()=>{t=null,this.float32Array=null,this.uint16Array=null,this.uint32Array=null,e.length!==0&&this.setBuffer(e.pop())}}},H,nt,rt=[],it=new tt(()=>new w);function at(e,t,n,r,i,a){H=it.getPrimitive(),nt=it.getPrimitive(),rt.push(H,nt),V.setBuffer(e._roots[t]);let o=ot(0,e.geometry,n,r,i,a);V.clearBuffer(),it.releasePrimitive(H),it.releasePrimitive(nt),rt.pop(),rt.pop();let s=rt.length;return s>0&&(nt=rt[s-1],H=rt[s-2]),o}function ot(e,t,n,r,i=null,a=0,o=0){let{float32Array:s,uint16Array:c,uint32Array:l}=V,u=e*2;if(j(u,c)){let t=M(e,l),n=N(u,c);return k(I(e),s,H),r(t,n,!1,o,a+e,H)}{let u=P(e),d=F(e,l),f=u,p=d,m,h,g,_;if(i&&(g=H,_=nt,k(I(f),s,g),k(I(p),s,_),m=i(g),h=i(_),h<m)){f=d,p=u;let e=m;m=h,h=e,g=_}g||(g=H,k(I(f),s,g));let v=j(f*2,c),y=n(g,v,m,o+1,a+f),b;if(y===2){let e=w(f);b=r(e,T(f)-e,!0,o+1,a+f,g)}else b=y&&ot(f,t,n,r,i,a,o+1);if(b)return!0;_=nt,k(I(p),s,_);let x=j(p*2,c),S=n(_,x,h,o+1,a+p),C;if(S===2){let e=w(p);C=r(e,T(p)-e,!0,o+1,a+p,_)}else C=S&&ot(p,t,n,r,i,a,o+1);return!!C;function w(e){let{uint16Array:t,uint32Array:n}=V,r=e*2;for(;!j(r,t);)e=P(e),r=e*2;return M(e,n)}function T(e){let{uint16Array:t,uint32Array:n}=V,r=e*2;for(;!j(r,t);)e=F(e,n),r=e*2;return M(e,n)+N(r,t)}}}var st=new o,ct=new o;function lt(e,t,n={},r=0,i=1/0){let a=r*r,o=i*i,s=1/0,c=null;if(e.shapecast({boundsTraverseOrder:e=>(st.copy(t).clamp(e.min,e.max),st.distanceToSquared(t)),intersectsBounds:(e,t,n)=>n<s&&n<o,intersectsTriangle:(e,n)=>{e.closestPointToPoint(t,st);let r=t.distanceToSquared(st);return r<s&&(ct.copy(st),s=r,c=n),r<a}}),s===1/0)return null;let l=Math.sqrt(s);return n.point?n.point.copy(ct):n.point=ct.clone(),n.distance=l,n.faceIndex=c,n}var ut=!0,U=new o,W=new o,G=new o,dt=new a,ft=new a,pt=new a,mt=new o,ht=new o,gt=new o,_t=new o;function vt(e,t,n,r,i,a,o,s){let c;if(c=a===1?e.intersectTriangle(r,n,t,!0,i):e.intersectTriangle(t,n,r,a!==2,i),c===null)return null;let l=e.origin.distanceTo(i);return l<o||l>s?null:{distance:l,point:i.clone()}}function yt(e,t,n,r,i,c,l,u,d,f,p){U.fromBufferAttribute(t,c),W.fromBufferAttribute(t,l),G.fromBufferAttribute(t,u);let m=vt(e,U,W,G,_t,d,f,p);if(m){let t=new o;s.getBarycoord(_t,U,W,G,t),r&&(dt.fromBufferAttribute(r,c),ft.fromBufferAttribute(r,l),pt.fromBufferAttribute(r,u),m.uv=s.getInterpolation(_t,U,W,G,dt,ft,pt,new a)),i&&(dt.fromBufferAttribute(i,c),ft.fromBufferAttribute(i,l),pt.fromBufferAttribute(i,u),m.uv1=s.getInterpolation(_t,U,W,G,dt,ft,pt,new a)),n&&(mt.fromBufferAttribute(n,c),ht.fromBufferAttribute(n,l),gt.fromBufferAttribute(n,u),m.normal=s.getInterpolation(_t,U,W,G,mt,ht,gt,new o),m.normal.dot(e.direction)>0&&m.normal.multiplyScalar(-1));let d={a:c,b:l,c:u,normal:new o,materialIndex:0};s.getNormal(U,W,G,d.normal),m.face=d,m.faceIndex=c,ut&&(m.barycoord=t)}return m}function bt(e,t,n,r,i,a,o){let s=r*3,c=s+0,l=s+1,u=s+2,d=e.index;e.index&&(c=d.getX(c),l=d.getX(l),u=d.getX(u));let{position:f,normal:p,uv:m,uv1:h}=e.attributes,g=yt(n,f,p,m,h,c,l,u,t,a,o);return g?(g.faceIndex=r,i&&i.push(g),g):null}function K(e,t,n,r){let i=e.a,a=e.b,o=e.c,s=t,c=t+1,l=t+2;n&&(s=n.getX(s),c=n.getX(c),l=n.getX(l)),i.x=r.getX(s),i.y=r.getY(s),i.z=r.getZ(s),a.x=r.getX(c),a.y=r.getY(c),a.z=r.getZ(c),o.x=r.getX(l),o.y=r.getY(l),o.z=r.getZ(l)}var xt=new o,St=new o,Ct=new o,wt=new a,Tt=new a,Et=new a;function Dt(e,t,n,r){let i=t.getIndex().array,c=t.getAttribute(`position`),l=t.getAttribute(`uv`),u=i[n*3],d=i[n*3+1],f=i[n*3+2];xt.fromBufferAttribute(c,u),St.fromBufferAttribute(c,d),Ct.fromBufferAttribute(c,f);let p=0,m=t.groups,h=n*3;for(let e=0,t=m.length;e<t;e++){let t=m[e],{start:n,count:r}=t;if(h>=n&&h<n+r){p=t.materialIndex;break}}let g=r&&r.barycoord?r.barycoord:new o;s.getBarycoord(e,xt,St,Ct,g);let _=null;return l&&(wt.fromBufferAttribute(l,u),Tt.fromBufferAttribute(l,d),Et.fromBufferAttribute(l,f),_=r&&r.uv?r.uv:new a,s.getInterpolation(e,xt,St,Ct,wt,Tt,Et,_)),r?(r.face||={},r.face.a=u,r.face.b=d,r.face.c=f,r.face.materialIndex=p,r.face.normal||(r.face.normal=new o),s.getNormal(xt,St,Ct,r.face.normal),_&&(r.uv=_),r.barycoord=g,r):{face:{a:u,b:d,c:f,materialIndex:p,normal:s.getNormal(xt,St,Ct,new o)},uv:_,barycoord:g}}function Ot(e,t,n,r,i,a,o,s){let{geometry:c,_indirectBuffer:l}=e;for(let e=r,l=r+i;e<l;e++)bt(c,t,n,e,a,o,s)}function kt(e,t,n,r,i,a,o){let{geometry:s,_indirectBuffer:c}=e,l=1/0,u=null;for(let e=r,c=r+i;e<c;e++){let r;r=bt(s,t,n,e,null,a,o),r&&r.distance<l&&(u=r,l=r.distance)}return u}function At(e,t,n,r,i,a,o){let{geometry:s}=n,{index:c}=s,l=s.attributes.position;for(let n=e,s=t+e;n<s;n++){let e;if(e=n,K(o,e*3,c,l),o.needsUpdate=!0,r(o,e,i,a))return!0}return!1}function jt(e,t=null){t&&Array.isArray(t)&&(t=new Set(t));let n=e.geometry,r=n.index?n.index.array:null,i=n.attributes.position,a,o,s,c,l=0,u=e._roots;for(let e=0,t=u.length;e<t;e++)a=u[e],o=new Uint32Array(a),s=new Uint16Array(a),c=new Float32Array(a),d(0,l),l+=a.byteLength;function d(e,n,a=!1){let l=e*2;if(s[l+15]===65535){let t=o[e+6],n=s[l+14],a=1/0,u=1/0,d=1/0,f=-1/0,p=-1/0,m=-1/0;for(let e=3*t,o=3*(t+n);e<o;e++){let t=r[e],n=i.getX(t),o=i.getY(t),s=i.getZ(t);n<a&&(a=n),n>f&&(f=n),o<u&&(u=o),o>p&&(p=o),s<d&&(d=s),s>m&&(m=s)}return c[e+0]!==a||c[e+1]!==u||c[e+2]!==d||c[e+3]!==f||c[e+4]!==p||c[e+5]!==m?(c[e+0]=a,c[e+1]=u,c[e+2]=d,c[e+3]=f,c[e+4]=p,c[e+5]=m,!0):!1}{let r=e+8,i=o[e+6],s=r+n,l=i+n,u=a,f=!1,p=!1;t?u||=(f=t.has(s),p=t.has(l),!f&&!p):(f=!0,p=!0);let m=u||f,h=u||p,g=!1;m&&(g=d(r,n,u));let _=!1;h&&(_=d(i,n,u));let v=g||_;if(v)for(let t=0;t<3;t++){let n=r+t,a=i+t,o=c[n],s=c[n+3],l=c[a],u=c[a+3];c[e+t]=o<l?o:l,c[e+t+3]=s>u?s:u}return v}}}function q(e,t,n,r,i){let a,o,s,c,l,u,d=1/n.direction.x,f=1/n.direction.y,p=1/n.direction.z,m=n.origin.x,h=n.origin.y,g=n.origin.z,_=t[e],v=t[e+3],y=t[e+1],b=t[e+3+1],x=t[e+2],S=t[e+3+2];return d>=0?(a=(_-m)*d,o=(v-m)*d):(a=(v-m)*d,o=(_-m)*d),f>=0?(s=(y-h)*f,c=(b-h)*f):(s=(b-h)*f,c=(y-h)*f),a>c||s>o||((s>a||isNaN(a))&&(a=s),(c<o||isNaN(o))&&(o=c),p>=0?(l=(x-g)*p,u=(S-g)*p):(l=(S-g)*p,u=(x-g)*p),a>u||l>o)?!1:((l>a||a!==a)&&(a=l),(u<o||o!==o)&&(o=u),a<=i&&o>=r)}function Mt(e,t,n,r,i,a,o,s){let{geometry:c,_indirectBuffer:l}=e;for(let e=r,u=r+i;e<u;e++)bt(c,t,n,l?l[e]:e,a,o,s)}function Nt(e,t,n,r,i,a,o){let{geometry:s,_indirectBuffer:c}=e,l=1/0,u=null;for(let e=r,d=r+i;e<d;e++){let r;r=bt(s,t,n,c?c[e]:e,null,a,o),r&&r.distance<l&&(u=r,l=r.distance)}return u}function Pt(e,t,n,r,i,a,o){let{geometry:s}=n,{index:c}=s,l=s.attributes.position;for(let s=e,u=t+e;s<u;s++){let e;if(e=n.resolveTriangleIndex(s),K(o,e*3,c,l),o.needsUpdate=!0,r(o,e,i,a))return!0}return!1}function Ft(e,t,n,r,i,a,o){V.setBuffer(e._roots[t]),It(0,e,n,r,i,a,o),V.clearBuffer()}function It(e,t,n,r,i,a,o){let{float32Array:s,uint16Array:c,uint32Array:l}=V,u=e*2;if(j(u,c))Ot(t,n,r,M(e,l),N(u,c),i,a,o);else{let c=P(e);q(c,s,r,a,o)&&It(c,t,n,r,i,a,o);let u=F(e,l);q(u,s,r,a,o)&&It(u,t,n,r,i,a,o)}}var Lt=[`x`,`y`,`z`];function Rt(e,t,n,r,i,a){V.setBuffer(e._roots[t]);let o=zt(0,e,n,r,i,a);return V.clearBuffer(),o}function zt(e,t,n,r,i,a){let{float32Array:o,uint16Array:s,uint32Array:c}=V,l=e*2;if(j(l,s))return kt(t,n,r,M(e,c),N(l,s),i,a);{let s=Re(e,c),l=Lt[s],u=r.direction[l]>=0,d,f;u?(d=P(e),f=F(e,c)):(d=F(e,c),f=P(e));let p=q(d,o,r,i,a)?zt(d,t,n,r,i,a):null;if(p){let e=p.point[l];if(u?e<=o[f+s]:e>=o[f+s+3])return p}let m=q(f,o,r,i,a)?zt(f,t,n,r,i,a):null;return p&&m?p.distance<=m.distance?p:m:p||m||null}}var Bt=new w,Vt=new R,Ht=new R,Ut=new E,Wt=new z,Gt=new z;function Kt(e,t,n,r){V.setBuffer(e._roots[t]);let i=qt(0,e,n,r);return V.clearBuffer(),i}function qt(e,t,n,r,i=null){let{float32Array:a,uint16Array:o,uint32Array:s}=V,c=e*2;if(i===null&&(n.boundingBox||n.computeBoundingBox(),Wt.set(n.boundingBox.min,n.boundingBox.max,r),i=Wt),j(c,o)){let i=t.geometry,l=i.index,u=i.attributes.position,d=n.index,f=n.attributes.position,p=M(e,s),m=N(c,o);if(Ut.copy(r).invert(),n.boundsTree)return k(I(e),a,Gt),Gt.matrix.copy(Ut),Gt.needsUpdate=!0,n.boundsTree.shapecast({intersectsBounds:e=>Gt.intersectsBox(e),intersectsTriangle:e=>{e.a.applyMatrix4(r),e.b.applyMatrix4(r),e.c.applyMatrix4(r),e.needsUpdate=!0;for(let t=p*3,n=(m+p)*3;t<n;t+=3)if(K(Ht,t,l,u),Ht.needsUpdate=!0,e.intersectsTriangle(Ht))return!0;return!1}});for(let e=p*3,t=(m+p)*3;e<t;e+=3){K(Vt,e,l,u),Vt.a.applyMatrix4(Ut),Vt.b.applyMatrix4(Ut),Vt.c.applyMatrix4(Ut),Vt.needsUpdate=!0;for(let e=0,t=d.count;e<t;e+=3)if(K(Ht,e,d,f),Ht.needsUpdate=!0,Vt.intersectsTriangle(Ht))return!0}}else{let o=e+8,c=s[e+6];return k(I(o),a,Bt),!!(i.intersectsBox(Bt)&&qt(o,t,n,r,i)||(k(I(c),a,Bt),i.intersectsBox(Bt)&&qt(c,t,n,r,i)))}}var Jt=new E,Yt=new z,Xt=new z,Zt=new o,Qt=new o,$t=new o,en=new o;function tn(e,t,n,r={},i={},a=0,o=1/0){t.boundingBox||t.computeBoundingBox(),Yt.set(t.boundingBox.min,t.boundingBox.max,n),Yt.needsUpdate=!0;let s=e.geometry,c=s.attributes.position,l=s.index,u=t.attributes.position,d=t.index,f=B.getPrimitive(),p=B.getPrimitive(),m=Zt,h=Qt,g=null,_=null;i&&(g=$t,_=en);let v=1/0,y=null,b=null;return Jt.copy(n).invert(),Xt.matrix.copy(Jt),e.shapecast({boundsTraverseOrder:e=>Yt.distanceToBox(e),intersectsBounds:(e,t,n)=>n<v&&n<o&&(t&&(Xt.min.copy(e.min),Xt.max.copy(e.max),Xt.needsUpdate=!0),!0),intersectsRange:(e,r)=>{if(t.boundsTree)return t.boundsTree.shapecast({boundsTraverseOrder:e=>Xt.distanceToBox(e),intersectsBounds:(e,t,n)=>n<v&&n<o,intersectsRange:(t,i)=>{for(let o=t,s=t+i;o<s;o++){K(p,3*o,d,u),p.a.applyMatrix4(n),p.b.applyMatrix4(n),p.c.applyMatrix4(n),p.needsUpdate=!0;for(let t=e,n=e+r;t<n;t++){K(f,3*t,l,c),f.needsUpdate=!0;let e=f.distanceToTriangle(p,m,g);if(e<v&&(h.copy(m),_&&_.copy(g),v=e,y=t,b=o),e<a)return!0}}}});{let i=_e(t);for(let t=0,o=i;t<o;t++){K(p,3*t,d,u),p.a.applyMatrix4(n),p.b.applyMatrix4(n),p.c.applyMatrix4(n),p.needsUpdate=!0;for(let n=e,i=e+r;n<i;n++){K(f,3*n,l,c),f.needsUpdate=!0;let e=f.distanceToTriangle(p,m,g);if(e<v&&(h.copy(m),_&&_.copy(g),v=e,y=n,b=t),e<a)return!0}}}}}),B.releasePrimitive(f),B.releasePrimitive(p),v===1/0?null:(r.point?r.point.copy(h):r.point=h.clone(),r.distance=v,r.faceIndex=y,i&&(i.point?i.point.copy(_):i.point=_.clone(),i.point.applyMatrix4(Jt),h.applyMatrix4(Jt),i.distance=h.sub(i.point).length(),i.faceIndex=b),r)}function nn(e,t=null){t&&Array.isArray(t)&&(t=new Set(t));let n=e.geometry,r=n.index?n.index.array:null,i=n.attributes.position,a,o,s,c,l=0,u=e._roots;for(let e=0,t=u.length;e<t;e++)a=u[e],o=new Uint32Array(a),s=new Uint16Array(a),c=new Float32Array(a),d(0,l),l+=a.byteLength;function d(n,a,l=!1){let u=n*2;if(s[u+15]===65535){let t=o[n+6],a=s[u+14],l=1/0,d=1/0,f=1/0,p=-1/0,m=-1/0,h=-1/0;for(let n=t,o=t+a;n<o;n++){let t=3*e.resolveTriangleIndex(n);for(let e=0;e<3;e++){let n=t+e;n=r?r[n]:n;let a=i.getX(n),o=i.getY(n),s=i.getZ(n);a<l&&(l=a),a>p&&(p=a),o<d&&(d=o),o>m&&(m=o),s<f&&(f=s),s>h&&(h=s)}}return c[n+0]!==l||c[n+1]!==d||c[n+2]!==f||c[n+3]!==p||c[n+4]!==m||c[n+5]!==h?(c[n+0]=l,c[n+1]=d,c[n+2]=f,c[n+3]=p,c[n+4]=m,c[n+5]=h,!0):!1}{let e=n+8,r=o[n+6],i=e+a,s=r+a,u=l,f=!1,p=!1;t?u||=(f=t.has(i),p=t.has(s),!f&&!p):(f=!0,p=!0);let m=u||f,h=u||p,g=!1;m&&(g=d(e,a,u));let _=!1;h&&(_=d(r,a,u));let v=g||_;if(v)for(let t=0;t<3;t++){let i=e+t,a=r+t,o=c[i],s=c[i+3],l=c[a],u=c[a+3];c[n+t]=o<l?o:l,c[n+t+3]=s>u?s:u}return v}}}function rn(e,t,n,r,i,a,o){V.setBuffer(e._roots[t]),an(0,e,n,r,i,a,o),V.clearBuffer()}function an(e,t,n,r,i,a,o){let{float32Array:s,uint16Array:c,uint32Array:l}=V,u=e*2;if(j(u,c))Mt(t,n,r,M(e,l),N(u,c),i,a,o);else{let c=P(e);q(c,s,r,a,o)&&an(c,t,n,r,i,a,o);let u=F(e,l);q(u,s,r,a,o)&&an(u,t,n,r,i,a,o)}}var on=[`x`,`y`,`z`];function sn(e,t,n,r,i,a){V.setBuffer(e._roots[t]);let o=cn(0,e,n,r,i,a);return V.clearBuffer(),o}function cn(e,t,n,r,i,a){let{float32Array:o,uint16Array:s,uint32Array:c}=V,l=e*2;if(j(l,s))return Nt(t,n,r,M(e,c),N(l,s),i,a);{let s=Re(e,c),l=on[s],u=r.direction[l]>=0,d,f;u?(d=P(e),f=F(e,c)):(d=F(e,c),f=P(e));let p=q(d,o,r,i,a)?cn(d,t,n,r,i,a):null;if(p){let e=p.point[l];if(u?e<=o[f+s]:e>=o[f+s+3])return p}let m=q(f,o,r,i,a)?cn(f,t,n,r,i,a):null;return p&&m?p.distance<=m.distance?p:m:p||m||null}}var ln=new w,un=new R,dn=new R,fn=new E,pn=new z,mn=new z;function hn(e,t,n,r){V.setBuffer(e._roots[t]);let i=gn(0,e,n,r);return V.clearBuffer(),i}function gn(e,t,n,r,i=null){let{float32Array:a,uint16Array:o,uint32Array:s}=V,c=e*2;if(i===null&&(n.boundingBox||n.computeBoundingBox(),pn.set(n.boundingBox.min,n.boundingBox.max,r),i=pn),j(c,o)){let i=t.geometry,l=i.index,u=i.attributes.position,d=n.index,f=n.attributes.position,p=M(e,s),m=N(c,o);if(fn.copy(r).invert(),n.boundsTree)return k(I(e),a,mn),mn.matrix.copy(fn),mn.needsUpdate=!0,n.boundsTree.shapecast({intersectsBounds:e=>mn.intersectsBox(e),intersectsTriangle:e=>{e.a.applyMatrix4(r),e.b.applyMatrix4(r),e.c.applyMatrix4(r),e.needsUpdate=!0;for(let n=p,r=m+p;n<r;n++)if(K(dn,3*t.resolveTriangleIndex(n),l,u),dn.needsUpdate=!0,e.intersectsTriangle(dn))return!0;return!1}});for(let e=p,n=m+p;e<n;e++){K(un,3*t.resolveTriangleIndex(e),l,u),un.a.applyMatrix4(fn),un.b.applyMatrix4(fn),un.c.applyMatrix4(fn),un.needsUpdate=!0;for(let e=0,t=d.count;e<t;e+=3)if(K(dn,e,d,f),dn.needsUpdate=!0,un.intersectsTriangle(dn))return!0}}else{let o=e+8,c=s[e+6];return k(I(o),a,ln),!!(i.intersectsBox(ln)&&gn(o,t,n,r,i)||(k(I(c),a,ln),i.intersectsBox(ln)&&gn(c,t,n,r,i)))}}var _n=new E,vn=new z,yn=new z,bn=new o,xn=new o,Sn=new o,Cn=new o;function wn(e,t,n,r={},i={},a=0,o=1/0){t.boundingBox||t.computeBoundingBox(),vn.set(t.boundingBox.min,t.boundingBox.max,n),vn.needsUpdate=!0;let s=e.geometry,c=s.attributes.position,l=s.index,u=t.attributes.position,d=t.index,f=B.getPrimitive(),p=B.getPrimitive(),m=bn,h=xn,g=null,_=null;i&&(g=Sn,_=Cn);let v=1/0,y=null,b=null;return _n.copy(n).invert(),yn.matrix.copy(_n),e.shapecast({boundsTraverseOrder:e=>vn.distanceToBox(e),intersectsBounds:(e,t,n)=>n<v&&n<o&&(t&&(yn.min.copy(e.min),yn.max.copy(e.max),yn.needsUpdate=!0),!0),intersectsRange:(r,i)=>{if(t.boundsTree){let s=t.boundsTree;return s.shapecast({boundsTraverseOrder:e=>yn.distanceToBox(e),intersectsBounds:(e,t,n)=>n<v&&n<o,intersectsRange:(t,o)=>{for(let x=t,S=t+o;x<S;x++){let t=s.resolveTriangleIndex(x);K(p,3*t,d,u),p.a.applyMatrix4(n),p.b.applyMatrix4(n),p.c.applyMatrix4(n),p.needsUpdate=!0;for(let t=r,n=r+i;t<n;t++){let n=e.resolveTriangleIndex(t);K(f,3*n,l,c),f.needsUpdate=!0;let r=f.distanceToTriangle(p,m,g);if(r<v&&(h.copy(m),_&&_.copy(g),v=r,y=t,b=x),r<a)return!0}}}})}{let o=_e(t);for(let t=0,s=o;t<s;t++){K(p,3*t,d,u),p.a.applyMatrix4(n),p.b.applyMatrix4(n),p.c.applyMatrix4(n),p.needsUpdate=!0;for(let n=r,o=r+i;n<o;n++){let r=e.resolveTriangleIndex(n);K(f,3*r,l,c),f.needsUpdate=!0;let i=f.distanceToTriangle(p,m,g);if(i<v&&(h.copy(m),_&&_.copy(g),v=i,y=n,b=t),i<a)return!0}}}}}),B.releasePrimitive(f),B.releasePrimitive(p),v===1/0?null:(r.point?r.point.copy(h):r.point=h.clone(),r.distance=v,r.faceIndex=y,i&&(i.point?i.point.copy(_):i.point=_.clone(),i.point.applyMatrix4(_n),h.applyMatrix4(_n),i.distance=h.sub(i.point).length(),i.faceIndex=b),r)}function Tn(){return typeof SharedArrayBuffer<`u`}var En=new V.constructor,Dn=new V.constructor,J=new tt(()=>new w),On=new w,kn=new w,An=new w,jn=new w,Mn=!1;function Nn(e,t,n,r){if(Mn)throw Error(`MeshBVH: Recursive calls to bvhcast not supported.`);Mn=!0;let i=e._roots,a=t._roots,o,s=0,c=0,l=new E().copy(n).invert();for(let e=0,t=i.length;e<t;e++){En.setBuffer(i[e]),c=0;let t=J.getPrimitive();k(I(0),En.float32Array,t),t.applyMatrix4(l);for(let e=0,i=a.length;e<i&&(Dn.setBuffer(a[e]),o=Y(0,0,n,l,r,s,c,0,0,t),Dn.clearBuffer(),c+=a[e].length,!o);e++);if(J.releasePrimitive(t),En.clearBuffer(),s+=i[e].length,o)break}return Mn=!1,o}function Y(e,t,n,r,i,a=0,o=0,s=0,c=0,l=null,u=!1){let d,f;u?(d=Dn,f=En):(d=En,f=Dn);let p=d.float32Array,m=d.uint32Array,h=d.uint16Array,g=f.float32Array,_=f.uint32Array,v=f.uint16Array,y=e*2,b=t*2,x=j(y,h),S=j(b,v),C=!1;if(S&&x)C=u?i(M(t,_),N(t*2,v),M(e,m),N(e*2,h),c,o+t,s,a+e):i(M(e,m),N(e*2,h),M(t,_),N(t*2,v),s,a+e,c,o+t);else if(S){let l=J.getPrimitive();k(I(t),g,l),l.applyMatrix4(n);let d=P(e),f=F(e,m);k(I(d),p,On),k(I(f),p,kn);let h=l.intersectsBox(On),_=l.intersectsBox(kn);C=h&&Y(t,d,r,n,i,o,a,c,s+1,l,!u)||_&&Y(t,f,r,n,i,o,a,c,s+1,l,!u),J.releasePrimitive(l)}else{let d=P(t),f=F(t,_);k(I(d),g,An),k(I(f),g,jn);let h=l.intersectsBox(An),v=l.intersectsBox(jn);if(h&&v)C=Y(e,d,n,r,i,a,o,s,c+1,l,u)||Y(e,f,n,r,i,a,o,s,c+1,l,u);else if(h){if(x)C=Y(e,d,n,r,i,a,o,s,c+1,l,u);else{let t=J.getPrimitive();t.copy(An).applyMatrix4(n);let l=P(e),f=F(e,m);k(I(l),p,On),k(I(f),p,kn);let h=t.intersectsBox(On),g=t.intersectsBox(kn);C=h&&Y(d,l,r,n,i,o,a,c,s+1,t,!u)||g&&Y(d,f,r,n,i,o,a,c,s+1,t,!u),J.releasePrimitive(t)}}else if(v){if(x)C=Y(e,f,n,r,i,a,o,s,c+1,l,u);else{let t=J.getPrimitive();t.copy(jn).applyMatrix4(n);let l=P(e),d=F(e,m);k(I(l),p,On),k(I(d),p,kn);let h=t.intersectsBox(On),g=t.intersectsBox(kn);C=h&&Y(f,l,r,n,i,o,a,c,s+1,t,!u)||g&&Y(f,d,r,n,i,o,a,c,s+1,t,!u),J.releasePrimitive(t)}}}return C}var Pn=new z,Fn=new w,In={strategy:0,maxDepth:40,maxLeafTris:10,useSharedArrayBuffer:!1,setBoundingBox:!0,onProgress:null,indirect:!1,verbose:!0,range:null},Ln=class e{static serialize(e,t={}){t={cloneBuffers:!0,...t};let n=e.geometry,r=e._roots,i=e._indirectBuffer,a=n.getIndex(),o;return o=t.cloneBuffers?{roots:r.map(e=>e.slice()),index:a?a.array.slice():null,indirectBuffer:i?i.slice():null}:{roots:r,index:a?a.array:null,indirectBuffer:i},o}static deserialize(t,n,r={}){r={setIndex:!0,indirect:!!t.indirectBuffer,...r};let{index:i,roots:a,indirectBuffer:o}=t,s=new e(n,{...r,[he]:!0});if(s._roots=a,s._indirectBuffer=o||null,r.setIndex){let e=n.getIndex();if(e===null){let e=new D(t.index,1,!1);n.setIndex(e)}else e.array!==i&&(e.array.set(i),e.needsUpdate=!0)}return s}get indirect(){return!!this._indirectBuffer}constructor(e,t={}){if(!e.isBufferGeometry)throw Error(`MeshBVH: Only BufferGeometries are supported.`);if(e.index&&e.index.isInterleavedBufferAttribute)throw Error(`MeshBVH: InterleavedBufferAttribute is not supported for the index attribute.`);if(t=Object.assign({...In,[he]:!1},t),t.useSharedArrayBuffer&&!Tn())throw Error(`MeshBVH: SharedArrayBuffer is not available.`);this.geometry=e,this._roots=null,this._indirectBuffer=null,t[he]||(Ye(this,t),!e.boundingBox&&t.setBoundingBox&&(e.boundingBox=this.getBoundingBox(new w))),this.resolveTriangleIndex=t.indirect?e=>this._indirectBuffer[e]:e=>e}refit(e=null){return(this.indirect?nn:jt)(this,e)}traverse(e,t=0){let n=this._roots[t],r=new Uint32Array(n),i=new Uint16Array(n);a(0);function a(t,o=0){let s=t*2,c=i[s+15]===pe;if(c){let a=r[t+6],l=i[s+14];e(o,c,new Float32Array(n,t*4,6),a,l)}else{let i=t+8,s=r[t+6],l=r[t+7];e(o,c,new Float32Array(n,t*4,6),l)||(a(i,o+1),a(s,o+1))}}}raycast(e,t=0,n=0,r=1/0){let i=this._roots,a=this.geometry,o=[],s=t.isMaterial,c=Array.isArray(t),l=a.groups,u=s?t.side:t,d=this.indirect?rn:Ft;for(let a=0,s=i.length;a<s;a++){let i=c?t[l[a].materialIndex].side:u,s=o.length;if(d(this,a,i,e,o,n,r),c){let e=l[a].materialIndex;for(let t=s,n=o.length;t<n;t++)o[t].face.materialIndex=e}}return o}raycastFirst(e,t=0,n=0,r=1/0){let i=this._roots,a=this.geometry,o=t.isMaterial,s=Array.isArray(t),c=null,l=a.groups,u=o?t.side:t,d=this.indirect?sn:Rt;for(let a=0,o=i.length;a<o;a++){let i=s?t[l[a].materialIndex].side:u,o=d(this,a,i,e,n,r);o!=null&&(c==null||o.distance<c.distance)&&(c=o,s&&(o.face.materialIndex=l[a].materialIndex))}return c}intersectsGeometry(e,t){let n=!1,r=this._roots,i=this.indirect?hn:Kt;for(let a=0,o=r.length;a<o&&(n=i(this,a,e,t),!n);a++);return n}shapecast(e){let t=B.getPrimitive(),n=this.indirect?Pt:At,{boundsTraverseOrder:r,intersectsBounds:i,intersectsRange:a,intersectsTriangle:o}=e;if(a&&o){let e=a;a=(r,i,a,s,c)=>e(r,i,a,s,c)?!0:n(r,i,this,o,a,s,t)}else a||=o?(e,r,i,a)=>n(e,r,this,o,i,a,t):(e,t,n)=>n;let s=!1,c=0,l=this._roots;for(let e=0,t=l.length;e<t;e++){let t=l[e];if(s=at(this,e,i,a,r,c),s)break;c+=t.byteLength}return B.releasePrimitive(t),s}bvhcast(e,t,n){let{intersectsRanges:r,intersectsTriangles:i}=n,a=B.getPrimitive(),o=this.geometry.index,s=this.geometry.attributes.position,c=this.indirect?e=>{let t=this.resolveTriangleIndex(e);K(a,t*3,o,s)}:e=>{K(a,e*3,o,s)},l=B.getPrimitive(),u=e.geometry.index,d=e.geometry.attributes.position,f=e.indirect?t=>{let n=e.resolveTriangleIndex(t);K(l,n*3,u,d)}:e=>{K(l,e*3,u,d)};if(i){let e=(e,n,r,o,s,u,d,p)=>{for(let m=r,h=r+o;m<h;m++){f(m),l.a.applyMatrix4(t),l.b.applyMatrix4(t),l.c.applyMatrix4(t),l.needsUpdate=!0;for(let t=e,r=e+n;t<r;t++)if(c(t),a.needsUpdate=!0,i(a,l,t,m,s,u,d,p))return!0}return!1};if(r){let t=r;r=function(n,r,i,a,o,s,c,l){return t(n,r,i,a,o,s,c,l)?!0:e(n,r,i,a,o,s,c,l)}}else r=e}return Nn(this,e,t,r)}intersectsBox(e,t){return Pn.set(e.min,e.max,t),Pn.needsUpdate=!0,this.shapecast({intersectsBounds:e=>Pn.intersectsBox(e),intersectsTriangle:e=>Pn.intersectsTriangle(e)})}intersectsSphere(e){return this.shapecast({intersectsBounds:t=>e.intersectsBox(t),intersectsTriangle:t=>t.intersectsSphere(e)})}closestPointToGeometry(e,t,n={},r={},i=0,a=1/0){return(this.indirect?wn:tn)(this,e,t,n,r,i,a)}closestPointToPoint(e,t={},n=0,r=1/0){return lt(this,e,t,n,r)}getBoundingBox(e){return e.makeEmpty(),this._roots.forEach(t=>{k(0,new Float32Array(t),Fn),e.union(Fn)}),e}},Rn=new w,zn=new E,Bn=class extends d{get isMesh(){return!this.displayEdges}get isLineSegments(){return this.displayEdges}get isLine(){return this.displayEdges}getVertexPosition(...e){return C.prototype.getVertexPosition.call(this,...e)}constructor(e,t,n=10,r=0){super(),this.material=t,this.geometry=new y,this.name=`MeshBVHRootHelper`,this.depth=n,this.displayParents=!1,this.bvh=e,this.displayEdges=!0,this._group=r}raycast(){}update(){let e=this.geometry,t=this.bvh,n=this._group;if(e.dispose(),this.visible=!1,t){let r=this.depth-1,i=this.displayParents,a=0;t.traverse((e,t)=>{if(e>=r||t)return a++,!0;i&&a++},n);let o=0,s=new Float32Array(24*a);t.traverse((e,t,n)=>{let a=e>=r||t;if(a||i){k(0,n,Rn);let{min:e,max:t}=Rn;for(let n=-1;n<=1;n+=2){let r=n<0?e.x:t.x;for(let n=-1;n<=1;n+=2){let i=n<0?e.y:t.y;for(let n=-1;n<=1;n+=2){let a=n<0?e.z:t.z;s[o+0]=r,s[o+1]=i,s[o+2]=a,o+=3}}}return a}},n);let c,l;l=this.displayEdges?new Uint8Array([0,4,1,5,2,6,3,7,0,2,1,3,4,6,5,7,0,1,2,3,4,5,6,7]):new Uint8Array([0,1,2,2,1,3,4,6,5,6,7,5,1,4,5,0,4,1,2,3,6,3,7,6,0,2,4,2,6,4,1,5,3,3,5,7]),c=s.length>65535?new Uint32Array(l.length*a):new Uint16Array(l.length*a);let u=l.length;for(let e=0;e<a;e++){let t=e*8,n=e*u;for(let e=0;e<u;e++)c[n+e]=t+l[e]}e.setIndex(new D(c,1,!1)),e.setAttribute(`position`,new D(s,3,!1)),this.visible=!0}}},Vn=class e extends m{get color(){return this.edgeMaterial.color}get opacity(){return this.edgeMaterial.opacity}set opacity(e){this.edgeMaterial.opacity=e,this.meshMaterial.opacity=e}constructor(e=null,t=null,n=10){e instanceof Ln&&(n=t||10,t=e,e=null),typeof t==`number`&&(n=t,t=null),super(),this.name=`MeshBVHHelper`,this.depth=n,this.mesh=e,this.bvh=t,this.displayParents=!1,this.displayEdges=!0,this.objectIndex=0,this._roots=[];let r=new h({color:65416,transparent:!0,opacity:.3,depthWrite:!1}),i=new v({color:65416,transparent:!0,opacity:.3,depthWrite:!1});i.color=r.color,this.edgeMaterial=r,this.meshMaterial=i,this.update()}update(){let e=this.mesh,t=this.bvh||e.geometry.boundsTree||null;if(e.isBatchedMesh&&e.boundsTrees&&!t){let n=e._drawInfo[this.objectIndex];n&&(t=e.boundsTrees[n.geometryIndex]||t)}let n=t?t._roots.length:0;for(;this._roots.length>n;){let e=this._roots.pop();e.geometry.dispose(),this.remove(e)}for(let e=0;e<n;e++){let{depth:n,edgeMaterial:r,meshMaterial:i,displayParents:a,displayEdges:o}=this;if(e>=this._roots.length){let i=new Bn(t,r,n,e);this.add(i),this._roots.push(i)}let s=this._roots[e];s.bvh=t,s.depth=n,s.displayParents=a,s.displayEdges=o,s.material=o?r:i,s.update()}}updateMatrixWorld(...e){let t=this.mesh,n=this.parent;t!==null&&(t.updateWorldMatrix(!0,!1),n?this.matrix.copy(n.matrixWorld).invert().multiply(t.matrixWorld):this.matrix.copy(t.matrixWorld),(t.isInstancedMesh||t.isBatchedMesh)&&(t.getMatrixAt(this.objectIndex,zn),this.matrix.multiply(zn)),this.matrix.decompose(this.position,this.quaternion,this.scale)),super.updateMatrixWorld(...e)}copy(e){this.depth=e.depth,this.mesh=e.mesh,this.bvh=e.bvh,this.opacity=e.opacity,this.color.copy(e.color)}clone(){return new e(this.mesh,this.bvh,this.depth)}dispose(){this.edgeMaterial.dispose(),this.meshMaterial.dispose();let e=this.children;for(let t=0,n=e.length;t<n;t++)e[t].geometry.dispose()}},Hn=new w,Un=new w,Wn=new o;function Gn(e){switch(typeof e){case`number`:return 8;case`string`:return e.length*2;case`boolean`:return 4;default:return 0}}function Kn(e){return/(Uint|Int|Float)(8|16|32)Array/.test(e.constructor.name)}function qn(e,t){let n={nodeCount:0,leafNodeCount:0,depth:{min:1/0,max:-1/0},tris:{min:1/0,max:-1/0},splits:[0,0,0],surfaceAreaScore:0};return e.traverse((e,t,r,i,a)=>{let o=r[3]-r[0],s=r[4]-r[1],c=r[5]-r[2],l=2*(o*s+s*c+c*o);n.nodeCount++,t?(n.leafNodeCount++,n.depth.min=Math.min(e,n.depth.min),n.depth.max=Math.max(e,n.depth.max),n.tris.min=Math.min(a,n.tris.min),n.tris.max=Math.max(a,n.tris.max),n.surfaceAreaScore+=l*fe*a):(n.splits[i]++,n.surfaceAreaScore+=l*1)},t),n.tris.min===1/0&&(n.tris.min=0,n.tris.max=0),n.depth.min===1/0&&(n.depth.min=0,n.depth.max=0),n}function Jn(e){return e._roots.map((t,n)=>qn(e,n))}function Yn(e){let t=new Set,n=[e],r=0;for(;n.length;){let e=n.pop();if(!t.has(e)){t.add(e);for(let t in e){if(!Object.hasOwn(e,t))continue;r+=Gn(t);let i=e[t];i&&(typeof i==`object`||typeof i==`function`)?Kn(i)||Tn()&&i instanceof SharedArrayBuffer||i instanceof ArrayBuffer?r+=i.byteLength:n.push(i):r+=Gn(i)}}}return r}function Xn(e){let t=e.geometry,n=[],r=t.index,i=t.getAttribute(`position`),a=!0;return e.traverse((t,o,s,c,l)=>{n[t]={depth:t,isLeaf:o,boundingData:s,offset:c,count:l},k(0,s,Hn);let u=n[t-1];if(o)for(let t=c,n=c+l;t<n;t++){let n=e.resolveTriangleIndex(t),o=3*n,s=3*n+1,c=3*n+2;r&&(o=r.getX(o),s=r.getX(s),c=r.getX(c));let l;Wn.fromBufferAttribute(i,o),l=Hn.containsPoint(Wn),Wn.fromBufferAttribute(i,s),l&&=Hn.containsPoint(Wn),Wn.fromBufferAttribute(i,c),l&&=Hn.containsPoint(Wn),console.assert(l,`Leaf bounds does not fully contain triangle.`),a&&=l}if(u){k(0,s,Un);let e=Un.containsBox(Hn);console.assert(e,`Parent bounds does not fully contain child.`),a&&=e}}),a}function Zn(e){let t=[];return e.traverse((e,n,r,i,a)=>{let o={bounds:k(0,r,new w)};n?(o.count=a,o.offset=i):(o.left=null,o.right=null),t[e]=o;let s=t[e-1];s&&(s.left===null?s.left=o:s.right=o)}),t[0]}function Qn(e,t,n){return e===null?null:(e.point.applyMatrix4(t.matrixWorld),e.distance=e.point.distanceTo(n.ray.origin),e.object=t,e)}var $n=!0,er=new t,tr=new o,nr=new E,rr=C.prototype.raycast,ir=te.prototype.raycast,ar=new o,X=new C,or=[];function sr(e,t){this.isBatchedMesh?cr.call(this,e,t):lr.call(this,e,t)}function cr(e,t){if(this.boundsTrees){let r=this.boundsTrees,i=this._drawInfo||this._instanceInfo,a=this._drawRanges||this._geometryInfo,o=this.matrixWorld;X.material=this.material,X.geometry=this.geometry;let s=X.geometry.boundsTree,c=X.geometry.drawRange;X.geometry.boundingSphere===null&&(X.geometry.boundingSphere=new n);for(let n=0,s=i.length;n<s;n++){if(!this.getVisibleAt(n))continue;let s=i[n].geometryIndex;if(X.geometry.boundsTree=r[s],this.getMatrixAt(n,X.matrixWorld).premultiply(o),!X.geometry.boundsTree){this.getBoundingBoxAt(s,X.geometry.boundingBox),this.getBoundingSphereAt(s,X.geometry.boundingSphere);let e=a[s];X.geometry.setDrawRange(e.start,e.count)}X.raycast(e,or);for(let e=0,r=or.length;e<r;e++){let r=or[e];r.object=this,r.batchId=n,t.push(r)}or.length=0}X.geometry.boundsTree=s,X.geometry.drawRange=c,X.material=null,X.geometry=null}else ir.call(this,e,t)}function lr(e,t){if(this.geometry.boundsTree){if(this.material===void 0)return;nr.copy(this.matrixWorld).invert(),er.copy(e.ray).applyMatrix4(nr),ar.setFromMatrixScale(this.matrixWorld),tr.copy(er.direction).multiply(ar);let n=tr.length(),r=e.near/n,i=e.far/n,a=this.geometry.boundsTree;if(e.firstHitOnly===!0){let n=Qn(a.raycastFirst(er,this.material,r,i),this,e);n&&t.push(n)}else{let n=a.raycast(er,this.material,r,i);for(let r=0,i=n.length;r<i;r++){let i=Qn(n[r],this,e);i&&t.push(i)}}}else rr.call(this,e,t)}function ur(e={}){return this.boundsTree=new Ln(this,e),this.boundsTree}function dr(){this.boundsTree=null}function fr(e=-1,t={}){if(!$n)throw Error(`BatchedMesh: Three r166+ is required to compute bounds trees.`);t.indirect&&console.warn(`"Indirect" is set to false because it is not supported for BatchedMesh.`),t={...t,indirect:!1,range:null};let n=this._drawRanges||this._geometryInfo,r=this._geometryCount;this.boundsTrees||=Array(r).fill(null);let i=this.boundsTrees;for(;i.length<r;)i.push(null);if(e<0){for(let e=0;e<r;e++)t.range=n[e],i[e]=new Ln(this.geometry,t);return i}return e<n.length&&(t.range=n[e],i[e]=new Ln(this.geometry,t)),i[e]||null}function pr(e=-1){e<0?this.boundsTrees.fill(null):e<this.boundsTree.length&&(this.boundsTrees[e]=null)}function mr(e){switch(e){case 1:return`R`;case 2:return`RG`;case 3:return`RGBA`;case 4:return`RGBA`}throw Error()}function hr(e){switch(e){case 1:return re;case 2:return ie;case 3:return ae;case 4:return ae}}function gr(e){switch(e){case 1:return u;case 2:return l;case 3:return p;case 4:return p}}var _r=class extends T{constructor(){super(),this.minFilter=_,this.magFilter=_,this.generateMipmaps=!1,this.overrideItemSize=null,this._forcedType=null}updateFrom(t){let n=this.overrideItemSize,i=t.itemSize,a=t.count;if(n!==null){if(i*a%n!==0)throw Error(`VertexAttributeTexture: overrideItemSize must divide evenly into buffer length.`);t.itemSize=n,t.count=a*i/n}let o=t.itemSize,s=t.count,c=t.normalized,l=t.array.constructor,u=l.BYTES_PER_ELEMENT,d=this._forcedType,p=o;if(d===null)switch(l){case Float32Array:d=ee;break;case Uint8Array:case Uint16Array:case Uint32Array:d=e;break;case Int8Array:case Int16Array:case Int32Array:d=S}let m,h,g,_,v=mr(o);switch(d){case ee:g=1,h=hr(o),c&&u===1?(_=l,v+=`8`,l===Uint8Array?m=x:(m=f,v+=`_SNORM`)):(_=Float32Array,v+=`32F`,m=ee);break;case S:v+=u*8+`I`,g=c?2**(l.BYTES_PER_ELEMENT*8-1):1,h=gr(o),u===1?(_=Int8Array,m=f):u===2?(_=Int16Array,m=r):(_=Int32Array,m=S);break;case e:v+=u*8+`UI`,g=c?2**(l.BYTES_PER_ELEMENT*8-1):1,h=gr(o),u===1?(_=Uint8Array,m=x):u===2?(_=Uint16Array,m=b):(_=Uint32Array,m=e)}p===3&&(h===1023||h===1033)&&(p=4);let y=Math.ceil(Math.sqrt(s))||1,C=p*y*y,w=new _(C),T=t.normalized;t.normalized=!1;for(let e=0;e<s;e++){let n=p*e;w[n]=t.getX(e)/g,o>=2&&(w[n+1]=t.getY(e)/g),o>=3&&(w[n+2]=t.getZ(e)/g,p===4&&(w[n+3]=1)),o>=4&&(w[n+3]=t.getW(e)/g)}t.normalized=T,this.internalFormat=v,this.format=h,this.type=m,this.image.width=y,this.image.height=y,this.image.data=w,this.needsUpdate=!0,this.dispose(),t.itemSize=i,t.count=a}},vr=class extends _r{constructor(){super(),this._forcedType=e}},yr=class extends _r{constructor(){super(),this._forcedType=S}},br=class extends _r{constructor(){super(),this._forcedType=ee}},xr=class{constructor(){this.index=new vr,this.position=new br,this.bvhBounds=new T,this.bvhContents=new T,this._cachedIndexAttr=null,this.index.overrideItemSize=3}updateFrom(e){let{geometry:t}=e;if(Cr(e,this.bvhBounds,this.bvhContents),this.position.updateFrom(t.attributes.position),e.indirect){let n=e._indirectBuffer;if(this._cachedIndexAttr===null||this._cachedIndexAttr.count!==n.length){if(t.index)this._cachedIndexAttr=t.index.clone();else{let e=ve(ge(t));this._cachedIndexAttr=new D(e,1,!1)}}Sr(t,n,this._cachedIndexAttr),this.index.updateFrom(this._cachedIndexAttr)}else this.index.updateFrom(t.index)}dispose(){let{index:e,position:t,bvhBounds:n,bvhContents:r}=this;e&&e.dispose(),t&&t.dispose(),n&&n.dispose(),r&&r.dispose()}};function Sr(e,t,n){let r=n.array,i=e.index?e.index.array:null;for(let e=0,n=t.length;e<n;e++){let n=3*e,a=3*t[e];for(let e=0;e<3;e++)r[n+e]=i?i[a+e]:a+e}}function Cr(t,n,r){let i=t._roots;if(i.length!==1)throw Error(`MeshBVHUniformStruct: Multi-root BVHs not supported.`);let a=i[0],o=new Uint16Array(a),s=new Uint32Array(a),c=new Float32Array(a),u=a.byteLength/32,d=2*Math.ceil(Math.sqrt(u/2)),f=new Float32Array(4*d*d),p=Math.ceil(Math.sqrt(u)),m=new Uint32Array(2*p*p);for(let e=0;e<u;e++){let t=e*32/4,n=t*2,r=I(t);for(let t=0;t<3;t++)f[8*e+0+t]=c[r+0+t],f[8*e+4+t]=c[r+3+t];if(j(n,o)){let r=N(n,o),i=M(t,s),a=4294901760|r;m[e*2+0]=a,m[e*2+1]=i}else{let n=4*F(t,s)/32,r=Re(t,s);m[e*2+0]=r,m[e*2+1]=n}}n.image.data=f,n.image.width=d,n.image.height=d,n.format=ae,n.type=ee,n.internalFormat=`RGBA32F`,n.minFilter=_,n.magFilter=_,n.generateMipmaps=!1,n.needsUpdate=!0,n.dispose(),r.image.data=m,r.image.width=p,r.image.height=p,r.format=l,r.type=e,r.internalFormat=`RG32UI`,r.minFilter=_,r.magFilter=_,r.generateMipmaps=!1,r.needsUpdate=!0,r.dispose()}var Z=new o,Q=new o,$=new o,wr=new c,Tr=new o,Er=new o,Dr=new c,Or=new c,kr=new E,Ar=new E;function jr(e,t){if(!e&&!t)return;let n=e.count===t.count,r=e.normalized===t.normalized,i=e.array.constructor===t.array.constructor,a=e.itemSize===t.itemSize;if(!n||!r||!i||!a)throw Error()}function Mr(e,t=null){let n=e.array.constructor,r=e.normalized,i=e.itemSize,a=t===null?e.count:t;return new D(new n(i*a),i,r)}function Nr(e,t,n=0){if(e.isInterleavedBufferAttribute){let r=e.itemSize;for(let i=0,a=e.count;i<a;i++){let a=i+n;t.setX(a,e.getX(i)),r>=2&&t.setY(a,e.getY(i)),r>=3&&t.setZ(a,e.getZ(i)),r>=4&&t.setW(a,e.getW(i))}}else{let r=t.array,i=r.constructor,a=r.BYTES_PER_ELEMENT*e.itemSize*n;new i(r.buffer,a,e.array.length).set(e.array)}}function Pr(e,t,n){let r=e.elements,i=t.elements;for(let e=0,t=i.length;e<t;e++)r[e]+=i[e]*n}function Fr(e,t,n){let r=e.skeleton,i=e.geometry,a=r.bones,o=r.boneInverses;Dr.fromBufferAttribute(i.attributes.skinIndex,t),Or.fromBufferAttribute(i.attributes.skinWeight,t),kr.elements.fill(0);for(let e=0;e<4;e++){let t=Or.getComponent(e);if(t!==0){let n=Dr.getComponent(e);Ar.multiplyMatrices(a[n].matrixWorld,o[n]),Pr(kr,Ar,t)}}return kr.multiply(e.bindMatrix).premultiply(e.bindMatrixInverse),n.transformDirection(kr),n}function Ir(e,t,n,r,i){Tr.set(0,0,0);for(let a=0,o=e.length;a<o;a++){let o=t[a],s=e[a];o!==0&&(Er.fromBufferAttribute(s,r),n?Tr.addScaledVector(Er,o):Tr.addScaledVector(Er.sub(i),o))}i.add(Tr)}function Lr(e,t={useGroups:!1,updateIndex:!1,skipAttributes:[]},n=new y){let r=e[0].index!==null,{useGroups:i=!1,updateIndex:a=!1,skipAttributes:o=[]}=t,s=new Set(Object.keys(e[0].attributes)),c={},l=0;n.clearGroups();for(let t=0;t<e.length;++t){let a=e[t],o=0;if(r!==(a.index!==null))throw Error(`StaticGeometryGenerator: All geometries must have compatible attributes; make sure index attribute exists among all geometries, or in none of them.`);for(let e in a.attributes){if(!s.has(e))throw Error(`StaticGeometryGenerator: All geometries must have compatible attributes; make sure "`+e+`" attribute exists among all geometries, or in none of them.`);c[e]===void 0&&(c[e]=[]),c[e].push(a.attributes[e]),o++}if(o!==s.size)throw Error(`StaticGeometryGenerator: Make sure all geometries have the same number of attributes.`);if(i){let e;if(r)e=a.index.count;else if(a.attributes.position!==void 0)e=a.attributes.position.count;else throw Error(`StaticGeometryGenerator: The geometry must have either an index or a position attribute`);n.addGroup(l,e,t),l+=e}}if(r){let t=!1;if(!n.index){let r=0;for(let t=0;t<e.length;++t)r+=e[t].index.count;n.setIndex(new D(new Uint32Array(r),1,!1)),t=!0}if(a||t){let t=n.index,r=0,i=0;for(let n=0;n<e.length;++n){let a=e[n],s=a.index;if(o[n]!==!0)for(let e=0;e<s.count;++e)t.setX(r,s.getX(e)+i),r++;i+=a.attributes.position.count}}}for(let e in c){let t=c[e];if(!(e in n.attributes)){let r=0;for(let e in t)r+=t[e].count;n.setAttribute(e,Mr(c[e][0],r))}let r=n.attributes[e],i=0;for(let e=0,n=t.length;e<n;e++){let n=t[e];o[e]!==!0&&Nr(n,r,i),i+=n.count}}return n}function Rr(e,t){if(e===null||t===null)return e===t;if(e.length!==t.length)return!1;for(let n=0,r=e.length;n<r;n++)if(e[n]!==t[n])return!1;return!0}function zr(e){let{index:t,attributes:n}=e;if(t)for(let e=0,n=t.count;e<n;e+=3){let n=t.getX(e),r=t.getX(e+2);t.setX(e,r),t.setX(e+2,n)}else for(let e in n){let t=n[e],r=t.itemSize;for(let e=0,n=t.count;e<n;e+=3)for(let n=0;n<r;n++){let r=t.getComponent(e,n),i=t.getComponent(e+2,n);t.setComponent(e,n,i),t.setComponent(e+2,n,r)}}return e}var Br=class{constructor(e){this.matrixWorld=new E,this.geometryHash=null,this.boneMatrices=null,this.primitiveCount=-1,this.mesh=e,this.update()}update(){let e=this.mesh,t=e.geometry,n=e.skeleton,r=(t.index?t.index.count:t.attributes.position.count)/3;if(this.matrixWorld.copy(e.matrixWorld),this.geometryHash=t.attributes.position.version,this.primitiveCount=r,n){n.boneTexture||n.computeBoneTexture(),n.update();let e=n.boneMatrices;!this.boneMatrices||this.boneMatrices.length!==e.length?this.boneMatrices=e.slice():this.boneMatrices.set(e)}else this.boneMatrices=null}didChange(){let e=this.mesh,t=e.geometry,n=(t.index?t.index.count:t.attributes.position.count)/3;return!(this.matrixWorld.equals(e.matrixWorld)&&this.geometryHash===t.attributes.position.version&&Rr(e.skeleton&&e.skeleton.boneMatrices||null,this.boneMatrices)&&this.primitiveCount===n)}},Vr=class{constructor(e){Array.isArray(e)||(e=[e]);let t=[];e.forEach(e=>{e.traverseVisible(e=>{e.isMesh&&t.push(e)})}),this.meshes=t,this.useGroups=!0,this.applyWorldTransforms=!0,this.attributes=[`position`,`normal`,`color`,`tangent`,`uv`,`uv2`],this._intermediateGeometry=Array(t.length).fill().map(()=>new y),this._diffMap=new WeakMap}getMaterials(){let e=[];return this.meshes.forEach(t=>{Array.isArray(t.material)?e.push(...t.material):e.push(t.material)}),e}generate(e=new y){let t=[],{meshes:n,useGroups:r,_intermediateGeometry:i,_diffMap:a}=this;for(let e=0,r=n.length;e<r;e++){let r=n[e],o=i[e],s=a.get(r);!s||s.didChange(r)?(this._convertToStaticGeometry(r,o),t.push(!1),s?s.update():a.set(r,new Br(r))):t.push(!0)}if(i.length===0){e.setIndex(null);let t=e.attributes;for(let n in t)e.deleteAttribute(n);for(let t in this.attributes)e.setAttribute(this.attributes[t],new D(new Float32Array,4,!1))}else Lr(i,{useGroups:r,skipAttributes:t},e);for(let t in e.attributes)e.attributes[t].needsUpdate=!0;return e}_convertToStaticGeometry(e,t=new y){let n=e.geometry,r=this.applyWorldTransforms,i=this.attributes.includes(`normal`),a=this.attributes.includes(`tangent`),o=n.attributes,s=t.attributes;!t.index&&n.index&&(t.index=n.index.clone()),s.position||t.setAttribute(`position`,Mr(o.position)),i&&!s.normal&&o.normal&&t.setAttribute(`normal`,Mr(o.normal)),a&&!s.tangent&&o.tangent&&t.setAttribute(`tangent`,Mr(o.tangent)),jr(n.index,t.index),jr(o.position,s.position),i&&jr(o.normal,s.normal),a&&jr(o.tangent,s.tangent);let c=o.position,l=i?o.normal:null,u=a?o.tangent:null,d=n.morphAttributes.position,f=n.morphAttributes.normal,p=n.morphAttributes.tangent,m=n.morphTargetsRelative,h=e.morphTargetInfluences,_=new g;_.getNormalMatrix(e.matrixWorld),n.index&&t.index.array.set(n.index.array);for(let t=0,n=o.position.count;t<n;t++)Z.fromBufferAttribute(c,t),l&&Q.fromBufferAttribute(l,t),u&&(wr.fromBufferAttribute(u,t),$.fromBufferAttribute(u,t)),h&&(d&&Ir(d,h,m,t,Z),f&&Ir(f,h,m,t,Q),p&&Ir(p,h,m,t,$)),e.isSkinnedMesh&&(e.applyBoneTransform(t,Z),l&&Fr(e,t,Q),u&&Fr(e,t,$)),r&&Z.applyMatrix4(e.matrixWorld),s.position.setXYZ(t,Z.x,Z.y,Z.z),l&&(r&&Q.applyNormalMatrix(_),s.normal.setXYZ(t,Q.x,Q.y,Q.z)),u&&(r&&$.transformDirection(e.matrixWorld),s.tangent.setXYZW(t,$.x,$.y,$.z,wr.w));for(let e in this.attributes){let n=this.attributes[e];n!==`position`&&n!==`tangent`&&n!==`normal`&&n in o&&(s[n]||t.setAttribute(n,Mr(o[n])),jr(o[n],s[n]),Nr(o[n],s[n]))}return e.matrixWorld.determinant()<0&&zr(t),t}},Hr=`

// A stack of uint32 indices can can store the indices for
// a perfectly balanced tree with a depth up to 31. Lower stack
// depth gets higher performance.
//
// However not all trees are balanced. Best value to set this to
// is the trees max depth.
#ifndef BVH_STACK_DEPTH
#define BVH_STACK_DEPTH 60
#endif

#ifndef INFINITY
#define INFINITY 1e20
#endif

// Utilities
uvec4 uTexelFetch1D( usampler2D tex, uint index ) {

	uint width = uint( textureSize( tex, 0 ).x );
	uvec2 uv;
	uv.x = index % width;
	uv.y = index / width;

	return texelFetch( tex, ivec2( uv ), 0 );

}

ivec4 iTexelFetch1D( isampler2D tex, uint index ) {

	uint width = uint( textureSize( tex, 0 ).x );
	uvec2 uv;
	uv.x = index % width;
	uv.y = index / width;

	return texelFetch( tex, ivec2( uv ), 0 );

}

vec4 texelFetch1D( sampler2D tex, uint index ) {

	uint width = uint( textureSize( tex, 0 ).x );
	uvec2 uv;
	uv.x = index % width;
	uv.y = index / width;

	return texelFetch( tex, ivec2( uv ), 0 );

}

vec4 textureSampleBarycoord( sampler2D tex, vec3 barycoord, uvec3 faceIndices ) {

	return
		barycoord.x * texelFetch1D( tex, faceIndices.x ) +
		barycoord.y * texelFetch1D( tex, faceIndices.y ) +
		barycoord.z * texelFetch1D( tex, faceIndices.z );

}

void ndcToCameraRay(
	vec2 coord, mat4 cameraWorld, mat4 invProjectionMatrix,
	out vec3 rayOrigin, out vec3 rayDirection
) {

	// get camera look direction and near plane for camera clipping
	vec4 lookDirection = cameraWorld * vec4( 0.0, 0.0, - 1.0, 0.0 );
	vec4 nearVector = invProjectionMatrix * vec4( 0.0, 0.0, - 1.0, 1.0 );
	float near = abs( nearVector.z / nearVector.w );

	// get the camera direction and position from camera matrices
	vec4 origin = cameraWorld * vec4( 0.0, 0.0, 0.0, 1.0 );
	vec4 direction = invProjectionMatrix * vec4( coord, 0.5, 1.0 );
	direction /= direction.w;
	direction = cameraWorld * direction - origin;

	// slide the origin along the ray until it sits at the near clip plane position
	origin.xyz += direction.xyz * near / dot( direction, lookDirection );

	rayOrigin = origin.xyz;
	rayDirection = direction.xyz;

}
`,Ur=`

float dot2( vec3 v ) {

	return dot( v, v );

}

// https://www.shadertoy.com/view/ttfGWl
vec3 closestPointToTriangle( vec3 p, vec3 v0, vec3 v1, vec3 v2, out vec3 barycoord ) {

    vec3 v10 = v1 - v0;
    vec3 v21 = v2 - v1;
    vec3 v02 = v0 - v2;

	vec3 p0 = p - v0;
	vec3 p1 = p - v1;
	vec3 p2 = p - v2;

    vec3 nor = cross( v10, v02 );

    // method 2, in barycentric space
    vec3  q = cross( nor, p0 );
    float d = 1.0 / dot2( nor );
    float u = d * dot( q, v02 );
    float v = d * dot( q, v10 );
    float w = 1.0 - u - v;

	if( u < 0.0 ) {

		w = clamp( dot( p2, v02 ) / dot2( v02 ), 0.0, 1.0 );
		u = 0.0;
		v = 1.0 - w;

	} else if( v < 0.0 ) {

		u = clamp( dot( p0, v10 ) / dot2( v10 ), 0.0, 1.0 );
		v = 0.0;
		w = 1.0 - u;

	} else if( w < 0.0 ) {

		v = clamp( dot( p1, v21 ) / dot2( v21 ), 0.0, 1.0 );
		w = 0.0;
		u = 1.0-v;

	}

	barycoord = vec3( u, v, w );
    return u * v1 + v * v2 + w * v0;

}

float distanceToTriangles(
	// geometry info and triangle range
	sampler2D positionAttr, usampler2D indexAttr, uint offset, uint count,

	// point and cut off range
	vec3 point, float closestDistanceSquared,

	// outputs
	inout uvec4 faceIndices, inout vec3 faceNormal, inout vec3 barycoord, inout float side, inout vec3 outPoint
) {

	bool found = false;
	vec3 localBarycoord;
	for ( uint i = offset, l = offset + count; i < l; i ++ ) {

		uvec3 indices = uTexelFetch1D( indexAttr, i ).xyz;
		vec3 a = texelFetch1D( positionAttr, indices.x ).rgb;
		vec3 b = texelFetch1D( positionAttr, indices.y ).rgb;
		vec3 c = texelFetch1D( positionAttr, indices.z ).rgb;

		// get the closest point and barycoord
		vec3 closestPoint = closestPointToTriangle( point, a, b, c, localBarycoord );
		vec3 delta = point - closestPoint;
		float sqDist = dot2( delta );
		if ( sqDist < closestDistanceSquared ) {

			// set the output results
			closestDistanceSquared = sqDist;
			faceIndices = uvec4( indices.xyz, i );
			faceNormal = normalize( cross( a - b, b - c ) );
			barycoord = localBarycoord;
			outPoint = closestPoint;
			side = sign( dot( faceNormal, delta ) );

		}

	}

	return closestDistanceSquared;

}

float distanceSqToBounds( vec3 point, vec3 boundsMin, vec3 boundsMax ) {

	vec3 clampedPoint = clamp( point, boundsMin, boundsMax );
	vec3 delta = point - clampedPoint;
	return dot( delta, delta );

}

float distanceSqToBVHNodeBoundsPoint( vec3 point, sampler2D bvhBounds, uint currNodeIndex ) {

	uint cni2 = currNodeIndex * 2u;
	vec3 boundsMin = texelFetch1D( bvhBounds, cni2 ).xyz;
	vec3 boundsMax = texelFetch1D( bvhBounds, cni2 + 1u ).xyz;
	return distanceSqToBounds( point, boundsMin, boundsMax );

}

// use a macro to hide the fact that we need to expand the struct into separate fields
#define	bvhClosestPointToPoint(		bvh,		point, faceIndices, faceNormal, barycoord, side, outPoint	)	_bvhClosestPointToPoint(		bvh.position, bvh.index, bvh.bvhBounds, bvh.bvhContents,		point, faceIndices, faceNormal, barycoord, side, outPoint	)

float _bvhClosestPointToPoint(
	// bvh info
	sampler2D bvh_position, usampler2D bvh_index, sampler2D bvh_bvhBounds, usampler2D bvh_bvhContents,

	// point to check
	vec3 point,

	// output variables
	inout uvec4 faceIndices, inout vec3 faceNormal, inout vec3 barycoord,
	inout float side, inout vec3 outPoint
 ) {

	// stack needs to be twice as long as the deepest tree we expect because
	// we push both the left and right child onto the stack every traversal
	int ptr = 0;
	uint stack[ BVH_STACK_DEPTH ];
	stack[ 0 ] = 0u;

	float closestDistanceSquared = pow( 100000.0, 2.0 );
	bool found = false;
	while ( ptr > - 1 && ptr < BVH_STACK_DEPTH ) {

		uint currNodeIndex = stack[ ptr ];
		ptr --;

		// check if we intersect the current bounds
		float boundsHitDistance = distanceSqToBVHNodeBoundsPoint( point, bvh_bvhBounds, currNodeIndex );
		if ( boundsHitDistance > closestDistanceSquared ) {

			continue;

		}

		uvec2 boundsInfo = uTexelFetch1D( bvh_bvhContents, currNodeIndex ).xy;
		bool isLeaf = bool( boundsInfo.x & 0xffff0000u );
		if ( isLeaf ) {

			uint count = boundsInfo.x & 0x0000ffffu;
			uint offset = boundsInfo.y;
			closestDistanceSquared = distanceToTriangles(
				bvh_position, bvh_index, offset, count, point, closestDistanceSquared,

				// outputs
				faceIndices, faceNormal, barycoord, side, outPoint
			);

		} else {

			uint leftIndex = currNodeIndex + 1u;
			uint splitAxis = boundsInfo.x & 0x0000ffffu;
			uint rightIndex = boundsInfo.y;
			bool leftToRight = distanceSqToBVHNodeBoundsPoint( point, bvh_bvhBounds, leftIndex ) < distanceSqToBVHNodeBoundsPoint( point, bvh_bvhBounds, rightIndex );//rayDirection[ splitAxis ] >= 0.0;
			uint c1 = leftToRight ? leftIndex : rightIndex;
			uint c2 = leftToRight ? rightIndex : leftIndex;

			// set c2 in the stack so we traverse it later. We need to keep track of a pointer in
			// the stack while we traverse. The second pointer added is the one that will be
			// traversed first
			ptr ++;
			stack[ ptr ] = c2;
			ptr ++;
			stack[ ptr ] = c1;

		}

	}

	return sqrt( closestDistanceSquared );

}
`,Wr=`

#ifndef TRI_INTERSECT_EPSILON
#define TRI_INTERSECT_EPSILON 1e-5
#endif

// Raycasting
bool intersectsBounds( vec3 rayOrigin, vec3 rayDirection, vec3 boundsMin, vec3 boundsMax, out float dist ) {

	// https://www.reddit.com/r/opengl/comments/8ntzz5/fast_glsl_ray_box_intersection/
	// https://tavianator.com/2011/ray_box.html
	vec3 invDir = 1.0 / rayDirection;

	// find intersection distances for each plane
	vec3 tMinPlane = invDir * ( boundsMin - rayOrigin );
	vec3 tMaxPlane = invDir * ( boundsMax - rayOrigin );

	// get the min and max distances from each intersection
	vec3 tMinHit = min( tMaxPlane, tMinPlane );
	vec3 tMaxHit = max( tMaxPlane, tMinPlane );

	// get the furthest hit distance
	vec2 t = max( tMinHit.xx, tMinHit.yz );
	float t0 = max( t.x, t.y );

	// get the minimum hit distance
	t = min( tMaxHit.xx, tMaxHit.yz );
	float t1 = min( t.x, t.y );

	// set distance to 0.0 if the ray starts inside the box
	dist = max( t0, 0.0 );

	return t1 >= dist;

}

bool intersectsTriangle(
	vec3 rayOrigin, vec3 rayDirection, vec3 a, vec3 b, vec3 c,
	out vec3 barycoord, out vec3 norm, out float dist, out float side
) {

	// https://stackoverflow.com/questions/42740765/intersection-between-line-and-triangle-in-3d
	vec3 edge1 = b - a;
	vec3 edge2 = c - a;
	norm = cross( edge1, edge2 );

	float det = - dot( rayDirection, norm );
	float invdet = 1.0 / det;

	vec3 AO = rayOrigin - a;
	vec3 DAO = cross( AO, rayDirection );

	vec4 uvt;
	uvt.x = dot( edge2, DAO ) * invdet;
	uvt.y = - dot( edge1, DAO ) * invdet;
	uvt.z = dot( AO, norm ) * invdet;
	uvt.w = 1.0 - uvt.x - uvt.y;

	// set the hit information
	barycoord = uvt.wxy; // arranged in A, B, C order
	dist = uvt.z;
	side = sign( det );
	norm = side * normalize( norm );

	// add an epsilon to avoid misses between triangles
	uvt += vec4( TRI_INTERSECT_EPSILON );

	return all( greaterThanEqual( uvt, vec4( 0.0 ) ) );

}

bool intersectTriangles(
	// geometry info and triangle range
	sampler2D positionAttr, usampler2D indexAttr, uint offset, uint count,

	// ray
	vec3 rayOrigin, vec3 rayDirection,

	// outputs
	inout float minDistance, inout uvec4 faceIndices, inout vec3 faceNormal, inout vec3 barycoord,
	inout float side, inout float dist
) {

	bool found = false;
	vec3 localBarycoord, localNormal;
	float localDist, localSide;
	for ( uint i = offset, l = offset + count; i < l; i ++ ) {

		uvec3 indices = uTexelFetch1D( indexAttr, i ).xyz;
		vec3 a = texelFetch1D( positionAttr, indices.x ).rgb;
		vec3 b = texelFetch1D( positionAttr, indices.y ).rgb;
		vec3 c = texelFetch1D( positionAttr, indices.z ).rgb;

		if (
			intersectsTriangle( rayOrigin, rayDirection, a, b, c, localBarycoord, localNormal, localDist, localSide )
			&& localDist < minDistance
		) {

			found = true;
			minDistance = localDist;

			faceIndices = uvec4( indices.xyz, i );
			faceNormal = localNormal;

			side = localSide;
			barycoord = localBarycoord;
			dist = localDist;

		}

	}

	return found;

}

bool intersectsBVHNodeBounds( vec3 rayOrigin, vec3 rayDirection, sampler2D bvhBounds, uint currNodeIndex, out float dist ) {

	uint cni2 = currNodeIndex * 2u;
	vec3 boundsMin = texelFetch1D( bvhBounds, cni2 ).xyz;
	vec3 boundsMax = texelFetch1D( bvhBounds, cni2 + 1u ).xyz;
	return intersectsBounds( rayOrigin, rayDirection, boundsMin, boundsMax, dist );

}

// use a macro to hide the fact that we need to expand the struct into separate fields
#define	bvhIntersectFirstHit(		bvh,		rayOrigin, rayDirection, faceIndices, faceNormal, barycoord, side, dist	)	_bvhIntersectFirstHit(		bvh.position, bvh.index, bvh.bvhBounds, bvh.bvhContents,		rayOrigin, rayDirection, faceIndices, faceNormal, barycoord, side, dist	)

bool _bvhIntersectFirstHit(
	// bvh info
	sampler2D bvh_position, usampler2D bvh_index, sampler2D bvh_bvhBounds, usampler2D bvh_bvhContents,

	// ray
	vec3 rayOrigin, vec3 rayDirection,

	// output variables split into separate variables due to output precision
	inout uvec4 faceIndices, inout vec3 faceNormal, inout vec3 barycoord,
	inout float side, inout float dist
) {

	// stack needs to be twice as long as the deepest tree we expect because
	// we push both the left and right child onto the stack every traversal
	int ptr = 0;
	uint stack[ BVH_STACK_DEPTH ];
	stack[ 0 ] = 0u;

	float triangleDistance = INFINITY;
	bool found = false;
	while ( ptr > - 1 && ptr < BVH_STACK_DEPTH ) {

		uint currNodeIndex = stack[ ptr ];
		ptr --;

		// check if we intersect the current bounds
		float boundsHitDistance;
		if (
			! intersectsBVHNodeBounds( rayOrigin, rayDirection, bvh_bvhBounds, currNodeIndex, boundsHitDistance )
			|| boundsHitDistance > triangleDistance
		) {

			continue;

		}

		uvec2 boundsInfo = uTexelFetch1D( bvh_bvhContents, currNodeIndex ).xy;
		bool isLeaf = bool( boundsInfo.x & 0xffff0000u );

		if ( isLeaf ) {

			uint count = boundsInfo.x & 0x0000ffffu;
			uint offset = boundsInfo.y;

			found = intersectTriangles(
				bvh_position, bvh_index, offset, count,
				rayOrigin, rayDirection, triangleDistance,
				faceIndices, faceNormal, barycoord, side, dist
			) || found;

		} else {

			uint leftIndex = currNodeIndex + 1u;
			uint splitAxis = boundsInfo.x & 0x0000ffffu;
			uint rightIndex = boundsInfo.y;

			bool leftToRight = rayDirection[ splitAxis ] >= 0.0;
			uint c1 = leftToRight ? leftIndex : rightIndex;
			uint c2 = leftToRight ? rightIndex : leftIndex;

			// set c2 in the stack so we traverse it later. We need to keep track of a pointer in
			// the stack while we traverse. The second pointer added is the one that will be
			// traversed first
			ptr ++;
			stack[ ptr ] = c2;

			ptr ++;
			stack[ ptr ] = c1;

		}

	}

	return found;

}
`,Gr=`
struct BVH {

	usampler2D index;
	sampler2D position;

	sampler2D bvhBounds;
	usampler2D bvhContents;

};
`,Kr=i({bvh_distance_functions:()=>Ur,bvh_ray_functions:()=>Wr,bvh_struct_definitions:()=>Gr,common_functions:()=>Hr}),qr=Gr,Jr=Ur,Yr=`
	${Hr}
	${Wr}
`;export{se as AVERAGE,Kr as BVHShaderGLSL,oe as CENTER,de as CONTAINED,R as ExtendedTriangle,br as FloatVertexAttributeTexture,ue as INTERSECTED,yr as IntVertexAttributeTexture,Ln as MeshBVH,Vn as MeshBVHHelper,xr as MeshBVHUniformStruct,le as NOT_INTERSECTED,z as OrientedBox,ce as SAH,Vr as StaticGeometryGenerator,vr as UIntVertexAttributeTexture,_r as VertexAttributeTexture,sr as acceleratedRaycast,fr as computeBatchedBoundsTree,ur as computeBoundsTree,pr as disposeBatchedBoundsTree,dr as disposeBoundsTree,Yn as estimateMemoryInBytes,Jn as getBVHExtremes,Zn as getJSONStructure,Dt as getTriangleHitPointInfo,Jr as shaderDistanceFunction,Yr as shaderIntersectFunction,qr as shaderStructs,Xn as validateBounds};