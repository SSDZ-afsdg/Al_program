<!-- AiConsult.vue —— AI法律咨询页面 -->
<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import {
  listConversations, createConversation, deleteConversation,
  listMessages, sendMessageStream,
} from '@/api/chat'

// 配置 marked：关闭换行不渲染（让 \n 正常换行），开启代码高亮等
marked.setOptions({ breaks: true, gfm: true })

const conversations = ref([])
const currentId = ref(null)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const loadingConv = ref(false)
const loadingMsg = ref(false)

const msgContainer = ref(null)

/** 将 Markdown 文本渲染为 HTML（供 v-html 使用） */
function renderMd(content) {
  if (!content) return ''
  return marked.parse(content)
}

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  })
}

async function loadConversations() {
  loadingConv.value = true
  try {
    conversations.value = await listConversations()
    if (conversations.value.length && !currentId.value) {
      selectConversation(conversations.value[0].id)
    }
  } finally { loadingConv.value = false }
}

async function selectConversation(id) {
  currentId.value = id
  messages.value = []
  loadingMsg.value = true
  try {
    messages.value = await listMessages(id)
    scrollToBottom()
  } finally { loadingMsg.value = false }
}

async function handleCreateConversation() {
  try {
    const conv = await createConversation({ title: '新的法律咨询' })
    conversations.value.unshift(conv)
    selectConversation(conv.id)
  } catch (e) { /* 全局已提示 */ }
}

