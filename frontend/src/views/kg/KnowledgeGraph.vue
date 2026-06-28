<template>
  <div class="kg-page">
    <div class="kg-header">
      <div class="kg-title-wrap">
        <IconMindmap :size="28" color="#a855f7" />
        <h2>知识图谱</h2>
      </div>
      <div class="kg-toolbar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索笔记或概念..."
          size="default"
          clearable
          class="search-input"
          @input="handleSearch"
        >
          <template #prefix>
            <IconSearch :size="16" />
          </template>
        </el-input>
        <el-button :type="is2DMode ? 'primary' : 'default'" @click="switchTo2D">
          2D 视图
        </el-button>
        <el-button :type="!is2DMode ? 'primary' : 'default'" @click="switchTo3D">
          3D 视图
        </el-button>
        <el-button @click="refreshGraph" :loading="isRefreshing">
          刷新图谱
        </el-button>
      </div>
    </div>

    <div class="kg-content">
      <div class="kg-canvas-wrap" ref="canvasWrap">
        <canvas ref="canvasEl" class="kg-canvas"></canvas>
        <div v-if="loading" class="kg-loading">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <p>正在生成知识图谱...</p>
        </div>
        <div v-if="!loading && graphData.nodes.length === 0" class="kg-empty">
          <el-empty description="还没有笔记，先去写几篇笔记吧~" />
        </div>
      </div>

      <div class="kg-detail-panel" :class="{ show: selectedNode }">
        <template v-if="selectedNode">
          <div class="detail-header">
            <span class="detail-type">{{ selectedNode.type === 'note' ? '笔记' : '概念' }}</span>
            <el-button size="small" text @click="selectedNode = null">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
          <h3 class="detail-title">{{ selectedNode.label }}</h3>

          <!-- 关联的概念 -->
          <div v-if="getNodeRelations(selectedNode.id).concepts.length > 0" class="relation-section">
            <div class="relation-title">
              <span class="relation-icon">💡</span>
              包含的概念
            </div>
            <div class="relation-list">
              <div
                v-for="concept in getNodeRelations(selectedNode.id).concepts"
                :key="concept.id"
                class="relation-item concept-item"
                @click="selectRelatedNode(concept.id)"
              >
                <span class="relation-name">{{ concept.name }}</span>
                <span class="relation-weight">{{ (concept.weight * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>

          <!-- 关联的笔记 -->
          <div v-if="getNodeRelations(selectedNode.id).similarNotes.length > 0" class="relation-section">
            <div class="relation-title">
              <span class="relation-icon">📝</span>
              相似笔记
            </div>
            <div class="relation-list">
              <div
                v-for="note in getNodeRelations(selectedNode.id).similarNotes"
                :key="note.id"
                class="relation-item note-item"
                @click="selectRelatedNode(note.id)"
              >
                <span class="relation-name">{{ note.name }}</span>
                <span class="relation-weight">{{ (note.weight * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>

          <!-- 概念节点显示关联的笔记 -->
          <div v-if="selectedNode.type === 'concept' && getNodeRelations(selectedNode.id).similarNotes.length === 0 && getNodeRelations(selectedNode.id).concepts.length === 0" class="relation-empty">
            暂无关联笔记
          </div>

          <div class="detail-actions">
            <el-button v-if="selectedNode.type === 'note'" type="primary" size="small" @click="openNote">
              打开笔记
            </el-button>
            <el-button size="small" @click="focusNode">
              聚焦
            </el-button>
          </div>
        </template>
      </div>
    </div>

    <div class="kg-stats" v-if="graphData.stats">
      <span>📝 笔记: {{ graphData.stats.note_count || 0 }}</span>
      <span>💡 概念: {{ graphData.stats.concept_count || 0 }}</span>
      <span>🔗 关系: {{ graphData.stats.edge_count || 0 }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Close } from '@element-plus/icons-vue'
import { IconMindmap, IconSearch } from '@/components/icons'
import { kgApi } from '@/api/kg'
import { MESSAGE_DURATION } from '@/utils/common'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js'
import { gsap } from 'gsap'

const router = useRouter()
const canvasWrap = ref(null)
const canvasEl = ref(null)
const loading = ref(true)
const isRefreshing = ref(false)
const searchKeyword = ref('')
const selectedNode = ref(null)
const is2DMode = ref(true)

const graphData = ref({
  nodes: [],
  edges: [],
  stats: {},
})

let scene = null
let camera = null
let renderer = null
let labelRenderer = null
let controls = null
let animationId = null
let nodeMeshes = []
let nodeLabels = []
let edgeLines = []
let nodeMap = new Map()
let raycaster = null
let mouse = new THREE.Vector2()
let isInteracting = false
let interactionJustEndedAt = 0
let hoveredNode = null
let draggedNode = null
let dragPlane = new THREE.Plane()
let dragOffset = new THREE.Vector3()
let dragIntersectPoint = new THREE.Vector3()
let forceSimulationRunning = false
const FORCE_CONFIG = {
  repulsionStrength: 12000,
  springStrength: 0.015,
  springLength: 150,
  gravityStrength: 0.005,
  damping: 0.9,
  velocityDecay: 0.88,
}

async function loadGraph() {
  loading.value = true
  try {
    const data = await kgApi.getGraph()
    graphData.value = data
    if (scene) {
      buildGraph()
    }
  } catch (error) {
    console.error('加载知识图谱失败:', error)
    ElMessage.error({
      message: error.response?.data?.detail || '加载图谱失败',
      duration: MESSAGE_DURATION.NORMAL,
    })
  } finally {
    loading.value = false
  }
}

async function refreshGraph() {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    await kgApi.refreshGraph()
    ElMessage.success({ message: '正在重新生成图谱...', duration: MESSAGE_DURATION.SHORT })
    await checkStatus()
  } catch (error) {
    if (error.response?.status === 409) {
      ElMessage.info({ message: error.response.data.detail, duration: MESSAGE_DURATION.SHORT })
    } else {
      console.error('刷新图谱失败:', error)
      ElMessage.error({
        message: error.response?.data?.detail || '刷新失败',
        duration: MESSAGE_DURATION.NORMAL,
      })
    }
  } finally {
    isRefreshing.value = false
  }
}

async function checkStatus() {
  let maxAttempts = 60
  let attempts = 0
  const poll = async () => {
    if (attempts >= maxAttempts) return
    attempts++
    try {
      const status = await kgApi.getStatus()
      if (status.status === 'ready' || status.status === 'failed') {
        if (status.status === 'ready') {
          await loadGraph()
          ElMessage.success({ message: '图谱更新完成！', duration: MESSAGE_DURATION.SHORT })
        } else {
          ElMessage.error({
            message: status.error_msg || '图谱生成失败',
            duration: MESSAGE_DURATION.NORMAL,
          })
        }
        return
      }
      setTimeout(poll, 1000)
    } catch {
      setTimeout(poll, 2000)
    }
  }
  poll()
}

function initThree() {
  if (!canvasEl.value || !canvasWrap.value) return

  const width = canvasWrap.value.clientWidth
  const height = canvasWrap.value.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xfafafa)

  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 10000)
  camera.position.set(0, 0, 500)

  renderer = new THREE.WebGLRenderer({
    canvas: canvasEl.value,
    antialias: true,
    alpha: true,
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 50
  controls.maxDistance = 2000

  controls.addEventListener('start', () => {
    isInteracting = true
  })
  controls.addEventListener('end', () => {
    isInteracting = false
    interactionJustEndedAt = performance.now()
  })

  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(width, height)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0'
  labelRenderer.domElement.style.left = '0'
  labelRenderer.domElement.style.pointerEvents = 'none'
  canvasWrap.value.appendChild(labelRenderer.domElement)

  raycaster = new THREE.Raycaster()

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const pointLight = new THREE.PointLight(0xffffff, 1, 0)
  pointLight.position.set(200, 300, 400)
  scene.add(pointLight)

  animate()

  window.addEventListener('resize', onWindowResize)
  canvasEl.value.addEventListener('pointerdown', onPointerDown)
  canvasEl.value.addEventListener('pointermove', onPointerMove)
  canvasEl.value.addEventListener('pointerup', onPointerUp)
}

let pointerDownPos = { x: 0, y: 0 }
let hasMoved = false

function onPointerDown(e) {
  pointerDownPos.x = e.clientX
  pointerDownPos.y = e.clientY
  hasMoved = false

  updateMouse(e)
  const intersects = getIntersects()
  if (intersects.length > 0) {
    const mesh = intersects[0].object
    const node = mesh.userData
    draggedNode = node
    controls.enabled = false
    document.body.style.cursor = 'grabbing'

    if (is2DMode.value) {
      dragPlane.set(new THREE.Vector3(0, 0, 1), -mesh.position.z)
    } else {
      const normal = new THREE.Vector3()
      camera.getWorldDirection(normal)
      dragPlane.setFromNormalAndCoplanarPoint(normal, mesh.position)
    }

    raycaster.setFromCamera(mouse, camera)
    raycaster.ray.intersectPlane(dragPlane, dragIntersectPoint)
    dragOffset.copy(mesh.position).sub(dragIntersectPoint)
  }
}

function onPointerMove(e) {
  const dx = Math.abs(e.clientX - pointerDownPos.x)
  const dy = Math.abs(e.clientY - pointerDownPos.y)
  if (dx > 4 || dy > 4) {
    hasMoved = true
  }

  updateMouse(e)

  if (draggedNode && draggedNode.mesh) {
    raycaster.setFromCamera(mouse, camera)
    if (raycaster.ray.intersectPlane(dragPlane, dragIntersectPoint)) {
      const newPos = dragIntersectPoint.add(dragOffset)
      draggedNode.mesh.position.copy(newPos)
      updateConnectedEdges(draggedNode)
    }
    return
  }

  const intersects = getIntersects()
  if (intersects.length > 0) {
    document.body.style.cursor = 'pointer'
    hoveredNode = intersects[0].object.userData
  } else {
    document.body.style.cursor = 'grab'
    hoveredNode = null
  }
}

function onPointerUp(e) {
  if (draggedNode) {
    const wasDragging = hasMoved
    if (wasDragging) {
      if (is2DMode.value) {
        draggedNode.targetPos2D.copy(draggedNode.mesh.position.clone())
      } else {
        draggedNode.targetPos3D.copy(draggedNode.mesh.position.clone())
      }
      draggedNode.velocity.set(0, 0, 0)
    } else {
      selectedNode.value = draggedNode
    }
    draggedNode = null
    controls.enabled = true
    document.body.style.cursor = hoveredNode ? 'pointer' : 'grab'
    return
  }

  if (e.button !== 0) return
  if (hasMoved) return
  if (isInteracting) return
  if (performance.now() - interactionJustEndedAt < 200) return

  updateMouse(e)
  const intersects = getIntersects()
  if (intersects.length > 0) {
    const node = intersects[0].object.userData
    selectedNode.value = node
  }
}

function updateConnectedEdges(node) {
  if (!node || !node.mesh) return
  edgeLines.forEach((line) => {
    const { edge, sourceMesh, targetMesh } = line.userData
    if (!sourceMesh || !targetMesh) return
    if (edge.source === node.id || edge.target === node.id) {
      const positions = line.geometry.attributes.position
      positions.setXYZ(0, sourceMesh.position.x, sourceMesh.position.y, sourceMesh.position.z)
      positions.setXYZ(1, targetMesh.position.x, targetMesh.position.y, targetMesh.position.z)
      positions.needsUpdate = true
    }
  })
}

function updateAllEdges() {
  edgeLines.forEach((line) => {
    const { sourceMesh, targetMesh } = line.userData
    if (!sourceMesh || !targetMesh) return
    const positions = line.geometry.attributes.position
    positions.setXYZ(0, sourceMesh.position.x, sourceMesh.position.y, sourceMesh.position.z)
    positions.setXYZ(1, targetMesh.position.x, targetMesh.position.y, targetMesh.position.z)
    positions.needsUpdate = true
  })
}

function applyForces2D() {
  const nodes = graphData.value.nodes
  if (nodes.length < 2) return

  nodes.forEach((node) => {
    node.force.set(0, 0, 0)
  })

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const n1 = nodes[i]
      const n2 = nodes[j]
      if (!n1.mesh || !n2.mesh) continue

      const dx = n2.mesh.position.x - n1.mesh.position.x
      const dy = n2.mesh.position.y - n1.mesh.position.y
      let dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 1) dist = 1

      const repulsion = FORCE_CONFIG.repulsionStrength / (dist * dist)
      const fx = (dx / dist) * repulsion
      const fy = (dy / dist) * repulsion

      n2.force.x += fx
      n2.force.y += fy
      n1.force.x -= fx
      n1.force.y -= fy
    }
  }

  graphData.value.edges.forEach((edge) => {
    const source = graphData.value.nodes.find((n) => n.id === edge.source)
    const target = graphData.value.nodes.find((n) => n.id === edge.target)
    if (!source || !target || !source.mesh || !target.mesh) return

    const dx = target.mesh.position.x - source.mesh.position.x
    const dy = target.mesh.position.y - source.mesh.position.y
    let dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < 1) dist = 1

    const springLen = FORCE_CONFIG.springLength * (1 + edge.weight * 0.5)
    const displacement = dist - springLen
    const springForce = displacement * FORCE_CONFIG.springStrength

    const fx = (dx / dist) * springForce
    const fy = (dy / dist) * springForce

    source.force.x += fx
    source.force.y += fy
    target.force.x -= fx
    target.force.y -= fy
  })

  nodes.forEach((node) => {
    if (!node.mesh) return
    node.force.x -= node.mesh.position.x * FORCE_CONFIG.gravityStrength
    node.force.y -= node.mesh.position.y * FORCE_CONFIG.gravityStrength
  })

  nodes.forEach((node) => {
    if (!node.mesh) return
    if (draggedNode && draggedNode.id === node.id) return

    node.velocity.x = (node.velocity.x + node.force.x) * FORCE_CONFIG.velocityDecay
    node.velocity.y = (node.velocity.y + node.force.y) * FORCE_CONFIG.velocityDecay

    node.mesh.position.x += node.velocity.x
    node.mesh.position.y += node.velocity.y

    node.targetPos2D.x = node.mesh.position.x
    node.targetPos2D.y = node.mesh.position.y
  })

  updateAllEdges()
}

function startForceSimulation() {
  forceSimulationRunning = true
}

function stopForceSimulation() {
  forceSimulationRunning = false
}

function applyForces3D() {
  const nodes = graphData.value.nodes
  if (nodes.length < 2) return

  nodes.forEach((node) => {
    node.force.set(0, 0, 0)
  })

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const n1 = nodes[i]
      const n2 = nodes[j]
      if (!n1.mesh || !n2.mesh) continue

      const dx = n2.mesh.position.x - n1.mesh.position.x
      const dy = n2.mesh.position.y - n1.mesh.position.y
      const dz = n2.mesh.position.z - n1.mesh.position.z
      let dist = Math.sqrt(dx * dx + dy * dy + dz * dz)
      if (dist < 1) dist = 1

      const repulsion = FORCE_CONFIG.repulsionStrength * 1.5 / (dist * dist)
      const fx = (dx / dist) * repulsion
      const fy = (dy / dist) * repulsion
      const fz = (dz / dist) * repulsion

      n2.force.x += fx
      n2.force.y += fy
      n2.force.z += fz
      n1.force.x -= fx
      n1.force.y -= fy
      n1.force.z -= fz
    }
  }

  graphData.value.edges.forEach((edge) => {
    const source = graphData.value.nodes.find((n) => n.id === edge.source)
    const target = graphData.value.nodes.find((n) => n.id === edge.target)
    if (!source || !target || !source.mesh || !target.mesh) return

    const dx = target.mesh.position.x - source.mesh.position.x
    const dy = target.mesh.position.y - source.mesh.position.y
    const dz = target.mesh.position.z - source.mesh.position.z
    let dist = Math.sqrt(dx * dx + dy * dy + dz * dz)
    if (dist < 1) dist = 1

    const springLen = FORCE_CONFIG.springLength * 2 * (1 + edge.weight * 0.5)
    const displacement = dist - springLen
    const springForce = displacement * FORCE_CONFIG.springStrength * 0.8

    const fx = (dx / dist) * springForce
    const fy = (dy / dist) * springForce
    const fz = (dz / dist) * springForce

    source.force.x += fx
    source.force.y += fy
    source.force.z += fz
    target.force.x -= fx
    target.force.y -= fy
    target.force.z -= fz
  })

  nodes.forEach((node) => {
    if (!node.mesh) return
    const dist = Math.sqrt(
      node.mesh.position.x ** 2 +
      node.mesh.position.y ** 2 +
      node.mesh.position.z ** 2
    )
    if (dist > 1) {
      const sphereRadius = 200
      const pullStrength = FORCE_CONFIG.gravityStrength * 0.5
      const factor = (sphereRadius - dist) * pullStrength
      node.force.x += (node.mesh.position.x / dist) * factor
      node.force.y += (node.mesh.position.y / dist) * factor
      node.force.z += (node.mesh.position.z / dist) * factor
    }
  })

  nodes.forEach((node) => {
    if (!node.mesh) return
    if (draggedNode && draggedNode.id === node.id) return

    node.velocity.x = (node.velocity.x + node.force.x) * FORCE_CONFIG.velocityDecay
    node.velocity.y = (node.velocity.y + node.force.y) * FORCE_CONFIG.velocityDecay
    node.velocity.z = (node.velocity.z + node.force.z) * FORCE_CONFIG.velocityDecay

    node.mesh.position.x += node.velocity.x
    node.mesh.position.y += node.velocity.y
    node.mesh.position.z += node.velocity.z

    node.targetPos3D.x = node.mesh.position.x
    node.targetPos3D.y = node.mesh.position.y
    node.targetPos3D.z = node.mesh.position.z
  })

  updateAllEdges()
}

