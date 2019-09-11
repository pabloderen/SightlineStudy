var scene = new THREE.Scene();
        //Selection 
        var raycaster = new THREE.Raycaster();
        var mouse = new THREE.Vector2(), INTERSECTED;
        //https://discourse.threejs.org/t/gltf-loading-but-not-appearing/911/7
        // Load Camera Perspektive
        var camera = new THREE.PerspectiveCamera(25, window.innerWidth / window.innerHeight, 1, 20000);
        camera.position.set(50, 50, 100);

        // Load a Renderer
        var renderer = new THREE.WebGLRenderer({ alpha: false });
        renderer.setClearColor(0xC5C5C3);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);

        //Click select

        function onMouseClick(event) {

            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = - (event.clientY / window.innerHeight) * 2 + 1;


            raycaster.setFromCamera(mouse, camera);
            var intersects = raycaster.intersectObjects(scene.children, true);
            if (intersects.length > 0) {
                if (INTERSECTED != intersects[0].object) {
                    if (INTERSECTED) INTERSECTED.material.emissive.setHex(INTERSECTED.currentHex);
                    INTERSECTED = intersects[0].object;
                    INTERSECTED.currentHex = INTERSECTED.material.emissive.getHex();
                    INTERSECTED.material.emissive.setHex(0xff0000);
                }
            } else {
                if (INTERSECTED) INTERSECTED.material.emissive.setHex(INTERSECTED.currentHex);
                INTERSECTED = null;
            }

            renderer.render(scene, camera);
            console.log(INTERSECTED);

        }

        // Load the Orbitcontroller
        var controls = new THREE.OrbitControls(camera, renderer.domElement);

        // Load Light
        var ambientLight = new THREE.AmbientLight(0xcccccc);
        scene.add(ambientLight);

        var directionalLight = new THREE.DirectionalLight(0xffffff);
        directionalLight.position.set(0, 1, 1).normalize();
        scene.add(directionalLight);

        // glTf 2.0 Loader
        var loader = new THREE.GLTFLoader();
        loader.load('model/Untitled.gltf', function (gltf) {

            for (let index = 0; index < gltf.scene.children.length; index++) {
                const element = gltf.scene.children[index];
                scene.add(element);
            }

        });



        function render() {

            renderer.render(scene, camera);

        }

        window.addEventListener('dblclick', onMouseClick);


        function animate() {
            render();
            requestAnimationFrame(animate);
        }

        render();
        animate();