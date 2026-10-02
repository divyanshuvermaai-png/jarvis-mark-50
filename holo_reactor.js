/**
 * J.A.R.V.I.S. Center Stage 3D Holographic Arc Reactor — Cinema Prop Edition
 * Full-fidelity Three.js Arc Reactor matching the Marvel Studios Iron Man prop:
 * - 10 Copper-wound solenoids with 7 stacked micro-wire turns & brass lugs
 * - Laser-cut clear acrylic ring with internal frosted cyan light pipe
 * - 20 Countersunk Allen socket-cap bolts with dark hex recesses
 * - 3 Heavy chest-mount retaining clamps at 120° (-90°, 30°, 150°)
 * - Multi-element anamorphic lens flare with 4-point starburst
 * - 3 Concentric Fresnel caustic ridges on quartz dome cap
 * - 60 Orbiting quantum embers with physics damping
 * - Procedural high-voltage electric discharge arcs
 * - Live audio reactivity, voice pulsation, and interactive mouse parallax
 */
import * as THREE from './three.module.min.js';

class HoloReactorApp {
    constructor() {
        this.container = document.querySelector('.center-hologram');
        if (!this.container) return;

        this.canvas = document.createElement('canvas');
        this.canvas.id = 'holoReactorCanvas';
        this.canvas.style.position = 'absolute';
        this.canvas.style.inset = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '1';

        this.container.innerHTML = '';
        this.container.appendChild(this.canvas);

        this.width = this.container.clientWidth || 640;
        this.height = this.container.clientHeight || 640;

        // Scene, Camera, Renderer
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(42, this.width / this.height, 0.1, 100);
        this.camera.position.set(0, 0.8, 8.8);

        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            alpha: true,
            antialias: true,
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(this.width, this.height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.28;

        // State
        this.time = 0;
        this.isSpeaking = false;
        this.isListening = false;
        this.surgeIntensity = 0;
        this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
        this.holoMode = 'reactor';

        this.buildLighting();
        this.buildReactor();
        this.buildMarkSuitArmor();
        this.buildGauntlet();
        this.buildAnamorphicFlare();
        this.buildParticles();
        this.buildEnergyArcs();
        this.bindEvents();
        this.animate = this.animate.bind(this);
        requestAnimationFrame(this.animate);
    }

    buildLighting() {
        const ambient = new THREE.AmbientLight(0x001a33, 0.9);
        this.scene.add(ambient);

        // Crisp white key light catching copper turns, chrome bolts, and aluminum bevels
        const keyLight = new THREE.DirectionalLight(0xffffff, 3.4);
        keyLight.position.set(6, 8, 11);
        this.scene.add(keyLight);

        // Electric cyan rim light outlining outer casing
        const cyanRim = new THREE.DirectionalLight(0x00e5ff, 2.6);
        cyanRim.position.set(-5, 6, -7);
        this.scene.add(cyanRim);

        // Deep blue underside fill light
        const blueFill = new THREE.DirectionalLight(0x0055bb, 1.4);
        blueFill.position.set(0, -6, 6);
        this.scene.add(blueFill);
    }

    buildReactor() {
        this.rootGroup = new THREE.Group();
        this.scene.add(this.rootGroup);

        // ── PBR Materials ──
        this.copperMat = new THREE.MeshStandardMaterial({
            color: 0xb45322,
            metalness: 0.96,
            roughness: 0.16
        });

        this.chromeMat = new THREE.MeshStandardMaterial({
            color: 0xddeef8,
            metalness: 0.98,
            roughness: 0.08
        });

        this.brushedAlloyMat = new THREE.MeshStandardMaterial({
            color: 0x8fa2b4,
            metalness: 0.92,
            roughness: 0.28
        });

        this.darkAlloyMat = new THREE.MeshStandardMaterial({
            color: 0x12171f,
            metalness: 0.88,
            roughness: 0.38
        });

        this.goldMat = new THREE.MeshStandardMaterial({
            color: 0xd4af37,
            metalness: 0.92,
            roughness: 0.18
        });

        // 1. Central Core & Cathode Emitter
        this.reactorGroup = new THREE.Group();
        this.rootGroup.add(this.reactorGroup);

        this.coreGroup = new THREE.Group();
        this.reactorGroup.add(this.coreGroup);

        // White-hot central singularity
        this.singularity = new THREE.Mesh(
            new THREE.SphereGeometry(0.32, 32, 32),
            new THREE.MeshBasicMaterial({ color: 0xffffff })
        );
        this.coreGroup.add(this.singularity);

        // Vibranium plasma sphere
        this.plasmaSphere = new THREE.Mesh(
            new THREE.SphereGeometry(0.52, 32, 32),
            new THREE.MeshBasicMaterial({
                color: 0x00e5ff,
                transparent: true,
                opacity: 0.65,
                wireframe: true
            })
        );
        this.coreGroup.add(this.plasmaSphere);

        // 3 Concentric Fresnel Caustic Ridges on the Core Cap
        for (let r = 0; r < 3; r++) {
            const ridgeRadius = 0.62 + r * 0.15;
            const ridge = new THREE.Mesh(
                new THREE.TorusGeometry(ridgeRadius, 0.024, 16, 48),
                new THREE.MeshStandardMaterial({
                    color: 0x00e5ff,
                    metalness: 0.85,
                    roughness: 0.12,
                    emissive: 0x00a8ff,
                    emissiveIntensity: 0.8
                })
            );
            ridge.position.z = 0.04 - r * 0.02;
            this.coreGroup.add(ridge);
        }

        // Stepped cathode outer collar
        const cathodeCollar = new THREE.Mesh(
            new THREE.TorusGeometry(1.02, 0.038, 16, 56),
            this.chromeMat
        );
        cathodeCollar.position.z = 0.08;
        this.coreGroup.add(cathodeCollar);

        // Central 3-Point Aperture Teeth
        for (let i = 0; i < 3; i++) {
            const angle = (i * 120 * Math.PI) / 180;
            const tooth = new THREE.Mesh(
                new THREE.BoxGeometry(0.08, 0.28, 0.08),
                this.chromeMat
            );
            tooth.position.set(Math.cos(angle) * 0.88, Math.sin(angle) * 0.88, 0.08);
            tooth.rotation.z = angle + Math.PI / 2;
            this.coreGroup.add(tooth);
        }

        // 2. Clear Acrylic Base Ring with Internal Glowing Light Pipe
        const acrylicRing = new THREE.Mesh(
            new THREE.TorusGeometry(2.05, 0.38, 32, 80),
            new THREE.MeshPhysicalMaterial({
                color: 0x001428,
                metalness: 0.1,
                roughness: 0.06,
                transmission: 0.72,
                transparent: true,
                opacity: 0.68
            })
        );
        this.reactorGroup.add(acrylicRing);

        this.glowTube = new THREE.Mesh(
            new THREE.TorusGeometry(2.05, 0.24, 24, 80),
            new THREE.MeshBasicMaterial({
                color: 0x00e5ff,
                transparent: true,
                opacity: 0.75
            })
        );
        this.reactorGroup.add(this.glowTube);

        // Circular PCB Ring behind Solenoids with 10 SMD Micro-LEDs
        const pcbRing = new THREE.Mesh(
            new THREE.RingGeometry(1.72, 2.38, 64),
            new THREE.MeshStandardMaterial({
                color: 0x0a1e1e,
                metalness: 0.6,
                roughness: 0.4,
                side: THREE.DoubleSide
            })
        );
        pcbRing.position.z = -0.12;
        this.reactorGroup.add(pcbRing);

        this.smdLeds = [];
        for (let i = 0; i < 10; i++) {
            const angle = (i * 36 + 18) * (Math.PI / 180);
            const led = new THREE.Mesh(
                new THREE.BoxGeometry(0.06, 0.04, 0.03),
                new THREE.MeshBasicMaterial({ color: i % 2 === 0 ? 0x00e5ff : 0xffaa00 })
            );
            led.position.set(Math.cos(angle) * 2.05, Math.sin(angle) * 2.05, -0.09);
            led.rotation.z = angle;
            this.reactorGroup.add(led);
            this.smdLeds.push(led);
        }

        // 3. 10 Movie-Accurate Solenoids with Real Copper Windings
        this.solenoidGroup = new THREE.Group();
        this.reactorGroup.add(this.solenoidGroup);

        for (let i = 0; i < 10; i++) {
            const angle = (i * 36 * Math.PI) / 180;
            const x = Math.cos(angle) * 2.05;
            const y = Math.sin(angle) * 2.05;

            const coil = new THREE.Group();
            coil.position.set(x, y, 0.14);
            coil.rotation.z = angle;

            // Dark Delrin Bobbin Block
            const bobbin = new THREE.Mesh(
                new THREE.BoxGeometry(0.38, 0.54, 0.36),
                this.darkAlloyMat
            );
            coil.add(bobbin);

            // 7 Real Copper Wire Windings
            for (let w = -3; w <= 3; w++) {
                const wireTurn = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.24, 0.24, 0.048, 24),
                    this.copperMat
                );
                wireTurn.position.y = w * 0.066;
                wireTurn.rotation.x = Math.PI / 2;
                coil.add(wireTurn);
            }

            // Mirror-Chrome Retaining Strap
            const band = new THREE.Mesh(
                new THREE.BoxGeometry(0.42, 0.085, 0.4),
                this.chromeMat
            );
            band.position.z = 0.09;
            coil.add(band);

            // Brass Terminal Lugs
            const lug1 = new THREE.Mesh(
                new THREE.CylinderGeometry(0.026, 0.026, 0.09, 10),
                this.goldMat
            );
            lug1.position.set(0.12, 0.24, 0.16);
            lug1.rotation.x = Math.PI / 2;
            coil.add(lug1);

            const lug2 = lug1.clone();
            lug2.position.x = -0.12;
            coil.add(lug2);

            this.solenoidGroup.add(coil);
        }