function getNodeRelations(nodeId) {
  const relations = {
    concepts: [],
    notes: [],
    similarNotes: [],
  }
  const edges = graphData.value.edges
  const nodes = graphData.value.nodes

  edges.forEach((edge) => {
    if (edge.source === nodeId) {
      const targetNode = nodes.find((n) => n.id === edge.target)
      if (targetNode) {
        if (edge.type === 'note-concept' || edge.type === 'concept-note') {
          if (targetNode.type === 'concept') {
            relations.concepts.push({
              id: targetNode.id,
              name: targetNode.label,
              weight: edge.weight,
            })
          } else {
            relations.similarNotes.push({
              id: targetNode.id,
              name: targetNode.label,
              weight: edge.weight,
            })
          }
        } else {
          relations.similarNotes.push({
            id: targetNode.id,
            name: targetNode.label,
            weight: edge.weight,
          })
        }
      }
    }
    if (edge.target === nodeId) {
      const sourceNode = nodes.find((n) => n.id === edge.source)
      if (sourceNode) {
        if (edge.type === 'note-concept' || edge.type === 'concept-note') {
          if (sourceNode.type === 'concept') {
            relations.concepts.push({
              id: sourceNode.id,
              name: sourceNode.label,
              weight: edge.weight,
            })
          } else {
            relations.similarNotes.push({
              id: sourceNode.id,
              name: sourceNode.label,
              weight: edge.weight,
            })
          }
        } else {
          relations.similarNotes.push({
            id: sourceNode.id,
            name: sourceNode.label,
            weight: edge.weight,
          })
        }
      }
    }
  })

  relations.concepts.sort((a, b) => b.weight - a.weight)
  relations.similarNotes.sort((a, b) => b.weight - a.weight)

  return relations
}

