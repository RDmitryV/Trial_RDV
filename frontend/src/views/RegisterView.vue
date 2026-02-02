<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import { useForm } from 'vee-validate'
import * as yup from 'yup'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const schema = yup.object({
  full_name: yup.string().required('Имя обязательно').min(2, 'Минимум 2 символа'),
  email: yup.string().required('Email обязателен').email('Неверный формат email'),
  password: yup.string().required('Пароль обязателен').min(6, 'Минимум 6 символов'),
  confirmPassword: yup
    .string()
    .required('Подтверждение пароля обязательно')
    .oneOf([yup.ref('password')], 'Пароли не совпадают'),
})

const { errors, defineField, handleSubmit } = useForm({
  validationSchema: schema,
})

const [full_name] = defineField('full_name')
const [email] = defineField('email')
const [password] = defineField('password')
const [confirmPassword] = defineField('confirmPassword')
const loading = ref(false)

const onSubmit = handleSubmit(async (values) => {
  try {
    loading.value = true
    await authStore.register({
      full_name: values.full_name,
      email: values.email,
      password: values.password,
    })
    toast.add({
      severity: 'success',
      summary: 'Успешно',
      detail: 'Регистрация выполнена',
      life: 3000,
    })
    router.push({ name: 'dashboard' })
  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: error.response?.data?.detail || 'Ошибка регистрации',
      life: 5000,
    })
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="surface-ground flex align-items-center justify-content-center min-h-screen p-4">
    <Card class="w-full max-w-25rem">
      <template #title>
        <div class="text-center">
          <div class="text-3xl font-bold mb-2">🤖 Маркетолух</div>
          <div class="text-xl">Регистрация</div>
        </div>
      </template>
      <template #content>
        <form @submit="onSubmit" class="flex flex-column gap-3">
          <div class="flex flex-column gap-2">
            <label for="full_name">Полное имя</label>
            <InputText
              id="full_name"
              v-model="full_name"
              placeholder="Иван Иванов"
              :class="{ 'p-invalid': errors.full_name }"
            />
            <small v-if="errors.full_name" class="p-error">{{ errors.full_name }}</small>
          </div>

          <div class="flex flex-column gap-2">
            <label for="email">Email</label>
            <InputText
              id="email"
              v-model="email"
              type="email"
              placeholder="your@email.com"
              :class="{ 'p-invalid': errors.email }"
            />
            <small v-if="errors.email" class="p-error">{{ errors.email }}</small>
          </div>

          <div class="flex flex-column gap-2">
            <label for="password">Пароль</label>
            <Password
              id="password"
              v-model="password"
              placeholder="Минимум 6 символов"
              toggle-mask
              :class="{ 'p-invalid': errors.password }"
            />
            <small v-if="errors.password" class="p-error">{{ errors.password }}</small>
          </div>

          <div class="flex flex-column gap-2">
            <label for="confirmPassword">Подтвердите пароль</label>
            <Password
              id="confirmPassword"
              v-model="confirmPassword"
              placeholder="Повторите пароль"
              :feedback="false"
              toggle-mask
              :class="{ 'p-invalid': errors.confirmPassword }"
            />
            <small v-if="errors.confirmPassword" class="p-error">{{ errors.confirmPassword }}</small>
          </div>

          <Button
            type="submit"
            label="Зарегистрироваться"
            :loading="loading"
            class="w-full"
          />

          <div class="text-center mt-2">
            <span class="text-600">Уже есть аккаунт? </span>
            <router-link to="/login" class="font-semibold">
              Войти
            </router-link>
          </div>
        </form>
      </template>
    </Card>
  </div>
</template>
