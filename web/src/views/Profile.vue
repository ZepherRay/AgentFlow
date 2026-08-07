<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <div class="profile-header">
        <div class="avatar-wrapper">
          <el-avatar :size="120" :src="avatarUrl" class="avatar">
            <User />
          </el-avatar>
          <div class="avatar-upload-btn">
            <el-button type="primary" size="small" icon="Upload" @click="triggerUpload">更换头像</el-button>
            <input type="file" ref="fileInput" accept="image/*" class="hidden-input" @change="handleAvatarUpload" />
          </div>
        </div>
        <div class="user-info">
          <h2>{{ userForm.nickname || userForm.username }}</h2>
          <p>{{ userForm.username }}</p>
        </div>
      </div>
      <el-form ref="formRef" :model="userForm" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="userForm.nickname" />
        </el-form-item>
        <el-form-item label="新密码（选填）">
          <el-input v-model="userForm.newPassword" type="password" placeholder="不填则不修改密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="userForm.confirmPassword" type="password" placeholder="确认新密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleUpdate">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const fileInput = ref(null)
const avatarVersion = ref(Date.now())

const avatarUrl = computed(() => {
  let url = userForm.avatar
  if (!url) return ''
  // Backward compat: old records stored bare filename
  if (!url.startsWith('/') && !url.startsWith('http')) {
    url = `/uploads/avatars/${url}`
  }
  return `${url}?t=${avatarVersion.value}`
})

const userForm = reactive({
  id: 0,
  username: '',
  email: '',
  nickname: '',
  avatar: '',
  newPassword: '',
  confirmPassword: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  nickname: [
    { max: 50, message: '昵称长度不能超过50', trigger: 'blur' }
  ]
}

function triggerUpload() {
  fileInput.value?.click()
}

async function handleAvatarUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片文件')
    return
  }
  const loadingInstance = ElLoading.service({ text: '上传中...', background: 'rgba(255,255,255,0.7)' })
  try {
    const res = await api.users.uploadAvatar(file)
    userForm.avatar = res.data.url
    avatarVersion.value = Date.now()
    // Notify other components (navbar avatar) to refresh
    window.dispatchEvent(new CustomEvent('avatar-updated', { detail: { url: res.data.url, ts: avatarVersion.value } }))
    ElMessage.success('头像上传成功')
  } catch (error) {
    ElMessage.error(error.message || '上传失败')
  } finally {
    loadingInstance.close()
    event.target.value = ''
  }
}

onMounted(async () => {
  try {
    const res = await api.auth.getMe()
    Object.assign(userForm, res.data)
  } catch {
    router.push('/login')
  }
})

async function handleUpdate() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (userForm.newPassword && userForm.newPassword !== userForm.confirmPassword) {
    ElMessage.error('两次密码不一致')
    return
  }
  loading.value = true
  try {
    const updateData = {
      email: userForm.email,
      nickname: userForm.nickname
    }
    if (userForm.newPassword) {
      updateData.password = userForm.newPassword
    }
    await api.users.updateMe(updateData)
    ElMessage.success('更新成功')
  } catch (error) {
    ElMessage.error(error.message || '更新失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-container { max-width: 720px; margin: 0 auto; height: 100%; background: var(--bg-1); }
.profile-card { padding: 40px; border-radius: var(--r-lg); border: 1px solid var(--border); background: var(--surface); backdrop-filter: blur(12px); }
.profile-header { display: flex; align-items: center; gap: 32px; margin-bottom: 36px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }
.avatar-wrapper { flex-shrink: 0; position: relative; }
.avatar { width: 120px; height: 120px; cursor: pointer; transition: all 0.3s; border: 4px solid var(--border); }
.avatar:hover { transform: scale(1.05); border-color: var(--ac); }
.avatar-upload-btn { margin-top: 16px; display: flex; justify-content: center; }
.avatar-upload-btn :deep(.el-button--small) { border-radius: 8px; font-weight: 500; }
.hidden-input { display: none; }
.user-info h2 { margin: 0 0 8px 0; font-size: 24px; font-weight: 700; color: var(--t-0); }
.user-info p { margin: 0; color: var(--t-3); font-size: 15px; }
:deep(.el-form-item__label) { color: var(--t-2); }
:deep(.el-input__wrapper) { background: var(--bg-2); border: 1px solid var(--border); box-shadow: none; }
:deep(.el-input__wrapper:hover) { border-color: var(--ac); }
:deep(.el-input__wrapper.is-focus) { border-color: var(--ac); }
:deep(.el-input__inner) { color: var(--t-0); background: transparent; }
:deep(.el-input__inner::placeholder) { color: var(--t-3); }

@media (max-width: 768px) {
  .profile-container { padding: 0 16px; }
  .profile-card { padding: 24px; }
  .profile-header { flex-direction: column; gap: 20px; margin-bottom: 24px; }
  .avatar { width: 100px; height: 100px; }
  .user-info h2 { font-size: 20px; }
}

@media (max-width: 480px) {
  .profile-container { padding: 0 12px; }
  .profile-card { padding: 16px; }
  .profile-header { gap: 16px; padding-bottom: 16px; }
  .avatar { width: 80px; height: 80px; }
  .user-info h2 { font-size: 18px; }
  .user-info p { font-size: 13px; }
}
</style>
