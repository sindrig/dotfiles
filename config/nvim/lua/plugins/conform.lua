return {
  {
    "stevearc/conform.nvim",
    opts = {
      formatters_by_ft = {
        python = { "ruff_fix", "ruff_format" },
        typescript = { "prettier" },
        vue = { "prettier" },
      },
      formatters = {
        ruff_fix = {
          command = "ruff",
          args = { "check", "--fix", "--stdin-filename", "$FILENAME", "-" },
          stdin = true,
        },
      },
    },
  },
}
