<template>
  <div class="profile-page">
    <el-card class="profile-card">
      <div class="profile-header">
        <div class="avatar-section">
          <el-avatar :size="100" class="main-avatar">
            {{ userForm.nickname?.charAt(0) || userForm.username?.charAt(0) || 'U' }}
          </el-avatar>
          <div class="avatar-actions">
            <el-button type="text" size="small">更换头像</el-button>
          </div>
        </div>
        <div class="user-detail">
          <h2 class="user-name">{{ userForm.nickname || userForm.username }}</h2>
          <p class="user-username">@{{ userForm.username }}</p>
          <div class="user-stats">
            <span class="stat">
              <span class="num">0</span>
              <span class="label">智能体</span>
            </span>
            <span class="stat">
              <span class="num">0</span>
              <span class="label">工作流</span>
            </span>
            <span class="stat">
              <span class="num">0</span>
              <span class="label">知识库</span>
            </span>
          </div>
        </div>
      </div>
      
      <div class="profile-tabs">
        <el-tabs v-model="activeTab" type="card">
          <el-tab-pane label="基本信息" name="basic">
            <el-form ref="formRef" :model="userForm" :rules="rules" label-width="120px">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="用户名" prop="username">
                    <el-input v-model="userForm.username" disabled class="disabled-input" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="邮箱" prop="email">
                    <el-input v-model="userForm.email" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="昵称" prop="nickname">
                    <el-input v-model="userForm.nickname" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="手机号" prop="phone">
                    <el-input v-model="userForm.phone" placeholder="选填" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item>
                <el-button type="primary" :loading="loading" @click="handleUpdate">保存修改</el-button>
                <el-button @click="resetForm">重置</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="安全设置" name="security">
            <div class="security-section">
              <div class="security-item">
                <div class="item-info">
                  <span class="item-title">修改密码</span>
                  <span class="item-desc">定期更换密码以保证账户安全</span>
                </div>
                <el-button type="primary" size="small" @click="showChangePassword = true">修改</el-button>
              </div>
              <div class="security-item">
                <div class="item-info">
                  <span class="item-title">绑定手机</span>
                  <span class="item-desc">{{ userForm.phone || '未绑定' }}</span>
                </div>
                <el-button type="primary" size="small" :disabled="!!userForm.phone">绑定</el-button>
              </div>
              <div class="security-item">
                <div class="item-info">
                  <span class="item-title">登录记录</span>
                  <span class="item-desc">最近登录：{{ lastLoginTime }}</span>
                </div>
                <el-button type="text" size="small">查看</el-button>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="API Key" name="apikey">
            <div class="apikey-section">
              <div class="key-display">
                <el-input v-model="apiKey" disabled type="password" show-password />
                <el-button type="primary" size="small" @click="regenerateKey">重新生成</el-button>
              </div>
              <p class="key-tip">API Key 用于调用 AgentFlow API，请妥善保管</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>
    
    <el-dialog v-model="showChangePassword" title="修改密码" width="400px" :close-on-click-modal="false">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px">
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input v-model="pwdForm.oldPassword" type="password" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="pwdForm.newPassword" type="password" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="pwdForm.confirmPassword" type="password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePassword = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="handleChangePassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const router = useRouter()
const formRef = ref(null)
const pwdFormRef = ref(null)
const loading = ref(false)
const pwdLoading = ref(false)
const activeTab = ref('basic')
const showChangePassword = ref(false)
const apiKey = ref('sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

const userForm = reactive({
  id: 0,
  username: '',
  email: '',
  nickname: '',
  phone: '',
  avatar: ''
})

const originalForm = reactive({})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  nickname: [
    { max: 50, message: '昵称长度不能超过50', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ]
}

const pwdForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.newPassword) {
          callback(new Error('两次密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const lastLoginTime = ref('2025-07-09 09:30:00')

onMounted(async () => {
  try {
    const res = await api.auth.getMe()
    Object.assign(userForm, res.data)
    Object.assign(originalForm, res.data)
  } catch {
    router.push('/login')
  }
})

function resetForm() {
  Object.assign(userForm, originalForm)
}

async function handleUpdate() {
  await formRef.value.validate()
  loading.value = true
  try {
    const updateData = {
      email: userForm.email,
      nickname: userForm.nickname,
      phone: userForm.phone,
      avatar: userForm.avatar
    }
    await api.users.updateMe(updateData)
    ElMessage.success('更新成功')
    Object.assign(originalForm, userForm)
  } catch (error) {
    ElMessage.error(error.message || '更新失败')
  } finally {
    loading.value = false
  }
}

async function handleChangePassword() {
  await pwdFormRef.value.validate()
  pwdLoading.value = true
  try {
    await api.users.changePassword(pwdForm)
    ElMessage.success('密码修改成功')
    showChangePassword.value = false
    pwdForm.oldPassword = ''
    pwdForm.newPassword = ''
    pwdForm.confirmPassword = ''
  } catch (error) {
    ElMessage.error(error.message || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

function regenerateKey() {
  ElMessage.info('API Key 重新生成功能开发中')
}
</script>

<style scoped>
.profile-page {
  padding: 0;
}

.profile-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.profile-header {
  display: flex;
  gap: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 24px;
}

.avatar-section {
  flex-shrink: 0;
}

.main-avatar {
  background: linear-gradient(135deg, #409eff 0%, #7c3aed 100%);
  color: #fff;
  font-size: 32px;
  font-weight: 600;
}

.avatar-actions {
  text-align: center;
  margin-top: 12px;
}

.user-detail {
  flex: 1;
}

.user-name {
  font-size: 22px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.user-username {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 16px 0;
}

.user-stats {
  display: flex;
  gap: 32px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat .num {
  font-size: 20px;
  font-weight: 700;
  color: #3b82f6;
}

.stat .label {
  font-size: 13px;
  color: #64748b;
  margin-top: 2px;
}

.profile-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.disabled-input :deep(.el-input__wrapper) {
  background: #f1f5f9;
  cursor: not-allowed;
}

.security-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.security-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.item-info {
  display: flex;
  flex-direction: column;
}

.item-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.item-desc {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.apikey-section {
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
}

.key-display {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.key-display :deep(.el-input) {
  flex: 1;
}

.key-tip {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}
</style>