        // 4. CNC Brushed Aluminum Outer Bezel with 20 Countersunk Allen Screws
        const outerBezel = new THREE.Mesh(
            new THREE.TorusGeometry(2.58, 0.13, 24, 72),
            this.brushedAlloyMat
        );
        this.reactorGroup.add(outerBezel);

        // 20 Countersunk Allen Bolts with Hex Recesses
        for (let i = 0; i < 20; i++) {
            const angle = (i * 18 * Math.PI) / 180;
            const bolt = new THREE.Mesh(
                new THREE.CylinderGeometry(0.048, 0.048, 0.045, 14),
                this.chromeMat
            );
            bolt.position.set(Math.cos(angle) * 2.58, Math.sin(angle) * 2.58, 0.13);
            bolt.rotation.x = Math.PI / 2;

            // Dark Hex Socket Recess
            const socket = new THREE.Mesh(
                new THREE.CylinderGeometry(0.023, 0.023, 0.05, 6),
                this.darkAlloyMat
            );
            socket.position.set(0, 0.012, 0);
            bolt.add(socket);

            this.reactorGroup.add(bolt);
        }

        // 5. 3 Heavy Chest-Mount Retaining Clamps at 120 Degrees (-90°, 30°, 150°)
        const clampAngles = [-Math.PI / 2, Math.PI / 6, (5 * Math.PI) / 6];
        clampAngles.forEach((angle) => {
            const clampGroup = new THREE.Group();
            clampGroup.position.set(Math.cos(angle) * 2.72, Math.sin(angle) * 2.72, 0.15);
            clampGroup.rotation.z = angle + Math.PI / 2;

            // Heavy Titanium Mounting Arm
            const arm = new THREE.Mesh(
                new THREE.BoxGeometry(0.26, 0.58, 0.2),
                this.darkAlloyMat
            );
            clampGroup.add(arm);

            // Large Hex Bolt with Brass Washer
            const bolt = new THREE.Mesh(
                new THREE.CylinderGeometry(0.065, 0.065, 0.26, 12),
                this.chromeMat
            );
            bolt.rotation.x = Math.PI / 2;
            clampGroup.add(bolt);

            const washer = new THREE.Mesh(
                new THREE.CylinderGeometry(0.09, 0.09, 0.03, 12),
                this.goldMat
            );
            washer.rotation.x = Math.PI / 2;
            washer.position.z = -0.05;
            clampGroup.add(washer);

            this.reactorGroup.add(clampGroup);
        });

