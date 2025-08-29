import { createI18n } from 'vue-i18n'
import zhHans from '@/i18n/zh-Hans'
import enUS from '@/i18n/en-US'
export const i18n = createI18n({
    locale: 'en-US',
    fallbackLocale: 'en-US',
    messages: {
        'en-US': enUS,
        'zh-Hans': zhHans
    }
})
export type I18nType = typeof i18n.global.locale

if (window.pywebview && window.pywebview.api) {
    init()
} else {
    window.addEventListener('pywebviewready', () => {
        init()
    })
}
function init() {
    window.pywebview.api.get_config().then(config => {
        console.log(config.editor.tie.language.value)
        i18n.global.locale = config.editor.tie.language.value as I18nType
    }).catch(() => { })
}