function selectRelatedNode(nodeId) {
  const nodes = graphData.value.nodes
  const node = nodes.find((n) => n.id === nodeId)
  if (node) {
    selectedNode.value = node
  }
}

function updateMouse(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
}

function getIntersects() {
  raycaster.setFromCamera(mouse, camera)
  return raycaster.intersectObjects(nodeMeshes)
}

function onWindowResize() {
  if (!canvasWrap.value || !camera || !renderer) return
  const width = canvasWrap.value.clientWidth
  const height = canvasWrap.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
  if (labelRenderer) {
    labelRenderer.setSize(width, height)
  }
}

function animate() {
  animationId = requestAnimationFrame(animate)
  if (controls) controls.update()
  if (graphData.value.nodes.length > 1 && forceSimulationRunning) {
    if (is2DMode.value) {
      applyForces2D()
    } else {
      applyForces3D()
    }
  }
  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
  if (labelRenderer && scene && camera) {
    labelRenderer.render(scene, camera)
  }
}

function buildGraph() {
  if (!scene) return

  nodeMeshes.forEach((m) => scene.remove(m))
  nodeLabels.forEach((l) => scene.remove(l))
  edgeLines.forEach((l) => scene.remove(l))
  nodeMeshes = []
  nodeLabels = []
  edgeLines = []
  nodeMap.clear()

  const nodes = graphData.value.nodes
  const edges = graphData.value.edges

  if (!nodes.length) return

  compute2DPositions(nodes)
  compute3DPositions(nodes)

  nodes.forEach((node) => {
    const geometry = new THREE.SphereGeometry(node.size / 5, 32, 32)
    const color = new THREE.Color(node.color)
    const material = new THREE.MeshPhongMaterial({
      color: color,
      transparent: true,
      opacity: 0.9,
      shininess: 100,
      emissive: color,
      emissiveIntensity: 0.1,
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(node.pos2d.x, node.pos2d.y, 0)
    mesh.userData = node
    node.targetPos2D = new THREE.Vector3(node.pos2d.x, node.pos2d.y, 0)
    node.targetPos3D = new THREE.Vector3(node.pos3d.x, node.pos3d.y, node.pos3d.z)
    node.velocity = new THREE.Vector3(0, 0, 0)
    node.force = new THREE.Vector3(0, 0, 0)
    node.mesh = mesh
    nodeMap.set(node.id, mesh)
    scene.add(mesh)
    nodeMeshes.push(mesh)

    const labelDiv = document.createElement('div')
    labelDiv.className = 'kg-node-label'
    labelDiv.textContent = node.label
    labelDiv.style.cssText = `
      color: #303133;
      font-size: 12px;
      padding: 2px 8px;
      background: rgba(255,255,255,0.85);
      border-radius: 10px;
      white-space: nowrap;
      pointer-events: none;
      box-shadow: 0 1px 4px rgba(0,0,0,0.1);
      max-width: 120px;
      overflow: hidden;
      text-overflow: ellipsis;
      transform: translate(-50%, -100%);
      margin-top: -8px;
      font-weight: 500;
    `
    const label = new CSS2DObject(labelDiv)
    label.position.set(0, node.size / 5 + 5, 0)
    mesh.add(label)
    nodeLabels.push(label)
    node.labelObj = label
  })

  edges.forEach((edge) => {
    const sourceMesh = nodeMap.get(edge.source)
    const targetMesh = nodeMap.get(edge.target)
    if (!sourceMesh || !targetMesh) return

    const points = [
      new THREE.Vector3().copy(sourceMesh.position),
      new THREE.Vector3().copy(targetMesh.position),
    ]
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const color = edge.type === 'concept-note' ? 0xa855f7 : 0x4facfe
    const material = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.3 + edge.weight * 0.4,
    })
    const line = new THREE.Line(geometry, material)
    line.userData = { edge, sourceMesh, targetMesh }
    scene.add(line)
    edgeLines.push(line)
  })

  if (is2DMode.value) {
    setup2DCamera()
  } else {
    setup3DCamera()
  }
  startForceSimulation()
}

