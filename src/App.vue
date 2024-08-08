<template>
  <div id="app">
    <div class="chat-container">
      <h1>Chatbot</h1>
      <div class="chat-box">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.sender]"
          v-html="renderMessage(message.text)"
      > 
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
          {{ isFetching ? "Sending..." : "Send" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>

import { marked } from 'marked';

export default {

  data() {
    return {
      userInput: "",
      messages: [],
      isFetching: false,
      websocket: null,
    };
  },
  methods: {
    handleButtonClick() {
      if (!this.isFetching) {
        this.sendMessage();
      }
    },
    connectWebSocket() {
      console.log("connectWebSocket()")
      this.websocket = new WebSocket("ws://localhost:8000/ws/chat");

      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // console.log("data: ", data)

        if (data.response === "[END]") {
          this.isFetching = false;
        } else {
          if (this.messages.length > 0 && this.messages[this.messages.length - 1].sender === "Bot") {
            // 마지막 메시지가 Bot의 메시지인 경우 업데이트
            const lastMessage = this.messages[this.messages.length - 1];
            lastMessage.text = data.response;
          } else {
            // 새 Bot 메시지 추가
            this.messages.push({ sender: "Bot", text: data.response });
          }
        }
      };

      this.websocket.onclose = () => {
        console.log("WebSocket connection closed");
        this.isFetching = false;
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.isFetching = false;
      };
    },
    sendMessage() {
      console.log("sendMessage()")
      if (this.userInput.trim() === "") return;
      // User의 메시지 추가
      this.messages.push({ sender: "User", text: this.userInput });
      this.isFetching = true;
      // 웹소켓을 통해 메시지 전송
      this.websocket.send(JSON.stringify({ message: this.userInput }));
      // 입력창 초기화
      this.userInput = "";
    },
    renderMessage(text) {
      return marked.parse(text);  // 마크다운을 HTML로 변환
    }
  },
  mounted() {
    this.connectWebSocket(); // 컴포넌트가 마운트되면 웹소켓 연결
  },
};
</script>

<style src="./App.css"></style>