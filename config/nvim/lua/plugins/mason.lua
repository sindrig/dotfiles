return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        pyright = false,
        basedpyright = false,
        -- ty = {
        --   -- If lspconfig has a built-in 'ty' server entry, this will work.
        --   -- Otherwise, use the fallback autostart below.
        --   -- cmd = { "ty", "server" },
        --   settings = { ty = {} },
        -- },
      },
    },
  },
}
