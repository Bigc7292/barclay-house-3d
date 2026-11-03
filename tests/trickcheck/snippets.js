// #2 meshopt loading (three.js)
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
loader.setMeshoptDecoder(MeshoptDecoder);            // model-viewer: ModelViewerElement.meshoptDecoderLocation='./meshopt_decoder.js'
// #3 glass + faience (GLB already carries KHR_materials_clearcoat 0.6/0.15 on Burmantofts_white_glazed_faience; glass has none)
const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
gltf.scene.traverse(o => { if (!o.isMesh) return;
  if (o.material.name === 'Glass_dark') o.material = new THREE.MeshPhysicalMaterial({ color: 0x1a2228, roughness: 0.05, metalness: 0,
    transmission: isMobile ? 0 : 0.9, ior: 1.52, thickness: 0.01, transparent: true, opacity: isMobile ? 0.85 : 1, clearcoat: 1, clearcoatRoughness: 0.05 }); });
// #10 canal water (MIT three/examples/jsm/objects/Water.js + textures/waternormals.jpg)
import { Water } from 'three/addons/objects/Water.js';
const canal = gltf.scene.getObjectByName('Canal_water');
const water = new Water(canal.geometry, { textureWidth: isMobile ? 256 : 512, textureHeight: isMobile ? 256 : 512,
  waterNormals: new THREE.TextureLoader().load('waternormals.jpg', t => t.wrapS = t.wrapT = THREE.RepeatWrapping),
  sunDirection: sunDir.clone().normalize(), sunColor: 0xffffff, waterColor: 0x1e2b22, distortionScale: 1.2 });
water.position.copy(canal.position); water.quaternion.copy(canal.quaternion); canal.parent.add(water); canal.visible = false;
renderer.setAnimationLoop(() => { water.material.uniforms.time.value += 0.25 / 60; /* slow canal */ renderer.render(scene, camera); });