function compute2DPositions(nodes) {
  const noteNodes = nodes.filter((n) => n.type === 'note')
  const conceptNodes = nodes.filter((n) => n.type === 'concept')

  const centerX = 0
  const centerY = 0
  const noteRadius = Math.max(150, noteNodes.length * 12)

  noteNodes.forEach((node, i) => {
    const angle = (i / noteNodes.length) * Math.PI * 2 - Math.PI / 2
    const r = noteRadius * (0.7 + Math.random() * 0.3)
    node.pos2d = {
      x: centerX + Math.cos(angle) * r,
      y: centerY + Math.sin(angle) * r,
    }
  })

  const conceptRadius = noteRadius + 80
  conceptNodes.forEach((node, i) => {
    const angle = (i / conceptNodes.length) * Math.PI * 2
    const r = conceptRadius * (0.8 + Math.random() * 0.4)
    node.pos2d = {
      x: centerX + Math.cos(angle) * r,
      y: centerY + Math.sin(angle) * r,
    }
  })
}

function compute3DPositions(nodes) {
  const noteNodes = nodes.filter((n) => n.type === 'note')
  const conceptNodes = nodes.filter((n) => n.type === 'concept')

  const noteRadius = Math.max(120, noteNodes.length * 10)
  noteNodes.forEach((node, i) => {
    const phi = Math.acos(-1 + (2 * i) / noteNodes.length)
    const theta = Math.sqrt(noteNodes.length * Math.PI) * phi
    const r = noteRadius * (0.7 + Math.random() * 0.3)
    node.pos3d = {
      x: r * Math.sin(phi) * Math.cos(theta),
      y: r * Math.sin(phi) * Math.sin(theta),
      z: r * Math.cos(phi),
    }
  })

  const conceptRadius = noteRadius + 100
  conceptNodes.forEach((node, i) => {
    const phi = Math.acos(-1 + (2 * (i + 0.5)) / conceptNodes.length)
    const theta = Math.sqrt(conceptNodes.length * Math.PI) * phi
    const r = conceptRadius * (0.75 + Math.random() * 0.25)
    node.pos3d = {
      x: r * Math.sin(phi) * Math.cos(theta),
      y: r * Math.sin(phi) * Math.sin(theta),
      z: r * Math.cos(phi),
    }
  })
}

