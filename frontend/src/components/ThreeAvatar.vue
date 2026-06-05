<template>
  <div class="three-avatar-wrapper clickable" ref="wrapperRef" @click="handleClick">
    <div class="three-avatar-container" ref="containerRef">
      <div v-if="loading" class="avatar-loading">
        <div class="loading-spinner"></div>
        <p>{{ loadingText }}</p>
      </div>
      <div v-if="error" class="avatar-error">
        <span class="error-icon">&#x26A0;&#xFE0F;</span>
        <p>{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'

const emit = defineEmits(['avatar-ready'])

const containerRef = ref(null)
const wrapperRef = ref(null)
const loading = ref(true)
const loadingText = ref('正在加载...')
const error = ref('')

let scene, camera, renderer, model, clock, mixer, animationFrameId
let THREE, GLTFLoader, DRACOLoader
let runAction = null
let isRunning = false
let runDirection = 1  // 1=左→右, -1=右→左

// 眨眼相关
let blinkMorphTargets = []  // [{ mesh, index, name }]
let eyeBones = []         // 眼睛骨骼数组
let isBlinking = false
let blinkStartTime = 0
const BLINK_INTERVAL = 4000   // 每4秒眨眼一次
const BLINK_DURATION = 300    // 眨眼动画持续 300ms
let lastBlinkTime = 0

const initThree = async () => {
  try {
    const threeModule = await import('three')
    THREE = threeModule

    const gltfLoaderModule = await import('three/examples/jsm/loaders/GLTFLoader.js')
    GLTFLoader = gltfLoaderModule.GLTFLoader

    const dracoLoaderModule = await import('three/examples/jsm/loaders/DRACOLoader.js')
    DRACOLoader = dracoLoaderModule.DRACOLoader

    const container = containerRef.value
    const wrapper = wrapperRef.value
    if (!container || !wrapper) throw new Error('容器未找到')

    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    if (!gl) throw new Error('浏览器不支持 WebGL')

    // 场景 - 无背景（透明）
    scene = new THREE.Scene()
    scene.background = null

    // 使用父容器尺寸（确保非零值，避免 getBoundingClientRect 报错）
    const width = Math.max(wrapper.clientWidth, wrapper.offsetWidth, 340)
    const height = Math.max(wrapper.clientHeight, wrapper.offsetHeight, 340)
    
    // 相机位置调整：展示全身，人物居中
    camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 1000)
    camera.position.set(0, 0.6, 4)
    camera.lookAt(0, 0.3, 0)

    // 渲染器 - 透明背景
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.setClearColor(0x000000, 0)
    container.appendChild(renderer.domElement)
    // canvas 点击穿透，让 Vue 的 @click 能触发
    renderer.domElement.style.pointerEvents = 'none'

    // 灯光
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5)
    directionalLight.position.set(3, 8, 5)
    scene.add(directionalLight)

    const fillLight = new THREE.DirectionalLight(0xb0d4ff, 0.6)
    fillLight.position.set(-3, 3, -3)
    scene.add(fillLight)

    clock = new THREE.Clock()

    loadModel()
    animate()
  } catch (err) {
    console.error('[ThreeAvatar] 初始化失败:', err)
    loading.value = false
  }
}