        // 6. Holographic Blueprint Reticles
        this.reticle1 = new THREE.Mesh(
            new THREE.RingGeometry(2.85, 2.88, 72),
            new THREE.MeshBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0.4, side: THREE.DoubleSide })
        );
        this.reticle1.position.z = -0.15;
        this.reactorGroup.add(this.reticle1);

        this.reticle2 = new THREE.Mesh(
            new THREE.RingGeometry(3.18, 3.2, 56),
            new THREE.MeshBasicMaterial({ color: 0x0066ff, transparent: true, opacity: 0.28, side: THREE.DoubleSide })
        );
        this.reticle2.position.z = -0.28;
        this.reactorGroup.add(this.reticle2);
    }

    buildAnamorphicFlare() {
        this.flareGroup = new THREE.Group();
        this.flareGroup.position.z = 0.22;
        this.reactorGroup.add(this.flareGroup);

        // Horizontal Anamorphic Flare Streak (Marvel Cinema Signature)
        const streakGeo = new THREE.PlaneGeometry(5.2, 0.08);
        const streakMat = new THREE.MeshBasicMaterial({
            color: 0x00e5ff,
            transparent: true,
            opacity: 0.65,
            blending: THREE.AdditiveBlending,
            side: THREE.DoubleSide
        });
        this.streak = new THREE.Mesh(streakGeo, streakMat);
        this.flareGroup.add(this.streak);

        // 4-Point Starburst Cross-Flares
        for (let i = 0; i < 4; i++) {
            const rot = (i * 45 * Math.PI) / 180;
            const beam = new THREE.Mesh(
                new THREE.PlaneGeometry(1.8, 0.04),
                new THREE.MeshBasicMaterial({
                    color: 0xffffff,
                    transparent: true,
                    opacity: 0.75,
                    blending: THREE.AdditiveBlending,
                    side: THREE.DoubleSide
                })
            );
            beam.rotation.z = rot;
            this.flareGroup.add(beam);
        }
    }

    buildParticles() {
        const count = 60;
        const positions = new Float32Array(count * 3);
        const angles = new Float32Array(count);
        const radii = new Float32Array(count);
        const speeds = new Float32Array(count);
        const heights = new Float32Array(count);

        for (let i = 0; i < count; i++) {
            angles[i] = Math.random() * Math.PI * 2;
            radii[i] = 0.7 + Math.random() * 2.3;
            speeds[i] = 0.4 + Math.random() * 0.9;
            heights[i] = (Math.random() - 0.5) * 0.9;

            positions[i * 3] = Math.cos(angles[i]) * radii[i];
            positions[i * 3 + 1] = Math.sin(angles[i]) * radii[i];
            positions[i * 3 + 2] = heights[i];
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const mat = new THREE.PointsMaterial({
            color: 0x00e5ff,
            size: 0.09,
            transparent: true,
            opacity: 0.9,
            blending: THREE.AdditiveBlending
        });

        this.particleData = { geo, angles, radii, speeds, heights, count };
        this.particles = new THREE.Points(geo, mat);
        this.rootGroup.add(this.particles);
    }

    buildEnergyArcs() {
        this.arcGroup = new THREE.Group();
        this.reactorGroup.add(this.arcGroup);
        this.arcs = [];

        const arcMat = new THREE.LineBasicMaterial({
            color: 0x99ffff,
            transparent: true,
            opacity: 0.85,
            blending: THREE.AdditiveBlending
        });

        for (let i = 0; i < 5; i++) {
            const curve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(0, 0, 0.12),
                new THREE.Vector3(0.6, 0.4, 0.22),
                new THREE.Vector3(1.2, 0.9, 0.14),
                new THREE.Vector3(2.05, 0, 0.15)
            ]);
            const geo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(24));
            const line = new THREE.Line(geo, arcMat);
            line.visible = false;
            this.arcGroup.add(line);
            this.arcs.push({ line });
        }
    }

    buildMarkSuitArmor() {
        this.suitGroup = new THREE.Group();
        this.suitGroup.visible = false;
        this.rootGroup.add(this.suitGroup);

        const armorWireMat = new THREE.MeshBasicMaterial({
            color: 0x00e5ff,
            wireframe: true,
            transparent: true,
            opacity: 0.55
        });

        const goldTrimMat = new THREE.MeshStandardMaterial({
            color: 0xc49a2a,
            metalness: 0.9,
            roughness: 0.22,
            transparent: true,
            opacity: 0.92
        });

        const crimsonMat = new THREE.MeshStandardMaterial({
            color: 0x5a0b12,
            metalness: 0.88,
            roughness: 0.25,
            transparent: true,
            opacity: 0.92
        });

        const glowCyanMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
        const glowWhiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

        // ── 1. HELMET ──
        const headGroup = new THREE.Group();
        headGroup.position.set(0, 1.85, 0);

        const domeGeo = new THREE.DodecahedronGeometry(0.5, 1);
        headGroup.add(new THREE.Mesh(domeGeo, crimsonMat));
        headGroup.add(new THREE.Mesh(domeGeo, armorWireMat));

        const faceplate = new THREE.Mesh(
            new THREE.BoxGeometry(0.55, 0.65, 0.25),
            goldTrimMat
        );
        faceplate.position.set(0, -0.05, 0.32);
        faceplate.rotation.x = 0.12;
        headGroup.add(faceplate);

        [-0.14, 0.14].forEach(x => {
            const eye = new THREE.Mesh(
                new THREE.BoxGeometry(0.14, 0.04, 0.08),
                glowCyanMat
            );
            eye.position.set(x, 0.02, 0.46);
            eye.rotation.z = (x < 0 ? 0.15 : -0.15);
            headGroup.add(eye);
        });

        [-0.48, 0.48].forEach(x => {
            const ear = new THREE.Mesh(
                new THREE.CylinderGeometry(0.1, 0.1, 0.12, 16),
                goldTrimMat
            );
            ear.position.set(x, -0.05, 0.05);
            ear.rotation.z = Math.PI / 2;
            headGroup.add(ear);
        });

        this.suitGroup.add(headGroup);

        // ── 2. TORSO & MINI CHEST ARC REACTOR ──
        const torsoGroup = new THREE.Group();
        torsoGroup.position.set(0, 0.65, 0);

        const chestGeo = new THREE.BoxGeometry(1.6, 0.95, 0.75);
        torsoGroup.add(new THREE.Mesh(chestGeo, crimsonMat));
        torsoGroup.add(new THREE.Mesh(chestGeo, armorWireMat));

        [-0.45, 0.45].forEach(x => {
            const wing = new THREE.Mesh(
                new THREE.BoxGeometry(0.5, 0.65, 0.15),
                goldTrimMat
            );
            wing.position.set(x, 0.1, 0.4);
            wing.rotation.z = (x < 0 ? -0.15 : 0.15);
            torsoGroup.add(wing);
        });

        const chestArcGroup = new THREE.Group();
        chestArcGroup.position.set(0, 0.15, 0.42);

        const arcBezel = new THREE.Mesh(
            new THREE.TorusGeometry(0.18, 0.035, 16, 32),
            goldTrimMat
        );
        chestArcGroup.add(arcBezel);

        this.suitArcCore = new THREE.Mesh(
            new THREE.CylinderGeometry(0.12, 0.12, 0.06, 24),
            glowWhiteMat
        );
        this.suitArcCore.rotation.x = Math.PI / 2;
        chestArcGroup.add(this.suitArcCore);

        for (let i = 0; i < 4; i++) {
            const ang = (i * Math.PI) / 2 + Math.PI / 4;
            const conduit = new THREE.Mesh(
                new THREE.BoxGeometry(0.04, 0.28, 0.02),
                glowCyanMat
            );
            conduit.position.set(Math.cos(ang) * 0.28, Math.sin(ang) * 0.28, 0.02);
            conduit.rotation.z = ang;
            chestArcGroup.add(conduit);
        }
        torsoGroup.add(chestArcGroup);

        for (let i = 0; i < 4; i++) {
            const abW = 1.05 - i * 0.08;
            const ab = new THREE.Mesh(
                new THREE.BoxGeometry(abW, 0.18, 0.65 - i * 0.04),
                goldTrimMat
            );
            ab.position.set(0, -0.6 - i * 0.22, 0.02);
            torsoGroup.add(ab);
        }

        this.suitGroup.add(torsoGroup);

        // ── 3. SHOULDERS & ARMS ──
        [-1, 1].forEach(side => {
            const armGroup = new THREE.Group();
            armGroup.position.set(side * 1.15, 0.95, 0);

            const pauldronGeo = new THREE.SphereGeometry(0.38, 16, 16);
            pauldronGeo.scale(1.2, 0.8, 1.0);
            const pauldron = new THREE.Mesh(pauldronGeo, crimsonMat);
            pauldron.position.set(side * 0.15, 0.1, 0);
            armGroup.add(pauldron);

            const bicep = new THREE.Mesh(
                new THREE.CylinderGeometry(0.2, 0.18, 0.65, 16),
                goldTrimMat
            );
            bicep.position.set(side * 0.18, -0.4, 0);
            armGroup.add(bicep);

            const gauntlet = new THREE.Mesh(
                new THREE.CylinderGeometry(0.22, 0.16, 0.7, 16),
                crimsonMat
            );
            gauntlet.position.set(side * 0.22, -1.05, 0.1);
            armGroup.add(gauntlet);

            const repulsor = new THREE.Mesh(
                new THREE.CylinderGeometry(0.09, 0.09, 0.04, 16),
                glowCyanMat
            );
            repulsor.position.set(side * 0.24, -1.5, 0.14);
            repulsor.rotation.x = Math.PI / 2;
            armGroup.add(repulsor);

            this.suitGroup.add(armGroup);
        });

        // ── 4. LEGS & BOOT THRUSTERS ──
        [-0.45, 0.45].forEach(side => {
            const legGroup = new THREE.Group();
            legGroup.position.set(side, -0.4, 0);

            const thigh = new THREE.Mesh(
                new THREE.BoxGeometry(0.48, 0.95, 0.52),
                goldTrimMat
            );
            thigh.position.set(0, -0.45, 0);
            legGroup.add(thigh);

            const knee = new THREE.Mesh(
                new THREE.BoxGeometry(0.42, 0.24, 0.2),
                crimsonMat
            );
            knee.position.set(0, -0.98, 0.25);
            legGroup.add(knee);

            const calf = new THREE.Mesh(
                new THREE.CylinderGeometry(0.24, 0.19, 0.95, 16),
                crimsonMat
            );
            calf.position.set(0, -1.55, 0);
            legGroup.add(calf);

            const thruster = new THREE.Mesh(
                new THREE.ConeGeometry(0.18, 0.35, 16),
                glowCyanMat
            );
            thruster.position.set(0, -2.15, 0.05);
            thruster.rotation.x = Math.PI;
            legGroup.add(thruster);

            this.suitGroup.add(legGroup);
        });

        // ── 5. HOLOGRAPHIC SCAN RING ──
        const scanRingGeo = new THREE.TorusGeometry(1.65, 0.02, 16, 64);
        this.suitScanRing = new THREE.Mesh(
            scanRingGeo,
            new THREE.MeshBasicMaterial({
                color: 0x00e5ff,
                transparent: true,
                opacity: 0.8
            })
        );
        this.suitScanRing.rotation.x = Math.PI / 2;
        this.suitGroup.add(this.suitScanRing);
    }

    buildGauntlet() {
        this.gauntletGroup = new THREE.Group();
        this.gauntletGroup.visible = false;
        this.rootGroup.add(this.gauntletGroup);

        const goldMat = new THREE.MeshStandardMaterial({
            color: 0xd4af37, metalness: 0.92, roughness: 0.18
        });
        const crimsonMat = new THREE.MeshStandardMaterial({
            color: 0x6e0e18, metalness: 0.88, roughness: 0.22
        });
        const glowCyanMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
        const glowWhiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

        const arm = new THREE.Mesh(
            new THREE.CylinderGeometry(0.85, 0.65, 2.2, 16),
            crimsonMat
        );
        arm.position.set(0, -0.5, 0);
        this.gauntletGroup.add(arm);

        const cowl = new THREE.Mesh(
            new THREE.BoxGeometry(1.1, 1.8, 0.4),
            goldMat
        );
        cowl.position.set(0, -0.4, -0.4);
        this.gauntletGroup.add(cowl);

        const palm = new THREE.Mesh(
            new THREE.BoxGeometry(1.2, 1.0, 0.45),
            goldMat
        );
        palm.position.set(0, 0.9, 0);
        this.gauntletGroup.add(palm);

        const repBezel = new THREE.Mesh(
            new THREE.TorusGeometry(0.38, 0.05, 16, 32),
            goldMat
        );
        repBezel.position.set(0, 0.9, 0.25);
        this.gauntletGroup.add(repBezel);

        this.gauntletLens = new THREE.Mesh(
            new THREE.CylinderGeometry(0.32, 0.32, 0.08, 32),
            glowWhiteMat
        );
        this.gauntletLens.position.set(0, 0.9, 0.26);
        this.gauntletLens.rotation.x = Math.PI / 2;
        this.gauntletGroup.add(this.gauntletLens);

        const missilePod = new THREE.Mesh(
            new THREE.BoxGeometry(0.65, 0.4, 0.3),
            crimsonMat
        );
        missilePod.position.set(0, 0.4, -0.45);
        this.gauntletGroup.add(missilePod);

        [-0.42, -0.21, 0, 0.21, 0.42].forEach((x) => {
            const fGroup = new THREE.Group();
            fGroup.position.set(x, 1.4, 0);

            const p1 = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.35, 0.16), crimsonMat);
            p1.position.y = 0.18;
            fGroup.add(p1);

            const p2 = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.3, 0.14), goldMat);
            p2.position.y = 0.48;
            fGroup.add(p2);

            const led = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 8), glowCyanMat);
            led.position.set(0, 0.02, 0.08);
            fGroup.add(led);

            this.gauntletGroup.add(fGroup);
        });
    }

    setHoloMode(mode) {
        this.holoMode = mode;
        this.surgeIntensity = 2.0;

        const isReactor = (mode === 'reactor');
        const isSuit = (mode === 'suit');
        const isGauntlet = (mode === 'gauntlet');

        if (this.reactorGroup) this.reactorGroup.visible = isReactor;
        if (this.suitGroup) this.suitGroup.visible = isSuit;
        if (this.gauntletGroup) this.gauntletGroup.visible = isGauntlet;

        // Scale & centering adjustment for suit/gauntlet models
        if (isSuit) {
            this.currentScale = 0.72;
            this.gestureScale = 0.72;
        } else if (isGauntlet) {
            this.currentScale = 0.95;
            this.gestureScale = 0.95;
        } else {
            this.currentScale = 1.0;
            this.gestureScale = 1.0;
        }

        if (window.StarkAudio) window.StarkAudio.servoClick();
        if (window.toast) {
            const labels = {
                reactor: 'HOLO MATRIX: ARC REACTOR CORE',
                suit: 'HOLO MATRIX: MARK 85 SUIT TELEMETRY',
                gauntlet: 'HOLO MATRIX: REPULSOR GAUNTLET'
            };
            window.toast(labels[mode] || 'HOLO MATRIX UPDATED');
        }
    }

    bindEvents() {
        window.addEventListener('resize', () => {
            this.width = this.container.clientWidth || 640;
            this.height = this.container.clientHeight || 640;
            this.camera.aspect = this.width / this.height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.width, this.height);
        });

        window.addEventListener('mousemove', (e) => {
            const normX = (e.clientX / window.innerWidth) * 2 - 1;
            const normY = -(e.clientY / window.innerHeight) * 2 + 1;
            this.mouse.targetX = normX * 0.38;
            this.mouse.targetY = normY * 0.28;
        });

        // Global integration hooks for UI, Voice, and Gestures
        this.gestureScale = 1.0;
        this.currentScale = 1.0;
        this.gestureRotZ = 0.0;
        this.currentRotZ = 0.0;
        this.gestureRotY = 0.0;
        this.gesturePosX = 0.0;
        this.gesturePosY = 0.0;
        this.currentPosX = 0.0;
        this.currentPosY = 0.0;
        this.baseAngle = 0.0;

        window.HoloReactor = {
            pulse: (intensity = 1.0) => {
                this.surgeIntensity = Math.min(this.surgeIntensity + intensity, 3.5);
            },
            setSpeaking: (val) => {
                this.isSpeaking = Boolean(val);
            },
            setListening: (val) => {
                this.isListening = Boolean(val);
            },
            setGestureScale: (scale) => {
                this.gestureScale = Math.max(0.5, Math.min(2.5, scale));
            },
            setGestureRotation: (rotZ, rotY) => {
                this.gestureRotZ = rotZ || 0;
                if (rotY !== undefined) this.gestureRotY = rotY;
            },
            setGesturePosition: (x, y) => {
                this.gesturePosX = x || 0;
                this.gesturePosY = y || 0;
            },
            triggerRepulsorBurst: () => {
                this.surgeIntensity = 3.5;
            },
            setMode: (mode) => {
                this.setHoloMode(mode);
            },
            getMode: () => {
                return this.holoMode;
            }
        };
    }

    animate() {
        requestAnimationFrame(this.animate);
        this.time += 0.016;

        // Smooth mouse parallax damping
        this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.08;
        this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.08;

        // Hand gesture position parallax (Mid-air hologram drag)
        this.currentPosX += (this.gesturePosX - this.currentPosX) * 0.08;
        this.currentPosY += (this.gesturePosY - this.currentPosY) * 0.08;
        this.rootGroup.position.x = this.currentPosX;
        this.rootGroup.position.y = this.currentPosY;

        // Hand gesture rotation damping (smooth 1-to-1 orientation)
        this.currentRotZ += (this.gestureRotZ - this.currentRotZ) * 0.12;
        this.rootGroup.rotation.y = this.mouse.x + (this.gestureRotY || 0);
        this.rootGroup.rotation.x = -this.mouse.y;

        // Smooth gesture scale interpolation
        this.currentScale += (this.gestureScale - this.currentScale) * 0.1;
        this.rootGroup.scale.set(this.currentScale, this.currentScale, this.currentScale);

        // Surge decay
        if (this.surgeIntensity > 0.01) {
            this.surgeIntensity *= 0.94;
        }

        // Audio reactivity factors
        const speechPulse = this.isSpeaking ? Math.sin(this.time * 16) * 0.4 + 0.4 : 0;
        const listenPulse = this.isListening ? Math.sin(this.time * 24) * 0.5 + 0.5 : 0;
        const totalEnergy = 1.0 + speechPulse + listenPulse + this.surgeIntensity;

        // Natural continuous rotation + 1-to-1 hand orientation tracking
        this.baseAngle += 0.009 * totalEnergy;
        this.coreGroup.rotation.z = this.baseAngle + this.currentRotZ;
        if (this.suitGroup && this.suitGroup.visible) {
            this.suitGroup.rotation.y = Math.sin(this.time * 0.6) * 0.35 + (this.gestureRotY || 0);
        }
        if (this.gauntletGroup && this.gauntletGroup.visible) {
            this.gauntletGroup.rotation.y = Math.sin(this.time * 0.8) * 0.25 + (this.gestureRotY || 0);
        }

        // Animate Suit scan ring and chest core
        if (this.suitScanRing && this.suitGroup && this.suitGroup.visible) {
            this.suitScanRing.position.y = Math.sin(this.time * 2.5) * 2.2;
            if (this.suitArcCore) {
                const s = 1.0 + Math.sin(this.time * 6) * 0.15 + (totalEnergy - 1.0) * 0.3;
                this.suitArcCore.scale.set(s, s, s);
            }
        }

        // Animate Gauntlet repulsor lens pulse
        if (this.gauntletLens && this.gauntletGroup && this.gauntletGroup.visible) {
            const gs = 1.0 + Math.sin(this.time * 8) * 0.12 + (totalEnergy - 1.0) * 0.35;
            this.gauntletLens.scale.set(gs, gs, gs);
        }
        if (this.reactorGroup && this.reactorGroup.visible) {
            this.reticle1.rotation.z += 0.004;
            this.reticle2.rotation.z -= 0.003;

            // Singularity core pulse
            const singScale = 1.0 + Math.sin(this.time * 6) * 0.08 + (totalEnergy - 1.0) * 0.25;
            this.singularity.scale.set(singScale, singScale, singScale);

            // Plasma sphere pulse
            const plasmaScale = 1.0 + Math.sin(this.time * 4) * 0.05 + (totalEnergy - 1.0) * 0.2;
            this.plasmaSphere.scale.set(plasmaScale, plasmaScale, plasmaScale);

            // Light tube breathing opacity
            this.glowTube.material.opacity = 0.6 + Math.sin(this.time * 3) * 0.15 + (totalEnergy - 1.0) * 0.3;

            // Anamorphic flare horizontal breathing
            const flareScaleX = 1.0 + Math.sin(this.time * 5) * 0.15 + (totalEnergy - 1.0) * 0.4;
            this.streak.scale.set(flareScaleX, 1.0, 1.0);
            this.streak.material.opacity = 0.55 + (totalEnergy - 1.0) * 0.35;

            // SMD micro-LED alternate blinking
            for (let i = 0; i < this.smdLeds.length; i++) {
                const ledPhase = Math.sin(this.time * 4 + i * 0.6);
                this.smdLeds[i].scale.setScalar(ledPhase > 0 ? 1.2 : 0.8);
            }

            // Procedural electric lightning discharges
            if (Math.random() < 0.1 || this.surgeIntensity > 0.4) {
                const arc = this.arcs[Math.floor(Math.random() * this.arcs.length)];
                const targetAngle = Math.random() * Math.PI * 2;
                const p0 = new THREE.Vector3(0, 0, 0.12);
                const p1 = new THREE.Vector3(Math.cos(targetAngle) * 0.9, Math.sin(targetAngle) * 0.9, 0.2);
                const p2 = new THREE.Vector3(Math.cos(targetAngle) * 1.55, Math.sin(targetAngle) * 1.55, 0.1);
                const p3 = new THREE.Vector3(Math.cos(targetAngle) * 2.05, Math.sin(targetAngle) * 2.05, 0.15);
                const curve = new THREE.CatmullRomCurve3([p0, p1, p2, p3]);
                arc.line.geometry.setFromPoints(curve.getPoints(20));
                arc.line.visible = true;
                setTimeout(() => { arc.line.visible = false; }, 60);
            }
        }

        // Quantum particles physics update
        const pos = this.particleData.geo.attributes.position.array;
        for (let i = 0; i < this.particleData.count; i++) {
            this.particleData.angles[i] += 0.013 * this.particleData.speeds[i] * totalEnergy;
            const r = this.particleData.radii[i];
            const a = this.particleData.angles[i];
            pos[i * 3] = Math.cos(a) * r;
            pos[i * 3 + 1] = Math.sin(a) * r;
            pos[i * 3 + 2] = this.particleData.heights[i] + Math.sin(this.time * 2.5 + i) * 0.06;
        }
        this.particleData.geo.attributes.position.needsUpdate = true;

        this.renderer.render(this.scene, this.camera);
    }
}

// Auto-initialize once DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new HoloReactorApp());
} else {
    new HoloReactorApp();
}
