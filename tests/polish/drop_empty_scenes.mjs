import {NodeIO} from '@gltf-transform/core';import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);const [i,o]=process.argv.slice(2);const d=await io.read(i);
const r=d.getRoot();for(const s of r.listScenes())if(s.listChildren().length===0)s.dispose();r.setDefaultScene(r.listScenes()[0]);await io.write(o,d);console.log('scenes',r.listScenes().length)