async function handleDeleteConversation(conv) {
  try {
    await ElMessageBox.confirm(`确定删除对话「${conv.title}」吗？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await deleteConversation(conv.id)
    ElMessage.success('已删除')
    conversations.value = conversations.value.filter((c) => c.id !== conv.id)
    if (currentId.value === conv.id) { currentId.value = null; messages.value = [] }
  } catch (e) { /* 全局已提示 */ }
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || sending.value) return
  if (!currentId.value) { ElMessage.warning('请先新建或选择一个对话'); return }

  sending.value = true
  // 先追加用户消息
  messages.value.push({ role: 'user', content: text })
  // 追加一条空的 assistant 消息占位，流式内容会实时填充
  const assistantIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })
  inputText.value = ''
  scrollToBottom()

  try {
    await sendMessageStream(currentId.value, { content: text }, {
      onMessage(chunk) {
        // 实时拼接流式文本
        messages.value[assistantIdx].content += chunk
        scrollToBottom()
      },
      onDone() {
        sending.value = false
        scrollToBottom()
      },
      onError(errMsg) {
        // 出错时把已拼接的内容保留，并追加错误提示
        const cur = messages.value[assistantIdx].content
        messages.value[assistantIdx].content = cur
          ? cur + '\n\n> ⚠️ ' + errMsg
          : '⚠️ ' + errMsg
        sending.value = false
        ElMessage.error(errMsg)
      },
    })
  } catch (e) {
    // fetch 网络错误等
    messages.value[assistantIdx].content = '⚠️ 网络异常，请稍后重试'
    sending.value = false
    ElMessage.error('请求失败')
  }
}

onMounted(loadConversations)
</script>

<template>
  <div class="consult-page">
    <aside class="conv-sidebar">
      <el-button type="primary" class="new-conv-btn" :icon="Plus" @click="handleCreateConversation">新建对话</el-button>
      <div v-loading="loadingConv" class="conv-list">
        <div v-for="conv in conversations" :key="conv.id" class="conv-item" :class="{ active: conv.id === currentId }" @click="selectConversation(conv.id)">
          <span class="conv-title" :title="conv.title">{{ conv.title }}</span>
          <el-icon class="del-btn" @click.stop="handleDeleteConversation(conv)"><Delete /></el-icon>
        </div>
        <p v-if="!conversations.length && !loadingConv" class="empty-tip">暂无对话，点击上方「新建对话」开始咨询</p>
      </div>
    </aside>

    <section class="chat-area">
      <div class="chat-header">
        <el-icon class="chat-title-icon"><ChatDotRound /></el-icon>
        <span>AI法律咨询</span>
      </div>

      <div ref="msgContainer" v-loading="loadingMsg" class="msg-list">
        <div v-if="!currentId" class="empty-state">
          <el-icon :size="56" class="empty-icon"><ChatDotRound /></el-icon>
          <p class="empty-title">开始您的法律咨询</p>
          <p class="empty-desc">点击左侧「新建对话」，向 AI 提问法律问题</p>
        </div>
        <div v-for="(msg, idx) in messages" :key="idx" class="msg-item" :class="msg.role">
          <el-icon class="msg-avatar"><User v-if="msg.role === 'user'" /><Service v-else /></el-icon>
          <div class="msg-bubble" :class="{ 'md-body': msg.role === 'assistant' }">
            <template v-if="msg.role === 'assistant'">
              <div v-if="msg.content" v-html="renderMd(msg.content)"></div>
              <span v-else class="typing-cursor">▍</span>
            </template>
            <template v-else>{{ msg.content }}</template>
          </div>
        </div>
      </div>

      <div class="input-area">
        <el-input v-model="inputText" type="textarea" :rows="2" placeholder="请输入您的法律问题，按 Ctrl+Enter 发送" :disabled="!currentId" @keydown.ctrl.enter="handleSend" />
        <el-button type="primary" class="send-btn" :loading="sending" :disabled="!currentId || !inputText.trim()" @click="handleSend">
          <el-icon><Promotion /></el-icon>发送
        </el-button>
      </div>
    </section>
  </div>
</template>

<script>
import { Plus, Delete, User, Service, Promotion, ChatDotRound } from '@element-plus/icons-vue'
export default { name: 'AiConsult' }
</script>

<style scoped>
.consult-page { display: flex; min-height: calc(100vh - 64px - 200px); background: var(--color-bg-page); }

.conv-sidebar {
  width: 260px; background: #fff; border-right: 1px solid var(--color-border);
  display: flex; flex-direction: column; padding: 16px; gap: 12px;
}
.new-conv-btn {
  width: 100%;
  --el-button-bg-color: var(--color-primary); --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-light); --el-button-hover-border-color: var(--color-primary-light);
}
.conv-list { flex: 1; overflow-y: auto; }
.conv-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; margin-bottom: 6px; border-radius: 6px; cursor: pointer; transition: background 0.2s;
}
.conv-item:hover { background: #f0f3f7; }
.conv-item.active { background: rgba(26,58,92,0.08); color: var(--color-primary); font-weight: 600; }
.conv-title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-right: 8px; }
.del-btn { opacity: 0; color: #c0392b; transition: opacity 0.2s; }
.conv-item:hover .del-btn { opacity: 1; }
.empty-tip { text-align: center; color: var(--color-text-secondary); font-size: 13px; padding: 24px 8px; line-height: 1.6; }

.chat-area { flex: 1; display: flex; flex-direction: column; background: #fff; }
.chat-header { display: flex; align-items: center; gap: 8px; padding: 14px 20px; border-bottom: 1px solid var(--color-border); font-size: 16px; font-weight: 600; color: var(--color-primary); }
.chat-title-icon { color: var(--color-gold); }

.msg-list { flex: 1; overflow-y: auto; padding: 20px; background: #f7f9fc; }
.empty-state { text-align: center; padding: 80px 20px; color: var(--color-text-secondary); }
.empty-icon { color: var(--color-primary); opacity: 0.5; }
.empty-title { font-size: 18px; font-weight: 600; color: var(--color-text-main); margin: 16px 0 8px; }
.empty-desc { font-size: 13px; }

.msg-item { display: flex; gap: 10px; margin-bottom: 18px; }
.msg-item.user { flex-direction: row-reverse; }
.msg-avatar { width: 36px; height: 36px; border-radius: 50%; background: var(--color-primary); color: #fff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.msg-item.user .msg-avatar { background: var(--color-gold); }
.msg-bubble { max-width: 70%; padding: 10px 14px; border-radius: 10px; background: #fff; border: 1px solid var(--color-border); line-height: 1.6; font-size: 14px; }
.msg-item.user .msg-bubble { background: var(--color-primary); color: #fff; border-color: var(--color-primary); white-space: pre-wrap; }

/* AI 助手消息：渲染 Markdown，保留格式 */
.msg-bubble.md-body { white-space: normal; }
.msg-bubble.md-body :deep(h1), .msg-bubble.md-body :deep(h2), .msg-bubble.md-body :deep(h3),
.msg-bubble.md-body :deep(h4) { margin: 12px 0 6px; font-weight: 600; line-height: 1.4; color: var(--color-primary); }
.msg-bubble.md-body :deep(h1) { font-size: 18px; }
.msg-bubble.md-body :deep(h2) { font-size: 16px; }
.msg-bubble.md-body :deep(h3) { font-size: 15px; }
.msg-bubble.md-body :deep(h4) { font-size: 14px; }
.msg-bubble.md-body :deep(p) { margin: 6px 0; }
.msg-bubble.md-body :deep(strong) { font-weight: 600; color: #2c3e50; }
.msg-bubble.md-body :deep(em) { font-style: italic; }
.msg-bubble.md-body :deep(ul), .msg-bubble.md-body :deep(ol) { margin: 6px 0; padding-left: 22px; }
.msg-bubble.md-body :deep(li) { margin: 3px 0; }
.msg-bubble.md-body :deep(blockquote) { margin: 8px 0; padding: 6px 12px; border-left: 3px solid var(--color-gold); background: #faf6ee; color: #666; }
.msg-bubble.md-body :deep(code) { background: #f0f3f7; padding: 1px 5px; border-radius: 3px; font-size: 13px; color: #c0392b; font-family: Consolas, Monaco, monospace; }
.msg-bubble.md-body :deep(pre) { background: #2c3e50; color: #ecf0f1; padding: 10px 12px; border-radius: 6px; overflow-x: auto; margin: 8px 0; }
.msg-bubble.md-body :deep(pre code) { background: none; color: inherit; padding: 0; }
.msg-bubble.md-body :deep(a) { color: var(--color-primary); text-decoration: underline; }
.msg-bubble.md-body :deep(hr) { border: none; border-top: 1px solid var(--color-border); margin: 10px 0; }
.msg-bubble.md-body :deep(table) { border-collapse: collapse; margin: 8px 0; }
.msg-bubble.md-body :deep(th), .msg-bubble.md-body :deep(td) { border: 1px solid var(--color-border); padding: 4px 8px; }

/* 打字光标闪烁 */
.typing-cursor { display: inline-block; animation: blink 1s infinite; color: var(--color-primary); font-weight: bold; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }

.input-area { display: flex; align-items: flex-end; gap: 12px; padding: 16px 20px; border-top: 1px solid var(--color-border); background: #fff; }
.input-area :deep(.el-textarea__inner) { resize: none; }
.send-btn { height: 74px; --el-button-bg-color: var(--color-primary); --el-button-border-color: var(--color-primary); --el-button-hover-bg-color: var(--color-primary-light); --el-button-hover-border-color: var(--color-primary-light); }

@media (max-width: 768px) { .conv-sidebar { width: 180px; } }
</style>