function setup2DCamera() {
  if (!camera || !controls) return
  camera.position.set(0, 0, 500)
  camera.lookAt(0, 0, 0)
  controls.target.set(0, 0, 0)
  controls.enableRotate = false
  controls.update()
}

function setup3DCamera() {
  if (!camera || !controls) return
  camera.position.set(300, 200, 400)
  camera.lookAt(0, 0, 0)
  controls.target.set(0, 0, 0)
  controls.enableRotate = true
  controls.update()
}

function switchTo2D() {
  if (is2DMode.value || !nodeMeshes.length) return
  is2DMode.value = true
  animateTransition(true)
  setTimeout(() => {
    startForceSimulation()
  }, 1500)
}

function switchTo3D() {
  if (!is2DMode.value || !nodeMeshes.length) return
  is2DMode.value = false
  animateTransition(false)
  setTimeout(() => {
    startForceSimulation()
  }, 1500)
}

function animateTransition(to2D) {
  const nodes = graphData.value.nodes

  nodes.forEach((node) => {
    const mesh = node.mesh
    if (!mesh) return
    const target = to2D ? node.targetPos2D : node.targetPos3D
    gsap.to(mesh.position, {
      x: target.x,
      y: target.y,
      z: target.z,
      duration: 1.5,
      ease: 'power3.inOut',
    })
  })

  edgeLines.forEach((line) => {
    const { sourceMesh, targetMesh } = line.userData
    if (!sourceMesh || !targetMesh) return
    const positions = line.geometry.attributes.position
    const sourceTarget = to2D
      ? sourceMesh.userData.targetPos2D
      : sourceMesh.userData.targetPos3D
    const targetTarget = to2D
      ? targetMesh.userData.targetPos2D
      : targetMesh.userData.targetPos3D

    const startPos = [positions.getX(0), positions.getY(0), positions.getZ(0)]
    const endPos = [positions.getX(1), positions.getY(1), positions.getZ(1)]

    gsap.to(
      {},
      {
        duration: 1.5,
        ease: 'power3.inOut',
        onUpdate: function () {
          const t = this.progress()
          positions.setXYZ(
            0,
            startPos[0] + (sourceTarget.x - startPos[0]) * t,
            startPos[1] + (sourceTarget.y - startPos[1]) * t,
            startPos[2] + (sourceTarget.z - startPos[2]) * t,
          )
          positions.setXYZ(
            1,
            endPos[0] + (targetTarget.x - endPos[0]) * t,
            endPos[1] + (targetTarget.y - endPos[1]) * t,
            endPos[2] + (targetTarget.z - endPos[2]) * t,
          )
          positions.needsUpdate = true
        },
      },
    )
  })

  gsap.to(camera.position, {
    x: to2D ? 0 : 300,
    y: to2D ? 0 : 200,
    z: to2D ? 500 : 400,
    duration: 1.5,
    ease: 'power3.inOut',
    onUpdate: () => {
      camera.lookAt(0, 0, 0)
      controls.target.set(0, 0, 0)
    },
  })

  gsap.to(controls, {
    enableRotate: !to2D,
    duration: 0.1,
    delay: to2D ? 1.4 : 0,
  })
}

