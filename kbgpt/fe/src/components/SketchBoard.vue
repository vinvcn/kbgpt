<template>
  <div></div>
</template>
  
  
  <script>
export default {
  name: "SketchBoard",
  data: function () {
    return {
      subgraph1: {
        sel: {
          selectors: [
            { node: "embed_question", key: "result", to_key: "embedding" },
            { node: "search_context", key: "result", to_key: "context" },
            { node: "is_context_related", key: "result", to_key: "is_related" },
          ],
          mode: "all",
        },
        nodes: {
          embed_question: {
            node: {
              engine: {
                type: "embed_engine",
                key_and_labels: { question: "" },
              },
              frm: {
                selectors: [{ node: "seed", key: "question", to_key: "" }],
                mode: "all",
              },
              sel: {},
              pre: null,
              post: null,
            },
            trigger: 0,
          },
          search_context: {
            node: {
              engine: {
                type: "similarity_search_engine",
                index: "bullsmart-customer-services",
                k: 3,
                min_threshold: null,
              },
              frm: {
                selectors: [
                  {
                    node: "embed_question",
                    key: "result",
                    to_key: "embedding",
                  },
                ],
                mode: "all",
              },
              sel: {},
              pre: null,
              post: null,
            },
            trigger: 0,
          },
          is_context_related: {
            node: {
              engine: {
                type: "jinja_engine",
                stream: false,
                temperature: 0.0,
                keys_in: ["question", "context"],
                models: ["gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
                name: "qa.is_context_related",
                persist_level: "info",
                client_style: "native",
              },
              frm: {
                selectors: [
                  { node: "seed", key: "question", to_key: "" },
                  { node: "search_context", key: "result", to_key: "context" },
                ],
                mode: "all",
              },
              sel: {},
              pre: null,
              post: null,
            },
            trigger: 0,
          },
        },
      },
    };
  },
  created: function () {},
  beforeRouteLeave: function () {},
  methods: {},
};
</script>
  
  <style scoped>
</style>