<template>
  <div id="app">
    <div class="chat-container">
      <h1>Chatbot</h1>
      <div class="chat-box">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.sender]"
        >
          <div class="message-content">
            <strong>{{ message.sender }}:</strong> {{ message.text }}
          </div>
        </div>
        <div v-if="isTyping" class="message Bot">
          <div class="message-content">
            <strong>Bot:</strong> {{ currentBotMessage }}
          </div>
        </div>
        <div v-if="isFetching" class="loading-indicator">
          Loading...
        </div>
      </div>
      <div class="input-container">
        <input
          v-model="userInput"
          @keyup.enter="handleButtonClick"
          placeholder="Type a message..."
          class="input-box"
          :disabled="isFetching"
        />
        <button @click="handleButtonClick" class="send-button">
          {{ isTyping ? "Stop" : "Send" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      userInput: "",
      messages: [],
      currentBotMessage: "",
      isTyping: false,
      isFetching: false,
      typingTimeout: null,
      abortController: null,
      partialMessage: "", // 부분적으로 출력된 메시지를 저장
    };
  },
  methods: {
    handleButtonClick() {
      if (this.isTyping) {
        this.stopTyping();
      } else {
        this.sendMessage();
      }
    },
    sendMessage() {
      if (this.userInput.trim() === "") return;

      this.messages.push({ sender: "User", text: this.userInput });
      this.isFetching = true;

      this.abortController = new AbortController(); // AbortController 생성
      const signal = this.abortController.signal;

      fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: this.userInput }),
        signal, // 요청에 신호 추가
      })
        .then((response) => response.json())
        .then((data) => {
          this.displayBotMessage(data.response);
        })
        .catch((error) => {
          if (error.name === "AbortError") {
            console.log("Fetch aborted");
            if (this.partialMessage) {
              this.messages.push({ sender: "Bot", text: this.partialMessage });
            }
          } else {
            console.error("Error:", error);
          }
        })
        .finally(() => {
          this.isFetching = false;
        });

      this.userInput = "";
    },
    displayBotMessage(message) {
      this.currentBotMessage = "";
      this.isTyping = true;
      this.partialMessage = ""; // 부분 메시지 초기화
      let index = 0;

      const type = () => {
        if (index < message.length) {
          this.currentBotMessage += message[index];
          this.partialMessage += message[index]; // 현재까지의 부분 메시지를 저장
          index++;
          this.typingTimeout = setTimeout(type, 50);
        } else {
          this.messages.push({ sender: "Bot", text: this.currentBotMessage });
          this.isTyping = false;
        }
      };

      type();
    },
    stopTyping() {
      clearTimeout(this.typingTimeout); // 타이머 정지
      this.isTyping = false;
      this.currentBotMessage = ""; // 현재 메시지 초기화

      if (this.abortController) {
        this.abortController.abort(); // 요청 취소
      }
      // 부분적으로 출력된 메시지를 메시지 목록에 추가
      if (this.partialMessage) {
        this.messages.push({ sender: "Bot", text: this.partialMessage });
      }
    },
  },
};
</script>

<style src="./App.css"></style>