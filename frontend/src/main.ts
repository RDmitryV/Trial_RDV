import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'
import StyleClass from 'primevue/styleclass'
import router from './router'
import App from './App.vue'

// Sakai styles
import '@/assets/styles/tailwind.css'
import '@/assets/styles/styles.scss'

// PrimeVue icons
import 'primeicons/primeicons.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: '.app-dark',
            cssLayer: false
        }
    },
    ripple: true
})
app.use(ToastService)
app.use(ConfirmationService)

app.directive('tooltip', Tooltip)
app.directive('styleclass', StyleClass)

app.mount('#app')