function handleSearch(keyword) {
  if (!keyword.trim()) {
    nodeMeshes.forEach((mesh) => {
      mesh.material.opacity = 0.9
      mesh.material.emissiveIntensity = 0.1
    })
    edgeLines.forEach((line) => {
      line.material.opacity = line.userData.edge ? 0.3 + line.userData.edge.weight * 0.4 : 0.3
    })
    return
  }

  const kw = keyword.toLowerCase()
  const matchedIds = new Set()

  graphData.value.nodes.forEach((node) => {
    if (node.label.toLowerCase().includes(kw)) {
      matchedIds.add(node.id)
    }
  })

  graphData.value.edges.forEach((edge) => {
    if (matchedIds.has(edge.source) || matchedIds.has(edge.target)) {
      matchedIds.add(edge.source)
      matchedIds.add(edge.target)
    }
  })

  nodeMeshes.forEach((mesh) => {
    const node = mesh.userData
    if (matchedIds.has(node.id)) {
      mesh.material.opacity = 1
      mesh.material.emissiveIntensity = 0.5
    } else {
      mesh.material.opacity = 0.15
      mesh.material.emissiveIntensity = 0
    }
  })

  edgeLines.forEach((line) => {
    const { sourceMesh, targetMesh } = line.userData
    const sourceMatched = sourceMesh && matchedIds.has(sourceMesh.userData.id)
    const targetMatched = targetMesh && matchedIds.has(targetMesh.userData.id)
    line.material.opacity = sourceMatched && targetMatched ? 0.8 : 0.05
  })
}

