return {
    "neovim/nvim-lspconfig",
    dependencies = {
        "hrsh7th/cmp-nvim-lsp",
    },
    config = function()
        local lspconfig = require("lspconfig")
        local capabilities = require("cmp_nvim_lsp").default_capabilities()
        local keymaps = require("config.keymaps")

        local on_attach = function(client, bufnr)
            keymaps.lsp_keymaps(bufnr)
        end

        lspconfig.omnisharp.setup({
            capabilities = capabilities,
            on_attach = on_attach,
            cmd = { "omnisharp", "--languageserver", "--hostPID", tostring(vim.fn.getpid()) },
            settings = {
                FormattingOptions = {
                    EnableEditorConfigSupport = true,
                },
                RoslynExtensionsOptions = {
                    EnableAnalyzersSupport = true,
                },
            },
        })

        lspconfig.gopls.setup({
            capabilities = capabilities,
            on_attach = on_attach,
            settings = {
                gopls = {
                    analyses = {
                        unusedparams = true,
                    },
                    staticcheck = true,
                },
            },
        })

        lspconfig.rust_analyzer.setup({
            capabilities = capabilities,
            on_attach = on_attach,
            settings = {
                ["rust-analyzer"] = {
                    checkOnSave = {
                        command = "clippy",
                    },
                    diagnostics = {
                        enable = true,
                    },
                },
            },
        })
    end,
}
