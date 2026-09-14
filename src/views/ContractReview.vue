<!-- ContractReview.vue —— 合同审查页面 -->
<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadContract, reviewContract, listContracts, getContractDetail, exportReviewPdf } from '@/api/contract'
import { saveBlobAs, throwIfBlobError } from '@/utils/download'

const uploading = ref(false)
// 当前操作的合同记录 { id, name }（上传成功或加载历史后赋值）
const currentContract = ref(null)
const extractedText = ref('')   // 合同文本预览（前 200 字，上传后展示）
const fullText = ref('')        // 合同原文全文（审查完成后 / 加载历史时拉取，用于风险高亮定位）

async function handleFileChange(file) {
  const raw = file.raw || file
  const ext = (raw.name.split('.').pop() || '').toLowerCase()
  if (!['docx', 'pdf'].includes(ext)) { ElMessage.error('仅支持 .docx 或 .pdf 格式'); return false }
  uploading.value = true
  try {
    const res = await uploadContract(raw)
    currentContract.value = { id: res.id, name: res.file_name || raw.name, length: res.text_length }
    extractedText.value = res.text_preview
    fullText.value = ''        // 新上传的合同清空旧全文，审查后再加载
    reviewResult.value = null
    ElMessage.success('文件上传成功，已提取合同文本')
  } catch (e) { /* 全局已提示 */ }
  finally { uploading.value = false }
  return false
}

const reviewing = ref(false)
const reviewResult = ref(null)
const progress = ref(0)
const progressTimer = ref(null)

function startProgress() {
  progress.value = 0
  progressTimer.value = setInterval(() => {
    if (progress.value < 90) {
      const step = Math.max(0.5, (90 - progress.value) * 0.05)
      progress.value = Math.min(90, progress.value + step)
    }
  }, 200)
}
function finishProgress() {
  if (progressTimer.value) { clearInterval(progressTimer.value); progressTimer.value = null }
  progress.value = 100
}
onUnmounted(() => { if (progressTimer.value) clearInterval(progressTimer.value) })

const levelMeta = {
  高: { type: 'danger', color: '#c0392b' },
  中: { type: 'warning', color: '#e67e22' },
  低: { type: 'success', color: '#27ae60' },
}
// 高亮样式的数字类名映射（避免中文 class 名的兼容性隐患）
const levelClassMap = { 高: 'lv-high', 中: 'lv-mid', 低: 'lv-low' }

async function handleReview() {
  if (!currentContract.value) return
  reviewing.value = true
  reviewResult.value = null
  startProgress()
  try {
    const res = await reviewContract(currentContract.value.id)
    reviewResult.value = res.review_result
    finishProgress()
    ElMessage.success('审查完成')
    loadHistory()
    // 审查完成后拉取合同全文，展示"原文 + 风险高亮"视图
    await loadFullText(currentContract.value.id)
  } catch (e) {
    finishProgress()
  } finally { reviewing.value = false }
}

/** 拉取合同记录详情（含原文全文），用于风险条款定位高亮 */
async function loadFullText(contractId) {
  try {
    const detail = await getContractDetail(contractId)
    fullText.value = detail.original_text || ''
  } catch (e) {
    // 全文加载失败不影响审查结果展示，仅隐藏高亮视图
    fullText.value = ''
  }
}

