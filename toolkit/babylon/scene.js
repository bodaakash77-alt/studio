// Paste into https://playground.babylonjs.com/ (replaces default code). Playground exposes BABYLON globally.
// Scene: sunset hill, boy with red helmet, green visor, red T-shirt, blue jeans, red shoes; slow push-in.
var createScene = function () {
  var scene = new BABYLON.Scene(engine);
  scene.clearColor = new BABYLON.Color4(0.96, 0.82, 0.66, 1);

  var camera = new BABYLON.UniversalCamera("cam", new BABYLON.Vector3(0, 2.2, 14), scene);
  camera.setTarget(new BABYLON.Vector3(0, 1.4, 0));
  camera.fov = 0.62;

  var hemi = new BABYLON.HemisphericLight("hemi", new BABYLON.Vector3(0, 1, 0), scene);
  hemi.intensity = 0.8; hemi.groundColor = new BABYLON.Color3(0.35, 0.28, 0.2);
  var sun = new BABYLON.DirectionalLight("sun", new BABYLON.Vector3(-0.6, -0.8, -0.4), scene);
  sun.intensity = 2.2; sun.diffuse = new BABYLON.Color3(1, 0.85, 0.65);
  var shadows = new BABYLON.ShadowGenerator(2048, sun);
  shadows.useBlurExponentialShadowMap = true;

  var mat = function (name, rgb, rough) {
    var m = new BABYLON.PBRMaterial(name, scene);
    m.albedoColor = new BABYLON.Color3(rgb[0], rgb[1], rgb[2]);
    m.roughness = rough; m.metallic = 0; return m;
  };

  var ground = BABYLON.MeshBuilder.CreateGround("g", { width: 200, height: 200 }, scene);
  ground.material = mat("gm", [0.45, 0.5, 0.3], 0.95); ground.receiveShadows = true;

  var hill = BABYLON.MeshBuilder.CreateSphere("hill", { diameterX: 18, diameterY: 8, diameterZ: 12, segments: 24 }, scene);
  hill.position = new BABYLON.Vector3(0, -2.5, -7); hill.material = mat("hm", [0.35, 0.5, 0.25], 0.9);
  hill.receiveShadows = true;

  // character (origin at feet)
  var root = new BABYLON.TransformNode("boy", scene); root.position = new BABYLON.Vector3(1.8, 0, 0);
  var part = function (mesh, mt, x, y, z) {
    mesh.material = mt; mesh.position = new BABYLON.Vector3(x, y, z);
    mesh.parent = root; shadows.addShadowCaster(mesh); return mesh;
  };
  var jeans = mat("jeans", [0.12, 0.25, 0.6], 0.7), red = mat("red", [0.85, 0.08, 0.08], 0.6),
      skin = mat("skin", [0.75, 0.55, 0.42], 0.6), helmet = mat("helmet", [0.9, 0.06, 0.06], 0.35),
      visor = mat("visor", [0.1, 0.85, 0.3], 0.1), shoe = mat("shoe", [0.8, 0.05, 0.05], 0.5);
  part(BABYLON.MeshBuilder.CreateCylinder("l1", { height: 0.9, diameter: 0.42 }, scene), jeans, -0.13, 0.45, 0);
  part(BABYLON.MeshBuilder.CreateCylinder("l2", { height: 0.9, diameter: 0.42 }, scene), jeans, 0.13, 0.45, 0);
  part(BABYLON.MeshBuilder.CreateBox("s1", { width: 0.12, height: 0.08, depth: 0.24 }, scene), shoe, -0.13, 0.04, 0.05);
  part(BABYLON.MeshBuilder.CreateBox("s2", { width: 0.12, height: 0.08, depth: 0.24 }, scene), shoe, 0.13, 0.04, 0.05);
  part(BABYLON.MeshBuilder.CreateBox("tee", { width: 0.55, height: 0.62, depth: 0.3 }, scene), red, 0, 1.2, 0);
  part(BABYLON.MeshBuilder.CreateSphere("head", { diameter: 0.4 }, scene), skin, 0, 1.78, 0);
  part(BABYLON.MeshBuilder.CreateSphere("helm", { diameter: 0.5, slice: 0.5 }, scene), helmet, 0, 1.84, 0);
  part(BABYLON.MeshBuilder.CreateBox("vis", { width: 0.34, height: 0.09, depth: 0.05 }, scene), visor, 0, 1.78, -0.2);

  // slow push-in with ease-in-out, 8 s at 30 fps (240 frames)
  var anim = new BABYLON.Animation("push", "position", 30, BABYLON.Animation.ANIMATIONTYPE_VECTOR3, BABYLON.Animation.ANIMATIONLOOPMODE_CONSTANT);
  anim.setKeys([{ frame: 0, value: new BABYLON.Vector3(0, 2.2, 14) }, { frame: 240, value: new BABYLON.Vector3(0, 2.0, 7.5) }]);
  var ease = new BABYLON.CubicEase(); ease.setEasingMode(BABYLON.EasingFunction.EASINGMODE_EASEINOUT); anim.setEasingFunction(ease);
  camera.animations = [anim];
  scene.beginAnimation(camera, 0, 240, false);
  return scene;
};
