return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      inlay_hints = { enabled = false },
      servers = {
        -- pyright = false,
        -- basedpyright = false,
        -- ty = {
        --   settings = {
        --     ty = {
        --       inlayHints = {
        --         variableTypes = false,
        --         callArgumentNames = false,
        --         functionReturnTypes = false,
        --       },
        --     },
        --   },
        -- },
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
