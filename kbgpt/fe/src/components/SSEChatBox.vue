<template>
  <div>
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
    <button id="sendButton" @click="sendMessage" ref="sendBtn">Send</button>
    <div>
      <p id="helpMessage">{{ helpMessages[selectedOption] }}</p>
    </div>
    <div class="controls">
      <label>
        <input type="radio" value="similarity" v-model="selectedOption" />
        Similarity
      </label>
      <label>
        <input type="radio" value="gpt4" v-model="selectedOption" /> GPT4
      </label>
      <label>
        <input type="radio" value="gpt3.5" v-model="selectedOption" /> GPT3.5
      </label>
    </div>
    <fieldset :disabled="selectedOption == 'similarity'" v-show="selectedOption != 'similarity'">
      <div class="controls">
        <label>
          <input
            class="thresholdBar"
            type="range"
            v-model="temperature"
            :min="0"
            :max="1"
            step="0.005"
          />
          Temperature: {{ temperature }}
        </label>
      </div> 
    </fieldset>
    <fieldset :disabled="selectedOption != 'similarity'" v-show="selectedOption == 'similarity'">
      <div class="controls">
        <label>
          <input
            class="thresholdBar"
            type="range"
            v-model="csliderValue"
            :min="0"
            :max="1"
            step="0.005"
          />
          QThreshold: {{ csliderValue }}
        </label>
      </div>
      <div class="controls">
        <label>
          <input
            class="thresholdBar"
            type="range"
            v-model="asliderValue"
            :min="0"
            :max="1"
            step="0.005"
          />
          AThreshold: {{ asliderValue }}
        </label>
      </div>
    </fieldset>
  </div>
</template>