function openNote() {
  if (!selectedNode.value || selectedNode.value.type !== 'note') return
  router.push(`/notes/edit/${selectedNode.value.note_id}`)
}

function focusNode() {
  if (!selectedNode.value || !selectedNode.value.mesh || !camera) return
  const mesh = selectedNode.value.mesh
  gsap.to(camera.position, {
    x: mesh.position.x + (is2DMode.value ? 0 : 100),
    y: mesh.position.y + (is2DMode.value ? 0 : 80),
    z: mesh.position.z + (is2DMode.value ? 200 : 150),
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      controls.target.copy(mesh.position)
    },
  })
}

watch(
  () => selectedNode.value,
  (newNode, oldNode) => {
    if (oldNode && oldNode.mesh) {
      oldNode.mesh.material.emissiveIntensity = 0.1
      oldNode.mesh.scale.set(1, 1, 1)
    }
    if (newNode && newNode.mesh) {
      newNode.mesh.material.emissiveIntensity = 0.6
      gsap.to(newNode.mesh.scale, {
        x: 1.3,
        y: 1.3,
        z: 1.3,
        duration: 0.3,
        ease: 'back.out(2)',
      })
    }
  },
)

onMounted(async () => {
  await nextTick()
  initThree()
  await loadGraph()
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (controls) {
    controls.dispose()
  }
  if (renderer) {
    renderer.dispose()
  }
  if (labelRenderer && labelRenderer.domElement && canvasWrap.value) {
    canvasWrap.value.removeChild(labelRenderer.domElement)
  }
  window.removeEventListener('resize', onWindowResize)
  if (canvasEl.value) {
    canvasEl.value.removeEventListener('pointerdown', onPointerDown)
    canvasEl.value.removeEventListener('pointermove', onPointerMove)
    canvasEl.value.removeEventListener('pointerup', onPointerUp)
  }
  document.body.style.cursor = ''
})
</script>

