<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useResearchStore } from '@/stores/research'
import { useToast } from 'primevue/usetoast'
import AppLayout from '@/components/common/AppLayout.vue'
import Card from 'primevue/card'
import Stepper from 'primevue/stepper'
import StepperPanel from 'primevue/stepperpanel'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import type { CreateResearchRequest } from '@/types'

const router = useRouter()
const researchStore = useResearchStore()
const toast = useToast()
const activeStep = ref(0)

// Industries list
const industries = [
  'IT и технологии',
  'Розничная торговля',
  'Общественное питание',
  'Финансы и банки',
  'Образование',
  'Здравоохранение',
  'Строительство и недвижимость',
  'Транспорт и логистика',
  'Производство',
  'Сельское хозяйство',
]

// Russian regions
const regions = [
  'Москва',
  'Санкт-Петербург',
  'Московская область',
  'Ленинградская область',
  'Новосибирская область',
  'Свердловская область',
  'Республика Татарстан',
  'Краснодарский край',
  'Ростовская область',
  'Нижегородская область',
]

const schema = yup.object({
  title: yup.string().required('Название обязательно').min(5, 'Минимум 5 символов'),
  description: yup.string().required('Описание обязательно').min(20, 'Минимум 20 символов'),
  product_description: yup
    .string()
    .required('Описание продукта обязательно')
    .min(20, 'Минимум 20 символов'),
  industry: yup.string().required('Выберите отрасль'),
  region: yup.string().required('Выберите регион'),
})

const { errors, defineField, handleSubmit, validate } = useForm({
  validationSchema: schema,
})

const [title] = defineField('title')
const [description] = defineField('description')
const [product_description] = defineField('product_description')
const [industry] = defineField('industry')
const [region] = defineField('region')
const loading = ref(false)

const nextStep = async () => {
  // Validate current step fields
  const result = await validate()
  if (result.valid) {
    activeStep.value++
  }
}

const prevStep = () => {
  if (activeStep.value > 0) {
    activeStep.value--
  }
}

const onSubmit = handleSubmit(async (values) => {
  try {
    loading.value = true
    const research = await researchStore.create(values as CreateResearchRequest)
    toast.add({
      severity: 'success',
      summary: 'Успешно',
      detail: 'Исследование создано',
      life: 3000,
    })
    router.push({ name: 'research-detail', params: { id: research.id } })
  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: error.response?.data?.detail || 'Не удалось создать исследование',
      life: 5000,
    })
  } finally {
    loading.value = false
  }
})

const cancel = () => {
  router.push({ name: 'dashboard' })
}
</script>

<template>
  <AppLayout>
    <div class="p-4">
      <Card>
        <template #title>Новое маркетинговое исследование</template>
        <template #content>
          <Stepper :active-step="activeStep" linear>
            <StepperPanel header="Основная информация">
              <template #content>
                <div class="flex flex-column gap-4 py-4">
                  <div class="flex flex-column gap-2">
                    <label for="title">Название исследования *</label>
                    <InputText
                      id="title"
                      v-model="title"
                      placeholder="Например: Анализ рынка доставки еды в Москве"
                      :class="{ 'p-invalid': errors.title }"
                    />
                    <small v-if="errors.title" class="p-error">{{ errors.title }}</small>
                  </div>

                  <div class="flex flex-column gap-2">
                    <label for="description">Описание исследования *</label>
                    <Textarea
                      id="description"
                      v-model="description"
                      rows="4"
                      placeholder="Краткое описание целей и задач исследования"
                      :class="{ 'p-invalid': errors.description }"
                    />
                    <small v-if="errors.description" class="p-error">{{ errors.description }}</small>
                  </div>

                  <div class="flex gap-2 justify-content-end">
                    <Button label="Отмена" severity="secondary" outlined @click="cancel" />
                    <Button label="Далее" @click="nextStep" />
                  </div>
                </div>
              </template>
            </StepperPanel>

            <StepperPanel header="Продукт/Услуга">
              <template #content>
                <div class="flex flex-column gap-4 py-4">
                  <div class="flex flex-column gap-2">
                    <label for="product_description">Описание продукта/услуги *</label>
                    <Textarea
                      id="product_description"
                      v-model="product_description"
                      rows="6"
                      placeholder="Подробно опишите ваш продукт или услугу, целевую аудиторию, особенности"
                      :class="{ 'p-invalid': errors.product_description }"
                    />
                    <small v-if="errors.product_description" class="p-error">{{
                      errors.product_description
                    }}</small>
                  </div>

                  <div class="flex gap-2 justify-content-end">
                    <Button label="Назад" severity="secondary" outlined @click="prevStep" />
                    <Button label="Далее" @click="nextStep" />
                  </div>
                </div>
              </template>
            </StepperPanel>

            <StepperPanel header="Отрасль и регион">
              <template #content>
                <div class="flex flex-column gap-4 py-4">
                  <div class="flex flex-column gap-2">
                    <label for="industry">Отрасль *</label>
                    <Dropdown
                      id="industry"
                      v-model="industry"
                      :options="industries"
                      placeholder="Выберите отрасль"
                      :class="{ 'p-invalid': errors.industry }"
                    />
                    <small v-if="errors.industry" class="p-error">{{ errors.industry }}</small>
                  </div>

                  <div class="flex flex-column gap-2">
                    <label for="region">Регион *</label>
                    <Dropdown
                      id="region"
                      v-model="region"
                      :options="regions"
                      placeholder="Выберите регион"
                      :class="{ 'p-invalid': errors.region }"
                    />
                    <small v-if="errors.region" class="p-error">{{ errors.region }}</small>
                  </div>

                  <div class="flex gap-2 justify-content-end">
                    <Button label="Назад" severity="secondary" outlined @click="prevStep" />
                    <Button
                      label="Создать исследование"
                      :loading="loading"
                      @click="onSubmit"
                    />
                  </div>
                </div>
              </template>
            </StepperPanel>
          </Stepper>
        </template>
      </Card>
    </div>
  </AppLayout>
</template>