// ---- 风险条款定位高亮：将原文切分为"普通文本 / 高亮片段"交替的段落数据 ----
const segments = computed(() => {
  const text = fullText.value
  const risks = reviewResult.value?.risks || []
  if (!text || !risks.length) return []

  // 1) 计算每条风险条款在原文中的匹配区间
  const marks = []
  risks.forEach((r, idx) => {
    const clause = (r.clause || '').trim()
    if (!clause) return
    let start = text.indexOf(clause)
    if (start >= 0) {
      marks.push({ start, end: start + clause.length, riskIdx: idx })
      return
    }
    // 精确匹配失败（常见于 PDF 提取文本被换行打断）：
    // 用"去空白归一化"方式匹配，再映射回原文区间
    const normMap = []   // 归一化文本索引 -> 原文索引
    let normText = ''
    for (let i = 0; i < text.length; i++) {
      if (!/\s/.test(text[i])) { normMap.push(i); normText += text[i] }
    }
    const normClause = clause.replace(/\s+/g, '')
    const nPos = normText.indexOf(normClause)
    if (nPos >= 0 && normClause) {
      const s = normMap[nPos]
      const e = normMap[Math.min(nPos + normClause.length - 1, normMap.length - 1)] + 1
      marks.push({ start: s, end: e, riskIdx: idx })
    }
  })

  // 2) 按起始位置排序，切分为交替的普通/高亮片段（重叠的高亮保留先出现的）
  marks.sort((a, b) => a.start - b.start || a.end - b.end)
  const result = []
  let cursor = 0
  for (const m of marks) {
    if (m.start < cursor) continue                 // 与前一个高亮重叠，跳过
    if (m.start > cursor) result.push({ text: text.slice(cursor, m.start), riskIdx: null })
    result.push({ text: text.slice(m.start, m.end), riskIdx: m.riskIdx })
    cursor = m.end
  }
  if (cursor < text.length) result.push({ text: text.slice(cursor), riskIdx: null })
  return result
})

// 原文高亮视图的显示条件：已有全文且审查结果存在
const showFullText = computed(() => segments.value.length > 0)

/**
 * 点击风险卡片的"定位原文"：滚动到原文中对应的高亮片段并闪烁提示
 * @param {number} riskIdx - 风险条目下标
 */
function locateInText(riskIdx) {
  nextTick(() => {
    const el = document.getElementById(`risk-loc-${riskIdx}`)
    if (!el) { ElMessage.info('未能在原文中定位到该条款'); return }
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    // 闪烁动画提示（重复点击时先移除再添加，保证动画重新触发）
    el.classList.remove('flash')
    void el.offsetWidth  // 强制回流，重启动画
    el.classList.add('flash')
    setTimeout(() => el.classList.remove('flash'), 2400)
  })
}

// ---- 审查报告 PDF 导出 ----
const exportingPdf = ref(false)

async function handleExportPdf() {
  if (!currentContract.value) return
  exportingPdf.value = true
  try {
    const blob = await exportReviewPdf(currentContract.value.id)
    await throwIfBlobError(blob)
    // 文件名：审查报告_原合同文件名(去扩展名).pdf
    const stem = (currentContract.value.name || `contract_${currentContract.value.id}`).replace(/\.[^.]+$/, '')
    saveBlobAs(blob, `审查报告_${stem}.pdf`)
    ElMessage.success('审查报告 PDF 已开始下载')
  } catch (e) {
    // 拦截器已对接口错误（如未审查/字体缺失）给出中文提示；此处兜底覆盖下载环节异常
    if (!e?.response) ElMessage.error('PDF 导出失败，请稍后重试')
  } finally { exportingPdf.value = false }
}

const history = ref([])
async function loadHistory() {
  try { history.value = await listContracts() } catch (e) { /* 忽略 */ }
}

/** 点击历史记录：加载详情（原文全文 + 审查结果），可继续审查或导出报告 */
async function viewHistory(item) {
  try {
    const detail = await getContractDetail(item.id)
    currentContract.value = { id: detail.id, name: detail.file_name }
    fullText.value = detail.original_text || ''
    extractedText.value = (detail.original_text || '').slice(0, 200)
    reviewResult.value = detail.review_result || null
    if (!detail.review_result) {
      ElMessage.info('该记录尚未审查，可直接点击「开始智能审查」')
    } else {
      ElMessage.info(`已加载记录 #${item.id} 的审查结果`)
    }
  } catch (e) { /* 全局已提示 */ }
}

const riskCount = computed(() => {
  if (!reviewResult.value) return { 高: 0, 中: 0, 低: 0 }
  return reviewResult.value.risks.reduce((acc, r) => ((acc[r.level] = (acc[r.level] || 0) + 1), acc), { 高: 0, 中: 0, 低: 0 })
})

onMounted(loadHistory)
</script>