<style scoped>
.kg-page {
  max-width: 100%;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
}

.kg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.kg-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.kg-title-wrap h2 {
  margin: 0;
  font-size: 24px;
  background: linear-gradient(135deg, #a855f7, #4facfe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.kg-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input {
  width: 240px;
}

.kg-content {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

.kg-canvas-wrap {
  flex: 1;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #fafafa;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.kg-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.kg-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(250, 250, 250, 0.9);
  color: #909399;
}

.kg-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.kg-detail-panel {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow-y: auto;
  opacity: 0;
  transform: translateX(100%);
  transition: opacity 0.3s ease, transform 0.3s ease, visibility 0.3s;
  visibility: hidden;
  margin-right: -280px;
}

.kg-detail-panel.show {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
  visibility: visible;
  margin-right: 0;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.detail-type {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  background: linear-gradient(135deg, #a855f7, #4facfe);
  color: #fff;
}

.detail-title {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #303133;
  word-break: break-all;
}

.detail-preview {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 16px 0;
  word-break: break-all;
}

.detail-actions,
.detail-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-stats p {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.relation-section {
  margin-bottom: 16px;
}

.relation-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

.relation-icon {
  font-size: 14px;
}

.relation-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.relation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 8px;
  background: #f5f7fa;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.relation-item:hover {
  transform: translateX(4px);
}

.relation-item.concept-item {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(79, 172, 254, 0.1));
  border-left: 3px solid #a855f7;
}

.relation-item.concept-item:hover {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(79, 172, 254, 0.2));
}

.relation-item.note-item {
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.1), rgba(52, 211, 153, 0.1));
  border-left: 3px solid #4facfe;
}

.relation-item.note-item:hover {
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.2), rgba(52, 211, 153, 0.2));
}

.relation-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #303133;
}

.relation-weight {
  flex-shrink: 0;
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
}

.relation-empty {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.kg-stats {
  flex-shrink: 0;
  display: flex;
  gap: 20px;
  justify-content: center;
  padding: 12px;
  color: #909399;
  font-size: 13px;
}

@media (max-width: 768px) {
  .kg-content {
    flex-direction: column;
  }
  .kg-detail-panel {
    width: 100% !important;
    margin-right: 0 !important;
    margin-top: 0;
    max-height: 0;
    border-radius: 0 0 12px 12px;
  }
  .kg-detail-panel.show {
    max-height: 300px;
    margin-top: 12px;
  }
  .search-input {
    width: 160px;
  }
}
</style>
