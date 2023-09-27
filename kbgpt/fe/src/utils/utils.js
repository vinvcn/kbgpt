export function get_base_url() {
  if (process.env.VUE_APP_ACTIVE_PROFILE === "DEFAULT") {
    return "http://localhost:8081";
  } else if (process.env.VUE_APP_ACTIVE_PROFILE === "FAT") {
    return "http://py-kbgpt.testbs.surfin.sg";
  } else if (process.env.VUE_APP_ACTIVE_PROFILE === "PRE") {
    return "http://py-kbgpt-pre.bullsmart.in";
  } else if (process.env.VUE_APP_ACTIVE_PROFILE === "PRO") {
    return "http://py-kbgpt.bullsmart.in";
  } else
    alert(
      `env not set correctly: VUE_APP_ACTIVE_PROFILE==${process.env.VUE_APP_ACTIVE_PROFILE}`
    );
}
