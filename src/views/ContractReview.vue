<!-- ContractReview.vue —— 合同审查页面 -->
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadContract, reviewContract, listContracts } from '@/api/contract'

const uploading = ref(false)
const currentFile = ref(null)
const uploadedContractId = ref(null)
const extractedText = ref('')

async function handleFileChange(file) {
  const raw = file.raw || file
  const ext = (raw.name.split('.').pop() || '').toLowerCase()
  if (!['docx', 'pdf'].includes(ext)) { ElMessage.error('仅支持 .docx 或 .pdf 格式'); return false }
  uploading.value = true
  try {
    const res = await uploadContract(raw)
    uploadedContractId.value = res.id
    extractedText.value = res.text_preview
    currentFile.value = { name: raw.name, length: res.text_length }
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

async function handleReview() {
  if (!uploadedContractId.value) return
  reviewing.value = true
  reviewResult.value = null
  startProgress()
  try {
    const res = await reviewContract(uploadedContractId.value)
    reviewResult.value = res.review_result
    finishProgress()
    ElMessage.success('审查完成')
    loadHistory()
  } catch (e) {
    finishProgress()
  } finally { reviewing.value = false }
}

const history = ref([])
async function loadHistory() {
  try { history.value = await listContracts() } catch (e) { /* 忽略 */ }
}

function viewHistory(item) {
  if (!item.review_result) { ElMessage.info('该记录尚未完成审查'); return }
  reviewResult.value = item.review_result
  ElMessage.info(`已加载记录 #${item.id} 的审查结果`)
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

      <div v-if="currentFile" class="file-info">
        <el-icon><Document /></el-icon>
        <span class="file-name">{{ currentFile.name }}</span>
        <span class="file-meta">({{ currentFile.length }} 字)</span>
      </div>

      <div class="text-preview">
        <h3>合同原文预览</h3>
        <div v-if="extractedText" class="preview-content">{{ extractedText }}...</div>
        <p v-else class="empty-tip">上传文件后将在此显示提取的文本</p>
      </div>

      <el-button type="primary" class="review-btn" :loading="reviewing" :disabled="!uploadedContractId" :icon="View" @click="handleReview">开始智能审查</el-button>
    </section>

    <section class="right-panel">
      <h2 class="panel-title"><el-icon class="title-icon"><Warning /></el-icon>审查结果</h2>

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
import { Upload, UploadFilled, Document, View, Warning } from '@element-plus/icons-vue'
export default { name: 'ContractReview' }
</script>

<style scoped>
.contract-page { display: flex; gap: 20px; padding: 24px; max-width: 1280px; margin: 0 auto; min-height: calc(100vh - 64px - 200px); }
.left-panel, .right-panel { background: #fff; border-radius: 10px; box-shadow: var(--shadow-card); padding: 24px; display: flex; flex-direction: column; }
.left-panel { flex: 0 0 380px; }
.right-panel { flex: 1; }

.panel-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 600; color: var(--color-primary); margin-bottom: 16px; }
.title-icon { color: var(--color-gold); }

.upload-icon { color: var(--color-primary); opacity: 0.6; }
.upload-text { color: var(--color-text-secondary); margin-top: 8px; }
.upload-text em { color: var(--color-primary); font-style: normal; }
.upload-hint { font-size: 12px; color: #999; margin-top: 4px; }

.file-info { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding: 8px 12px; background: #f0f3f7; border-radius: 6px; font-size: 13px; }
.file-name { color: var(--color-primary); font-weight: 600; }
.file-meta { color: #999; }

.text-preview { margin-top: 16px; flex: 1; min-height: 200px; }
.text-preview h3 { font-size: 14px; color: var(--color-text-main); margin-bottom: 8px; }
.preview-content { background: #f7f9fc; border: 1px solid var(--color-border); border-radius: 6px; padding: 12px; font-size: 13px; line-height: 1.7; max-height: 260px; overflow-y: auto; }

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

.risk-list { display: flex; flex-direction: column; gap: 12px; max-height: 420px; overflow-y: auto; }
.risk-card { border: 1px solid var(--color-border); border-radius: 8px; padding: 14px 16px; background: #fff; }
.risk-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.risk-no { font-size: 13px; color: var(--color-text-secondary); }
.risk-card > div { font-size: 13px; line-height: 1.7; margin-bottom: 6px; }
.risk-card strong { color: var(--color-text-main); }
.risk-suggestion span { color: #27ae60; }

.history-section { margin-top: 20px; border-top: 1px solid var(--color-border); padding-top: 16px; }
.history-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
.history-list { max-height: 160px; overflow-y: auto; }
.history-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
.history-item:hover { background: #f0f3f7; }
.h-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 13px; }
.h-time { font-size: 12px; color: #999; }
.empty-tip { color: var(--color-text-secondary); font-size: 13px; text-align: center; padding: 12px; }

@media (max-width: 960px) { .contract-page { flex-direction: column; } .left-panel { flex: none; } }
</style>
