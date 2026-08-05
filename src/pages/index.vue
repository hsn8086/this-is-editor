<template>
  <div v-if="checking" class="d-flex align-center justify-center fill-height">
    <v-progress-circular color="primary" indeterminate />
  </div>
  <EnvironmentPage v-else />
</template>

<script lang="ts" setup>
  import { onMounted, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import EnvironmentPage from '@/components/EnvironmentPage.vue'
  import { environmentService } from '@/services'

  const checking = ref(true)
  const router = useRouter()

  onMounted(async () => {
    if (await environmentService.isSetupComplete()) {
      await router.replace('/editor')
      return
    }
    checking.value = false
  })
</script>