<template>
  <div class="contract-page">
    <section class="left-panel">
      <h2 class="panel-title"><el-icon class="title-icon"><Upload /></el-icon>上传合同文件</h2>
      <el-upload :auto-upload="false" :show-file-list="false" :on-change="handleFileChange" drag accept=".docx,.pdf">
        <el-icon class="upload-icon" :size="40"><UploadFilled /></el-icon>
        <div class="upload-text">将文件拖到此处，或<em>点击上传</em></div>
        <div class="upload-hint">仅支持 .docx / .pdf 格式，最大 10MB</div>
      </el-upload>

      <div v-if="currentContract" class="file-info">
        <el-icon><Document /></el-icon>
        <span class="file-name" :title="currentContract.name">{{ currentContract.name }}</span>
        <span class="file-meta">({{ currentContract.length }} 字)</span>
      </div>

      <!-- 合同文本区：审查完成后切换为"原文 + 风险高亮"视图 -->
      <div class="text-preview">
        <template v-if="showFullText">
          <div class="preview-header">
            <h3>合同原文（风险高亮）</h3>
            <div class="legend">
              <span class="legend-item lv-high">高</span>
              <span class="legend-item lv-mid">中</span>
              <span class="legend-item lv-low">低</span>
            </div>
          </div>
          <div class="full-text-content">
            <template v-for="(seg, i) in segments" :key="i">
              <mark
                v-if="seg.riskIdx !== null"
                :id="`risk-loc-${seg.riskIdx}`"
                class="risk-mark"
                :class="levelClassMap[reviewResult.risks[seg.riskIdx].level] || 'lv-low'"
              >{{ seg.text }}</mark>
              <span v-else>{{ seg.text }}</span>
            </template>
          </div>
        </template>
        <template v-else>
          <h3>合同原文预览</h3>
          <div v-if="extractedText" class="preview-content">{{ extractedText }}...</div>
          <p v-else class="empty-tip">上传文件后将在此显示提取的文本</p>
        </template>
      </div>

      <el-button type="primary" class="review-btn" :loading="reviewing" :disabled="!currentContract" :icon="View" @click="handleReview">开始智能审查</el-button>
    </section>

    <section class="right-panel">
      <div class="right-header">
        <h2 class="panel-title"><el-icon class="title-icon"><Warning /></el-icon>审查结果</h2>
        <!-- 审查完成后展示导出报告按钮 -->
        <el-button
          v-if="reviewResult && currentContract"
          type="primary"
          size="small"
          :icon="Download"
          :loading="exportingPdf"
          @click="handleExportPdf"
        >导出审查报告 PDF</el-button>
      </div>

      <div v-if="reviewing" class="review-loading">
        <div class="loading-box">
          <div class="loading-icon"><el-icon :size="40"><Warning /></el-icon></div>
          <p class="loading-title">AI 正在审查合同...</p>
          <p class="loading-tip">正在逐条分析风险条款、检索相关法律依据，请稍候</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <p class="progress-text">{{ Math.round(progress) }}%</p>
        </div>
      </div>

      <div v-else-if="!reviewResult" class="empty-state">
        <el-icon :size="56" class="empty-icon"><View /></el-icon>
        <p>上传合同文件并点击「开始智能审查」</p>
        <p class="sub">系统将识别高/中/低风险条款并给出修改建议</p>
      </div>

      <template v-else>
        <div class="risk-summary" :style="{ borderColor: levelMeta[reviewResult.risk_level].color }">
          <div class="risk-level" :style="{ color: levelMeta[reviewResult.risk_level].color }">总体风险等级：{{ reviewResult.risk_level }}</div>
          <div class="risk-stats">
            <span class="stat high">高风险 {{ riskCount.高 }} 项</span>
            <span class="stat mid">中风险 {{ riskCount.中 }} 项</span>
            <span class="stat low">低风险 {{ riskCount.低 }} 项</span>
          </div>
          <p class="risk-summary-text">{{ reviewResult.summary }}</p>
        </div>

        <div class="risk-list">
          <div v-for="(risk, idx) in reviewResult.risks" :key="idx" class="risk-card">
            <div class="risk-card-header">
              <el-tag :type="levelMeta[risk.level].type" effect="dark">{{ risk.level }}风险</el-tag>
              <span class="risk-no">风险条款 #{{ idx + 1 }}</span>
              <!-- 定位原文按钮：仅当该条款在原文中被高亮时显示 -->
              <el-icon
                v-if="showFullText"
                class="locate-btn"
                title="在原文中定位"
                @click="locateInText(idx)"
              ><Aim /></el-icon>
            </div>
            <div class="risk-clause"><strong>原文引用：</strong><span>{{ risk.clause }}</span></div>
            <div class="risk-analysis"><strong>风险分析：</strong><span>{{ risk.analysis }}</span></div>
            <div class="risk-suggestion"><strong>修改建议：</strong><span>{{ risk.suggestion }}</span></div>
          </div>
        </div>
      </template>

      <div class="history-section">
        <h3 class="history-title">审查历史</h3>
        <ul v-if="history.length" class="history-list">
          <li v-for="item in history" :key="item.id" class="history-item" @click="viewHistory(item)">
            <span class="h-name" :title="item.file_name">{{ item.file_name }}</span>
            <el-tag v-if="item.reviewed" type="success" size="small">已审查</el-tag>
            <el-tag v-else type="info" size="small">待审查</el-tag>
            <span class="h-time">{{ item.created_at }}</span>
          </li>
        </ul>
        <p v-else class="empty-tip">暂无审查历史</p>
      </div>
    </section>
  </div>
