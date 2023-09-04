<template>
  <div id="chat" ref="chat">
    <div v-for="item in messages" :key="item.id">
      <div :class="['message', item.role]">
        <div>{{ item.message }}</div>
        <div v-if="item.recommend && item.recommend.length > 0">
          <br />
          <div>Recommendations:</div>
          <div v-for="(intent, index) in item.recommend" :key="index">
            {{ index + 1 }}. {{ intent }}
          </div>
        </div>
        <div>{{ item.product }}</div>
      </div>
    </div>
  </div>
  <input
    type="text"
    id="userInput"
    placeholder="Type your message..."
    @keypress="handleKeyPress"
    ref="userInput"
  />
  <button id="sendButton" @click="sendMessage">Send</button>
</template>


<script>
import { get_base_url } from '@/utils/utils';
export default {
  name: "ChatBox",
  data: function () {
    return {
      messages: [{role:"bot", message:"How may I assist you today?"}],
    };
  },
  methods: {
    appendMessage: function (sender, message) {
      this.messages.push({
        role: sender.toLowerCase(),
        ...message,
      });

      this.scrollToBottom()
    },
    scrollToBottom: function() {
      this.$nextTick(() => {
        const chatElement = this.$refs.chat;
        chatElement.scrollTop = chatElement.scrollHeight;
      });
    },
    sendMessage: function () {
      const userInput = this.$refs.userInput;
      const message = userInput.value;
      userInput.value = "";

      this.appendMessage("User", { message: message });
      const body = { product_name: message };
      //   const body = { role: "user", content: message };
      fetch(`${get_base_url()}/api/v1/aigc/qa/get_recomm`, {
      // fetch(`http://localhost:8081/api/v1/aigc/qa/get_recomm`, {
        method: "POST",
        // mode: "no-cors", // no-cors
        body: JSON.stringify(body),
      })
        .then((resp) => resp.json())
        .then((data) => {
          if (data.success == false){
            this.appendMessage("Bot", {message:data.error});
          } else {
            if (data.match_names){
              for (let i = 0; i < data.match_names.length; i ++){
                  this.appendMessage("Bot", {message: data.match_names[i]});
              }
            }
          }
        })
        .catch((rea) => {
          console.error(rea);
        });
    },
    handleKeyPress: function (event) {
      console.log(event);
      if (event.keyCode === 13) {
        // 按下回车键
        this.sendMessage();
      }
    },
  },
};
</script>

<style scoped>
body {
  font-family: Arial, sans-serif;
  padding: 10px;
  background-color: #f5f5f5;
}
pre {
  font-family: Arial, sans-serif;
  font-size: 14px;
}
#chat {
  border: 1px solid #ccc;
  background-color: #fff;
  padding: 20px;
  width: 500px;
  height: 400px;
  overflow-y: scroll;
  margin-bottom: 10px;
  font-size: 14px;
}
#userInput {
  width: 400px;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 14px;
}
#sendButton {
  padding: 5px 10px;
  border: none;
  background-color: #007bff;
  color: #fff;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}
#sendButton:hover {
  background-color: #0056b3;
}
.message {
  margin: 5px 0;
  clear: both;
  overflow: hidden;
  position: relative;
  padding: 5px;
  border-radius: 10px; /* 调整边框半径为10px */
  max-width: 80%;
  white-space: pre-wrap;
}
.user {
  color: #007bff;
  float: left;
  background-color: #e6f2ff;
}
.user::before {
  content: "User";
  position: absolute;
  top: -15px;
  left: 10px;
  font-size: 10px;
  color: #666;
}
.bot {
  color: #28a745;
  float: right;
  background-color: #e6ffe6;
}

.bot::before {
  content: "Bot";
  position: absolute;
  top: -15px;
  right: 10px;
  font-size: 10px;
  color: #666;
}
</style>