const loadModel = () => {
  try {
    const loader = new GLTFLoader()
    const modelUrl = '/models/avatar.glb'

    const dracoLoader = new DRACOLoader()
    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')
    dracoLoader.setDecoderConfig({ type: 'js' })
    loader.setDRACOLoader(dracoLoader)

    console.log('[ThreeAvatar] 开始加载模型:', modelUrl)

    loader.load(
      modelUrl,
      (gltf) => {
        console.log('[ThreeAvatar] 模型加载成功!', gltf)
        try {
          model = gltf.scene
          mixer = new THREE.AnimationMixer(model)

          // 查找跑步/行走动画剪辑
          if (gltf.animations && gltf.animations.length > 0) {
            console.log('[ThreeAvatar] 可用动画:', gltf.animations.map(a => a.name || '未命名'))
            // 按名称匹配，找不到就用第一个
            const anim = gltf.animations.find(a => {
              const name = (a.name || '').toLowerCase()
              return name.includes('run') || name.includes('walk') ||
                     name.includes('jog') || name.includes('sprint')
            }) || gltf.animations[0]
            runAction = mixer.clipAction(anim)
            runAction.setLoop(THREE.LoopRepeat)
            console.log('[ThreeAvatar] 使用动画:', anim.name || '未命名')
          } else {
            console.warn('[ThreeAvatar] 模型没有内置动画剪辑')
          }

          const box = new THREE.Box3().setFromObject(model)
          const size = box.getSize(new THREE.Vector3())
          const center = box.getCenter(new THREE.Vector3())

          // 缩放模型
          const targetHeight = 1.0
          const scale = targetHeight / size.y
          model.scale.setScalar(scale)

          // 将模型居中于场景原点，然后往上抬以便全身显示
          model.position.sub(center.multiplyScalar(scale))
          model.position.y = size.y * scale * 0.5
          model.rotation.y = 0

          scene.add(model)

          // 分析模型结构，查找眨眼相关资源
          model.traverse((child) => {
            // 查找面部 morph targets
            if (child.isMesh && child.morphTargetDictionary) {
              const dict = child.morphTargetDictionary
              Object.keys(dict).forEach((key) => {
                const lowerKey = key.toLowerCase()
                if (lowerKey.includes('blink') || (lowerKey.includes('eye') && lowerKey.includes('close')) ||
                    key.includes('闭') || key.includes('眨') || key.includes('眼睛')) {
                  console.log('[ThreeAvatar] 找到可能的眨眼 morph:', key, 'index:', dict[key])
                  blinkMorphTargets.push({ mesh: child, index: dict[key], name: key })
                }
              })
            }

            // 查找 SkinnedMesh 的骨骼
            if (child.isSkinnedMesh && child.skeleton) {
              child.skeleton.bones.forEach((bone) => {
                const name = bone.name.toLowerCase()
                if (name.includes('eye') || name.includes('lid') || name.includes('眼睑') ||
                    name.includes('upperlid') || name.includes('lowerlid')) {
                  console.log('[ThreeAvatar] 找到眼睛骨骼:', bone.name)
                  eyeBones.push(bone)
                }
              })
            }
          })

          if (blinkMorphTargets.length > 0) {
            console.log('[ThreeAvatar] 将使用 morph target 实现眨眼')
          } else if (eyeBones.length >= 2) {
            console.log('[ThreeAvatar] 将使用骨骼实现眨眼, 找到', eyeBones.length, '个眼睛骨骼')
          } else {
            console.warn('[ThreeAvatar] 未找到眨眼相关资源（morph target 或骨骼）')
          }

          loading.value = false
          loadingText.value = ''
          emit('avatar-ready', model)
        } catch (err) {
          console.error('[ThreeAvatar] 模型处理失败:', err)
          loading.value = false
        }
      },
      (xhr) => {
        const percent = xhr.total ? Math.round((xhr.loaded / xhr.total) * 100) : '?'
        loadingText.value = `\u52A0\u8F7D\u4E2D ${percent}%`
      },
      (err) => {
        console.error('[ThreeAvatar] 模型加载失败:', err)
        loading.value = false
      }
    )
  } catch (err) {
    console.error('[ThreeAvatar] GLTFLoader 初始化失败:', err)
    loading.value = false
  }
}

// ===== 渲染循环 =====
const animate = () => {
  animationFrameId = requestAnimationFrame(animate)
  const delta = clock.getDelta()
  const now = Date.now()

  if (mixer) mixer.update(delta)

  // 定时眨眼触发（只在站立不动时）
  if (!isRunning && !isBlinking && now - lastBlinkTime > BLINK_INTERVAL) {
    isBlinking = true
    blinkStartTime = now
    lastBlinkTime = now
  }

  // 更新眨眼动画
  if (isBlinking && (blinkMorphTargets.length > 0 || eyeBones.length >= 2)) {
    const blinkElapsed = now - blinkStartTime
    const t = Math.min(blinkElapsed / BLINK_DURATION, 1)
    let eyeCloseAmount = 0
    if (t < 0.2) {
      eyeCloseAmount = t / 0.2
    } else if (t < 0.4) {
      eyeCloseAmount = 1
    } else {
      eyeCloseAmount = 1 - (t - 0.4) / 0.6
    }
    if (blinkMorphTargets.length > 0) {
      blinkMorphTargets.forEach(({ mesh, index }) => {
        mesh.morphTargetInfluences[index] = eyeCloseAmount
      })
    }
    if (eyeBones.length >= 2) {
      eyeBones.forEach((bone) => {
        bone.rotation.x = eyeCloseAmount * 0.5
      })
    }
    if (t >= 1) {
      if (blinkMorphTargets.length > 0) {
        blinkMorphTargets.forEach(({ mesh, index }) => {
          mesh.morphTargetInfluences[index] = 0
        })
      }
      if (eyeBones.length >= 2) {
        eyeBones.forEach((bone) => {
          bone.rotation.x = 0
        })
      }
      isBlinking = false
    }
  }

  // 更新抬手动画
  if (isRaising && armBones.length > 0) {
    const raiseElapsed = now - raiseStartTime
    const t = Math.min(raiseElapsed / RAISE_DURATION, 1)
    // 抬手曲线：0-40% 抬起，40-100% 放下
    let raiseAmount = 0
    if (t < 0.4) {
      raiseAmount = t / 0.4
    } else {
      raiseAmount = 1 - (t - 0.4) / 0.6
    }
    armBones.forEach(({ bone, originalRot }) => {
      bone.rotation.z = originalRot.z - raiseAmount * 1.2
    })
    if (t >= 1) {
      armBones.forEach(({ bone, originalRot }) => {
        bone.rotation.z = originalRot.z
      })
      isRaising = false
    }
  }

  if (renderer && scene && camera) renderer.render(scene, camera)
}