</template>

<script>
import { Upload, UploadFilled, Document, View, Warning, Download, Aim } from '@element-plus/icons-vue'
export default { name: 'ContractReview' }
</script>

<style scoped>
.contract-page { display: flex; gap: 20px; padding: 24px; max-width: 1280px; margin: 0 auto; min-height: calc(100vh - 64px - 200px); }
.left-panel, .right-panel { background: #fff; border-radius: 10px; box-shadow: var(--shadow-card); padding: 24px; display: flex; flex-direction: column; min-width: 0; }
.left-panel { flex: 0 0 380px; }
.right-panel { flex: 1; min-width: 0; }

.panel-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 600; color: var(--color-primary); margin-bottom: 16px; }
.title-icon { color: var(--color-gold); }

/* 右侧头部：标题 + 导出报告按钮同行排布 */
.right-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.right-header .panel-title { margin-bottom: 16px; }
.right-header .el-button--primary {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-light);
  --el-button-hover-border-color: var(--color-primary-light);
}

.upload-icon { color: var(--color-primary); opacity: 0.6; }
.upload-text { color: var(--color-text-secondary); margin-top: 8px; }
.upload-text em { color: var(--color-primary); font-style: normal; }
.upload-hint { font-size: 12px; color: #999; margin-top: 4px; }

.file-info { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding: 8px 12px; background: #f0f3f7; border-radius: 6px; font-size: 13px; }
.file-name { color: var(--color-primary); font-weight: 600; }
.file-meta { color: #999; }

.text-preview { margin-top: 16px; flex: 1; min-height: 200px; display: flex; flex-direction: column; }
.preview-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.preview-header h3 { font-size: 14px; color: var(--color-text-main); margin: 0; }
.text-preview h3 { font-size: 14px; color: var(--color-text-main); margin-bottom: 8px; }
.preview-content { background: #f7f9fc; border: 1px solid var(--color-border); border-radius: 6px; padding: 12px; font-size: 13px; line-height: 1.7; max-height: 260px; overflow-y: auto; }

/* ===== 合同原文风险高亮视图 ===== */
/* 高/中/低图例 */
.legend { display: flex; gap: 6px; }
.legend-item { font-size: 11px; padding: 1px 8px; border-radius: 10px; line-height: 1.6; }
.legend-item.lv-high { background: rgba(192,57,43,0.12); color: #c0392b; }
.legend-item.lv-mid { background: rgba(230,126,34,0.12); color: #e67e22; }
.legend-item.lv-low { background: rgba(39,174,96,0.12); color: #27ae60; }
/* 全文滚动容器：撑满左侧剩余空间 */
.full-text-content {
  flex: 1; background: #f7f9fc; border: 1px solid var(--color-border); border-radius: 6px;
  padding: 14px; font-size: 13px; line-height: 2; overflow-y: auto; min-height: 200px;
  white-space: pre-wrap; word-break: break-all; color: #3d4a56;
}
/* 风险条款高亮 mark：按风险等级着色（下边框加深以强化视觉对比） */
.risk-mark { padding: 1px 2px; border-radius: 3px; }
.risk-mark.lv-high { background: rgba(192,57,43,0.15); border-bottom: 2px solid #c0392b; }
.risk-mark.lv-mid { background: rgba(230,126,34,0.15); border-bottom: 2px solid #e67e22; }
.risk-mark.lv-low { background: rgba(39,174,96,0.13); border-bottom: 2px solid #27ae60; }
/* 点击"定位原文"时的闪烁提示动画 */
.risk-mark.flash { animation: mark-flash 1.2s ease 2; }
@keyframes mark-flash {
  0%, 100% { background-color: rgba(201,169,110,0.15); }
  50% { background-color: rgba(201,169,110,0.75); }
}

.review-btn { margin-top: 16px; --el-button-bg-color: var(--color-primary); --el-button-border-color: var(--color-primary); --el-button-hover-bg-color: var(--color-primary-light); --el-button-hover-border-color: var(--color-primary-light); }

.empty-state { text-align: center; color: var(--color-text-secondary); padding: 60px 20px; }
.empty-icon { color: var(--color-primary); opacity: 0.4; margin-bottom: 12px; }
.empty-state .sub { font-size: 13px; margin-top: 6px; }

/* ===== 审查中加载状态 ===== */
.review-loading { text-align: center; padding: 60px 20px; }
.loading-box { display: inline-block; width: 100%; max-width: 360px; }
.loading-icon { color: var(--color-primary); animation: float 1.5s ease-in-out infinite; margin-bottom: 16px; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.loading-title { font-size: 16px; font-weight: 600; color: var(--color-primary); margin: 0 0 6px; }
.loading-tip { font-size: 13px; color: var(--color-text-secondary); margin: 0 0 20px; }
.progress-bar { width: 100%; height: 8px; background: #eef1f6; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--color-primary), var(--color-gold)); border-radius: 4px; transition: width 0.2s ease; }
.progress-text { margin-top: 10px; font-size: 13px; color: var(--color-text-secondary); font-weight: 600; }

.risk-summary { border: 2px solid; border-radius: 10px; padding: 16px; margin-bottom: 20px; background: #fdfcf9; }
.risk-level { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
.risk-stats { display: flex; gap: 16px; margin-bottom: 10px; }
.risk-stats .stat { font-size: 13px; }
.risk-stats .stat.high { color: #c0392b; }
.risk-stats .stat.mid { color: #e67e22; }
.risk-stats .stat.low { color: #27ae60; }
.risk-summary-text { font-size: 13px; line-height: 1.7; color: var(--color-text-secondary); }

.risk-list { display: flex; flex-direction: column; gap: 12px; max-height: 420px; overflow-y: auto; overflow-x: hidden; min-width: 0; }
.risk-card { border: 1px solid var(--color-border); border-radius: 8px; padding: 14px 16px; background: #fff; min-width: 0; }
.risk-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.risk-no { font-size: 13px; color: var(--color-text-secondary); }
/* 定位原文按钮：hover 浮现，金色主题呼应页面配色 */
.locate-btn { margin-left: auto; color: var(--color-gold); cursor: pointer; font-size: 15px; transition: transform 0.15s; }
.locate-btn:hover { transform: scale(1.2); color: var(--color-primary); }
.risk-card > div { font-size: 13px; line-height: 1.7; margin-bottom: 6px; word-break: break-word; }
.risk-card strong { color: var(--color-text-main); }
.risk-suggestion span { color: #27ae60; }

.history-section { margin-top: 20px; border-top: 1px solid var(--color-border); padding-top: 16px; min-width: 0; }
.history-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
.history-list { max-height: 160px; overflow-y: auto; min-width: 0; }
.history-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 6px; cursor: pointer; transition: background 0.2s; min-width: 0; }
.history-item:hover { background: #f0f3f7; }
.h-name { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 13px; }
.h-time { flex: 0 0 140px; font-size: 12px; color: #999; text-align: right; }
.empty-tip { color: var(--color-text-secondary); font-size: 13px; text-align: center; padding: 12px; }

@media (max-width: 960px) { .contract-page { flex-direction: column; } .left-panel { flex: none; } }
</style>
