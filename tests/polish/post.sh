# post.sh RAW OUT TEXSIZE : gltf-transform meshopt + webp, then Khronos glTF-Validator (node module in /workspace/barclay/.gltf)
set -e
G=$(cd "$(dirname "$0")/../.." && pwd)/.gltf/node_modules
RAW=$1; OUT=$2; SZ=$3
npx -y @gltf-transform/cli@4 optimize "$RAW" "$OUT" --compress meshopt --texture-compress webp --texture-size $SZ --simplify false --join false --flatten false --instance false >/dev/null 2>&1
ls -la "$OUT" | awk '{print $5, $9}'
node -e "
const v=require('$G/gltf-validator');const b=require('fs').readFileSync('$OUT');
v.validateBytes(new Uint8Array(b),{maxIssues:200}).then(r=>{const i=r.issues;console.log('VALIDATOR',JSON.stringify({errors:i.numErrors,warnings:i.numWarnings,infos:i.numInfos,hints:i.numHints}));i.messages.filter(m=>m.severity==0).slice(0,8).forEach(m=>console.log(m.code,m.message,m.pointer))})"