// 抬手相关
let armBones = []
let isRaising = false
let raiseStartTime = 0
const RAISE_DURATION = 600  // 抬手动画持续 600ms

// ===== 点击抬手 =====
const handleClick = (e) => {
  if (e) e.preventDefault()
  console.log('[ThreeAvatar] 点击了人物!')
  if (isRaising || !model) return

  // 首次点击时只选上臂/肩部骨骼，保存原始旋转
  if (armBones.length === 0) {
    const candidates = []
    model.traverse((child) => {
      if (child.isBone) {
        const name = child.name.toLowerCase()
        if (name.includes('upperarm') || name.includes('upper_arm') ||
            name.includes('shoulder') || name.includes('clavicle')) {
          candidates.push(child)
        }
      }
    })
    if (candidates.length === 0) {
      // 退化：SkinnedMesh骨架
      model.traverse((child) => {
        if (child.isSkinnedMesh && child.skeleton) {
          child.skeleton.bones.forEach((bone) => {
            const name = bone.name.toLowerCase()
            if (name.includes('upperarm') || name.includes('upper_arm') ||
                name.includes('shoulder') || name.includes('clavicle')) {
              candidates.push(bone)
            }
          })
        }
      })
    }
    // 只取前2个（左右各一）
    const picked = candidates.slice(0, 2)
    if (picked.length > 0) {
      console.log('[ThreeAvatar] 抬手使用骨骼:', picked.map(b => b.name))
      armBones = picked.map(bone => ({
        bone,
        originalRot: { x: bone.rotation.x, y: bone.rotation.y, z: bone.rotation.z }
      }))
    } else {
      const allBones = []
      model.traverse((child) => { if (child.isBone) allBones.push(child.name) })
      console.log('[ThreeAvatar] 所有骨骼:', allBones)
    }
  }

  if (armBones.length === 0) {
    console.warn('[ThreeAvatar] 未找到手臂骨骼（查看上方骨骼列表自行调整关键词）')
    return
  }

  isRaising = true
  raiseStartTime = Date.now()
}

const handleResize = () => {
  const container = containerRef.value
  const wrapper = wrapperRef.value
  if (!container || !wrapper || !camera || !renderer) return
  
  const width = wrapper.clientWidth
  const height = wrapper.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

onMounted(() => {
  nextTick(() => {
    initThree()
  })
  window.addEventListener('resize', handleResize)
  // 让容器可点击
  if (wrapperRef.value) {
    wrapperRef.value.style.cursor = 'pointer'
  }
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrameId)
  window.removeEventListener('resize', handleResize)

  if (mixer) mixer.stopAllAction()

  if (model) {
    model.traverse((child) => {
      if (child.geometry) child.geometry.dispose()
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(m => m.dispose())
        } else {
          child.material.dispose()
        }
      }
    })
  }
  if (renderer) {
    renderer.dispose()
    renderer.forceContextLoss()
  }
})
</script>

<style scoped>
.three-avatar-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: pointer;
}

.three-avatar-wrapper.clickable {
  cursor: pointer;
}

.three-avatar-container {
  width: 100%;
  height: 100%;
  background: transparent;
}

.avatar-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6366f1;
  font-size: 14px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(99, 102, 241, 0.2);
  border-top: 4px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.avatar-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #ef4444;
  font-size: 14px;
  padding: 20px;
  text-align: center;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 8px;
}
</style>
