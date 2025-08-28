<template>
  <v-container>
    <v-card v-for="(license, index) in licenses" :key="index" class="mb-4">
      <v-card-title>{{ license.name }}</v-card-title>
      <v-card-text>
        <v-textarea
          readonly
          auto-grow
          :model-value="license.content"
          variant="solo"
        />
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted } from "vue";

// Reactive variable to store licenses
const licenses = ref<{ name: string; content: string }[]>([]);

const modules = import.meta.glob("../../LICENSES/*", {
  as: "raw",
  eager: true,
});
for (const [path, module] of Object.entries(modules)) {
  const name = path.split("/").pop() || "Unknown";
  licenses.value.push({ name, content: module as string });
}
</script>
