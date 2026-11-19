<script setup>
import { ref } from 'vue'

const roomCode = ref('')
const isLoading = ref(false)

// Функция для создания комнаты
const createRoom = async () => {
  isLoading.value = true
  try {
    const response = await fetch('http://127.0.0.1:8000/api/rooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    const data = await response.json()
    roomCode.value = data.room_code
  } catch (error) {
    alert('Ошибка при создании комнаты. Сервер запущен?')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="container">
    <h1>Quiz App</h1>

    <!-- Если комната еще не создана -->
    <div v-if="!roomCode" class="create-screen">
      <button @click="createRoom" :disabled="isLoading">
        {{ isLoading ? 'Создание...' : 'Создать игру' }}
      </button>
    </div>

    <!-- Если комната создана -->
    <div v-else class="lobby-screen">
      <h2>Код комнаты:</h2>
      <div class="room-code">{{ roomCode }}</div>
      <p>Ожидание игроков...</p>
      <ul>
        <!-- Сюда позже будем выводить игроков -->
      </ul>
    </div>
  </div>
</template>

<style scoped>
.container {
  text-align: center;
  font-family: sans-serif;
  margin-top: 50px;
}
button {
  padding: 15px 30px;
  font-size: 20px;
  cursor: pointer;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 8px;
}
.room-code {
  font-size: 48px;
  font-weight: bold;
  letter-spacing: 5px;
  color: #2c3e50;
  margin: 20px 0;
  background: #f0f0f0;
  display: inline-block;
  padding: 10px 30px;
  border-radius: 10px;
}
</style>