<script>
export default {
  name: "SSEChatBox",
  data: function () {
    return {
      helpMessages: {
        similarity: "Use similarity to search the recommendation.",
        "gpt3.5": "Use gpt3.5 to reason about the recommendation",
        gpt4: "Use gpt4 to reason about the recommendation",
      },
      selectedOption: "gpt3.5",
      asliderValue: 0.175,
      csliderValue: 0.175,
      temperature: 0.7,
      messages: [{ role: "bot", message: "How may I assist you today?" }],
      products: {
        1: {
          id: "1",
          name: "Top Funds",
          description:
            "Top mutual funds are calculated by Bullsmart AI lab based on publicly available data from all mutual funds available in the Indian market. It is only for learning and research purposes and does not constitute to any investment advice. It includes the funds with the best data performance in the past.",
          intent:
            "Top Funds is the best performing mutual fund in India selected by Bullsmart's AI laboratory based on historical data.",
        },
        2: {
          id: "2",
          name: "AI Rank",
          description:
            "AI Rank is a fund screening tool powered by the Bullsmart AI lab. It is based on publicly available market data and should not be considered as any financial advise.Bullsmart has designed 8 distinctive classification dimensions that can help you quickly select funds based on your needs. These 8 categories are: low threshold, high return, long-term profit, most popular, Cost effective, leading benchmark, Sector leader, and Top companies.",
          intent:
            "You can use Bullsmart's artificial intelligence fund ranking to filter funds based on your needs. But this is not financial advice.",
        },
        3: {
          id: "3",
          name: "Start with Rs 100 !",
          description:
            "The Low Threshold Fund List is a list of equity funds with lower minimum investment amounts selected by Bullsmart based on AMC's public data. These funds are more friendly to novice users.Funds that can be invested when users have very little money.",
          intent:
            "Invest in equity funds with low minimum investment amounts suitable for novice users.",
        },
        4: {
          id: "4",
          name: "High Return",
          description:
            "The list of high return funds is based on publicly available data from AMC. Bullsmart selects funds with high returns and better profitability than industry benchmarks based on their past earnings performance.This type of fund is most concerned about their historical returns and is the group of funds with the highest historical CAGR in the Indian market",
          intent:
            "Bullsmart chose funds with high historical returns and stronger profitability than industry benchmarks.",
        },
        5: {
          id: "5",
          name: "Long-term Profit",
          description:
            "Long term Profit is a Bullsmart featured fund list.We search for funds that have been consistently profitable annually over the past 5 years based on publicly available data from AMC Corporation. They provide more sustainable returns compared to similar products.",
          intent:
            "Bullsmart chose funds that will continue to make profits for 5 years, providing sustainable returns.",
        },
        6: {
          id: "6",
          name: "Most Popular",
          description:
            "Based on the recent growth rate of AUM and other market public data, we will calculate the most popular funds in the market in the near future through Big data.",
          intent:
            "Bullsmart calculates popular funds based on the growth rate of AUM and other market data.",
        },
        7: {
          id: "7",
          name: "Cost effective",
          description:
            "Total Expense Ratio (TER) is the measure of the total costs or expenses in running a scheme. This measure is used by investors to compare the costs of the scheme with its peers and also in relation to the returns available from that scheme.AMC charges lower fees for these funds.",
          intent:
            "Bullsmart selects funds with lower fees compared to peers based on TER.",
        },
        8: {
          id: "8",
          name: "Leading Benchmark",
          description:
            "Leading Benchmark is based on the public Market data to screen the funds with the highest excess return rate in the same category in the market. These funds have shown significantly higher returns than the sub index in the past.",
          intent:
            "Bullsmart selects funds with returns higher than similar market indices.",
        },
        9: {
          id: "9",
          name: "Sector Leader",
          description:
            "Sector Leader is the largest fund under various categories in India, which is more trusted by investors and manages more assets.These funds have larger asset management scales and stronger market credibility",
          intent:
            "Bullsmart selects funds with large asset management scale and strong market reputation.",
        },
        10: {
          id: "10",
          name: "Top Company",
          description:
            "The funds in the Top Company focus on investing in the top listed companies in the Indian market.They focus on holding the top 100 listed companies in India",
          intent:
            "Focus on investing in top listed companies in the Indian market.",
        },
        11: {
          id: "11",
          name: "MF Categories",
          description:
            "MF Categories includes all categories of mutual funds. You can find various types of funds here.This includes all Bullsmart's funds that can be sold. Classification includes: Equity Funds, Hybrid Funds, Debt Funds, Big Cap Funds, Mid Cap Funds, Small Cap Funds, ELSS Funds, Liquid Funds.",
          intent:
            "All types of funds available, including Equity, Hybrid, Debt, Big Cap, Mid Cap, Small Cap, ELSS, and Liquid Funds.",
        },
        12: {
          id: "12",
          name: "Equity Funds",
          description:
            "An equity fund is a mutual fund scheme list that invests predominantly in equity stocks. In the Indian context, as per current SEBI Mutual Fund Regulations, an equity mutual fund scheme must invest at least 65% of the scheme's assets in equities and equity related instruments.",
          intent:
            "These mutual funds plan to invest at least 65% of their assets in stocks and stock related instruments.",
        },
        13: {
          id: "13",
          name: "Hybrid Funds",
          description:
            "Hybrid Funds are mutual fund schemes list which invest in more than one asset class i.e. equity, debt and other asset classes depending on the investment objective of the scheme. These funds invest in a mix of different asset classes to diversify the portfolio with an aim to minimize the risk involved.",
          intent:
            "These mutual funds diversify your investments through a combination of equity, debt, and other asset classes to minimize risk.",
        },
        14: {
          id: "14",
          name: "Debt Funds",
          description:
            "A debt fund is a mutual fund scheme list that invests in fixed income instruments, such as Corporate and Government Bonds, corporate debt securities, and money market instruments etc. that offer capital appreciation. Debt funds are also referred to as Income Funds or Bond Funds.",
          intent:
            "These mutual funds invest in fixed income instruments for capital appreciation.",
        },
        15: {
          id: "15",
          name: "Big Cap Funds",
          description:
            "Large cap mutual funds are equity funds that invest primarily in the top 100 companies of India",
          intent:
            "These mutual funds invest in the top 100 companies of India for potential returns.",
        },
        16: {
          id: "16",
          name: "Mid Cap Funds",
          description:
            "Mid Cap Mutual Funds are equity funds that invest in the mid-sized companies of India.",
          intent:
            "These mutual funds invest in mid-sized Indian companies for long-term growth.",
        },
        17: {
          id: "17",
          name: "Small Cap Funds",
          description:
            "As per current SEBI guidelines, Small Cap Equity Funds must invest at least 65% of their assets in Equity stocks of Small-Cap companies.",
          intent:
            "These mutual funds focus on small-cap companies for potential high returns.",
        },
        18: {
          id: "18",
          name: "Tax Saving(ELSS) Funds",
          description:
            "ELSS Funds are a class of mutual funds that are eligible for tax deductions under the provisions of Section 80C of the Income Tax Act, 1961. These mutual funds are equity-oriented and invest up to 65% of their portfolio in instruments such as shares. Investing in ELSS funds is an excellent way of planning your future while saving on taxes. An ELSS fund gives you the dual benefit of tax deductions and wealth creation over time.",
          intent:
            "ELSS funds are equity funds that can help you grow your wealth and are eligible for tax exemptions.",
        },
        19: {
          id: "19",
          name: "Liquid Funds",
          description:
            "Liquid funds meaning debt mutual fund schemes which invest in debt or money market instruments that mature within 91 days. Liquid funds are money market mutual fund schemes in which you can park your surplus funds for few weeks to few months.",
          intent:
            "Liquidity funds can safely store surplus funds in short-term debt or money market instruments.",
        },
        20: {
          id: "20",
          name: "All Funds",
          description: "This includes all the mutual funds we can trade",
          intent: "Explore and trade all our mutual fund offerings.",
        },
        21: {
          id: "21",
          name: "Smart Redeem",
          description:
            "Smart Redeem is a facility where investors can redeem some liquid funds at any time and receive money instantly. The risk of incurring losses on these funds is negligible, but these funds are geared to deliver marginally steady and higher returns than your savings account interest rate.With Smart Redeem you can receive money within 30 minutes of redemption at no extra cost. Normally, if you redeem other funds, you have to wait for T+1-T+3 working days to receive the funds._These funds are suitable to earn a little extra on idle money lying in your bank account. You may invest the money in these funds that you have kept aside for emergency requirements or any surplus money that you don't need for a few days or a year.These funds have the characteristics of low risk and quick redemption. If you pursue very high returns, it is not suitable for this type of fund.",
          intent:
            "Instantly redeem liquid funds with marginally steady returns and receive money within 30 minutes, suitable for idle money or emergency requirements. No waiting period, low risk.",
        },
        22: {
          id: "22",
          name: "Smart Nivesh",
          description:
            'In June 2023, Bullsmart released the Smart Nivesh feature. Smart Nivesh can help you design a healthy investment portfolio allocation plan based on your financial situation. You can use this feature by entering "Smart Nivesh" in Bullsmart\'s AI Services.We are a simple and intelligent process. You only need to input your basic financial information, and Smart Nivesh can help you calculate a healthy investment portfolio allocation plan.When building your investment portfolio, we will provide a list of funds based on different risk levels. You can build the most suitable investment portfolio based on your own judgment.',
          intent:
            "Design an investment portfolio plan based on your financial situation using Bullsmart's AI service. Calculate healthy investment allocation based on risk levels.",
        },
        23: {
          id: "23",
          name: "Goal Planning",
          description:
            "GoalPlanning is a tool and calculator. It can help you plan your future and achieve your goals. For example, planning to buy a new car, planning to buy a new house, preparing for one's daughter's wedding, preparing tuition fees, living expenses, or providing a retirement reserve fund. We have various calculators to help you plan your dreams. GoalPlanning will ask how much rupees your goal will cost and how long you want to spend to achieve it. Then, based on your target plan and referring to India's inflation rate, calculate how much money you need to invest through SIP and one-time investment based on your expected return on investment. GoalPlanning can help you clearly understand what efforts you need to make towards your goals.",
          intent:
            "Plan and achieve your future goals with calculators for car, house, wedding, education, retirement. Calculate required investments through SIP and one-time investments.",
        },
        24: {
          id: "24",
          name: "MF Filter",
          description:
            "By using the MF Filter tool, you can query a list of eligible funds based on AUM, CAGR, AMC, and other information. You can use MF Filter to discover more excellent funds and monitor the existing fund list. In order to identify better investment opportunities and control the buying timing. You can click the MF Filter button on the fund market page to enter the MF Filter function. Then you can enter the indicator parameters you want to filter according to your own needs. Finally, click submit and you will see the query results. You can directly invest in these funds or collect them in sequence",
          intent:
            "Query eligible funds based on AUM, CAGR, AMC to discover excellent investment opportunities. Control buying timing and invest directly or collect in sequence.",
        },
        25: {
          id: "25",
          name: "Return Calculator",
          description:
            "Investing for the future? Use this investment calculator to estimate how your contributions and returns may grow over time. The 'Return Calculator' can help you calculate the return on compound interest, and you can use it to calculate how much money you can have in the future if you continue to invest.",
          intent:
            "Estimate how your investments can grow over time with compound interest. Calculate future returns and plan for a financially secure future.",
        },
        26: {
          id: "26",
          name: "Financial Calculator",
          description:
            "A financial calculator can help you calculate the investment amount based on your personal financial goals. The calculator can calculate how much money you should invest in SIP/Lumpusm based on your target cost",
          intent:
            "Determine how much to invest based on personal financial goals. Calculate investment amount for SIP or Lumpsum investments.",
        },
        27: {
          id: "27",
          name: "Investing Personally Quiz",
          description:
            "When it comes to investing, there are so many different strategies for growing your money. In a way, investing is actually pretty customizable . According to Morningstar, a leading firm in investing analysis and management, there are four behavioral investor types. You're about to find out which one is yours! Just join the Investing Personally Quiz as honestly as possible.",
          intent:
            "Discover your investor type with this quiz. Find customized strategies for growing your money.",
        },
        28: {
          id: "28",
          name: "Daily",
          description:
            "The Fund Market Daily aims to provide investors with the latest information and insights on the fund market. The report will cover various types of funds, such as stock funds, bond funds, index funds, hybrid funds, etc., and provide the rise and fall of the market index on the day, the performance of various funds, and investment strategies for different market conditions.",
          intent:
            "Stay up-to-date with market insights and investment strategies through our daily fund market report.",
        },
        29: {
          id: "29",
          name: "Weekly",
          description:
            '"Market Report Weekly" is a weekly fund market report presented in video form, which aims to provide investors with a comprehensive summary of the fund market performance in the past week. Weekly reports will provide in-depth analysis of the performance of different types of funds, providing viewers with the latest insights on equity funds, bond funds, index funds, hybrid funds, and more.',
          intent:
            "Get a comprehensive summary of the fund market performance in video form. Analyze various types of funds for better investment decisions.",
        },
        30: {
          id: "30",
          name: "Monthly",
          description:
            '"Market Report Monthly" is a monthly fund market report in the form of video, which provides a detailed summary and analysis of the market performance in the past month. Through charts, data and professional interpretation, this monthly report presents investors with the latest developments of various fund types. Investors can understand market developments in a macro time frame, which is helpful for investors in long-term investment decisions. Choose wisely.',
          intent:
            "Gain in-depth knowledge of market trends and make informed long-term investment decisions with our monthly fund market report.",
        },
      },
    };
  },
  methods: {
    appendMessage: function (sender, message) {
      this.messages.push({
        role: sender.toLowerCase(),
        ...message,
      });

      this.scrollToBottom();
    },
    fetchProductCatalog: async function () {
      try {
        const fetchResponse = await fetch(
          "https://filesamples.com/samples/document/txt/sample3.txt"
        );
        console.log(fetchResponse.text());
      } catch (ex) {
        console.log("Error in fetch");
      }
    },
    scrollToBottom: function () {
      this.$nextTick(() => {
        const chatElement = this.$refs.chat;
        chatElement.scrollTop = chatElement.scrollHeight;
      });
    },
    sendMessage: async function () {
      const userInput = this.$refs.userInput;
      const message = userInput.value;
      userInput.value = "";
      if (!message.trim()) {
        return;
      }
      this.$refs.sendBtn.disabled = true;

      this.appendMessage("User", { message: message });
      const body = {
        question: message,
        recomm_type: this.selectedOption,
        athreshold: this.asliderValue,
        cthreshold: this.csliderValue,
        temperature: this.temperature
      };
      const response = await fetch(
        `${window.location.origin}/api/v1/aigc/qa/stream_qa`,
        {
          method: "POST",
          headers: {
            "Content-Type": "text/event-stream",
          },
          // mode: "no-cors", // no-cors
          body: JSON.stringify(body),
        }
      );
      const reader = response.body.getReader();
      let notdone = true;
      let streamingOfStream = false;
      while (notdone) {
        const { value, done } = await reader.read();
        if (done) break;

        const jsonString = new TextDecoder().decode(value);
        jsonString
          .split("data: ")
          .map((l) => {
            console.log(l);
            return l.trim().length == 0 ? null : JSON.parse(l);
          })
          .map((obj) => {
            if (obj) {
              if ('token' in obj && ! obj.token){
                streamingOfStream = !streamingOfStream
                if (streamingOfStream){
                  this.appendMessage("Bot", { message: "" });
                }
              }
              if (obj.token) {
                this.messages[this.messages.length - 1].message =
                  this.messages[this.messages.length - 1].message + obj.token;
                this.scrollToBottom();
              } else if (obj.answer) {
                console.log(obj.answer);
                this.messages[this.messages.length - 1].message = obj.answer;
              }
              if (obj.intents && obj.intents.length > 0) {
                console.log(obj);
                let toAttach = "Recommendations:\n";
                toAttach += obj.intents
                  .map((intent) => {
                    console.log(intent);
                    console.log(this.products[intent.id]);
                    return (
                      this.products[intent.id].name +
                      ": " +
                      this.products[intent.id].intent
                    );
                  })
                  .join("\n");
                this.appendMessage("Bot", { message: toAttach });
              }
            }
          });
      }
      this.$refs.sendBtn.disabled = false;
    },
    handleKeyPress: function (event) {
      if (event.keyCode === 13) {
        // 按下回车键
        this.sendMessage();
      }
    },
  },
};
</script>

<style scoped>
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
fieldset {
  border-width: 0px;
  display: contents;
}
.controls {
  font-family: Arial, sans-serif;
  font-size: smaller;
}
#userInput {
  width: 400px;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 14px;
}
.thresholdBar {
  width: 400px;
  padding: 5px;
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
.bot {
  color: #28a745;
  float: left;
  background-color: #e6ffe6;
}
.bot::before {
  content: "User";
  position: absolute;
  top: -15px;
  left: 10px;
  font-size: 10px;
  color: #666;
}
.user {
  color: #007bff;
  float: right;
  background-color: #e6f2ff;
}
.user::before {
  content: "Bot";
  position: absolute;
  top: -15px;
  right: 10px;
  font-size: 10px;
  color: #666;
}
</style>