<!-- DocGenerate.vue —— 文书生成页面 -->
<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
// 统一使用 renderMarkdown（已集成 DOMPurify XSS 清洗）
import { renderMarkdown } from '@/utils/markdown'
import { generateDocument, listDocuments, getDocument, exportDocumentWord } from '@/api/document'
import { saveBlobAs, throwIfBlobError } from '@/utils/download'

const TYPE_OPTIONS = ['起诉状', '答辩状', '律师函', '授权委托书']

const FORM_SCHEMAS = {
  起诉状: [
    { key: 'plaintiff', label: '原告姓名', placeholder: '请输入原告姓名' },
    { key: 'defendant', label: '被告姓名', placeholder: '请输入被告姓名' },
    { key: 'claim', label: '诉讼请求', type: 'textarea', placeholder: '请描述诉讼请求' },
    { key: 'facts', label: '事实与理由', type: 'textarea', placeholder: '请描述案件事实与理由' },
    { key: 'court', label: '受理法院', placeholder: '如：北京市朝阳区人民法院' },
  ],
  答辩状: [
    { key: 'respondent', label: '答辩人', placeholder: '请输入答辩人姓名' },
    { key: 'plaintiff', label: '原告', placeholder: '请输入原告姓名' },
    { key: 'case_reason', label: '案由', placeholder: '请输入案由' },
    { key: 'defense', label: '答辩意见', type: 'textarea', placeholder: '请阐述答辩意见' },
    { key: 'court', label: '受理法院', placeholder: '如：北京市朝阳区人民法院' },
  ],
  律师函: [
    { key: 'recipient', label: '致函对象', placeholder: '请输入对方姓名/单位' },
    { key: 'client', label: '委托人', placeholder: '请输入委托人姓名' },
    { key: 'matter', label: '涉及事项', placeholder: '请简要描述事项' },
    { key: 'demand', label: '要求事项', type: 'textarea', placeholder: '请说明要求对方履行的事项' },
    { key: 'lawyer', label: '经办律师', placeholder: '请输入律师姓名' },
    { key: 'law_firm', label: '律师事务所', placeholder: '请输入律所名称' },
  ],
  授权委托书: [
    { key: 'principal', label: '委托人', placeholder: '请输入委托人姓名' },
    { key: 'agent', label: '受托人', placeholder: '请输入受托人姓名' },
    { key: 'agent_org', label: '受托人单位', placeholder: '请输入受托人所在单位' },
    { key: 'opponent', label: '对方当事人', placeholder: '请输入对方当事人姓名' },
    { key: 'case_reason', label: '案由', placeholder: '请输入案由' },
    { key: 'scope', label: '代理权限', placeholder: '一般代理 / 特别授权' },
  ],
}

const docType = ref('起诉状')
const formSchema = computed(() => FORM_SCHEMAS[docType.value])
const formData = reactive({})
const currentForm = computed(() => formData[docType.value] || (formData[docType.value] = {}))

const generating = ref(false)
const resultContent = ref('')
const progress = ref(0)          // 模拟进度 0~100
const progressTimer = ref(null)  // 进度定时器
// 当前展示的文书记录 ID（生成成功或加载历史后赋值，用于导出 Word）
const currentDocId = ref(null)
// Word 导出请求进行中（按钮 loading 状态）
const exporting = ref(false)

/** 将 Markdown 文本安全渲染为 HTML（已通过 DOMPurify 清洗） */
function renderMd(content) {
  return renderMarkdown(content)
}

/** 启动模拟进度条：缓慢增长到 90%，请求完成后跳到 100% */
function startProgress() {
  progress.value = 0
  progressTimer.value = setInterval(() => {
    if (progress.value < 90) {
      // 越接近 90 增长越慢，营造"快完成了"的感觉
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

async function handleGenerate() {
  const hasContent = Object.values(currentForm.value).some((v) => v && String(v).trim())
  if (!hasContent) { ElMessage.warning('请至少填写一项表单内容'); return }
  generating.value = true
  resultContent.value = ''   // 清空旧结果，显示加载状态
  currentDocId.value = null  // 清空旧记录 ID
  startProgress()
  try {
    const res = await generateDocument({ doc_type: docType.value, form_data: currentForm.value })
    resultContent.value = res.generated_content
    currentDocId.value = res.id  // 记录新文书 ID，供下载 Word 使用
    finishProgress()
    ElMessage.success('文书生成成功')
    loadHistory()
  } catch (e) {
    finishProgress()
  } finally {
    generating.value = false
  }
}

function copyResult() {
  navigator.clipboard.writeText(resultContent.value).then(() => ElMessage.success('已复制到剪贴板'))
}

/** 下载当前文书为 Word 文件（后端排版生成 .docx） */
async function downloadWord() {
  if (!currentDocId.value) { ElMessage.warning('当前文书尚未保存，无法导出'); return }
  exporting.value = true
  try {
    const blob = await exportDocumentWord(currentDocId.value)
    await throwIfBlobError(blob)
    saveBlobAs(blob, `${docType.value}_${currentDocId.value}.docx`)
    ElMessage.success('Word 文档已开始下载')
  } catch (e) {
    // 拦截器已对接口错误给出中文提示；此处兜底覆盖下载环节的意外异常
    if (!e?.response) ElMessage.error('Word 导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

const history = ref([])
async function loadHistory() {
  try { history.value = await listDocuments() } catch (e) { /* 忽略 */ }
}

async function viewHistory(item) {
  try {
    const res = await getDocument(item.id)
    docType.value = res.doc_type
    formData[res.doc_type] = { ...res.form_data }
    resultContent.value = res.generated_content
    currentDocId.value = res.id  // 加载历史后同样记录 ID，供下载 Word 使用
    ElMessage.info(`已加载历史记录 #${item.id}`)
  } catch (e) { /* 全局已提示 */ }
}

onMounted(loadHistory)
</script>

<template>
  <div class="doc-page">
    <section class="form-panel">
      <h2 class="panel-title"><el-icon class="title-icon"><Edit /></el-icon>填写文书信息</h2>
      <el-form label-position="top">
        <el-form-item label="文书类型">
          <el-select v-model="docType" style="width: 100%">
            <el-option v-for="t in TYPE_OPTIONS" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item v-for="field in formSchema" :key="field.key" :label="field.label">
          <el-input v-model="currentForm[field.key]" :type="field.type === 'textarea' ? 'textarea' : 'text'" :rows="field.type === 'textarea' ? 4 : 1" :placeholder="field.placeholder" resize="none" />
        </el-form-item>
        <el-button type="primary" class="generate-btn" :loading="generating" :icon="MagicStick" @click="handleGenerate">生成文书</el-button>
      </el-form>
    </section>

    <section class="result-panel">
      <div class="result-header">
        <h2 class="panel-title"><el-icon class="title-icon"><Document /></el-icon>生成结果</h2>
        <div class="result-actions">
          <el-button :icon="CopyDocument" @click="copyResult" :disabled="!resultContent">复制</el-button>
          <el-button type="primary" :icon="Download" :loading="exporting" @click="downloadWord" :disabled="!resultContent || !currentDocId">下载 Word</el-button>
        </div>
      </div>
      <div v-if="generating" class="result-loading">
        <div class="loading-box">
          <div class="loading-icon"><el-icon :size="40"><MagicStick /></el-icon></div>
          <p class="loading-title">AI 正在为您生成{{ docType }}...</p>
          <p class="loading-tip">正在分析案情、检索法律条文、撰写文书，请稍候</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <p class="progress-text">{{ Math.round(progress) }}%</p>
        </div>
      </div>
      <div v-else-if="resultContent" class="result-content md-body" v-html="renderMd(resultContent)"></div>
      <div v-else class="result-empty">
        <el-icon :size="48" class="empty-icon"><Document /></el-icon>
        <p>填写左侧表单后点击「生成文书」</p>
      </div>

      <div class="history-section">
        <h3 class="history-title">历史记录</h3>
        <ul v-if="history.length" class="history-list">
          <li v-for="item in history" :key="item.id" class="history-item" @click="viewHistory(item)">
            <span class="h-type">{{ item.doc_type }}</span>
            <span class="h-preview" :title="item.content_preview">{{ item.content_preview }}</span>
            <span class="h-time">{{ item.created_at }}</span>
          </li>
        </ul>
        <p v-else class="empty-tip">暂无历史记录</p>
      </div>
    </section>
  </div>
</template>

<script>
import { Edit, MagicStick, CopyDocument, Download, Document } from '@element-plus/icons-vue'
export default { name: 'DocGenerate' }
</script>

<style scoped>
.doc-page { display: flex; gap: 20px; padding: 24px; max-width: 1280px; margin: 0 auto; min-height: calc(100vh - 64px - 200px); }
.form-panel, .result-panel { background: #fff; border-radius: 10px; box-shadow: var(--shadow-card); padding: 24px; min-width: 0; }
.form-panel { flex: 0 0 420px; }
.result-panel { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.panel-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 600; color: var(--color-primary); margin-bottom: 20px; }
.title-icon { color: var(--color-gold); }
.generate-btn { width: 100%; margin-top: 8px; --el-button-bg-color: var(--color-primary); --el-button-border-color: var(--color-primary); --el-button-hover-bg-color: var(--color-primary-light); --el-button-hover-border-color: var(--color-primary-light); }

.result-header { display: flex; align-items: center; justify-content: space-between; }
/* 主操作按钮统一主题色（深蓝底、悬停浅蓝） */
.result-actions .el-button--primary {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-light);
  --el-button-hover-border-color: var(--color-primary-light);
}
.result-content { flex: 1; background: #f7f9fc; border: 1px solid var(--color-border); border-radius: 8px; padding: 20px; line-height: 1.9; font-size: 14px; overflow-y: auto; overflow-x: hidden; min-height: 300px; max-height: 500px; min-width: 0; word-break: break-word; }
.result-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--color-text-secondary); min-height: 300px; }
.empty-icon { color: var(--color-primary); opacity: 0.4; margin-bottom: 12px; }

/* ===== 生成中加载状态 ===== */
.result-loading { flex: 1; display: flex; align-items: center; justify-content: center; min-height: 300px; }
.loading-box { text-align: center; width: 100%; max-width: 360px; }
.loading-icon { color: var(--color-primary); animation: float 1.5s ease-in-out infinite; margin-bottom: 16px; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.loading-title { font-size: 16px; font-weight: 600; color: var(--color-primary); margin: 0 0 6px; }
.loading-tip { font-size: 13px; color: var(--color-text-secondary); margin: 0 0 20px; }
.progress-bar { width: 100%; height: 8px; background: #eef1f6; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--color-primary), var(--color-gold)); border-radius: 4px; transition: width 0.2s ease; }
.progress-text { margin-top: 10px; font-size: 13px; color: var(--color-text-secondary); font-weight: 600; }

/* ===== 文书结果 Markdown 渲染 ===== */
.md-body { white-space: normal; }
.md-body :deep(h1), .md-body :deep(h2), .md-body :deep(h3), .md-body :deep(h4) { margin: 14px 0 8px; font-weight: 600; color: var(--color-primary); line-height: 1.4; }
.md-body :deep(h1) { font-size: 18px; text-align: center; }
.md-body :deep(h2) { font-size: 16px; }
.md-body :deep(h3) { font-size: 15px; }
.md-body :deep(p) { margin: 8px 0; text-indent: 2em; }
.md-body :deep(strong) { font-weight: 600; color: #2c3e50; }
.md-body :deep(ul), .md-body :deep(ol) { margin: 8px 0; padding-left: 2em; }
.md-body :deep(li) { margin: 4px 0; }
.md-body :deep(blockquote) { margin: 10px 0; padding: 8px 14px; border-left: 3px solid var(--color-gold); background: #faf6ee; color: #666; }
.md-body :deep(code) { background: #f0f3f7; padding: 1px 5px; border-radius: 3px; font-size: 13px; color: #c0392b; }
.md-body :deep(hr) { border: none; border-top: 1px dashed var(--color-border); margin: 14px 0; }

.history-section { margin-top: 20px; border-top: 1px solid var(--color-border); padding-top: 16px; min-width: 0; }
.history-title { font-size: 15px; font-weight: 600; color: var(--color-text-main); margin-bottom: 12px; }
.history-list { max-height: 180px; overflow-y: auto; min-width: 0; }
.history-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 6px; cursor: pointer; transition: background 0.2s; min-width: 0; }
.history-item:hover { background: #f0f3f7; }
.h-type { flex: 0 0 80px; font-size: 13px; color: var(--color-primary); font-weight: 600; }
.h-preview { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 13px; color: var(--color-text-secondary); }
.h-time { flex: 0 0 140px; font-size: 12px; color: #999; text-align: right; }
.empty-tip { color: var(--color-text-secondary); font-size: 13px; text-align: center; padding: 12px; }

@media (max-width: 960px) { .doc-page { flex-direction: column; } .form-panel { flex: none; } }
</style>
